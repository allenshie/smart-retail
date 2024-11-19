import cv2
import time
import numpy as np
from src.config.config import *
from src.services.decorator.decorator import  time_logger
from src.services.detect.salesArea.salesUtils import SalesUtils
from src.services.detect.salesArea.cameraContext import CameraContext
from src.services.detect.salesArea.detection_service import DetectionService
from src.services.track.areaInteractionMonitor import AreaInteractionMonitor
from src.services.track.objectTracker import ObjectTracker
from src.services.video.RecordingService import RecordingService
from src.views.view import View

class SalesAreaDetection:
    def __init__(self, not_exist_thres: int=PRODUCT_NO_EXIST_THRES):
        self.object_tracker = ObjectTracker(window_size=PRODUCT_WINDOW_SIZE, 
                                            min_avg_appearance=PRODUCT_MIN_AVG_APPEARANCE, 
                                            min_area=PRODUCT_AREA_THRES)
        self.sale_utils = SalesUtils()
        self.view = View()
        self.detection_service = DetectionService(
            fastsam_context=fastsam_context,
            person_context=person_context,
            reid_context=reid_context
        )
        self.roi_monitor_dict = dict()
        self.camera_contexts = dict()
        self.recording_services = dict()
        self.not_exist_thres = not_exist_thres
        self.max_area_bboxs_dict = dict()
        

    def get_camera_context(self, cameraId: str):
        if cameraId not in self.camera_contexts:
            self.camera_contexts[cameraId] = CameraContext()
        return self.camera_contexts[cameraId]
    
    def get_recording_service(self, cameraId: str):
        if cameraId not in self.recording_services:
            self.recording_services[cameraId] = RecordingService(
                                                    fps=RECORD_FPS,
                                                    pre_seconds=RECORD_PRETIME,
                                                    post_seconds=RECORD_POSTTIME,
                                                    output_dir=PROMOTION_OUTPUT_DIR)
        return self.recording_services[cameraId]

    @time_logger
    def detect(self, cameraId: str, image: np.ndarray, ROIs_info: list, record_mode: bool=False):
        camera_context = self.get_camera_context(cameraId=cameraId)
        recording_service = self.get_recording_service(cameraId=cameraId)

        camera_context.update_rois(ROIs_info=ROIs_info)
        ROIs = camera_context.roi_info_dict
        
        all_objects = self.detection_service.detect(cameraId=cameraId, image=image, ROIs=ROIs)            
        # 將所有物件分割為物件與行人
        objects, persons = self.sale_utils.get_objects_persons(all_objects=all_objects)
        
        # 以物件出現頻率過濾那些極少出現的物件，只有穩定出現的物件才會被拿來做使用
        filter_objects = self.object_tracker.filter_objects(current_objects=objects)

        # 將本次預測到的物件更新到物件字典內
        camera_context.update_objects(objects=filter_objects)
        
        if len(camera_context.objects_dict) > 0:
            for area_id, roi in ROIs.items():
                self.roi_monitor(cameraId=cameraId, area_id=area_id, roi_bbox=roi, 
                                persons=persons, objects_dict=camera_context.objects_dict, record_mode=record_mode)
            # self.check_ROI_missing_product(cameraId=cameraId, area_id=area_id, roi=roi, persons=persons)
        if record_mode:
            zones = [roi for _, roi in ROIs.items()]
            self.view.visualSalesArea(image=image, persons=persons, objects_dict=camera_context.objects_dict,
                                      zones=zones, interactiveAreas=self.max_area_bboxs_dict.get(cameraId, [])
                                      )
            recording_service.buffer_frame(image) if not recording_service.is_recording else recording_service.record_frame(image)
            
        return  camera_context.objects_dict, persons, ROIs, self.max_area_bboxs_dict.get(cameraId, [])
        
    def roi_monitor(self, cameraId: str, area_id: str, roi_bbox: list, persons: list, objects_dict: dict, record_mode: bool):
        id = f"{cameraId}_{area_id}"
        if id not in self.roi_monitor_dict:
            self.roi_monitor_dict.update({
                id: AreaInteractionMonitor(area_bbox=roi_bbox)
            })
        roi_monitor_instance = self.roi_monitor_dict[id]
        max_area_bboxs = roi_monitor_instance.process_person(persons=persons)
        self.max_area_bboxs_dict[cameraId] = max_area_bboxs
        roi_monitor_instance.monitor_area_interaction(persons=persons)
        
        # 检查物品丢失并启动录制
        if roi_monitor_instance.update_objects(camera_id=cameraId,
                                               area_id=area_id,
                                               current_time=time.time(),
                                               objects_dict=objects_dict):
            if record_mode:
                recording_service = self.get_recording_service(cameraId=cameraId)
                recording_service.start_recording(cameraId)
                
    def visual(self, cameraId, image, persons):
        camera_context = self.get_camera_context(cameraId=cameraId)
        ROIs = camera_context.roi_info_dict
        zones = [roi for _, roi in ROIs.items()]
        self.view.visualSalesArea(image=image, persons=persons, objects_dict=camera_context.objects_dict,
                                    zones=zones, interactiveAreas=self.max_area_bboxs_dict.get(cameraId, [])
                                    )
        cv2.imshow(cameraId, cv2.resize(image, (1440, 960))); cv2.waitKey(1)
