import cv2
from fastapi import APIRouter, BackgroundTasks
from src.config.database import initialize_database
from src.services.detect.experienceAreaDetection import ExperienceAreaDetection
from src.services.detect.salesAreaDetection import SalesAreaDetection
from src.services.utils.frameBuffer import FrameBuffer
from src.services.monitoring.healthCheck import HealthChecker
from src.services.monitoring.systemMonitor import SystemMonitor
from src.api.endpoints.experienceArea import ExperienceAreaHandler
from src.api.endpoints.salesArea import SalesAreaHandler
from src.models.responses import HealthCheckResponse
from src.services.lib.loggingService import log
from typing import Optional

class AIServerAPI:
    _instance: Optional['AIServerAPI'] = None
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            try:
                initialize_database()
                
                # 初始化基礎服務組件
                self.frame_buffer = FrameBuffer()
                self.health_checker = HealthChecker()
                self.system_monitor = SystemMonitor()
                
                # 初始化檢測服務
                self.experience_area_detection = ExperienceAreaDetection()
                self.sales_area_detection = SalesAreaDetection()
                
                # 初始化處理程序 - 不再在這裡創建進程池
                self.experience_area_handler = ExperienceAreaHandler(
                    self.experience_area_detection,
                    None,  # 進程池將在需要時創建
                    self.frame_buffer
                )
                self.sales_area_handler = SalesAreaHandler(
                    self.sales_area_detection,
                    None,  # 進程池將在需要時創建
                    self.frame_buffer
                )
                
                # 啟動系統監控
                self.background_tasks = BackgroundTasks()
                self.background_tasks.add_task(self.system_monitor.start_monitoring)
                
            except Exception as e:
                log.error(f"初始化錯誤: {str(e)}")
                raise

    @classmethod
    def get_instance(cls) -> 'AIServerAPI':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def router() -> APIRouter:
        router = APIRouter(prefix="/ai-server", tags=["AI Server"])
        
        # 使用單例模式
        api = AIServerAPI.get_instance()
        
        # 註冊路由
        router.post("/experience-area")(api.experience_area_handler.handle_request)
        router.post("/sales-area")(api.sales_area_handler.handle_request)
        router.get("/health", response_model=HealthCheckResponse)(api.health_check)
        router.post("/shutdown")(api.shutdown_endpoint)

        return router

    async def health_check(self) -> HealthCheckResponse:
        """系統健康檢查"""
        try:
            process_managers = {
                'experience_area': getattr(self.experience_area_handler, 'process_manager', None),
                'sales_area': getattr(self.sales_area_handler, 'process_manager', None)
            }
            
            process_status = self.health_checker.check_process_status(process_managers)
            system_load = self.health_checker.get_system_load()
            
            return HealthCheckResponse(
                status=process_status,
                system_load=system_load
            )
        except Exception as e:
            log.error(f"健康檢查時發生錯誤: {str(e)}")
            return HealthCheckResponse(
                status={"error": str(e)},
                system_load={"cpu_percent": 0, "memory_percent": 0, "disk_usage": 0}
            )

    async def shutdown_endpoint(self):
        """關閉系統"""
        self.shutdown()
        return {"message": "系統已安全關閉"}

    def shutdown(self):
        """關閉所有服務"""
        if hasattr(self, 'system_monitor'):
            self.system_monitor.stop_monitoring()
        cv2.destroyAllWindows()

    def __del__(self):
        """確保資源正確釋放"""
        self.shutdown()
        
router = AIServerAPI.router()