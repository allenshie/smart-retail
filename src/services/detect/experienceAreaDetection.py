import cv2
import time
import requests
import numpy as np  
from typing import List
from src.config.config import *
from src.utils.utils import utils
from src.services.decorator.decorator import time_logger
from src.services.database.ChairService import ChairService
from src.services.detect.experienceArea.cameraContext import CameraContext
from src.services.detect.experienceArea.detection_service import DetectionService
from src.services.detect.experienceArea.chair_manager import ChairManager, ChairStateEvent, ChairStateChange
from src.views.view import View
from src.services.lib.loggingService import log

class ExperienceAreaDetection:
    def __init__(self) -> None:
        self.detection_service = DetectionService(
            chair_context=chair_context,
            pillow_context=pillow_context,
            person_context=pose_person_context,
            reid_context=reid_context
        )
        self.chair_manager = ChairManager(data_ttl=300)
        self.view = View()
        self.product_dict = {
            "hands": "product_1",
            "pinto": "product_2", 
            "balance_on": "product_3",
            "cosios": "product_4",
            "doctor_air": "product_5",
        }
        self.camera_contexts = dict()
        self._visualization_windows = set()
        
    def __del__(self):
        """確保資源正確釋放"""
        self.cleanup_visualization()

    def cleanup_visualization(self):
        """清理所有已創建的視窗"""
        try:
            # 關閉所有已創建的視窗
            for window_name in self._visualization_windows:
                cv2.destroyWindow(window_name)
            self._visualization_windows.clear()
            
            # 確保所有窗口都被處理
            cv2.waitKey(1)
        except Exception as e:
            log.error(f"清理視覺化窗口時發生錯誤: {str(e)}")

    def get_camera_context(self, cameraId: str):
        if cameraId not in self.camera_contexts:
            self.camera_contexts[cameraId] = CameraContext()
        return self.camera_contexts[cameraId]

    @time_logger
    def detect(self, cameraId: str, image: np.ndarray, products_of_interest: list):
        chairs, pillows, persons = self.detection_service.detect(cameraId=cameraId, image=image)

        # 更新椅子信息
        self.chair_manager.update_chairs_info(
            camera_id=cameraId,
            chairs=chairs,
            persons=persons,
        )
        
        # 更新椅子類型和椅墊匹配
        self.chair_manager.update_chair_types(cameraId, pillows, persons)

        
        # 更新椅子狀態並獲取狀態變更事件
        state_events = self.chair_manager.update_chair_status(
            camera_id=cameraId,
            persons=persons,
            pillows=pillows,
            products_of_interest=products_of_interest
        )
        
        # 處理所有狀態變更事件
        for event in state_events:
            self._notify_state_change(event)
        
        # 如果啟用了視覺化，更新顯示
        if VISUAL:
            self.visual(cameraId, image, pillows, persons)  
        
        return chairs, pillows, persons
    
    def _notify_state_change(self, event: ChairStateEvent):
            """處理椅子狀態變更通知"""
            try:
                payload = {
                    'camera_id': event.camera_id,
                    'product_id': self.product_dict.get(event.chair_type),
                    'is_using': event.state_change == ChairStateChange.OCCUPIED
                }
                api_url = f"http://{NotificationENDPOINT}/experience-event"
                
                response = requests.post(api_url, json=payload)
                if response.status_code == 200:
                    log.info(f"Successfully notified status change for camera {event.camera_id} "
                        f"and chair {event.chair_type}")
                else:
                    log.error(f"Failed to send notification: status code {response.status_code}")
            except Exception as e:
                log.error(f"Error sending notification: {str(e)}")
                
    def visual(self, cameraId: str, image: np.ndarray, 
              pillows: List[dict], persons: List[dict]):
        """
        視覺化檢測結果
        Args:
            cameraId: 攝像頭ID
            image: 原始圖像
            pillows: 檢測到的椅墊列表
            persons: 檢測到的人物列表
        """
        try:
            # 從 ChairManager 獲取椅子信息
            chairs = self.chair_manager.get_camera_chairs(cameraId)
            
            # 添加到已創建視窗集合中
            self._visualization_windows.add(cameraId)
            
            # 視覺化處理
            self.view.visualExperienceArea(
                image=image,
                pillows=pillows,
                chairs=chairs,
                persons=persons
            )
            # 調整顯示大小和更新窗口
            resized_image = cv2.resize(image, (1440, 960))
            cv2.imshow(cameraId, resized_image)
            cv2.waitKey(1)
            
        except Exception as e:
            log.error(f"視覺化過程中發生錯誤: {str(e)}")
            self.cleanup_visualization()
            

 

