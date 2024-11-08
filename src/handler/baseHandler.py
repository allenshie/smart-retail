import torch
import numpy as np

class BaseHandler:
    def __init__(self):
        self.device = None
        self.model = None
        self.model_name = None
        self.device = torch.device("cpu")

    def initialize(self, context):
        pass


    def preprocess(self, data):
        return torch.as_tensor(data, device=self.device)
    
    def inference(self, data):
        with torch.no_grad():
            data = data.to(self.device)
            results = self.model(data)
        return results

    def postprocess(self, data):
        return data.tolist()

    def handle(self, data):
        if isinstance(data, np.ndarray):
            data_preprocess = self.preprocess(data)
            output = self.inference(data_preprocess)
            output = self.postprocess(output)
        else:
            output = {}
            
        return output
    

