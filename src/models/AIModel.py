from peewee import CharField, FloatField
from src.models.BaseModel import BaseModel

class AIModel(BaseModel):
    model_id = CharField(unique=True)
    model_name = CharField()
    model_dir = CharField()
    model_file = CharField()
    model_thres = FloatField()
    
    class Meta:
        table_name = 'ai_model'
        