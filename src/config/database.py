from peewee import SqliteDatabase
from src.config.config import DATABASE_FILE
# 定義數據庫
db = SqliteDatabase(DATABASE_FILE)

def initialize_database():
    """
    連接資料庫，創建表格並清空 Chair 表格。
    """
    from src.models.AIModel import AIModel  # 確保在此處導入模型
    from src.models.Chair import Chair
    db.connect()
    db.create_tables([AIModel, Chair], safe=True)  # safe=True 表示如果表已存在則跳過

    # 清空 Chair 表
    Chair.delete().execute()
    print("Chair table has been cleared.")