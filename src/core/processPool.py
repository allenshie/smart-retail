from multiprocessing import Pool, cpu_count

class ProcessPoolManager:
    def __init__(self):
        self.pool = Pool(processes=cpu_count())

    def execute_task(self, func, *args):
        """執行異步任務"""
        return self.pool.apply_async(func, args)

    def shutdown(self):
        """關閉進程池"""
        self.pool.close()
        self.pool.join()