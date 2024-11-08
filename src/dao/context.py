class Context:
    def __init__(self, model_name, model_dir, model_file="", cfg_path="", \
                 gpu_id=None, threshold=0.5):
        
        self.model_name  = model_name
        self.model_dir = model_dir
        self.model_file = model_file
        self.cfg_path = cfg_path
        self.gpu_id = gpu_id
        self.threshold = threshold

