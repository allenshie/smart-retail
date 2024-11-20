import time
from multiprocessing import Process, Event, Manager
from src.services.lib.loggingService import log


# 進程管理器，用來管理無限迴圈的啟動和停止
class ProcessManager:
    def __init__(self, target_function):
        """
        初始化進程管理器，設置目標函數並創建停止事件。
        
        :param target_function: 要在進程中運行的目標函數
        """
        self.target_function = target_function
        self.process = None
        self.manager = Manager()
        self.stop_event = None
        self.shared_state = self.manager.dict()

    def _run_target(self):
        """包裝目標函數的運行方法，將停止事件和共享狀態傳遞給目標函數。"""
        try:
            self.target_function(self.stop_event, self.shared_state)
        except Exception as e:
            log.error(f"進程執行錯誤: {str(e)}")
        finally:
            log.info("進程執行完成")
    
    def start(self):
        """啟動進程來執行目標函數，並確保同一時間僅有一個進程在運行。"""
        if self.process and self.process.is_alive():
            log.warning("進程已在運行中，無需重複啟動。")
            return {"status": "error", "message": "Process is already running"}

        # 檢查進程是否殘留
        if self.process:
            log.warning("檢測到殘留進程，嘗試清理...")
            self.stop()

        try:
            # 重置停止事件並創建新進程
            self.stop_event = Event()
            self.stop_event.clear()
            self.process = Process(target=self._run_target)
            self.process.daemon = True  # 設置為守護進程
            self.process.start()
            log.info(f"進程已成功啟動，PID: {self.process.pid}")
            return {"status": "success", "message": f"Process started successfully with PID: {self.process.pid}"}
        
        except Exception as e:
            log.error(f"啟動進程時發生錯誤: {str(e)}")
            return {"status": "error", "message": str(e)}


    def stop(self):
        """停止進程，通過觸發停止事件來安全地退出。"""
        if not self.process or not self.process.is_alive():
            log.warning("進程未在運行。")
            return {"status": "error", "message": "Process is not running"}

        try:
            log.info("正在停止進程...")
            self.stop_event.set()  # 通知進程退出
            self.process.join(timeout=5)  # 等待進程正常結束
            
            if self.process.is_alive():  # 進程未響應，強制終止
                log.warning("進程未響應停止事件，強制終止")
                self.process.terminate()
                self.process.join(timeout=2)

            # 確保進程資源釋放
            if self.process.is_alive():
                log.error("進程仍未退出，請檢查資源釋放問題")
                return {"status": "error", "message": "Failed to stop process"}

            # 清理資源
            self.process = None
            self.stop_event = None

            log.info("進程已成功停止")
            return {"status": "success", "message": "Process stopped successfully"}
            
        except Exception as e:
            log.error(f"停止進程時發生錯誤: {str(e)}")
            return {"status": "error", "message": str(e)}


    def update(self):
        """更新進程：通知進程更新或重啟進程。"""
        if self.process and self.process.is_alive():
            self.shared_state['update_requested'] = True
            log.info("更新請求已發送")
            return {"status": "success", "message": "Update request sent successfully"}
        else:
            log.info("進程未在運行，嘗試重新啟動")
            return self.start()