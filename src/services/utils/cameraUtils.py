import cv2
import requests
from src.services.lib.loggingService import log
from src.config.config import GetCameraInfoENDPOINT

def fetch_camera_area(type: str):
    """訪問 /camera-area API 並獲取對應的輸出"""
    url = f"http://{GetCameraInfoENDPOINT}/camera-area"
    params = {"type": type}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        log.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        log.error(f"An error occurred: {err}")
        return None

class CameraManager:
    @staticmethod
    def initialize_captures(camera_info):
        return {cameraId: cv2.VideoCapture(info['meta']['rtsp_url']) 
                for cameraId, info in camera_info.items()}

    @staticmethod
    def release_captures(captures):
        for cap in captures.values():
            cap.release()