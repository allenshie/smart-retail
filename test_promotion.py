import os
import cv2
from src.services.detect.salesAreaDetection import SalesAreaDetection
from src.services.video.videoWriteService import VideoWriteService
from src.views.view import View

if __name__ == "__main__":
    salesAreaDetection = SalesAreaDetection()
    view = View()
    video_dir_path = '/home/allen/Documents/project/smart_retail_space/data/videos/promotion'
    video_file_name = 'cam4.mp4'
    cameraId = 'camera_test1'
    source = os.path.join(video_dir_path, video_file_name)
    ROIs_info = [
    {
        "id": "area_1",
        "name": "Promotion Area 1",
        "position": [[1236,1548], [1560, 1548], [1560, 1824], [1236, 1824]]
    },
    {
        "id": "area_2",
        "name": "Promotion Area 2",
        "position": [[890,1580], [1208, 1580], [1208, 1824], [890, 1824]]
    },    
    {
        "id": "area_3",
        "name": "Promotion Area 3",
        "position": [[5,795], [1834, 795], [1834, 1574], [5, 1574]]
    }, 
    ]
    
    # source = 'rtmp://192.168.1.99/store_streaming/livestream'
    # ROIs_info = [
    #     {
    #         "id": "area_1",
    #         "name": "Promotion Area 1",
    #         "position": [[226, 193], [433, 172], [410, 473], [143, 478]]
    #     }, ]
  
    for roi in ROIs_info:
        roi['position'] = [[int(x), int(y)] for x, y in roi['position']]
        
  
    cap = cv2.VideoCapture(source)
    # videoWrite = VideoWriteService(cap=cap, output_path=os.path.join("output", 'promotion', os.path.basename(source)))
    while 1:
        ret, frame = cap.read()
        if ret:
            object_dict ,persons, ROIs, interactiveAreas = salesAreaDetection.detect(
                cameraId=cameraId, image=frame, ROIs_info=ROIs_info, record_mode=False)
            
            zones = [roi for _, roi in ROIs.items()]    

            view.visualSalesArea(image=frame, persons=persons, objects_dict=object_dict,
                                 zones=zones, interactiveAreas=interactiveAreas)

            # cv2.imshow("frame", frame)
            # videoWrite.write(frame=frame)
            cv2.imshow("frame", cv2.resize(frame, (1920, 1080)))

            if cv2.waitKey(1) & 0xFF==ord('q'):
                break
            
            

            
            
    
    