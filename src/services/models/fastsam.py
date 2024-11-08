import time
import torch 
import numpy as np
from ultralytics import FastSAM
from src.services.decorator.decorator import time_logger

class Sam:
    def __init__(self, ckpt: str, conf:float=0.5):
        self.device = "cuda:0"
        self.retina_masks = False
        self.imgsz = 640
        self.conf = conf
        self.iou = 0.9
        self.model = FastSAM(ckpt)
        
    @time_logger
    def detect(self, image: np.ndarray, ori_point: list=[0,0]):
        everything_results = self.model(image, 
                                        device=self.device,
                                        retina_masks=self.retina_masks,
                                        imgsz=self.imgsz,
                                        conf=self.conf,
                                        iou=self.iou
                                        )
        outputs = everything_results[0].boxes.data
        outputs = self.postprocess(outputs=outputs, ori_point=ori_point)
        
        return outputs

        
    def postprocess(self, outputs: torch.Tensor, ori_point: list):
        return  self.adjust_coordinates(tensor_data=outputs, origin=ori_point)



    def adjust_coordinates(self, tensor_data, origin):
        """
        對tensor_data中的(x1, y1, x2, y2)座標進行校正

        :param tensor_data: 張量形式的數據，每一行包含[x1, y1, x2, y2, conf, label]
        :param origin: 二元組，代表原點 (x, y) 進行校正
        :return: 校正後的tensor
        """
        tensor_data = tensor_data.clone()
        # 提取原點
        x_origin, y_origin = origin
        
        # 對每一行的座標 (x1, y1, x2, y2) 進行校正
        # 將原點座標從對應的列中減去
        tensor_data[:, 0] += x_origin  # 校正 x1
        tensor_data[:, 1] += y_origin  # 校正 y1
        tensor_data[:, 2] += x_origin  # 校正 x2
        tensor_data[:, 3] += y_origin  # 校正 y2
        
        return tensor_data
