from fastapi import HTTPException
from src.services.lib.loggingService import log
from src.models.requests import ExperienceAreaRequest
from src.services.lib.processManager import ProcessManager
from src.services.utils.cameraUtils import fetch_camera_area, CameraManager, FrameData
from src.services.monitoring.healthCheck import HealthChecker
from src.config.config import VISUAL
import threading
import signal
import queue
from typing import Optional
import time

class ExperienceAreaHandler:
    def __init__(self, detection_service, process_pool, frame_buffer):
        self.detection_service = detection_service
        self.frame_buffer = frame_buffer
        self.process_manager = None
        self.health_checker = HealthChecker()

    @staticmethod
    def _run_experience_area(stop_event, shared_state):
        """
        靜態方法用於在子進程中運行，避免傳遞類實例
        """
        try:
            # 在子進程中創建所需的對象
            from src.services.detect.experienceAreaDetection import ExperienceAreaDetection
            from src.services.monitoring.healthCheck import HealthChecker
            from src.services.utils.cameraUtils import CameraManager, fetch_camera_area
            
            detector = ExperienceAreaDetection()
            health_checker = HealthChecker()
            camera_manager = CameraManager(buffer_size=30)
            frame_queue = queue.Queue(maxsize=30)
            shutdown_event = threading.Event()
            
            # 設置信號處理
            def signal_handler(signum, frame):
                log.info(f"收到信號 {signum}，開始清理資源...")
                shutdown_event.set()
            
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)

            def process_frames():
                """影像擷取線程"""
                log.info("影像擷取線程已啟動")
                try:
                    while not (stop_event.is_set() or shutdown_event.is_set()):
                        try:
                            system_load = health_checker.get_system_load()
                            process_rate = 2 if system_load["cpu_percent"] > 80 else 1

                            for camera_id in list(camera_manager._streams.keys()):
                                if stop_event.is_set() or shutdown_event.is_set():
                                    return

                                frame_data = camera_manager.get_latest_frame(camera_id, timeout=0.05)
                                if not frame_data:
                                    continue

                                try:
                                    frame_queue.put(frame_data, timeout=0.1)
                                except queue.Full:
                                    try:
                                        frame_queue.get_nowait()
                                        frame_queue.put(frame_data, timeout=0.1)
                                    except (queue.Empty, queue.Full):
                                        pass

                            threading.Event().wait(0.001 * process_rate)

                        except Exception as e:
                            log.error(f"處理幀時發生錯誤: {str(e)}")
                            if stop_event.is_set() or shutdown_event.is_set():
                                return
                            threading.Event().wait(0.1)

                except Exception as e:
                    log.error(f"影像擷取線程發生錯誤: {str(e)}")
                finally:
                    log.info("影像擷取線程已退出")

            def analyze_frames():
                """影像分析線程"""
                log.info("影像分析線程已啟動")
                try:
                    while not (stop_event.is_set() or shutdown_event.is_set()):
                        try:
                            frame_data = frame_queue.get(timeout=0.1)
                            if frame_data is None:
                                continue

                            products_of_interest = frame_data.metadata.get('product_list', [])
                            products_of_interest = [p['name'] for p in products_of_interest]

                            chairs, pillows, persons = detector.detect(
                                cameraId=frame_data.camera_id,
                                image=frame_data.image,
                                products_of_interest=products_of_interest
                            )

                            if VISUAL and not (stop_event.is_set() or shutdown_event.is_set()):
                                detector.visual(
                                    cameraId=frame_data.camera_id,
                                    image=frame_data.image,
                                    pillows=pillows,
                                    persons=persons
                                )

                        except queue.Empty:
                            continue
                        except Exception as e:
                            log.error(f"分析幀時發生錯誤: {str(e)}")
                            if stop_event.is_set() or shutdown_event.is_set():
                                return
                            threading.Event().wait(0.1)

                except Exception as e:
                    log.error(f"影像分析線程發生錯誤: {str(e)}")
                finally:
                    log.info("影像分析線程已退出")

            def cleanup_resources():
                """清理資源"""
                log.info("開始清理資源...")
                shutdown_event.set()
                
                if detector:
                    try:
                        detector.cleanup_visualization()
                    except Exception as e:
                        log.error(f"清理視覺化窗口時發生錯誤: {str(e)}")
                
                if camera_manager:
                    try:
                        log.info("正在停止相機串流...")
                        camera_manager.stop_capture()
                    except Exception as e:
                        log.error(f"停止相機串流時發生錯誤: {str(e)}")
                
                while not frame_queue.empty():
                    try:
                        frame_queue.get_nowait()
                    except queue.Empty:
                        break
                
                log.info("資源清理完成")

            try:
                # 獲取相機資訊
                experience_area_info = fetch_camera_area(type='experience')
                if not experience_area_info:
                    log.error("未能獲取相機資訊，請檢查服務狀態。")
                    return

                # 初始化所有相機
                camera_manager.initialize_cameras(experience_area_info)
                camera_manager.start_capture()

                # 啟動工作線程
                threads = []
                for thread_func in [process_frames, analyze_frames]:
                    thread = threading.Thread(target=thread_func, daemon=True)
                    thread.start()
                    threads.append(thread)

                # 等待停止信號
                while not stop_event.is_set():
                    try:
                        if shared_state.get('update_requested', False):
                            experience_area_info = fetch_camera_area(type='experience')
                            for camera_id, info in experience_area_info.items():
                                camera_manager.update_camera_metadata(
                                    camera_id=camera_id,
                                    metadata={
                                        'product_list': info['product_list']
                                    }
                                )
                            shared_state['update_requested'] = False
                        time.sleep(0.2)
                    except Exception as e:
                        log.error(f"更新處理時發生錯誤: {str(e)}")
                        if stop_event.is_set():
                            break
                        time.sleep(0.1)

            except Exception as e:
                log.error(f"體驗區監控任務錯誤: {str(e)}")
            finally:
                cleanup_resources()
                log.info("體驗區監控任務已結束")

        except Exception as e:
            log.error(f"子進程執行錯誤: {str(e)}")

    async def handle_request(self, request: ExperienceAreaRequest):
        try:
            if not self.process_manager:
                self.process_manager = ProcessManager(target_function=self._run_experience_area)

            if request.action == "start":
                msg = self.process_manager.start()
                return {"message": msg['message']}
            elif request.action == "stop":
                msg = self.process_manager.stop()
                return {"message": msg['message']}
            else:
                raise HTTPException(status_code=400, detail="Invalid action")
        except Exception as e:
            log.error(f"體驗區狀態操作錯誤: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))