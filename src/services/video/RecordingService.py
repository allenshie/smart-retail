import os
import cv2
import time
from collections import deque

class RecordingService:
    def __init__(self, fps=30, pre_seconds=20, post_seconds=10, output_dir: str='output'):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir = output_dir
        self.fps = fps
        self.pre_frames = pre_seconds * fps
        self.post_frames = post_seconds * fps
        self.frame_buffer = deque(maxlen=self.pre_frames)
        self.is_recording = False
        self.post_recording_frames = 0
        self.out = None

    def buffer_frame(self, frame):
        """將當前影格加入緩存"""
        self.frame_buffer.append(frame)

    def start_recording(self, camera_id):
        """開始錄影並將緩存影格寫入影片"""
        if not self.is_recording:
            self.is_recording = True
            timestamp = int(time.time())
            output_path = os.path.join(self.output_dir, f'{camera_id}_{timestamp}.avi')
            self.out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'XVID'), 
                                       self.fps, (self.frame_buffer[0].shape[1], self.frame_buffer[0].shape[0]))

            for frame in self.frame_buffer:
                self.out.write(frame)
            self.post_recording_frames = 0

    def record_frame(self, frame):
        """錄製後續影格直到達到指定秒數"""
        if self.is_recording:
            self.out.write(frame)
            self.post_recording_frames += 1

            if self.post_recording_frames >= self.post_frames:
                self.is_recording = False
                self.out.release()
                self.out = None
