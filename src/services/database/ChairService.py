import time
from src.models.Chair import Chair

class ChairService:
    @staticmethod
    def get_chair_by_id(chair_id: str, camera_id: str):
        """
        根據 chair_id 和 camera_id 從資料庫中查詢椅子。
        """
        return Chair.get_or_none((Chair.chair_id == chair_id) & (Chair.camera_id == camera_id))

    @staticmethod
    def update_chair_position(chair_id: str, position: str, camera_id: str, chair_type: str):
        """
        更新椅子的位置、類型和相機ID。
        """
        chair = Chair.get_or_none((Chair.chair_id == chair_id) & (Chair.camera_id == camera_id))
        if chair:
            chair.position = position
            chair.type = chair_type  # 更新椅子的類型
            chair.last_updated_time = time.time()
            chair.save()

    @staticmethod
    def register_chair(chair_id: str, position: str, camera_id: str, chair_type: str, state: str = 'idle'):
        """
        註冊新椅子到資料庫，包含相機ID和類型。
        """
        current_time = time.time()
        Chair.create(
            chair_id=chair_id,
            position=position,
            camera_id=camera_id,  # 註冊時存入 camera_id
            type=chair_type,      # 註冊時存入椅子的類型
            state=state,
            last_updated_time=current_time
        )

    @staticmethod
    def update_chair_state(chair_id: str, state: str, camera_id: str):
        """
        更新椅子的狀態，根據 chair_id 和 camera_id。
        """
        chair = Chair.get_or_none((Chair.chair_id == chair_id) & (Chair.camera_id == camera_id))
        if chair:
            chair.state = state
            chair.save()

    @staticmethod
    def update_chair_last_updated_time(chair_id: str, last_updated_time: float, camera_id: str):
        """
        更新椅子的 last_updated_time。
        """
        chair = Chair.get_or_none((Chair.chair_id == chair_id) & (Chair.camera_id == camera_id))
        if chair:
            chair.last_updated_time = last_updated_time
            chair.save()

    @staticmethod
    def get_camera_chairs(camera_id: str):
        """
        根據 camera_id 獲取該相機來源的所有椅子資訊。
        """
        return list(Chair.select().where(Chair.camera_id == camera_id))

    @staticmethod
    def get_all_chairs():
        """
        獲取資料庫中所有椅子的資訊。
        """
        return [chair.__data__ for chair in Chair.select()]