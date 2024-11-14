import time
import requests
import numpy as np  
from src.config.config import *
from src.utils.utils import utils
from src.services.decorator.decorator import time_logger
from src.services.database.ChairService import ChairService
from src.services.detect.experienceArea.detection_service import DetectionService
from src.services.detect.experienceArea.chair_manager import ChairManager

class ExperienceAreaDetection:
    def __init__(self) -> None:
        self.detection_service = DetectionService(
            chair_context=chair_context,
            pillow_context=pillow_context,
            person_context=experience_person_context,
            reid_context=reid_context
        )
        self.chair_manager = ChairManager()
        self.product_dict = {
            "hands": "product_1",
            "pinto": "product_2", 
            "balance_on": "product_3",
            "cosios": "product_4",
            "doctor_air": "product_5",
        }

    @time_logger
    def detect(self, cameraId: str, image: np.ndarray):
        chairs, pillows, persons = self.detection_service.detect(cameraId=cameraId, image=image)
        dont_update = self.is_chair_overlapped_by_person(cameraId=cameraId, person_outputs=persons)
        
        # 1. 先進行椅子和座墊的匹配，並更新椅子的 type
        chairs = self.chair_manager.assign_chair_types(chairs=chairs, pillows=pillows)
        
        chairs_to_update = []  # 用於批量更新的椅子列表
        
        # 2. 遍歷椅子，判斷是否需要更新類型、位置和狀態
        for chair in chairs:
            chair_id = chair['id']
            position = chair['bbox']

            # 從資料庫中查詢該椅子是否已存在（根據 chair_id 和 camera_id）
            existing_chair = ChairService.get_chair_by_id(chair_id, cameraId)

            if existing_chair:
                # 更新位置
                chair['bbox'] = position

                # 判斷是否需要更新 type
                if existing_chair.type is None and chair['type'] is not None:
                    # 更新 type
                    chair['type'] = chair['type']  # 這裡的類型已經在 assign_chair_types 中確定
            else:
                # 如果是新椅子，註冊到資料庫
                if not dont_update:
                    ChairService.register_chair(chair_id, position, cameraId, chair['type'], state='idle')

            # 將要更新的椅子放入列表
            chairs_to_update.append(chair)

        # 3. 最後批量更新狀態
        self.chair_manager.update_chair_status(cameraId=cameraId, person_outputs=persons)

        # 4. 將最終結果批量更新到資料庫
        if not dont_update:
            for chair in chairs_to_update:
                ChairService.update_chair_position(chair['id'], chair['bbox'], cameraId, chair['type'])

        return chairs, pillows, persons
    
    def is_chair_overlapped_by_person(self, cameraId: str, person_outputs, iou_threshold=0.3):
        """
        根據 cameraId 從資料庫獲取椅子資訊，並與當前幀行人輸出進行比對。
        如果有椅子與行人有交集，返回 True，否則返回 False。

        :param cameraId: 相機 ID，用來從資料庫中篩選對應的椅子
        :param person_outputs: 當前幀中的行人檢測結果，包含每個行人的邊界框 (bbox)
        :param iou_threshold: IoU 閾值，超過該值認為有交集
        :return: True 如果有任意椅子與行人有交集，False 如果無交集
        """
        # 從資料庫中獲取屬於該 cameraId 的所有椅子
        chairs_in_db = ChairService.get_camera_chairs(cameraId)

        # 遍歷資料庫中的椅子，與行人輸出進行交集檢查
        for chair in chairs_in_db:
            chair_bbox = eval(chair.position)  # 將儲存在資料庫中的 position 轉為 [x1, y1, x2, y2]

            for person in person_outputs:
                person_bbox = person['bbox']
                iou = utils.calculate_iou(chair_bbox, person_bbox)  # 計算 IoU

                if iou >= iou_threshold:
                    return True  # 只要有交集，立即返回 True

        return False  # 如果沒有任何交集，返回 False

    def process_chairs(self, chair_status_history):
        """
        處理椅子的狀態變更，並在狀態變更時通報外部API。
        """
        chairs_from_db = ChairService.get_all_chairs()
        for chair in chairs_from_db:
            chair_id = chair['id']
            camera_id = chair['camera_id']  # 從 chair 直接獲取 camera_id
            current_state = chair['state']
            chair_type = chair['type']
            # 使用 camera_id 和 chair_id 組合作為唯一標識
            unique_key = f"{camera_id}_{chair_id}"
            
            # 檢查這個椅子是否有之前的狀態記錄
            previous_state = chair_status_history.get(unique_key, None)

            # 如果狀態變為 is_use，進行通報
            if current_state == 'in_use' and (previous_state is None or previous_state != 'in_use'):
                self.notify_external_api(chair_type=chair_type, camera_id=camera_id, is_using=True)
                # time.sleep(5)
                    
            # 如果狀態從 is_use 變為 idle，進行通報
            elif current_state == 'idle' and previous_state == 'in_use':
                self.notify_external_api(chair_type=chair_type, camera_id=camera_id, is_using=False)
                # time.sleep(5)

            # 更新椅子的狀態記錄
            chair_status_history[unique_key] = current_state

    def notify_external_api(self, chair_type, camera_id, is_using):
        """
        通報外部API，報告椅子的狀態變更。
        """
        if self.product_dict.get(chair_type):
            
            payload = {
                'camera_id': camera_id,
                'product_id': self.product_dict.get(chair_type),
                'is_using': is_using
            }
            api_url = f"http://{NotificationENDPOINT}/experience-event"
            
            try:
                response = requests.post(api_url, json=payload)
                if response.status_code == 200:
                    print(f"Notification sent successfully for camera {camera_id} and chair {chair_type}")
                else:
                    print(f"Failed to send notification for camera {camera_id} and chair {chair_type}")
            except Exception as e:
                print(f"Error sending notification: {e}")