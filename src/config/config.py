from src.dao.context import Context
fastsam_context = Context(
    model_name='FastSAM',
    model_dir='weights',
    model_file='FastSAM-x.pt',
    threshold=0.5
)
mobilesam_context = Context(
    model_name='MobileSAM',
    model_dir='weights',
    model_file='mobile_sam.pt',
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
    model_file='chair_yolo11m_v1.pt'
)
pillow_context = Context(
    model_name='Pillow',
    model_dir='weights',
    model_file='pillow_yolo11s_v2.pt'
)
# 基礎設定
DATABASE_FILE = 'smart_retail.db'
LOGPATH='log'
VISUAL = True #是否可視化AI影像
GetCameraInfoENDPOINT = '192.168.1.80:65334' # 訪問獲取相機資訊服務的IP
NotificationENDPOINT = '192.168.1.99:18080' # 訪問通報服務的IP
RECORD_MODE = False #是否錄下通報前後影像
RECORD_FPS = 10 # 紀錄事件影像的FPS
RECORD_PRETIME = 10  # 紀錄事件發生前的秒數
RECORD_POSTTIME = 5  # 紀錄事件發生後的秒數
EXPERIENCE_OUTPUT_DIR = 'output/experience' # 體驗區通報事件紀錄影像的存放位置
PROMOTION_OUTPUT_DIR = 'output/promotion' # 促銷區通報事件紀錄影像的存放位置

# 促銷區參數
PRODUCT_WINDOW_SIZE = 10 # 時間序列長度，用來觀察物件是否穩定存在
PRODUCT_MIN_AVG_APPEARANCE = 0.7 # 商品出現比例閾值（小於該值會過濾）
PRODUCT_AREA_THRES = 10000 # 物件面積閾值(小於該值會過濾)
PRODUCT_NO_EXIST_THRES = 10 #(物件消失時間門檻值，超時就會通報)
EXIT_THRESHOLD = 5  # 人员离开区域的时间阈值
CHECK_DURATION = 5  # 检查物品消失的时间窗口
NOT_EXIST_THRES = 10  # 物品消失的时间阈值
SSIM_THRESHOLD = 0.5  # 促銷區-商品SSIM相似度阈值
MASK_SIMILARITY_THRESHOLD = 0.5  # 促銷區-商品MASK相似度阈值
MAX_NOTIFICATIONS = 3 # 促銷區-區域最大通報次數

# 體驗區參數
EXPERIENCE_PRODUCT_DICT = {
            "hands": "product_1",
            "pinto": "product_2", 
            "balance_on": "product_3",
            "cosios": "product_4",
            "doctor_air": "product_5",
        }
EXPERIENCE_TIME_THRES = 3 # 顧客體驗座墊時間阈值
LEAVE_TIME_THRES = 3 # 顧客離開座墊時間阈值

