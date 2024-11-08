from collections import deque
from src.utils.utils import utils

class ObjectTracker:
    def __init__(self, window_size:int =100, min_avg_appearance: float=0.5, min_area: int=7000):
        """
        :param reid_model: 用于给物件分配ID的ReID模型
        :param fastsam_model: FastSAM模型用于检测物件
        :param window_size: 时间窗口大小，指帧数
        :param min_avg_appearance: 滑动窗口内出现频率的最小平均值
        """
        self.window_size = window_size
        self.min_avg_appearance = min_avg_appearance
        self.min_area = min_area
        self.object_windows = {}  # 用于记录每个物件的滑动窗口

    def initialize_window_for_all_objects(self):
        """
        初始化所有已知物件的滑动窗口，每一帧默认设置为 0
        """
        for object_id in self.object_windows:
            self.object_windows[object_id].append(0)  # 默认设置为 0，表示该帧没有出现

    def update_object_window(self, object_id):
        """
        更新物件的滑动窗口，记录其在当前帧是否出现
        """
        if object_id not in self.object_windows:
            # 初始化滑动窗口为 deque，初始填充0
            self.object_windows[object_id] = deque([0] * self.window_size, maxlen=self.window_size)
        
        # 将当前帧记录为1（出现）
        self.object_windows[object_id][-1] = 1  # 更新最后一位为 1，表示该物件在当前帧出现


    def calculate_average_appearance(self, object_id):
        """
        计算物件在滑动窗口内的平均出现频率
        """
        window = self.object_windows.get(object_id, [])
        if not window:
            return 0  # 如果没有窗口数据，返回0
        return sum(window) / len(window)

    def filter_objects(self, current_objects):
        """
        根据滑动窗口内的出现频率，过滤不稳定的物件
        :param current_objects: 当前帧中所有物件信息
        :return: 经过过滤后的物件列表
        """
        self.initialize_window_for_all_objects()
        filtered_objects = []
        for obj in current_objects:
            object_id = obj['id']
            bbox =  obj['bbox']
            if utils.calculate_area(bbox) > self.min_area:
                # 更新物件的滑动窗口
                self.update_object_window(object_id)
            
            # 计算滑动窗口内的平均出现频率
            avg_appearance = self.calculate_average_appearance(object_id)
            # 检查物件是否满足最小出现频率阈值
            if avg_appearance >= self.min_avg_appearance:
                filtered_objects.append(obj)
        
        return filtered_objects