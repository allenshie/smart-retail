from collections import Counter, defaultdict

class ObjectFilter:
    def __init__(self, area_tolerance=2000, min_group_size=5, use_advanced_filtering=False, max_color_diff=20, min_area=5000):
        """
        初始化篩選器
        :param area_tolerance: 面積分群的容忍度，控制將面積相近的物件劃分到同一群
        :param min_group_size: 每個群體中最小的物件數量，用於判定該群是否為商品群
        :param use_advanced_filtering: 是否啟用進階篩選，預設為False
        :param max_color_diff: 最大顏色分佈差異，僅在啟用進階篩選時使用
        """
        self.area_tolerance = area_tolerance
        self.min_group_size = min_group_size
        self.use_advanced_filtering = use_advanced_filtering
        self.max_color_diff = max_color_diff
        self.min_area = min_area
        self.object_windows = dict()
        

    @staticmethod
    def calculate_area(bbox):
        """
        計算物件的面積
        :param bbox: 邊界框 [x1, y1, x2, y2]
        :return: 面積
        """
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)

    def group_by_area(self, objects):
        """
        將物件基於面積相近度進行分群
        :param objects: 物件列表
        :return: 分群後的結果，群內物件列表的字典
        """
        groups = defaultdict(list)

        for obj in objects:
            area = self.calculate_area(obj["bbox"])
            if area> self.min_area:
                # 找到一個群，該群中所有物件的面積與當前物件的面積差值不超過 area_tolerance
                found_group = False
                for group_area in groups:
                    if abs(area - group_area) <= self.area_tolerance:
                        obj['group'] = group_area  # 將物件的群標識設為該群的面積
                        groups[group_area].append(obj)
                        found_group = True
                        break
                if not found_group:
                    # 如果沒有找到符合條件的群，創建一個新群，群標識設為物件的面積
                    obj['group'] = area
                    groups[area].append(obj)
        
        return groups

    def filter_by_group_size(self, groups):
        """
        根據群內的物件數量篩選出商品群
        :param groups: 分群後的物件
        :return: 被視為商品的物件列表
        """
        filtered_objects = []
        for group_area, group_objects in groups.items():
            if len(group_objects) >= self.min_group_size:
                filtered_objects.extend(group_objects)
        return filtered_objects

    @staticmethod
    def calculate_average_color_distribution(objects):
        """
        計算所有物件的平均顏色分佈，構建顏色模型
        :param objects: 物件列表
        :return: 平均顏色分佈（Counter）
        """
        total_color_distribution = Counter()
        for obj in objects:
            total_color_distribution.update(obj["color_distribution"])
        
        # 計算平均顏色分佈
        num_objects = len(objects)
        average_color_distribution = {color: count / num_objects for color, count in total_color_distribution.items()}
        
        return average_color_distribution

    def filter_by_color_distribution(self, objects, avg_color_dist):
        """
        根據平均顏色分佈進行篩選
        :param objects: 物件列表
        :param avg_color_dist: 平均顏色分佈模型
        :return: 篩選後的物件列表
        """
        final_filtered_objects = []
        for obj in objects:
            color_diff = self.color_distribution_similarity(obj["color_distribution"], avg_color_dist)
            if color_diff <= self.max_color_diff:  # 控制顏色分佈的差異範圍
                final_filtered_objects.append(obj)
        return final_filtered_objects

    def filter_objects(self, objects):
        """
        整合面積分群和顏色分佈篩選流程
        :param objects: 物件列表
        :return: 最終篩選後的物件列表，每個物件附加其所屬的群
        """
        # Step 1: 基於面積分群
        groups = self.group_by_area(objects); print(groups.keys())
        
        # Step 2: 根據群內物件數量篩選商品
        filtered_by_group = self.filter_by_group_size(groups)
        
        # Step 3: 如果啟用進階篩選，基於顏色分佈篩選
        if self.use_advanced_filtering:
            avg_color_distribution = self.calculate_average_color_distribution(filtered_by_group)
            final_filtered_objects = self.filter_by_color_distribution(filtered_by_group, avg_color_distribution)
        else:
            final_filtered_objects = filtered_by_group
        return final_filtered_objects