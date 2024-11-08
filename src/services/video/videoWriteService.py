import cv2
class VideoWriteService:
    def __init__(self, cap, output_path):
        self.out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"),
                    int(cap.get(5)), (int(cap.get(3)), int(cap.get(4))))
                
    def write(self, frame):
        try:
            self.out.write(frame)
        except Exception as e:
            print(e)
