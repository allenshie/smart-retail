import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, List
from src.controllers import aiServerController


app = FastAPI()

# 定義 Request Body 模型，並在字段中添加 description 屬性

# class SalesAreaRequest(BaseModel):
#     action: str = Field(..., description="三種動作請求: start (啟動), update (更新), stop (停止)")

# class ExperienceAreaRequest(BaseModel):
#     action: str = Field(..., description="兩種動作請求: start (啟動) 或 stop (停止)")

# class ExperienceAreaResponse(BaseModel):
#     message: str = Field(..., description="服務狀態的回應訊息")

# # 第一個 API：監控體驗區狀態
# @app.post(
#     "/experience-area", 
#     summary="監控體驗區狀態", 
#     description="監控體驗區內座墊的使用情況",
#     response_model=ExperienceAreaResponse
# )
# async def experience_area_status(
#     request: ExperienceAreaRequest = Body(..., description="根據 action 啟動或停止體驗區服務")
# ):
#     """
#     根據提交的 action 來啟動或停止體驗區椅子監控服務。

#     """
#     if request.action == "start":
#         return {"message": "Service started successfully"}
#     elif request.action == "stop":
#         return {"message": "Service stopped successfully"}
#     else:
#         raise HTTPException(status_code=400, detail="Invalid action")

# # 第二個 API：監控促銷區狀態
# @app.post(
#     "/sales-area", 
#     summary="監控促銷區狀態", 
#     description="監控促銷區的銷售情況",
#     response_model=ExperienceAreaResponse
# )
# async def sales_area_status(
#     request: SalesAreaRequest = Body(..., description="根據 action 提交要執行的操作")
# ):
#     """
#     根據提交的 action 來啟動、更新或停止促銷區域監控。

#     - **action**: 必要參數，接受 `start`、`update` 或 `stop`
#     - **data**: 當 `action` 是 `update` 時，包含要更新的區域和 RTSP 連接資料
#     """
#     if request.action == "start":
#         return {"message": "Service started successfully"}
#     elif request.action == "stop":
#         return {"message": "Service stopped successfully"}
#     elif request.action == "update":
#         return {"message": "Service updated successfully"}
#     else:
#         raise HTTPException(status_code=400, detail="Invalid action")
    
origins = [
"*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(aiServerController.router)
# 啟動應用的方式
if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
