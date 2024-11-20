import cv2
from fastapi import HTTPException
from src.services.lib.loggingService import log
from src.models.requests import SalesAreaRequest
from src.services.lib.processManager import ProcessManager
from src.services.utils.cameraUtils import fetch_camera_area, CameraManager
from src.services.monitoring.healthCheck import HealthChecker
from src.config.config import VISUAL, RECORD_MODE

class SalesAreaHandler:
    def __init__(self, detection_service, process_pool, frame_buffer):
        self.detection_service = detection_service
        self.process_pool = process_pool
        self.frame_buffer = frame_buffer
        self.process_manager = None
        self.health_checker = HealthChecker()

    async def handle_request(self, request: SalesAreaRequest):
        """處理促銷區請求"""
        if not self.process_manager:
            self.process_manager = ProcessManager(target_function=self.sales_area_task)

        try:
            if request.action == "start":
                msg = self.process_manager.start()
                return {"message": msg['message']}
            elif request.action == "stop":
                msg = self.process_manager.stop()
                return {"message": msg['message']}
            elif request.action == "update":
                msg = self.process_manager.update()
                return {"message": msg['message']}
            else:
                raise HTTPException(status_code=400, detail="Invalid action")
        except Exception as e:
            log.error(f"促銷區狀態操作錯誤: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def sales_area_task(self, stop_event, shared_state):
        """促銷區監控任務"""
        promotion_area_info = fetch_camera_area(type='promotion')
        frame_count = 0

        if not promotion_area_info:
            log.error("未能獲取促銷區相機資訊，請檢查服務狀態。")
            return

        # 使用 CameraManager 初始化攝像頭
        captures = CameraManager.initialize_captures(promotion_area_info)

        try:
            while not stop_event.is_set():
                if shared_state.get('update_requested', False):
                    promotion_area_info = fetch_camera_area(type='promotion')
                    captures = CameraManager.initialize_captures(promotion_area_info)
                    shared_state['update_requested'] = False

                # 獲取系統負載並調整處理頻率
                system_load = self.health_checker.get_system_load()
                process_rate = 2 if system_load["cpu_percent"] > 80 else 1
                frame_count += 1

                if frame_count % process_rate != 0:
                    continue

                for cameraId, cap in captures.items():
                    ret, frame = cap.read()
                    if ret:
                        # 將幀添加到緩存
                        self.frame_buffer.add_frame(cameraId, frame)
                        
                        ROIs_info = promotion_area_info[cameraId]['area_list']
                        
                        # 使用進程池處理檢測任務
                        object_list, persons, ROIs, interactiveAreas = self.detection_service.detect(
                                                        cameraId=cameraId,
                                                        image=frame,
                                                        ROIs_info=ROIs_info,
                                                        record_mode=RECORD_MODE
                                                    )
                                                
                        if VISUAL:
                            self.detection_service.visual(
                                cameraId=cameraId,
                                image=frame,
                                persons=persons
                            )
                    else:
                        log.warning(f"未獲取影像，相機編號：{cameraId} 嘗試重新連接...")
                        cap.release()
                        cap = cv2.VideoCapture(promotion_area_info[cameraId]['meta']['rtsp_url'])
                        captures[cameraId] = cap
                        
        except Exception as e:
            log.error(f"促銷區監控任務錯誤: {str(e)}")
        finally:
            CameraManager.release_captures(captures)
            log.info("進程接收到停止信號，已退出。")