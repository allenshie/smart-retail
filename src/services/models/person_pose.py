import numpy as np  
from ultralytics.models.yolo.pose.predict import PosePredictor

class PersonPose:
    def __init__(self, ckpt: str, conf: float=0.5):
        self.model = PosePredictor(overrides=dict(model=ckpt, conf=conf, source="", save=False))
        self.names = None

    def detect(self, image: np.ndarray, mode:str="object"):
        self.model.predict_cli(source=image)
        results = self.model.results
        
        if isinstance(self.names, type(None)):
            self.names = results[0].names
            
        if mode=='object':
            return results[0].boxes.data
        else:
            return 
    
