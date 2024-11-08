import os
from src.services.lib.loggingService import log
from src.dao.context import Context

class BaseDetection:
    def __init__(self):
        pass
        
    def _create_model(self, model_class, context: Context):
        model = None
        model_name = context.model_name
        weight_dir = context.model_dir
        weight_file = context.model_file
        threshold = context.threshold
        ckpt = os.path.join(weight_dir, weight_file)
        try: 
            model = model_class(ckpt=ckpt, conf=threshold)
            log.info(f" {model_name} 權重載入成功！！")
            
        except Exception as e:
            log.info(f" {model_name} 權重載入失敗，原因：{e}")

        return model
    
