import psutil
from typing import Dict, Optional
from src.services.lib.loggingService import log

class HealthChecker:
    @staticmethod
    def get_system_load() -> Dict[str, float]:
        """獲取系統負載信息"""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }

    @staticmethod
    def check_process_status(process_managers: dict) -> Dict[str, str]:
        """
        檢查所有進程的狀態，安全處理未初始化的進程管理器
        
        Args:
            process_managers: 進程管理器字典，鍵為進程名稱，值為進程管理器實例或None
            
        Returns:
            包含每個進程狀態的字典
        """
        status = {}
        for name, manager in process_managers.items():
            if manager is None:
                status[name] = "not_initialized"
            else:
                try:
                    if hasattr(manager, 'process') and manager.process and manager.process.is_alive():
                        status[name] = "running"
                    else:
                        status[name] = "stopped"
                except Exception as e:
                    log.error(f"檢查進程 {name} 狀態時發生錯誤: {str(e)}")
                    status[name] = "error"
        
        return status