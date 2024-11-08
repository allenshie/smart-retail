import time
from src.utils.utils import utils

class PersonAreaTracker:
    def __init__(self, area_bbox, exit_threshold: int=5):
        """
        :param area_bbox: 定义的区域边界框，格式为 [x1, y1, x2, y2]
        """
        self.area_bbox = area_bbox
        self.exit_threshold = exit_threshold
        self.person_data = {}  # 存储每个行人的交集数据
        
    def process_person(self, person_id, person_bbox):
        intersection = self.get_intersection(self.area_bbox, person_bbox)

        if intersection:
            if person_id not in self.person_data:
                # 新的行人，初始化其数据
                self.person_data[person_id] = {
                    'max_area_bbox': intersection,
                    'in_area': True,
                    'exit_timer': None
                }
            else:
                # 更新行人在区域内的最大轨迹矩形
                self.person_data[person_id]['max_area_bbox'] = utils.merge_bboxes(
                    self.person_data[person_id]['max_area_bbox'], intersection)
                self.person_data[person_id]['in_area'] = True
                self.person_data[person_id]['exit_timer'] = None  # 重置离开计时器
        else:
            if person_id in self.person_data and self.person_data[person_id]['in_area']:
                # 行人离开区域，开始计时
                if self.person_data[person_id]['exit_timer'] is None:
                    self.person_data[person_id]['exit_timer'] = time.time()
                elif time.time() - self.person_data[person_id]['exit_timer'] > self.exit_threshold:
                    # 超过阈值时间，标记行人离开区域
                    self.person_data[person_id]['in_area'] = False

    def get_final_intersections(self):
        """
        获取所有离开区域的行人的最终最大轨迹矩形。
        如果多个矩形有重叠，进行合并。
        :return: 合并后的最大轨迹矩形列表
        """
        final_intersections = []

        # 检查所有行人的状态并输出已经离开区域的最大轨迹
        for person_id, data in list(self.person_data.items()):
            # if not data['in_area'] and data['max_area_bbox']:
            #     final_intersections.append(data['max_area_bbox'])
            #     del self.person_data[person_id]  # 移除已经完成的追踪
            final_intersections.append(data['max_area_bbox'])


        # 合并重叠的矩形
        merged_intersections = []
        while final_intersections:
            current_bbox = final_intersections.pop(0)
            has_merged = False

            for i, merged_bbox in enumerate(merged_intersections):
                if utils.bboxes_overlap(current_bbox, merged_bbox):
                    merged_intersections[i] = utils.merge_bboxes(current_bbox, merged_bbox)
                    has_merged = True
                    break

            if not has_merged:
                merged_intersections.append(current_bbox)

        return merged_intersections

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
        :param new_bbox: 新的交集矩形 [x1, y1, x2, y2]
        :return: 更新后的包含所有交集的最小外接矩形
        """
        x1_min = min(existing_bbox[0], new_bbox[0])
        y1_min = min(existing_bbox[1], new_bbox[1])
        x2_max = max(existing_bbox[2], new_bbox[2])
        y2_max = max(existing_bbox[3], new_bbox[3])
        
        return [x1_min, y1_min, x2_max, y2_max]