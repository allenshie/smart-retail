from fastapi import APIRouter, HTTPException
from pydantic import BaseModel as PydanticBaseModel
from peewee import IntegrityError
from src.models.AIModel import AIModel
from src.config.database import db

class AIModelAPI:
    def __init__(self):
        # 通過 Peewee 獲取數據庫連接
        try:
            db.connect()
            db.create_tables([AIModel])
        except Exception as e:
            print(f"Error connecting to the database: {e}")

    @staticmethod
    def router() -> APIRouter:
        router = APIRouter(prefix="/ai-models", tags=["AI Models"])
        api = AIModelAPI()

        router.post("/")(api.create_ai_model)
        router.get("/")(api.get_all_ai_models)
        router.get("/{model_id}")(api.get_ai_model)
        router.put("/{model_id}")(api.update_ai_model)
        router.delete("/{model_id}")(api.delete_ai_model)

        return router

    # 定義 Pydantic 模型，用於處理請求和回應
    class AIModelRequest(PydanticBaseModel):
        model_id: str
        model_name: str
        model_dir: str
        model_file: str
        model_thres: float

    class AIModelResponse(PydanticBaseModel):
        model_id: str
        model_name: str
        model_dir: str
        model_file: str
        model_thres: float

    # 新增模型 (CREATE) 並檢查 model_name 是否已存在
    async def create_ai_model(self, model: AIModelRequest):
        # 檢查 model_name 是否已經存在
        if AIModel.select().where(AIModel.model_name == model.model_name).exists():
            raise HTTPException(status_code=400, detail="Model name already exists")

        try:
            new_model = AIModel.create(
                model_id=model.model_id,
                model_name=model.model_name,
                model_dir=model.model_dir,
                model_file=model.model_file,
                model_thres=model.model_thres
            )
            return self.AIModelResponse(
                model_id=new_model.model_id,
                model_name=new_model.model_name,
                model_dir=new_model.model_dir,
                model_file=new_model.model_file,
                model_thres=new_model.model_thres
            )
        except IntegrityError:
            raise HTTPException(status_code=400, detail="Model ID already exists")

    # 查詢所有模型 (READ)
    async def get_all_ai_models(self):
        models = AIModel.select()
        return [self.AIModelResponse(
            model_id=model.model_id,
            model_name=model.model_name,
            model_dir=model.model_dir,
            model_file=model.model_file,
            model_thres=model.model_thres
        ) for model in models]

    # 查詢特定模型 (READ)
    async def get_ai_model(self, model_id: str):
        try:
            model = AIModel.get(AIModel.model_id == model_id)
            return self.AIModelResponse(
                model_id=model.model_id,
                model_name=model.model_name,
                model_dir=model.model_dir,
                model_file=model.model_file,
                model_thres=model.model_thres
            )
        except AIModel.DoesNotExist:
            raise HTTPException(status_code=404, detail="Model not found")

    # 更新模型 (UPDATE)
    async def update_ai_model(self, model_id: str, model: AIModelRequest):
        try:
            query = AIModel.get(AIModel.model_id == model_id)
            query.model_name = model.model_name
            query.model_dir = model.model_dir
            query.model_file = model.model_file
            query.model_thres = model.model_thres
            query.save()
            return self.AIModelResponse(
                model_id=query.model_id,
                model_name=query.model_name,
                model_dir=query.model_dir,
                model_file=query.model_file,
                model_thres=query.model_thres
            )
        except AIModel.DoesNotExist:
            raise HTTPException(status_code=404, detail="Model not found")

    # 刪除模型 (DELETE)
    async def delete_ai_model(self, model_id: str):
        try:
            query = AIModel.get(AIModel.model_id == model_id)
            query.delete_instance()
            return {"message": "Model deleted successfully"}
        except AIModel.DoesNotExist:
            raise HTTPException(status_code=404, detail="Model not found")
        
router = AIModelAPI.router()
