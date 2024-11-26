import time

class CameraContext:
    def __init__(self):
        self.objects_dict = {}

    def update_chairs(self, chairs):
        for chair in chairs:
            obj_id = chair.get("id")
            self.objects_dict[obj_id] = {
                "object": chair,
                "time": time.time()
            }
        self.cleanup_expired_objects(timeout=300)

            
    def cleanup_expired_objects(self, timeout: int=300):
        """
        清理超時的物件。
        :param timeout: 超時的時間（秒），預設為300秒。
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
            
    