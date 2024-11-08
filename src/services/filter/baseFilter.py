class BaseFilter:
    def __init__(self, min_size: int=5000):
        self.min_size = min_size  
    
    
    @staticmethod
    def calculate_area(bbox: list):
        """
        計算物件的面積
        :param bbox: 邊界框 [x1, y1, x2, y2]
        :return: 面積
        """
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1) 
    
    
    def filter_by_area_size(self, objects: list):
        filtered_objects = []
        for object in objects:
            bbox = object.get('bbox')
            area = self.calculate_area(bbox=bbox)
            if area>=self.min_size:
                filtered_objects.append(object)
        return filtered_objects
        