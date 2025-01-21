import numpy as np
from ultralytics import SAM


class MobileSAM:
    def __init__(self, ckpt, **kwargs):
        self.model = SAM(ckpt)
        
    def detect(self, image: np.ndarray, bbox: list[int], label: list[int]):
        x1, y1, x2, y2 = bbox
        mask1 = None
        
        results = self.model.predict(image, bboxes=bbox, labels=label)
        for r in results:
            masks = r.masks.data
            for mask in masks:
                mask = mask.cpu().numpy()
                mask = (mask*255).astype('uint8')
                mask1 = mask[y1:y2, x1:x2]
        return mask1    
                            
                
