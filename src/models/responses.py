from pydantic import BaseModel, Field
from typing import Dict

class ExperienceAreaResponse(BaseModel):
    message: str = Field(..., description="服務狀態的回應訊息")

class HealthCheckResponse(BaseModel):
    status: Dict[str, str] = Field(
        ..., 
        description="各進程的運行狀態 (running/stopped/not_initialized/error)"
    )
    system_load: Dict[str, float] = Field(
        ..., 
        description="系統負載信息 (CPU, 內存, 磁盤使用率)"
    )