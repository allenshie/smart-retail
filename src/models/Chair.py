from peewee import CharField, FloatField
from src.models.BaseModel import BaseModel

class Chair(BaseModel):
    chair_id = CharField()
    position = CharField()  # 存儲為字符串，例如 "[x1, y1, x2, y2]"
    type = CharField(null=True, default=None)
    state = CharField(default='idle')
    last_updated_time = FloatField()
    camera_id = CharField()  # 新增欄位，表示來源相機

    class Meta:
        table_name = 'chair'
        indexes = (
            (('chair_id', 'camera_id'), True),
        )