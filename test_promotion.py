import os
import cv2
from src.services.detect.salesAreaDetection import SalesAreaDetection
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
        "position": [[10.223880597015, 550.1940298507463 ], [ 1950.373134328358, 550.1940298507463 ], [ 1950.373134328358, 1813.313432835821 ], [ 10.223880597015, 1813.313432835821 ]]
    }, ]
    
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
    while 1:
        ret, frame = cap.read()
        if ret:
            object_dict ,persons, ROIs, interactiveAreas = salesAreaDetection.detect(
                cameraId=cameraId, image=frame, ROIs_info=ROIs_info, record_mode=False)
            
            zones = [roi for _, roi in ROIs.items()]    
            print(f'出現人員數量： {len(persons)}')
            view.visualSalesArea(image=frame, persons=persons, objects_dict=object_dict,
                                 zones=zones, interactiveAreas=interactiveAreas)

            # cv2.imshow("frame", frame)
            cv2.imshow("frame", cv2.resize(frame, (1920, 1080)))

            if cv2.waitKey(1) & 0xFF==ord('q'):
                break
            
            

            
            
    
    