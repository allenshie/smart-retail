import os
import cv2
import argparse
from src.services.detect.experienceAreaDetection import ExperienceAreaDetection
from src.views.view import View
experienceArea_object_model = ExperienceAreaDetection()
view = View()

from src.config.database import initialize_database
from src.services.database.ChairService import ChairService
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='test')
    parser.add_argument('--video', type=str, default='video.mp4', help='Video path to predict')
    args = parser.parse_args()
    
    # source = ''# 可自定義source，放rtmp, rtsp等等串流
    source = args.video; cameraId= 'camera1'
    cap = cv2.VideoCapture(source)
    products_of_interest = ['hands', 'pinto', 'balance_on', 'cosios', 'doctor_air'] 
    # initialize_database()
    while 1:
        ret, frame = cap.read()
        if ret: 
            chairs, pillows, persons = experienceArea_object_model.detect(cameraId=cameraId, 
                                                                          image=frame, 
                                                                          products_of_interest=products_of_interest)
        #     chair_db = ChairService.get_camera_chairs(camera_id=cameraId)
        #     history_chairs = []
        #     for chair in chair_db:
        #         history_chairs.append({
        #             "category": "chair",
        #             "id": chair.chair_id,
        #             "bbox": eval(chair.position),
        #             "state": chair.state,
        #             "type": chair.type
        #         })
            
        #     for chair in history_chairs:
        #         view.drawChair(image=frame, chair=chair)
            
        #     for pillow in pillows:
        #         view.drawObject(image=frame, object=pillow, rectColor=(0,0,255))
            
        #     for person in persons:
        #         view.drawObject(image=frame, object=person, rectColor=(255, 0, 0))
                
        #     cv2.imshow("test", cv2.resize(frame, (1440, 920)))
        #     if cv2.waitKey(1) & 0xFF == ord('q'):
        #        break
           
        # else:
        #     pass     
    cv2.destroyAllWindows()

            
            

    
