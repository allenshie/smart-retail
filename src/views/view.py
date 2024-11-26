import cv2
import numpy as np
class View:
    def drawObject(self, image: np.ndarray, object: dict, text: str=None, rectColor: tuple=(255,0,0)):
        x1, y1, x2, y2 = object.get('bbox')
        category = object.get('category')
        id = object.get('id')  
        if isinstance(text, type(None)):
            if not isinstance(id, type(None)):
                category +=f'-{id}'
            text = category
        cv2.rectangle(image, (x1,y1), (x2,y2), color=rectColor, thickness=1)
        self._drawText(image=image, text=text, point=[x1,y1], color=rectColor)
        
    def _drawText(self, image, text, point, color, font_scale:float=1):
        text_str = text
        x1, y1 = point
        font_face = cv2.FONT_HERSHEY_DUPLEX
        font_scale = 1
        font_thickness = 1

        text_w, text_h = cv2.getTextSize(text_str, font_face, font_scale, font_thickness)[0]
        text_pt = (x1, y1 - 3)
        text_color = [255, 255, 255]

        cv2.rectangle(image, (x1, y1), (x1 + text_w, y1 - text_h - 4), color, -1)
        cv2.putText(image, text_str, text_pt, font_face, font_scale, text_color, font_thickness, cv2.LINE_AA)
        return image
    
    def drawChair(self, image: np.ndarray, chair: dict):
        def add_text(text: str, add_t: str):
            if add_t is not None:
                text+=f'-{add_t}'
            return text
        
        category = chair.get('category')
        type = chair.get('type')
        id = chair.get('id')
        state = chair.get('state')
        text = add_text(category, id)
        text = add_text(text, type)
        text = add_text(text, state)
        rectColor = (0,0,255) if  state== 'in_use' else (0, 155, 0)
        self.drawObject(image=image, object=chair, text=text, rectColor=rectColor)
        
    def visualSalesArea(self, image: np.ndarray, persons: list, objects_dict: dict, zones: list, 
                        interactiveAreas: list):
        for zone in zones:
            cv2.rectangle(image, zone[:2], zone[2:], (233, 189, 222), 3)
        
        for interactiveArea in interactiveAreas:
            cv2.rectangle(image, interactiveArea[:2], interactiveArea[2:], (0, 69, 255), 3)

        for person in persons:
            self.drawObject(image=image, object=person, rectColor=(0,188,0))
            
        for id, info in objects_dict.items():
            object = info['object']
            rectColor = (0,0,255) if info.get('notified') else (255,0,0)
            self.drawObject(image=image, object=object, rectColor=rectColor)
        
    def visualExperienceArea(self, image: np.ndarray, pillows, chairs, persons):
        history_chairs = []
        for chair in chairs:
            history_chairs.append({
                "category": "chair",
                "id": chair.chair_id,
                "bbox": chair.position,
                "state": chair.state,
                "type": chair.type
            })
        
        for chair in history_chairs:
            self.drawChair(image=image, chair=chair)
        
        for pillow in pillows:
            self.drawObject(image=image, object=pillow, rectColor=(0,0,255))
        
        for person in persons:
            self.drawObject(image=image, object=person, rectColor=(255, 0, 0))
    