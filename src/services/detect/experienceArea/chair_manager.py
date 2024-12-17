import time
import threading
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from src.utils.utils import utils

class ChairStateChange(Enum):
    OCCUPIED = "occupied"
    VACANT = "vacant"

@dataclass
class ChairStateEvent:
    camera_id: str
    chair_id: str
    chair_type: str
    state_change: ChairStateChange
    timestamp: float

@dataclass
class ChairInfo:
    chair_id: str
    position: List[float]
    type: Optional[str] = None
    state: str = 'idle'
    last_updated: float = field(default_factory=time.time)
    last_state_change: float = field(default_factory=time.time)
    matched_pillow: Optional[dict] = None
    related_ids: set = field(default_factory=set)
    occupying_person: Optional[dict] = None
    # 新增用於追蹤椅墊配對的欄位
    temp_pillow_match: Optional[dict] = None  # 暫時的椅墊配對
    pillow_match_start_time: Optional[float] = None  # 開始配對的時間
    vacant_start: float = field(default_factory=time.time)
    
class ChairManager:
    def __init__(self, data_ttl: int = 30):
        self._contexts: Dict[str, Dict[str, ChairInfo]] = {}
        self._lock = threading.RLock()
        self._data_ttl = data_ttl
        self._person_chair_assignments: Dict[str, Set[str]] = {}  # 記錄每個攝影機中每個人正在使用的椅子

    def find_chair_person_relations(self, chairs: Dict[str, ChairInfo], 
                                  persons: List[dict], 
                                  iou_threshold: float = 0.3) -> Dict[str, str]:
        """
        找出人與椅子的對應關係
        返回 Dict[chair_id, person_id]
        """
        relations = {}
        assigned_persons = set()

        # 計算所有人和椅子的IoU
        chair_person_ious = []
        for chair_id, chair in chairs.items():
            for person in persons:
                iou = utils.calculate_iou(chair.position, person['bbox'])
                if iou >= iou_threshold:
                    chair_person_ious.append((chair_id, person['id'], iou))

        # 按IoU降序排序
        chair_person_ious.sort(key=lambda x: x[2], reverse=True)

        # 貪婪分配，確保一個人最多只能分配到一張椅子
        for chair_id, person_id, iou in chair_person_ious:
            if chair_id not in relations and person_id not in assigned_persons:
                relations[chair_id] = person_id
                assigned_persons.add(person_id)

        return relations

    def update_chairs_info(self, camera_id: str, chairs: List[dict], 
                        persons: List[dict]) -> None:
        """
        更新椅子信息，處理ID關聯和位置更新
        重要：所有檢查都基於context中的資訊
        """
        current_time = time.time()
        
        with self._lock:
            if camera_id not in self._contexts:
                self._contexts[camera_id] = {}
            
            context = self._contexts[camera_id]
            
            # 檢查可以更新位置的椅子
            chairs_can_update_position = set()
            for chair_id, chair_info in context.items():
                if not self.check_chair_overlaps(chair_info.position, persons):
                    chairs_can_update_position.add(chair_id)
            
            # 處理每個檢測到的椅子
            for chair in chairs:
                chair_id = chair['id']
                new_position = chair['bbox']

                if chair_id not in context:
                    overlapping_id = self.find_overlapping_chair(chair, context)
                    
                    if overlapping_id:
                        # 將新ID加入關聯集合
                        context[overlapping_id].related_ids.add(chair_id)
                        # 更新位置（如果允許且新框更大）
                        if overlapping_id in chairs_can_update_position:
                            if utils.calculate_area(new_position) > utils.calculate_area(context[overlapping_id].position):
                                context[overlapping_id].position = new_position
                        # 始終更新時間戳
                        context[overlapping_id].last_updated = current_time
                    else:
                        # 創建新椅子記錄
                        context[chair_id] = ChairInfo(
                            chair_id=chair_id,
                            position=new_position,
                            last_updated=current_time,
                            related_ids={chair_id}
                        )
                else:
                    # 更新現有椅子
                    current_chair = context[chair_id]
                    
                    # 檢查是否是關聯ID的更新
                    is_related_update = False
                    for existing_id, chair_info in context.items():
                        if chair_id in chair_info.related_ids:
                            # 如果允許更新位置且新框更大，則更新位置
                            if existing_id in chairs_can_update_position:
                                if utils.calculate_area(new_position) > utils.calculate_area(chair_info.position):
                                    chair_info.position = new_position
                            # 始終更新時間戳
                            chair_info.last_updated = current_time
                            is_related_update = True
                            break
                    
                    if not is_related_update:
                        # 如果允許更新位置且新框更大，則更新位置
                        if chair_id in chairs_can_update_position:
                            if utils.calculate_area(new_position) > utils.calculate_area(current_chair.position):
                                current_chair.position = new_position
                        # 始終更新時間戳
                        current_chair.last_updated = current_time

    def update_chair_types(self, camera_id: str, pillows: List[dict], 
                        persons: List[dict],
                        match_time_threshold: float = 3.0,  # 需要持續配對的時間
                        overlap_threshold: float = 0.7) -> None:
        """
        更新椅子類型，基於椅墊匹配
        使用時間序列的匹配邏輯：
        1. 每個椅墊尋找最適合的椅子
        2. 只有持續配對超過閾值時間才會被正式接受
        3. 已有type的椅子不更新，但會參與匹配計算
        4. 與人重疊的椅子不更新type
        
        Args:
            camera_id (str): 攝影機ID
            pillows (List[dict]): 檢測到的椅墊列表
            persons (List[dict]): 檢測到的人物列表
            match_time_threshold (float): 需要持續配對的時間（秒）
            overlap_threshold (float): 椅墊與椅子重疊面積的閾值
        """
        current_time = time.time()
        context = self._contexts.get(camera_id, {})
        if not context:
            return

        # 檢查哪些椅子與人重疊
        chairs_with_person = set()
        for chair_id, chair in context.items():
            for person in persons:
                if utils.calculate_iou(chair.position, person['bbox']) > 0:  # 使用IOU > 0判斷重疊
                    chairs_with_person.add(chair_id)
                    break

        # 對每個椅墊進行匹配
        pillow_chair_matches = {}  # 記錄每個椅墊最佳匹配的椅子
        for pillow in pillows:
            pillow_bbox = pillow['bbox']
            chair_matches = []
            
            # 計算與所有椅子的重疊情況
            for chair_id, chair in context.items():
                pillow_overlap, _ = utils.calculate_overlap_ratio(pillow_bbox, chair.position)
                if pillow_overlap > overlap_threshold:
                    chair_matches.append({
                        'chair_id': chair_id,
                        'chair': chair,
                        'overlap': pillow_overlap
                    })
            
            # 如果有符合閾值的椅子，選擇重疊度最高的
            if chair_matches:
                chair_matches.sort(key=lambda x: x['overlap'], reverse=True)
                pillow_chair_matches[tuple(pillow_bbox)] = chair_matches[0]

        # 更新每個椅子的配對狀態
        for chair_id, chair in context.items():
            if chair.type is not None or chair_id in chairs_with_person:
                # 已有type或與人重疊的椅子，重置暫時配對狀態
                chair.temp_pillow_match = None
                chair.pillow_match_start_time = None
                continue

            # 尋找當前匹配到此椅子的椅墊
            current_match = None
            for pillow_bbox, match in pillow_chair_matches.items():
                if match['chair_id'] == chair_id:
                    current_match = {
                        'bbox': list(pillow_bbox),
                        'category': next(p['category'] for p in pillows if tuple(p['bbox']) == pillow_bbox)
                    }
                    break

            if current_match is None:
                # 如果沒有匹配到椅墊，重置配對狀態
                chair.temp_pillow_match = None
                chair.pillow_match_start_time = None
            else:
                if chair.temp_pillow_match is None:
                    # 新的配對開始
                    chair.temp_pillow_match = current_match
                    chair.pillow_match_start_time = current_time
                else:
                    # 檢查是否是同一個椅墊的持續配對
                    prev_bbox = chair.temp_pillow_match['bbox']
                    if utils.calculate_iou(prev_bbox, current_match['bbox']) > 0.5:  # 用IOU > 0.5判斷是否為同一個椅墊
                        # 是同一個椅墊，檢查持續時間
                        if (current_time - chair.pillow_match_start_time >= match_time_threshold and
                            chair.type is None):
                            # 持續時間達到閾值，正式配對
                            chair.matched_pillow = current_match
                            chair.type = current_match['category']
                    else:
                        # 不是同一個椅墊，重置配對狀態
                        chair.temp_pillow_match = current_match
                        chair.pillow_match_start_time = current_time

    def update_chair_status2(self, camera_id: str, persons: List[dict],
                            products_of_interest: List[str],
                            pillows: List[dict],
                            occupation_time_threshold: float = 3.0,
                            vacant_time_threshold: float = 2.0,
                            chair_overlap_threshold: float = 0.6,
                            pillow_overlap_threshold: float = 0.7
                            ) -> List[ChairStateEvent]:
        """
        更新椅子使用狀態並生成事件
        使用以人為主體的配對邏輯，確保一個人只會配對到一張椅子
        """
        current_time = time.time()
        state_events = []
        
        def calculate_distance(point1, point2):
            """計算兩點間的歐幾里得距離"""
            return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5
        
        with self._lock:
            if camera_id not in self._contexts:
                return state_events

            context = self._contexts[camera_id]
            
            # 建立人與椅子的配對結果字典
            person_chair_pairs = {}
            
            # 對每個人進行處理
            for person in persons:
                person_id = person['id']
                person_bbox = person['bbox']
                person_bottom_right = (person_bbox[2], person_bbox[3])  # x2, y2
                
                # 找出所有符合條件的椅子
                qualified_chairs = []
                
                for chair_id, chair in context.items():
                    # 跳過不符合條件的椅子
                    if not chair.matched_pillow or chair.type not in products_of_interest:
                        continue
                    
                    # 計算重疊
                    chair_overlap = utils.calculate_overlap_ratio(chair.position, person_bbox)[0]
                    if chair_overlap > chair_overlap_threshold:
                        pillow_bbox = chair.matched_pillow['bbox']
                        pillow_overlap = utils.calculate_overlap_ratio(pillow_bbox, person_bbox)[0]
                        
                        if pillow_overlap > pillow_overlap_threshold:
                            chair_bottom_right = (chair.position[2], chair.position[3])
                            distance = calculate_distance(person_bottom_right, chair_bottom_right)
                            qualified_chairs.append((chair_id, chair, distance))
                
                # 根據符合條件的椅子數量進行處理
                if len(qualified_chairs) == 1:
                    # 只有一張符合條件的椅子，直接配對
                    person_chair_pairs[person_id] = qualified_chairs[0]
                elif len(qualified_chairs) > 1:
                    # 多張符合條件的椅子，選擇距離最近的
                    nearest_chair = min(qualified_chairs, key=lambda x: x[2])
                    person_chair_pairs[person_id] = nearest_chair
            
            # 處理椅子狀態更新和事件生成
            for chair_id, chair in context.items():
                # 找出當前配對到這張椅子的人
                current_person = None
                for person_id, (matched_chair_id, _, _) in person_chair_pairs.items():
                    if matched_chair_id == chair_id:
                        current_person = next(p for p in persons if p['id'] == person_id)
                        break
                
                # 更新持續時間和狀態
                if current_person is not None:
                    if (chair.continuous_occupation_start is None or 
                        not chair.occupying_person or 
                        chair.occupying_person['id'] != current_person['id']):
                        chair.continuous_occupation_start = current_time
                        chair.occupying_person = current_person
                        # 重置離開時間
                        chair.vacant_start = None
                else:
                    chair.continuous_occupation_start = None
                    if chair.occupying_person is not None and chair.vacant_start is None:
                        chair.vacant_start = current_time
                    
                
                # 計算持續時間
                occupation_duration = (current_time - chair.continuous_occupation_start 
                                    if chair.continuous_occupation_start is not None 
                                    else 0)
                    
                # 狀態轉換邏輯
                if chair.state == 'idle':
                    if (current_person is not None and 
                        occupation_duration >= occupation_time_threshold):
                        
                        chair.state = 'in_use'
                        chair.last_state_change = current_time
                        
                        state_events.append(ChairStateEvent(
                            camera_id=camera_id,
                            chair_id=chair_id,
                            chair_type=chair.type,
                            state_change=ChairStateChange.OCCUPIED,
                            timestamp=current_time
                        ))
                
                elif chair.state == 'in_use':
                    if current_person is None and chair.vacant_start is not None:
                        vacant_duration = current_time - chair.vacant_start
                        if vacant_duration >= vacant_time_threshold:
                            chair.state = 'idle'
                            chair.last_state_change = current_time
                            chair.occupying_person = None
                            chair.vacant_start = None
                            
                            state_events.append(ChairStateEvent(
                                camera_id=camera_id,
                                chair_id=chair_id,
                                chair_type=chair.type,
                                state_change=ChairStateChange.VACANT,
                                timestamp=current_time
                            ))
                elif current_person is not None:
                    # 如果有人回來，重置離開時間
                    chair.vacant_start = None
        
        
        return state_events



    def update_chair_status(self, camera_id: str, persons: List[dict],
                        products_of_interest: List[str],
                        pillows: List[dict],
                        occupation_time_threshold: float = 3.0,  # 需要持續坐著的時間
                        vacant_time_threshold: float = 2.0,      # 需要持續離開的時間
                        chair_overlap_threshold: float = 0.6,    # 人與椅子重疊閾值
                        pillow_overlap_threshold: float = 0.7    # 人與椅墊重疊閾值
                        ) -> List[ChairStateEvent]:
        """
        更新椅子使用狀態並生成事件
        加入持續時間判斷，避免路過的人觸發使用狀態
        """
        current_time = time.time()
        state_events = []
        
        with self._lock:
            if camera_id not in self._contexts:
                return state_events

            context = self._contexts[camera_id]
            
            # 重置人員分配
            if camera_id not in self._person_chair_assignments:
                self._person_chair_assignments[camera_id] = set()
            self._person_chair_assignments[camera_id].clear()

            # 檢查每個在context中的椅子
            for chair_id, chair in context.items():
                # 只處理有配對椅墊的椅子
                if not chair.matched_pillow or chair.type not in products_of_interest:
                    continue

                # 尋找最大重疊的人
                max_overlap_person = None
                max_chair_overlap = 0
                max_pillow_overlap = 0
                
                for person in persons:
                    # 計算人與椅子的重疊
                    chair_overlap = utils.calculate_overlap_ratio(chair.position, person['bbox'])[0]
                    
                    # 如果與椅子有足夠重疊，檢查與椅墊的重疊
                    if chair_overlap > chair_overlap_threshold:
                        pillow_bbox = chair.matched_pillow['bbox']
                        pillow_overlap = utils.calculate_overlap_ratio(pillow_bbox, person['bbox'])[0]
                        
                        # 更新最大重疊的人
                        if chair_overlap > max_chair_overlap and pillow_overlap > pillow_overlap_threshold:
                            max_overlap_person = person
                            max_chair_overlap = chair_overlap
                            max_pillow_overlap = pillow_overlap

                # 更新持續遮擋時間
                if max_overlap_person is not None:
                    # 如果是新的遮擋開始或者是不同的人
                    if (chair.continuous_occupation_start is None or 
                        not chair.occupying_person or 
                        chair.occupying_person['id'] != max_overlap_person['id']):
                        chair.continuous_occupation_start = current_time
                        chair.occupying_person = max_overlap_person
                else:
                    # 如果沒有重疊的人，重置持續時間
                    chair.continuous_occupation_start = None
                    
                # 計算持續時間
                occupation_duration = (current_time - chair.continuous_occupation_start 
                                    if chair.continuous_occupation_start is not None 
                                    else 0)
                # 狀態轉換邏輯
                if chair.state == 'idle':
                    # 從閒置到使用中的轉換
                    if (max_overlap_person is not None and 
                        occupation_duration >= occupation_time_threshold and
                        max_overlap_person['id'] not in self._person_chair_assignments[camera_id]):
                        
                        chair.state = 'in_use'
                        chair.last_state_change = current_time
                        self._person_chair_assignments[camera_id].add(max_overlap_person['id'])
                        
                        state_events.append(ChairStateEvent(
                            camera_id=camera_id,
                            chair_id=chair_id,
                            chair_type=chair.type,
                            state_change=ChairStateChange.OCCUPIED,
                            timestamp=current_time
                        ))
                
                elif chair.state == 'in_use':
                    # 從使用中到閒置的轉換
                    if max_overlap_person is None:
                        # 計算空置時間
                        vacant_duration = current_time - chair.last_state_change
                        if vacant_duration >= vacant_time_threshold:
                            chair.state = 'idle'
                            chair.last_state_change = current_time
                            chair.occupying_person = None
                            
                            state_events.append(ChairStateEvent(
                                camera_id=camera_id,
                                chair_id=chair_id,
                                chair_type=chair.type,
                                state_change=ChairStateChange.VACANT,
                                timestamp=current_time
                            ))
                    elif chair.occupying_person and max_overlap_person['id'] != chair.occupying_person['id']:
                        # 如果是不同的人，保持原狀態直到確認原使用者真的離開
                        pass

        return state_events

    def check_chair_overlaps(self, chair_position: List[float], 
                        persons: List[dict], 
                        overlap_threshold: float = 0.3) -> bool:
        """
        檢查椅子是否與任何人物有顯著重疊
        
        Args:
            chair_position (List[float]): 椅子的位置 [x1, y1, x2, y2]
            persons (List[dict]): 檢測到的人物列表，每個人物應包含 'bbox' 欄位
            overlap_threshold (float): 重疊面積的閾值，預設為 0.3
            
        Returns:
            bool: 如果椅子與任何人物的重疊面積超過閾值，返回 True；否則返回 False
        """
        for person in persons:
            # 計算椅子與人物框的重疊比例（相對於椅子面積）
            overlap_ratio = utils.calculate_overlap_ratio(chair_position, person['bbox'])[0]
            
            # 如果重疊面積超過閾值，返回 True
            if overlap_ratio > overlap_threshold:
                return True
                
        return False

    def find_overlapping_chair(self, new_chair: dict, 
                             context: Dict[str, ChairInfo],
                             iou_threshold: float = 0.3) -> Optional[str]:
        """查找與新椅子高度重疊的已存在椅子"""
        new_bbox = new_chair['bbox']
        max_iou = iou_threshold
        matched_id = None

        for chair_id, chair_info in context.items():
            iou = utils.calculate_iou(new_bbox, chair_info.position)
            if iou > max_iou:
                max_iou = iou
                matched_id = chair_id

        return matched_id

    def get_camera_chairs(self, camera_id: str) -> List[ChairInfo]:
        """獲取指定相機的所有椅子信息"""
        with self._lock:
            return list(self._contexts.get(camera_id, {}).values())

    def _cleanup_expired_data(self, camera_id: str) -> None:
        """清理過期數據"""
        current_time = time.time()
        context = self._contexts.get(camera_id, {})
        
        expired_chairs = [
            chair_id for chair_id, chair in context.items()
            if current_time - chair.last_updated > self._data_ttl
        ]
        
        for chair_id in expired_chairs:
            del context[chair_id]