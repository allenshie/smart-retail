from pydantic import BaseModel, Field
from typing import List, Tuple

class SalesAreaRequest(BaseModel):
    action: str = Field(..., description="三種動作請求: start (啟動), update (更新), stop (停止)")

class ExperienceAreaRequest(BaseModel):
    action: str = Field(..., description="兩種動作請求: start (啟動) 或 stop (停止)")

class ROIInfo(BaseModel):
    id: str
    name: str
    position: List[Tuple[int, int]]

class CameraInput(BaseModel):
    cameraId: str
    ROIs_info: List[ROIInfo]
    base64_image: str