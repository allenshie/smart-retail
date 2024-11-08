import time
from src.utils.utils import utils

class CameraContext:
    def __init__(self):
        self.last_image_before_visit = None
        self.objects_dict = {}
        self.roi_info_dict = {}
        self.roi_state_dict = {}
        self.miss_product_dict = {}

    def update_last_image(self, image):
        self.last_image_before_visit = image

    def update_objects(self, objects):
        for obj in objects:
            obj_id = obj.get("id")
            self.objects_dict[obj_id] = {
                "object": obj,
                "time": time.time()
            }

    def update_rois(self, ROIs_info):
        for ROI in ROIs_info:
            roi_id = ROI['id']
            bbox = utils.find_min_bounding_box(points=ROI['position'])
            self.roi_info_dict[roi_id] = bbox