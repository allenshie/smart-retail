import time
from src.utils.utils import utils

class CameraContext:
    def __init__(self):
        self.objects_dict = {}
        self.roi_info_dict = {}

    def update_objects(self, objects):
        for obj in objects:
            obj_id = obj.get("id")
            self.objects_dict[obj_id] = {
                "object": obj,
                "time": time.time()
            }
        self.cleanup_expired_objects(timeout=300)
        
    def update_rois(self, ROIs_info):
        for ROI in ROIs_info:
            roi_id = ROI['id']
            bbox = utils.find_min_bounding_box(points=ROI['position'])
            self.roi_info_dict[roi_id] = bbox
            
    def cleanup_expired_objects(self, timeout: int=180):
        """
        清理超時的物件。
        :param timeout: 超時的時間（秒），預設為180秒。
        """
        current_time = time.time()
        expired_keys = [
            obj_id for obj_id, obj_data in self.objects_dict.items()
            if current_time - obj_data["time"] > timeout
        ]

        for obj_id in expired_keys:
            del self.objects_dict[obj_id]

        # 返回移除的物件數量，方便日誌記錄或調試
        return len(expired_keys)
            
    