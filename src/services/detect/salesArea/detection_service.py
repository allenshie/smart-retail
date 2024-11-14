import torch
import numpy as np
from src.dao.context import Context
from src.services.detect.base.baseDetection import BaseDetection
from src.services.detect.salesArea.salesUtils import SalesUtils
from src.services.decorator.decorator import  time_logger, postprocess_decorator
from src.services.models.person_pose import PersonPose
from src.services.models.object_detect import ObjectDetect
from src.services.models.fastsam import Sam
from src.services.models.reId import ReID

class DetectionService(BaseDetection):
    def __init__(self, 
                fastsam_context: Context,
                person_context: Context, 
                reid_context: Context):
        self.reid_context = reid_context
        self.sam_model = self._create_model(model_class=Sam, context=fastsam_context)
        self.person_model = self._create_model(model_class=ObjectDetect, context=person_context)
        self.reid_model_dict = dict()
        self.salesUtils = SalesUtils()
        
    @postprocess_decorator(names_dict={0: "object", 1: "person"})
    @time_logger
    def detect(self, cameraId: str, image: np.ndarray, ROIs: dict):
        reid_model_dict = self.getReidModel(cameraId=cameraId)
        person_reid_model = reid_model_dict['person']
        sam_reid_model = reid_model_dict['sam']
    
        # 處理行人模型的預測
        person_tensor_outputs = self.postprocess_person_output(self.person_model.detect(image=image))
        person_reid_outputs = person_reid_model.detect(data=person_tensor_outputs, image=image)
        if not self.salesUtils.being_visited(ROIs=ROIs, persons=person_tensor_outputs):
            all_sam_outputs = []

            # 處理 FastSAM 模型的每個 ROI
            for _, ROI in ROIs.items():
                x1, y1, x2, y2 = ROI
                roi_image = image[y1: y2, x1:x2]
                sam_tensor_outputs = self.sam_model.detect(image=roi_image, ori_point=[x1, y1])
                
                # 將 sam_tensor_outputs 添加到 all_sam_outputs 列表
                all_sam_outputs.append(sam_tensor_outputs)
            # 合併所有的sam tensor
            all_sam_outputs = torch.cat(all_sam_outputs, dim=0) if all_sam_outputs else torch.empty(0)
            all_sam_reid_outputs = sam_reid_model.detect(data=all_sam_outputs, image=image)
            
            all_objects = person_reid_outputs + all_sam_reid_outputs
    
        else:
            all_objects = person_reid_outputs
        
        return all_objects

    @postprocess_decorator(names_dict={0: "object"})
    def detect_all_objects(self, cameraId: str, image: np.ndarray, ROI: list):
        
        reid_model = self.getReidModel(cameraId=cameraId)
        x1, y1, x2, y2 = ROI
        roi_image = image[y1: y2, x1:x2]
        sam_tensor_outputs = self.sam_model.detect(image=roi_image, ori_point=[x1,y1])
        outputs = reid_model.detect(data=sam_tensor_outputs, image=image)
        return outputs

    def getReidModel(self, cameraId: str):
        if cameraId not in self.reid_model_dict:
            self.reid_model_dict.update({
                cameraId: {"person": ReID(context=self.reid_context), 
                           "sam": ReID(context=self.reid_context)}
            })
        return self.reid_model_dict.get(cameraId)

    def postprocess_person_output(self, outputs: list):
        outputs = outputs.clone()  # 創建張量的副本
        outputs[:, 5] = torch.where(outputs[:, 5] == 0, 
                                    torch.tensor(1.0, device='cuda:0'), outputs[:, 5])

        return outputs