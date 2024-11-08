import os
import cv2
import numpy as np
from src.services.lib.loggingService import log
from src.utils.utils import utils
from src.services.decorator.decorator import postprocess_decorator
from src.services.models.object_detect import ObjectDetect
from src.services.models.person_pose import PersonPose
from src.services.models.reId import ReID
from src.dao.context import Context

class DetectionService:
    def __init__(self, chair_context: Context, pillow_context: Context, person_context: Context, reid_context: Context):
        self.reid_context = reid_context
        self.chair_model = self._create_model(model_class=ObjectDetect, context=chair_context)
        self.pillow_model = self._create_model(model_class=ObjectDetect, context=pillow_context)
        self.person_model = self._create_model(model_class=PersonPose, context=person_context)        
        self.reid_model_dict = dict()
        
    def detect(self, cameraId: str, image: np.ndarray):
        chairs = self.detect_chair(cameraId=cameraId, image=image)
        pillows = self.detect_pillow(image=image)
        persons = self.detect_person(image=image)
        return chairs, pillows, self.correct_coordinates(persons=persons, image_shape=image.shape)

    def _create_model(self, model_class, context: Context):
        model = None
        model_name = context.model_name
        weight_dir = context.model_dir
        weight_file = context.model_file
        ckpt = os.path.join(weight_dir, weight_file)
        try: 
            model = model_class(ckpt=ckpt)
            log.info(f" {model_name} 權重載入成功！！")
            
        except Exception as e:
            log.info(f" {model_name} 權重載入失敗，原因：{e}")

        return model
        
    def getReidModel(self, cameraId: str):
        if cameraId not in self.reid_model_dict:
            reid_model = ReID(context=self.reid_context)
            self.reid_model_dict.update({
                cameraId: reid_model
            })
        return self.reid_model_dict.get(cameraId)


    def detect_chair(self, cameraId: str, image: np.ndarray):
        reid_model = self.getReidModel(cameraId=cameraId)
        chairs_tensor = self.chair_model.detect(image=image)
        
         # 动态调用装饰器，并传入 self.chair_model.names
        postprocessed_chairs = postprocess_decorator(
            names_dict=self.chair_model.names  # 在实例化后使用动态属性
        )(lambda: reid_model.detect(chairs_tensor, image))()

        return postprocessed_chairs    
    
    def detect_pillow(self, image: np.ndarray):
        """
        动态应用装饰器，处理 pillow 检测结果
        """
        pillows_tensor = self.pillow_model.detect(image=image)

        # 动态调用装饰器，传入 names_dict
        postprocessed_pillows = postprocess_decorator(
            names_dict=self.pillow_model.names
        )(lambda: pillows_tensor)()

        return postprocessed_pillows
        

    def detect_person(self, image: np.ndarray):
        """
        动态应用装饰器，处理 person 检测结果
        """
        rotate_image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        person_tensor = self.person_model.detect(image=rotate_image)

        # 动态调用装饰器，传入 names_dict
        postprocessed_persons = postprocess_decorator(
            names_dict=self.person_model.names
        )(lambda: person_tensor)()

        return postprocessed_persons
        
    def correct_coordinates(self, persons, image_shape):
        """
        将 person 检测结果的坐标从旋转后的图像坐标转换回原始图像坐标系。
        
        :param persons: 经过后处理的 person 对象列表
        :param image_shape: 原始图像的大小 (height, width, channels)
        :return: 调整过坐标的 person 对象列表
        """
        h, w, _ = image_shape
        for person in persons:
            x1, y1, x2, y2 = utils.rotate_bbox_back(person['bbox'], image_width=w, image_height=h)
            person['bbox'] = [x1, y1, x2, y2]
        return persons