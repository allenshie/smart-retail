import os
import cv2
import argparse
from src.services.detect.experienceAreaDetection import ExperienceAreaDetection
from src.views.view import View
experienceArea_object_model = ExperienceAreaDetection()
view = View()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='test')
    parser.add_argument('--video', type=str, default='video.mp4', help='Video path to predict')
    args = parser.parse_args()
    
    # source = ''# 可自定義source，放rtmp, rtsp等等串流
    source = args.video; cameraId= 'camera1'
    cap = cv2.VideoCapture(source)
    products_of_interest = ['hands', 'pinto', 'balance_on', 'cosios', 'doctor_air'] 
    while 1:
        ret, frame = cap.read()
        if ret: 
            chairs, pillows, persons, frame = experienceArea_object_model.detect(cameraId=cameraId, 
                                                                          image=frame, 
                                                                          products_of_interest=products_of_interest)
            # cv2.imshow("test", cv2.resize(frame, (1440, 920)))
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break
           
        # else:
        #     pass     
    cv2.destroyAllWindows()

            
            

    
