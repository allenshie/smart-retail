import time
import threading


# 線程管理器，用來管理無限迴圈的啟動和停止
class ThreadManager:
    def __init__(self, target_function):
        """
        初始化線程管理器，設置目標函數並創建停止事件。
        
        :param target_function: 要在線程中運行的目標函數
        """
        self.target_function = target_function
        self.thread = None
        self.stop_event = threading.Event()

    def _run_target(self):
        """
        包裝目標函數的運行方法，將停止事件傳遞給目標函數。
        """
        self.target_function(self.stop_event)
    
    def start(self):
        """
        啟動線程來執行目標函數，並確保同一時間僅有一個線程在運行。
        """
        if self.thread and self.thread.is_alive():
            print("線程已在運行中，無需重複啟動。")
            return {"status": "error", "message": "Thread is already running"}

        # 重置停止事件並創建新線程來運行目標函數
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_target)
        self.thread.start()
        print("線程已成功啟動。")
        return {"status": "success", "message": "Thread started successfully"}

    def stop(self):
        """
        停止線程，通過觸發停止事件來安全地退出無限迴圈。
        """
        if self.thread and self.thread.is_alive():
            self.stop_event.set()  # 觸發停止事件
            self.thread.join()  # 等待線程完成
            print("線程已成功停止。")
            return {"status": "success", "message": "Thread stopped successfully"}
        else:
            print("線程未在運行。")
            return {"status": "error", "message": "Thread is not running"}

    def update(self):
        """
        更新線程：停止當前線程，然後重新啟動。
        """
        self.stop()
        time.sleep(1)  # 稍作等待，確保線程完全停止後再重啟
        return self.start()