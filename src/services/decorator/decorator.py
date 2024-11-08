import time
from functools import wraps
from src.services.lib.threadManager import ThreadManager

def time_logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 檢查第一個參數是否是self，從而推測這個函數屬於哪個類
        class_name = args[0].__class__.__name__ if args and hasattr(args[0], '__class__') else None
        
        start_time = time.time()  # 記錄開始時間
        result = func(*args, **kwargs)  # 執行被裝飾的函數
        end_time = time.time()  # 記錄結束時間
        execution_time = end_time - start_time  # 計算執行時間

        if class_name:
            print(f"Function '{func.__name__}' from class '{class_name}' executed in {execution_time:.4f} seconds")
        else:
            print(f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")
        
        return result
    return wrapper


# 字典管理多個函數的 ThreadManager 實例
thread_managers = {}

# 定義一個裝飾器，用於給函數添加線程控制能力
def threaded_action(func):
    @wraps(func)
    def wrapper(self, action: str, instance):
        # 獲取函數名稱
        func_name = func.__name__
        
        # 如果沒有該函數的 ThreadManager，則創建一個新的
        if func_name not in thread_managers:
            thread_managers[func_name] = ThreadManager(func, instance)
        manager = thread_managers[func_name]
        
        if action == "start":
            manager.start()
            return {"message": f"{func_name} 線程已啟動"}
        
        elif action == "stop":
            manager.stop()
            # 確保返回字典格式
            return {"message": f"{func_name} 已停止"} if manager.thread else {"message": f"{func_name} 沒有運行中的線程"}

        elif action == "update":
            manager.update()
            return {"message": f"{func_name} 線程已重新啟動"}

        else:
            return {"status": "error", "message": f"未知的動作: {action}"}

    return wrapper


def postprocess_decorator(names_dict):
    """
    通用後處理裝飾器，根據輸入的 shape 自動判斷如何處理輸出結果。
    支援 B*7 和 B*6 格式的輸入。
    """
    def decorator_postprocess(func):
        @wraps(func)
        def wrapper_postprocess(*args, **kwargs):
            outputs = func(*args, **kwargs)  # 獲取原始輸出結果
            object_list = []

            for output in outputs:
                bbox = [int(pt) for pt in output[:4]]  # x1, y1, x2, y2
                score, label = round(float(output[4]), 3), int(output[5])
                id = int(output[6]) if len(output)>6 else None
                object_list.append({
                    "category": names_dict.get(label),
                    "id": id,
                    "score": score,
                    "bbox": bbox
                })

            return object_list
        return wrapper_postprocess
    return decorator_postprocess