import cv2
import numpy as np
from sklearn.cluster import KMeans
from collections import defaultdict

class ObjectFilterWithKMeans:
    def __init__(self, num_clusters=5, min_area=5000):
        """
        初始化篩選器
        :param num_clusters: K-means 的群數量
        :param min_area: 物件的最小面積要求，面積小於該值的物件會被移除
        """
        self.num_clusters = num_clusters
        self.min_area = min_area

    def calculate_area(self, bbox):
        """
        計算物件的面積
        :param bbox: 邊界框 [x1, y1, x2, y2]
        :return: 面積
        """
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)

    def filter_by_area_threshold(self, objects):
        """
        根據面積門檻過濾物件，移除小於 min_area 的物件
        :param objects: 物件列表
        :return: 只包含符合面積門檻的物件列表
        """
        filtered_objects = [obj for obj in objects if self.calculate_area(obj['bbox']) > self.min_area]
        return filtered_objects

    def extract_object_image(self, image, bbox):
        """
        從原始影像中提取物件的圖像區域
        :param image: 原始影像（np.array）
        :param bbox: 物件的邊界框 [x1, y1, x2, y2]
        :return: 物件的圖像區域（np.array）
        """
        x1, y1, x2, y2 = bbox
        return image[y1:y2, x1:x2]  # 截取圖像區域

    def prepare_data_for_clustering(self, objects, image):
        """
        準備物件的圖像數據，轉換為可供 K-means 演算法處理的特徵
        :param objects: 物件列表
        :param image: 原始影像
        :return: 可用於 K-means 的圖像數據
        """
        object_images = []
        for obj in objects:
            object_img = self.extract_object_image(image, obj['bbox'])
            resized_img = cv2.resize(object_img, (32, 32))  # 將每個圖像縮放到 32x32 大小
            object_images.append(resized_img.flatten())  # 將圖像轉換為一維數組
        return np.array(object_images)

    def cluster_objects(self, objects, image):
        """
        使用 K-means 對物件進行分群
        :param objects: 物件列表
        :param image: 原始影像
        :return: 包含每個物件所屬群的物件列表
        """
        data = self.prepare_data_for_clustering(objects, image)
        kmeans = KMeans(n_clusters=self.num_clusters)
        kmeans.fit(data)
        labels = kmeans.labels_

        # 將群標籤附加到每個物件上
        for i, obj in enumerate(objects):
            obj['group'] = labels[i]

        return objects

    def find_largest_group(self, objects):
        """
        找出最多成員的群
        :param objects: 物件列表
        :return: 最多成員的群標識
        """
        group_counts = defaultdict(int)

        # 統計每個群的成員數量
        for obj in objects:
            group = obj['group']
            group_counts[group] += 1

        # 找出成員數最多的群
        largest_group = max(group_counts, key=group_counts.get)
        largest_group_size = group_counts[largest_group]

        print(f"最多成員的群是：{largest_group}，擁有 {largest_group_size} 個成員")
        return largest_group

    def filter_objects_by_largest_group(self, objects):
        """
        篩選出最多成員的群中的所有物件
        :param objects: 物件列表
        :return: 最多成員群的物件列表
        """
        largest_group = self.find_largest_group(objects)
        return [obj for obj in objects if obj['group'] == largest_group]

