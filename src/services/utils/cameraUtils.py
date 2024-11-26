import cv2
import requests
import threading
import queue
import time
from typing import Dict, Optional, Any
import numpy as np
from dataclasses import dataclass
from src.services.lib.loggingService import log
from src.config.config import GetCameraInfoENDPOINT

@dataclass
class FrameData:
    timestamp: float
    image: np.ndarray
    camera_id: str
    metadata: Dict[str, Any]

def fetch_camera_area(type: str) -> Optional[Dict[str, Any]]:
    """訪問 /camera-area API 並獲取對應的輸出"""
    url = f"http://{GetCameraInfoENDPOINT}/camera-area"
    params = {"type": type}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        log.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        log.error(f"An error occurred: {err}")
        return None

class CameraManager:
    def __init__(self, buffer_size: int = 30):
        self._streams: Dict[str, dict] = {}
        self._running = False
        self._capture_thread = None
        self._frame_buffers: Dict[str, queue.Queue] = {}
        self._buffer_size = buffer_size
        self._lock = threading.Lock()
        self._camera_errors: Dict[str, int] = {}
        self.MAX_RETRY_ATTEMPTS = 3

    def initialize_camera(self, camera_id: str, rtsp_url: str, metadata: Dict[str, Any] = None) -> bool:
        """初始化單個攝影機"""
        with self._lock:
            if camera_id not in self._streams:
                self._streams[camera_id] = {
                    'url': rtsp_url,
                    'cap': None,
                    'metadata': metadata or {},
                    'last_frame_time': 0
                }
                self._frame_buffers[camera_id] = queue.Queue(maxsize=self._buffer_size)
                self._camera_errors[camera_id] = 0
                return True
            return False

    def initialize_cameras(self, camera_info: Dict[str, Any]) -> None:
        """初始化多個攝影機"""
        for camera_id, info in camera_info.items():
            self.initialize_camera(
                camera_id=camera_id,
                rtsp_url=info['meta']['rtsp_url'],
                metadata=info
            )

    def release_camera(self, camera_id: str) -> bool:
        """釋放單個攝影機資源"""
        with self._lock:
            if camera_id in self._streams:
                if self._streams[camera_id]['cap']:
                    self._streams[camera_id]['cap'].release()
                del self._streams[camera_id]
                del self._frame_buffers[camera_id]
                del self._camera_errors[camera_id]
                return True
            return False

    def release_all_cameras(self) -> None:
        """釋放所有攝影機資源"""
        with self._lock:
            camera_ids = list(self._streams.keys())
            for camera_id in camera_ids:
                self.release_camera(camera_id)

    def _initialize_capture(self, camera_id: str) -> bool:
        """初始化攝影機擷取"""
        try:
            cap = cv2.VideoCapture(self._streams[camera_id]['url'])
            if not cap.isOpened():
                self._camera_errors[camera_id] += 1
                log.error(f"無法連接攝影機 {camera_id}, 重試次數: {self._camera_errors[camera_id]}")
                return False
            
            # 設置緩衝區大小
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self._streams[camera_id]['cap'] = cap
            self._camera_errors[camera_id] = 0  # 重置錯誤計數
            return True
        except Exception as e:
            self._camera_errors[camera_id] += 1
            log.error(f"初始化攝影機 {camera_id} 時發生錯誤: {str(e)}")
            return False

    def _capture_frames(self):
        """在獨立線程中持續擷取影像"""
        while self._running:
            with self._lock:
                streams_copy = self._streams.copy()

            for camera_id, stream_info in streams_copy.items():
                try:
                    if self._camera_errors[camera_id] >= self.MAX_RETRY_ATTEMPTS:
                        log.error(f"攝影機 {camera_id} 重試次數過多，暫時停止嘗試")
                        continue

                    cap = stream_info['cap']
                    if cap is None or not cap.isOpened():
                        if not self._initialize_capture(camera_id):
                            continue

                    ret, frame = cap.read()
                    if not ret:
                        self._camera_errors[camera_id] += 1
                        log.warning(f"無法讀取攝影機 {camera_id} 的影像，重試次數: {self._camera_errors[camera_id]}")
                        if self._initialize_capture(camera_id):
                            continue
                        continue

                    current_time = time.time()
                    frame_data = FrameData(
                        timestamp=current_time,
                        image=frame,
                        camera_id=camera_id,
                        metadata=stream_info['metadata']
                    )

                    # 如果緩衝區滿了，移除最舊的影像
                    if self._frame_buffers[camera_id].full():
                        try:
                            self._frame_buffers[camera_id].get_nowait()
                        except queue.Empty:
                            pass

                    self._frame_buffers[camera_id].put_nowait(frame_data)
                    stream_info['last_frame_time'] = current_time

                except queue.Full:
                    continue
                except Exception as e:
                    log.error(f"處理攝影機 {camera_id} 時發生錯誤: {str(e)}")
                    self._camera_errors[camera_id] += 1

            # 短暫休息以避免CPU過載
            time.sleep(0.001)

    def start_capture(self):
        """啟動影像擷取線程"""
        if not self._running:
            self._running = True
            self._capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
            self._capture_thread.start()
            log.info("攝影機串流服務已啟動")

    def stop_capture(self):
        """停止影像擷取線程"""
        self._running = False
        if self._capture_thread:
            self._capture_thread.join(timeout=5)
        self.release_all_cameras()
        log.info("攝影機串流服務已停止")

    def get_latest_frame(self, camera_id: str, timeout: float = 1.0) -> Optional[FrameData]:
        """獲取最新的影像"""
        try:
            if camera_id in self._frame_buffers:
                return self._frame_buffers[camera_id].get(timeout=timeout)
        except queue.Empty:
            pass
        return None

    def get_frame_delay(self, camera_id: str) -> float:
        """獲取當前影像延遲時間（秒）"""
        with self._lock:
            if camera_id in self._streams:
                last_frame_time = self._streams[camera_id]['last_frame_time']
                if last_frame_time > 0:
                    return time.time() - last_frame_time
        return float('inf')

    def update_camera_metadata(self, camera_id: str, metadata: Dict[str, Any]) -> None:
        """更新攝影機元數據"""
        with self._lock:
            if camera_id in self._streams:
                self._streams[camera_id]['metadata'].update(metadata)

    def get_camera_status(self, camera_id: str) -> Dict[str, Any]:
        """獲取攝影機狀態信息"""
        with self._lock:
            if camera_id in self._streams:
                return {
                    'is_connected': self._streams[camera_id]['cap'] is not None,
                    'error_count': self._camera_errors[camera_id],
                    'last_frame_delay': self.get_frame_delay(camera_id),
                    'metadata': self._streams[camera_id]['metadata']
                }
        return {}