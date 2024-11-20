import cv2
from fastapi import HTTPException
from src.services.lib.loggingService import log
from src.models.requests import ExperienceAreaRequest
from src.services.lib.processManager import ProcessManager
from src.services.utils.cameraUtils import fetch_camera_area, CameraManager
from src.services.monitoring.healthCheck import HealthChecker
from src.config.config import VISUAL

class ExperienceAreaHandler:
    def __init__(self, detection_service, process_pool, frame_buffer):
        self.detection_service = detection_service
        self.process_pool = process_pool
        self.frame_buffer = frame_buffer
        self.process_manager = None
        self.health_checker = HealthChecker()

    async def handle_request(self, request: ExperienceAreaRequest):
        """處理體驗區請求"""
        if not self.process_manager:
            self.process_manager = ProcessManager(target_function=self.experience_area_task)

        try:
            if request.action == "start":
                msg = self.process_manager.start()
                return {"message": msg['message']}
            elif request.action == "stop":
                msg = self.process_manager.stop()
                return {"message": msg['message']}
            else:
                raise HTTPException(status_code=400, detail="Invalid action")
        except Exception as e:
            log.error(f"體驗區狀態操作錯誤: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def experience_area_task(self, stop_event, shared_state):
        """體驗區監控任務"""
        chair_status_history = shared_state.get('chair_status_history', {})
        experience_area_info = fetch_camera_area(type='experience')
        frame_count = 0

        if not experience_area_info:
            log.error("未能獲取相機資訊，請檢查服務狀態。")
            return

        # 使用 CameraManager 初始化攝像頭
        captures = CameraManager.initialize_captures(experience_area_info)

        try:
            while not stop_event.is_set():
                if shared_state.get('update_requested', False):
                    experience_area_info = fetch_camera_area(type='experience')
                    captures = CameraManager.initialize_captures(experience_area_info)
                    shared_state['update_requested'] = False

                # 獲取系統負載並調整處理頻率
                system_load = self.health_checker.get_system_load()
                process_rate = 2 if system_load["cpu_percent"] > 80 else 1
                frame_count += 1
                if frame_count % process_rate != 0:
                    continue
                for cameraId, cap in captures.items():
                    if stop_event.is_set():
                        break  # 檢查停止信號
                    ret, frame = cap.read()
                    if ret:
                        # 將幀添加到緩存
                        self.frame_buffer.add_frame(cameraId, frame)
                        products_of_interest = [
                            product_dict['name'] 
                            for product_dict in experience_area_info[cameraId]['product_list']
                        ]
                        
                        # 使用進程池處理檢測任務
                        if stop_event.is_set():
                            break  # 再次檢查停止信號
                        chairs, pillows, persons = self.detection_service.detect(
                                                    cameraId=cameraId,
                                                    image=frame
                                                )
                        
                        if stop_event.is_set():
                            break  # 再次檢查停止信號
                        self.detection_service.process_chairs(
                            chair_status_history=chair_status_history,
                            products_of_interest=products_of_interest
                        )
                        
                        if VISUAL and not stop_event.is_set():
                            self.detection_service.visual(
                                cameraId=cameraId,
                                image=frame,
                                pillows=pillows,
                                persons=persons
                            )
                    else:
                        log.warning(f"未獲取影像，相機編號：{cameraId} 嘗試重新連接...")
                        cap.release()
                        cap = cv2.VideoCapture(experience_area_info[cameraId]['meta']['rtsp_url'])
                        captures[cameraId] = cap
                        
        except Exception as e:
            log.error(f"體驗區監控任務錯誤: {str(e)}")
        finally:
            # 確保釋放資源
            CameraManager.release_captures(captures)
            log.info("進程接收到停止信號，已退出。")
