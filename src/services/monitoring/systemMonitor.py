import time
from typing import Dict
from src.services.lib.loggingService import log

class SystemMonitor:
    def __init__(self):
        self.monitoring_active = False

    def adjust_processing_rate(self, system_load: Dict[str, float]) -> int:
        """根據系統負載調整處理頻率"""
        if system_load["cpu_percent"] > 80 or system_load["memory_percent"] > 80:
            return 2  # 降低處理頻率
        return 1  # 正常處理頻率

    async def monitor_processes(self, process_managers: dict):
        """監控進程狀態並在必要時重啟"""
        while self.monitoring_active:
            for name, manager in process_managers.items():
                if manager.process and not manager.process.is_alive():
                    log.warning(f"進程 {name} 已停止，嘗試重啟...")
                    manager.start()
            time.sleep(10)

    def start_monitoring(self):
        """啟動監控"""
        self.monitoring_active = True

    def stop_monitoring(self):
        """停止監控"""
        self.monitoring_active = False