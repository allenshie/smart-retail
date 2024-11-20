import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
# from src.controllers import aiServerController
from src.api import aiServerController

app = FastAPI()

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
