import numpy as np
from src.services.decorator.decorator import time_logger
from src.dao.context import Context
from src.handler.deepSortHandler import DeepSortHandler

class ReID:
    def __init__(self, context: Context):
        self.context = context
        self.model = DeepSortHandler(self.context)
        
    @time_logger
    def detect(self, data: list, image:np.ndarray):
        return self.model.handle(data=data, image_ori=image)
        
