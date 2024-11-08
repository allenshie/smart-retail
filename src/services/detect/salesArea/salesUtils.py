from src.utils.utils import utils

class SalesUtils:
    def __init__(self):
        pass
    
            
    def get_objects_persons(self, all_objects: list):
        objects, persons = [], []
        for object in all_objects:
            category = object.get('category')
            if  category == 'object':
                objects.append(object)
            elif category == 'person':
                persons.append(object)
        return objects, persons
    
    # 檢測ROI狀態是否正在被訪問
    def being_visited(self, ROIs: dict, persons: list):
        visited = False
        for _, ROI in ROIs.items():
            if any([utils.calculate_iou(ROI, person[:4])>0 for person in persons]):
                visited = True
        return visited   
        
        
        
         
        
        