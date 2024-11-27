import multiprocessing as mp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import aiServerController

def create_app():
    app = FastAPI()
    
    # CORS設置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 註冊路由
    app.include_router(aiServerController.router)
    
    return app

if __name__ == "__main__":
    # 設置多進程啟動方法
    mp.set_start_method('spawn', force=True)
    
    # 創建應用
    app = create_app()
    
    # 使用 uvicorn 啟動應用
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=65333)
else:
    # 為 uvicorn 創建應用實例
    app = create_app()