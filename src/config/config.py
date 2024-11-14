from src.dao.context import Context
fastsam_context = Context(
    model_name='FastSAM',
    model_dir='weights',
    model_file='FastSAM-x.pt',
    threshold=0.5
)
pose_person_context = Context(
    model_name='Person',
    model_dir='weights',
    model_file='yolov8m-pose.pt',
    threshold=0.5
)
person_context = Context(
    model_name='Person',
    model_dir='weights',
    model_file='person_topview_yolov8m_v1.pt',
    threshold=0.5
)
reid_context = Context(
    model_name='REID',
    model_dir='weights',
    model_file='osnet_x0_25_msmt17.pt',
    gpu_id=0
)
chair_context = Context(
    model_name='Chair',
    model_dir='weights',
    model_file='chair_yolov8m_v0.pt'
)
pillow_context = Context(
    model_name='Pillow',
    model_dir='weights',
    model_file='pillow_yolov8m_v1.pt'
)
DATABASE_FILE = 'smart_retail.db'
LOGPATH='log'
RECORD_MODE = False #是否錄下通報前後20秒影像
PRODUCT_WINDOW_SIZE = 30 # 時間序列長度，用來觀察物件是否穩定存在
PRODUCT_MIN_AVG_APPEARANCE = 0.7 # 商品出現比例閾值（小於該值會過濾）
PRODUCT_AREA_THRES = 10000 # 物件面積閾值(小於該值會過濾)
PRODUCT_NO_EXIST_THRES = 10 #(物件消失時間門檻值，超時就會通報)

EXIT_THRESHOLD = 5  # 人员离开区域的时间阈值
CHECK_DURATION = 5  # 检查物品消失的时间窗口
NOT_EXIST_THRES = 10  # 物品消失的时间阈值

GetCameraInfoENDPOINT = '192.168.1.99:18080' # 訪問獲取相機資訊服務的IP
NotificationENDPOINT = '192.168.1.99:18080' # 訪問通報服務的IP

EXPERIENCE_OUTPUT_DIR = 'output/experience' # 體驗區通報事件紀錄影像的存放位置
PROMOTION_OUTPUT_DIR = 'output/promotion' # 促銷區通報事件紀錄影像的存放位置