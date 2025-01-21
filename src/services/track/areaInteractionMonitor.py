import time
import requests
import numpy as np  
from src.utils.utils import utils
from src.services.lib.loggingService import log
from src.config.config import NotificationENDPOINT, EXIT_THRESHOLD, CHECK_DURATION, NOT_EXIST_THRES, SSIM_THRESHOLD, MASK_SIMILARITY_THRESHOLD
from skimage.metrics import structural_similarity as ssim

class AreaInteractionMonitor:
    def __init__(self, area_bbox, mobilesam_model, exit_threshold: int=EXIT_THRESHOLD, check_duration: int=CHECK_DURATION):
        """
        :param area_bbox: 定义的区域边界框，格式为 [x1, y1, x2, y2]
        :param check_duration: 检查物品消失的时间窗口
        """
        self.area_bbox = area_bbox
        self.exit_threshold = exit_threshold
        self.check_duration = check_duration
        self.not_exist_thres = NOT_EXIST_THRES
        self.person_data = {}
        self.objects_dict = {}
        self.last_check_time = None
        self.active_intersections = []
        self.origin_frame = None
        self.mobilesam_model = mobilesam_model
        self.notification_count = 0  # 新增：通知計數器    
    
    def process_person(self, persons: list):
        for person in persons:
            visited = False
            person_id = person['id']
            person_bbox = person['bbox']
        
            intersection = self.get_intersection(self.area_bbox, person_bbox)
            if intersection:
                visited = True
                self.active_intersections.append(intersection)
                self.last_check_time = None  # 如果有人进入，重置全局计时器
                if person_id not in self.person_data:
                    self.person_data[person_id] = {
                        'max_area_bbox': intersection,
                        'in_area': True,
                        'exit_timer': None
                    }
                else:
                    self.person_data[person_id]['max_area_bbox'] = utils.merge_bboxes(
                        self.person_data[person_id]['max_area_bbox'], intersection)
                    self.person_data[person_id]['in_area'] = True
                    self.person_data[person_id]['exit_timer'] = None
                
            person.update({"visited": visited})
        print(self.person_data, '==============123')
        return [person_info['max_area_bbox'] for person_info in self.person_data.values()]

    def monitor_area_interaction(self, persons: list, current_frame: np.ndarray):
        if self.person_data:
            current_persons_dict = {person['id']: person['visited'] for person in persons}
            for person_id, info in self.person_data.items():
                if not current_persons_dict.get(person_id):
                    if info['exit_timer'] is None:
                        info['exit_timer'] = time.time()
                    elif time.time()-info['exit_timer']>self.exit_threshold:
                        info['in_area'] = False
                        
            if not any(data['in_area'] for data in self.person_data.values()):
                if self.last_check_time is None:
                    # print("start========================"); time.sleep(1)
                    self.last_check_time = time.time()
        else:
            self.origin_frame = current_frame   
            # print("更新origin_frame")
            
    def update_objects(self, camera_id, area_id, current_frame, current_time, objects_dict):
        self.objects_dict = objects_dict
        if self.last_check_time:
            print(f'=================計時秒數為：{current_time - self.last_check_time}')
        if self.last_check_time and (current_time - self.last_check_time > self.check_duration):
            self.notification_count = 0  # 重置通知計數器
            # 检查物品丢失
            missing_detected = self.check_missing_objects(current_time=current_time, camera_id=camera_id, area_id=area_id, current_frame=current_frame)
            self.reset_monitoring()
            return missing_detected
        return False

    def second_check(self, current_frame, obj_bbox):
        """
        二次檢查機制：使用 SSIM 和 MobileSAM 檢查是否為誤報。
        :param current_frame: 當前幀圖像
        :param obj_bbox: 物件的邊界框 [x1, y1, x2, y2]
        :return: 是否為真實丟失（True: 丟失，False: 誤報）
        """
        if self.origin_frame is None:
            log.warning("Origin frame is not set. Skipping second check.")
            return False

        # 提取 ROI 區域
        x1, y1, x2, y2 = map(int, obj_bbox)
        origin_roi = self.origin_frame[y1:y2, x1:x2]
        current_roi = current_frame[y1:y2, x1:x2]

        # 計算 SSIM
        ssim_score, _ = ssim(origin_roi, current_roi, full=True, channel_axis=-1)
        log.info(f"SSIM score: {ssim_score}")

        # 使用 MobileSAM 計算 Mask 相似度
        origin_mask = self.mobilesam_model.detect(self.origin_frame, bbox=[x1, y1, x2, y2], label=[1])
        current_mask = self.mobilesam_model.detect(current_frame, bbox=[x1, y1, x2, y2], label=[1])
        mask_similarity = utils.compare_masks(origin_mask, current_mask)
        log.info(f"Mask similarity: {mask_similarity}")

        # 判定是否為真實丟失
        if ssim_score < SSIM_THRESHOLD or mask_similarity < MASK_SIMILARITY_THRESHOLD:
            log.info("Object confirmed as missing.")
            return True
        
        log.info("Object misdetection confirmed.")
        return False

    def check_missing_objects(self, camera_id, area_id, current_time, current_frame):
        """
        检查物品是否消失，并在必要时通知外部API。
        :param current_time: 当前时间戳
        :param camera_id: 相机ID
        :param area_id: 区域ID
        :return: 是否检测到物品丢失
        """
        missing_detected = False
        for id, info in self.objects_dict.items():
            if self.notification_count >= 3:  # 限制每次最多通知三次
                log.info(f"Notification limit reached for Camera {camera_id}, Area {area_id}.")
                break
            
            object_bbox = info.get('object').get('bbox')
            last_time = info.get('time')
            # 检查物品是否在任何人的最大交互区域内
            is_in_interaction_area = any(
                utils.calculate_iou(object_bbox, person_info['max_area_bbox']) > 0
                for person_info in self.person_data.values()
            )
            if is_in_interaction_area:
                if current_time - last_time > self.not_exist_thres:
                    if self.second_check(current_frame, object_bbox) and info.get('notified') is None:     
                        print(f"{camera_id} 區域{area_id}的商品{id}被拿走了！！")
                        self.notify_external_api(camera_id, area_id)
                        # time.sleep(5)
                        info.update({'notified': True})
                        self.notification_count += 1  # 增加通知計數器
                        missing_detected = True
                        
        return missing_detected

    def reset_monitoring(self):
        self.person_data.clear()
        self.active_intersections.clear()
        self.last_check_time = None
        # self.objects_dict.clear()
        print('==========================清除資料')

    def notify_external_api(self, camera_id: str, area_id: str):
        """
        访问外部API通报『促销区』的商品数量有减少。
        """
        if not NotificationENDPOINT:
            print("Notification endpoint is not set.")
            return

        payload = {
            'camera_id': camera_id,
            'area_id': area_id,
        }
        api_url = f"http://{NotificationENDPOINT}/promotion-event"

        try:
            response = requests.post(api_url, json=payload)

            if response.status_code == 200:
                print(f"Notification sent successfully for camera {camera_id} and area_id {area_id}")
            else:
                print(f"Failed to send notification for camera {camera_id} and area_id {area_id}")

        except Exception as e:
            print(f"Error sending notification: {e}")
            
    def get_intersection(self, roi, person_bbox):
        """
        计算 ROI 和 person 边界框的交集区域（矩形）。
        :param roi: ROI 的坐标 [x1_roi, y1_roi, x2_roi, y2_roi]
        :param person_bbox: person 边界框的坐标 [x1_person, y1_person, x2_person, y2_person]
        :return: 交集矩形的坐标 [x1, y1, x2, y2]，如果没有交集则返回 None
        """
        x1_roi, y1_roi, x2_roi, y2_roi = roi
        x1_person, y1_person, x2_person, y2_person = person_bbox

        # 计算交集矩形的左上角和右下角
        x1_intersection = max(x1_roi, x1_person)
        y1_intersection = max(y1_roi, y1_person)
        x2_intersection = min(x2_roi, x2_person)
        y2_intersection = min(y2_roi, y2_person)

        # 检查是否有交集
        if x1_intersection < x2_intersection and y1_intersection < y2_intersection:
            return [x1_intersection, y1_intersection, x2_intersection, y2_intersection]
        else:
            return None  # 无交集


    def update_intersection_bbox(self, existing_bbox, new_bbox):
        """
        更新交集区域，扩展矩形以包含新的交集区域。
        :param existing_bbox: 当前的交集矩形 [x1, y1, x2, y2]
        :param new_bbox: 新的交集矩 [x1, y1, x2, y2]
        :return: 更新后的包含所有交集的最小外接矩形
        """
        x1_min = min(existing_bbox[0], new_bbox[0])
        y1_min = min(existing_bbox[1], new_bbox[1])
        x2_max = max(existing_bbox[2], new_bbox[2])
        y2_max = max(existing_bbox[3], new_bbox[3])
        
        return [x1_min, y1_min, x2_max, y2_max]