import time
import threading
from multiprocessing import Process, Event
from src.services.lib.loggingService import log

class ProcessManager:
    def __init__(self, target_function):
        self.target_function = target_function
        self.process = None
        self.stop_event = None
        self.shared_state = {}
        
    def _run_target(self):
        try:
            # 創建新的事件對象
            self.stop_event = Event()
            self.target_function(self.stop_event, self.shared_state)
        except Exception as e:
            log.error(f"進程執行錯誤: {str(e)}")
        finally:
            log.info("進程執行完成")

    def start(self):
        if self.process and self.process.is_alive():
            log.warning("進程已在運行中")
            return {"status": "error", "message": "Process is already running"}

        try:
            if self.stop_event:
                self.stop_event.clear()
                
            self.process = Process(
                target=self._run_target,
                daemon=False
            )
            self.process.start()
            
            time.sleep(0.5)
            
            if self.process.is_alive():
                log.info(f"進程已啟動，PID: {self.process.pid}")
                return {"status": "success", "message": f"Process started with PID: {self.process.pid}"}
            else:
                raise RuntimeError("進程啟動失敗")
            
        except Exception as e:
            log.error(f"啟動進程時發生錯誤: {str(e)}")
            return {"status": "error", "message": str(e)}

    def stop(self):
        if not self.process or not self.process.is_alive():
            log.warning("進程未在運行")
            return {"status": "error", "message": "Process is not running"}

        try:
            log.info(f"正在停止進程 {self.process.pid}...")
            
            if self.stop_event:
                self.stop_event.set()
            
            time.sleep(0.5)
            self.process.join(timeout=3)
            
            if self.process.is_alive():
                log.warning(f"進程 {self.process.pid} 未響應，嘗試強制終止")
                self.process.terminate()
                self.process.join(timeout=2)
                
                if self.process.is_alive():
                    log.error(f"進程 {self.process.pid} 仍在運行，使用 SIGKILL")
                    import signal, os
                    try:
                        os.kill(self.process.pid, signal.SIGKILL)
                        self.process.join(timeout=1)
                    except Exception as e:
                        log.error(f"強制終止進程失敗: {str(e)}")
                        return {"status": "error", "message": "Failed to kill process"}

            self.process = None
            self.shared_state.clear()
            
            log.info("進程已停止")
            return {"status": "success", "message": "Process stopped successfully"}
            
        except Exception as e:
            log.error(f"停止進程時發生錯誤: {str(e)}")
            return {"status": "error", "message": str(e)}

    def update(self):
        if self.process and self.process.is_alive():
            self.shared_state['update_requested'] = True
            log.info("更新請求已發送")
            return {"status": "success", "message": "Update request sent"}
        else:
            log.info("進程未運行，嘗試重新啟動")
            return self.start()

    def __del__(self):
        """確保資源正確釋放"""
        try:
            if hasattr(self, 'process') and self.process and self.process.is_alive():
                self.stop()
        except Exception as e:
            log.error(f"清理進程管理器資源時發生錯誤: {str(e)}")