import numpy as np

class Utils:
    def __init__(self):
        pass
    
    # 計算IoU（交集佔聯合的比例）
    def calculate_iou(self, bbox1, bbox2):
        x1, y1, x2, y2 = bbox1
        x1_p, y1_p, x2_p, y2_p = bbox2
        
        # 計算交集的邊界
        inter_x1 = max(x1, x1_p)
        inter_y1 = max(y1, y1_p)
        inter_x2 = min(x2, x2_p)
        inter_y2 = min(y2, y2_p)

        inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

        # 計算聯合的邊界
        bbox1_area = (x2 - x1) * (y2 - y1)
        bbox2_area = (x2_p - x1_p) * (y2_p - y1_p)

        union_area = bbox1_area + bbox2_area - inter_area

        return inter_area / union_area if union_area > 0 else 0

    # 計算中心點距離
    def calculate_distance(self, bbox1, bbox2):
        center1 = [(bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2]
        center2 = [(bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2]
        return np.sqrt((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2)

    def calculate_area(self, bbox):
        """
        計算物件的面積
        :param bbox: 邊界框 [x1, y1, x2, y2]
        :return: 面積
        """
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)


    # A物件有完全在Bj物件內嗎
    def is_A_fully_inside_B(self, A, B):
        """
        檢查A物件是否完全位於B物件內部。
        """
        A_x1, A_y1, A_x2, A_y2 = A.get('bbox')
        B_x1, B_y1, B_x2, B_y2 = B.get('bbox')
        return (A_x1 >= B_x1 and A_y1 >= B_y1 and
                A_x2 <= B_x2 and A_y2 <= B_y2)

    def rotate_bbox_back(self, bbox, image_width, image_height):
        """
        將順時針旋轉90度後影像中的座標框 (x1', y1', x2', y2') 矯正回旋轉前的座標框 (x1, y1, x2, y2)。
        
        :param x1: 旋轉後影像中左上角的 x' 坐標
        :param y1: 旋轉後影像中左上角的 y' 坐標
        :param x2: 旋轉後影像中右下角的 x' 坐標
        :param y2: 旋轉後影像中右下角的 y' 坐標
        :param image_width: 原始影像的寬度（旋轉前的寬度）
        :param image_height: 原始影像的高度（旋轉前的高度）
        :return: 矯正後的 (x1, y1, x2, y2) 坐標框
        """
        x1, y1, x2, y2 = bbox
        # 左上角 (x1', y1') 矯正回 (x1, y1)
        nx1 = y1
        ny1 = image_height - x2
        
        # 右下角 (x2', y2') 矯正回 (x2, y2)
        nx2 = y2
        ny2 = image_height - x1

        return nx1, ny1, nx2, ny2

    def merge_bboxes(self, bbox1, bbox2):
        """
        合并两个矩形框，返回一个包含两者的最小外接矩形
        :param bbox1: 第一个矩形 [x1, y1, x2, y2]
        :param bbox2: 第二个矩形 [x1, y1, x2, y2]
        :return: 合并后的矩形 [x1, y1, x2, y2]
        """
        x1 = min(bbox1[0], bbox2[0])
        y1 = min(bbox1[1], bbox2[1])
        x2 = max(bbox1[2], bbox2[2])
        y2 = max(bbox1[3], bbox2[3])
        return [x1, y1, x2, y2]

    def bboxes_overlap(self, bbox1, bbox2):
        """
        检查两个矩形是否有重叠
        :param bbox1: 第一个矩形 [x1, y1, x2, y2]
        :param bbox2: 第二个矩形 [x1, y1, x2, y2]
        :return: 布尔值，表示是否有重叠
        """
        x1_overlap = max(bbox1[0], bbox2[0])
        y1_overlap = max(bbox1[1], bbox2[1])
        x2_overlap = min(bbox1[2], bbox2[2])
        y2_overlap = min(bbox1[3], bbox2[3])
        return x1_overlap < x2_overlap and y1_overlap < y2_overlap
    
    def update_max_bbox(self, existing_bbox, new_bbox):
        """
        更新最大轨迹矩形，确保包含所有经过区域的轨迹。
        :param existing_bbox: 当前的最大矩形 [x1, y1, x2, y2]
        :param new_bbox: 新的交集矩形 [x1, y1, x2, y2]
        :return: 更新后的最大矩形
        """
        x1_min = min(existing_bbox[0], new_bbox[0])
        y1_min = min(existing_bbox[1], new_bbox[1])
        x2_max = max(existing_bbox[2], new_bbox[2])
        y2_max = max(existing_bbox[3], new_bbox[3])
        return [x1_min, y1_min, x2_max, y2_max]

    def find_min_bounding_box(self, points: list):
        # 獲取所有 x 和 y 座標
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        # 找出最小和最大的 x, y 值
        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        
        # 返回最小矩形的四個角座標
        return [min_x, min_y, max_x, max_y]
    
    def get_minimum_enclosing_bbox(self, bboxes):
        """
        計算包圍所有 bboxes 的最小矩形
        
        :param bboxes: List of bboxes, each bbox in format [x1, y1, x2, y2]
        :return: Minimum enclosing bbox in format [x_min, y_min, x_max, y_max]
        """
        if not bboxes:
            raise ValueError("The list of bboxes is empty")
        
        # 分別計算 x_min, y_min, x_max, y_max
        x_min = min(bbox[0] for bbox in bboxes)
        y_min = min(bbox[1] for bbox in bboxes)
        x_max = max(bbox[2] for bbox in bboxes)
        y_max = max(bbox[3] for bbox in bboxes)
        
        return [x_min, y_min, x_max, y_max]    

utils = Utils()