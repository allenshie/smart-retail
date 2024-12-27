import cv2
import requests
from typing import List, Tuple
from fastapi import APIRouter, HTTPException
from fastapi import  HTTPException, Body
from pydantic import BaseModel, Field
from src.config.database import initialize_database
from src.config.config import GetCameraInfoENDPOINT, RECORD_MODE, VISUAL
from src.services.lib.loggingService import log
from src.services.lib.threadManager import ThreadManager
from src.services.detect.experienceAreaDetection import ExperienceAreaDetection
from src.services.detect.salesAreaDetection import SalesAreaDetection

class SalesAreaRequest(BaseModel):
    action: str = Field(..., description="三種動作請求: start (啟動), update (更新), stop (停止)")

class ExperienceAreaRequest(BaseModel):
    action: str = Field(..., description="兩種動作請求: start (啟動) 或 stop (停止)")

class ExperienceAreaResponse(BaseModel):
    message: str = Field(..., description="服務狀態的回應訊息")

# 定义请求体的数据模型
class ROIInfo(BaseModel):
    id: str
    name: str
    position: List[Tuple[int, int]]

class CameraInput(BaseModel):
    cameraId: str
    ROIs_info: List[ROIInfo]
    base64_image: str


def fetch_camera_area(type: str):
    """
    訪問 /camera-area API 並獲取對應的輸出。

    :param type: 要查詢的區域類型 ('promotion' 或 'experience')
    :return: API 響應的 JSON 數據
    """
    url = f"http://{GetCameraInfoENDPOINT}/camera-area"  # 根據您的服務地址進行調整
    params = {
        "type": type
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # 檢查請求是否成功
        print(response.json())
        return response.json()  # 返回 JSON 數據
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # 輸出 HTTP 錯誤
    except Exception as err:
        print(f"An error occurred: {err}")  # 輸出其他錯誤


class AIServerAPI:
    def __init__(self):
        try:
            initialize_database()
            self.experienceAreaDetection = ExperienceAreaDetection()
            self.salesAreaDetection = SalesAreaDetection()
            self.thread_managers = {}
        except Exception as e:
            print(str(e))
        
        
    @staticmethod
    def router() -> APIRouter:
        router = APIRouter(prefix="/ai-server", tags=["AI Server"])
        api = AIServerAPI()
        
        router.post(
            "/experience-area",
            summary="監控體驗區狀態", 
            description="監控體驗區內座墊的使用情況",
            response_model=ExperienceAreaResponse
            )(api.experience_area_status)
        
        router.post(
            "/sales-area", 
            summary="監控促銷區狀態", 
            description="監控促銷區的銷售情況",
            response_model=ExperienceAreaResponse
        )(api.sales_area_status)

        return router
    
    async def experience_area_status(
        self, request: ExperienceAreaRequest = Body(..., description="根據 action 啟動或停止體驗區服務")
    ):
        """
        根據提交的 action 來啟動或停止體驗區椅子監控服務。

        """
        func_name = self.experienceArea_task.__name__
        if func_name not in self.thread_managers:
            self.thread_managers[func_name] = ThreadManager(target_function=self.experienceArea_task)
        manager = self.thread_managers[func_name]
        
        if request.action =="update":
            return {"message": "experienceArea_task 不支持 'update' 動作"}
        
        elif request.action =='start':
            msg = manager.start()
            message = "Service started successfully"
        
            if msg["status"] != "success":
                message = msg['message']
                
            return {"message": message}
        
        elif request.action=='stop':
            msg = manager.stop()
            message = "Service stopped successfully"
            
            if msg["status"] != "success":
                message = msg['message']
                
            return {"message": message} 
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    async def sales_area_status(self, request: SalesAreaRequest = Body(...)):
        """
        根據提交的 action 來啟動、更新或停止促銷區域監控。
        """
        func_name = self.salesArea_task.__name__
        if func_name not in self.thread_managers:
            self.thread_managers[func_name] = ThreadManager(target_function=self.salesArea_task)
        manager = self.thread_managers[func_name]
        
        if request.action == "start":
            msg = manager.start()
            message = "Service started successfully"

            if msg["status"] != "success":
                message = msg['message']
                
            return {"message": message}
            
        elif request.action == "stop":
            msg = manager.stop()
            message = "Service stopped successfully"
            
            if msg["status"] != "success":
                message = msg['message']
                
            return {"message": message}
        
        elif request.action == "update":
            manager.update()
            return {"message": "Service updated successfully"}

        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
    def experienceArea_task(self, stop_event):
        # 使用 fetch_camera_area 獲取相機資訊
        experience_area_info = fetch_camera_area(type='experience')  # 獲取體驗區相機資訊

        if not experience_area_info:
            print("未能獲取相機資訊，請檢查服務狀態。")
            return

        # 提取 RTSP URL 和相機 ID
        captures = {cameraId: cv2.VideoCapture(info['meta']['rtsp_url']) for cameraId, info in experience_area_info.items()}
        while not stop_event.is_set():
            
            for cameraId, cap in captures.items():
                ret, frame = cap.read()
                products_of_interest = [product_dict['name'] for product_dict in experience_area_info[cameraId]['product_list']]
                if ret:
                    log.info(f"體驗區-相機編號：{cameraId} 監控中...")
                    chairs, pillows, persons, image = self.experienceAreaDetection.detect(cameraId=cameraId, image=frame, products_of_interest=products_of_interest)

                else:
                    log.info(f"未獲取影像，相機編號：{cameraId} 嘗試重新連接...")
                    cap.release()
                    cap = cv2.VideoCapture(experience_area_info[cameraId]['meta']['rtsp_url'])
                    captures[cameraId] = cap
                    
        print("線程接收到停止信號，已退出。")
    
    def salesArea_task(self, stop_event):
        promotion_area_info = fetch_camera_area(type='promotion')  # 獲取促銷區相機資訊
        
        if not promotion_area_info:
            print("未能獲取促銷區相機資訊，請檢查服務狀態。")
            return
        
        captures = {cameraId: cv2.VideoCapture(info['meta']['rtsp_url']) for cameraId, info in promotion_area_info.items()}
        
        while not stop_event.is_set():
            for cameraId, cap in captures.items():
                ret, frame = cap.read()
                
                if ret:
                    log.info(f"促銷區-相機編號：{cameraId} 監控中...")
                    ROIs_info = promotion_area_info[cameraId]['area_list']
                    object_list, persons, ROIs, interactiveAreas = self.salesAreaDetection.detect(cameraId=cameraId, 
                                                        image=frame, ROIs_info=ROIs_info, record_mode=RECORD_MODE)
                    if VISUAL:
                        self.salesAreaDetection.visual(cameraId=cameraId, image=frame, persons=persons)

                else:
                    log.info(f"未獲取影像，相機編號：{cameraId} 嘗試重新連接...")
                    cap.release()
                    cap = cv2.VideoCapture(promotion_area_info[cameraId]['meta']['rtsp_url'])
                    captures[cameraId] = cap
                    
        print("線程接收到停止信號，已退出。")
             
router = AIServerAPI.router()
