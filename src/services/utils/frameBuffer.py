from collections import deque

class FrameBuffer:
    """影像幀緩存類"""
    def __init__(self, maxlen=10):
        self.buffer = {}
        self.maxlen = maxlen

    def add_frame(self, camera_id: str, frame):
        if camera_id not in self.buffer:
            self.buffer[camera_id] = deque(maxlen=self.maxlen)
        self.buffer[camera_id].append(frame)

    def get_latest_frame(self, camera_id: str):
        if camera_id in self.buffer and self.buffer[camera_id]:
            return self.buffer[camera_id][-1]
        return None