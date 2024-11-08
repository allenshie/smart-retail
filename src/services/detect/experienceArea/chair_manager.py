import time
from src.utils.utils import utils
from src.services.database.ChairService import ChairService 

class ChairManager:
    def update_chair_status(self, cameraId: str, person_outputs: list, iou_threshold:float=0.3, time_threshold: float=3):
        current_time = time.time()
        # 從資料庫中獲取所有屬於該相機且 type 非 None 的椅子
        chairs = ChairService.get_camera_chairs(cameraId)
        chairs = [chair for chair in chairs if chair.type is not None]  # 過濾 type 非 None 的椅子
        chair_matches = self.find_best_match(chairs, person_outputs, iou_threshold)
        for chair in chairs:
            chair_id = chair.chair_id

            # 依據字典中的匹配結果來判斷椅子的狀態
            if chair.state == 'idle':
                if chair_matches.get(chair_id):
                    # 椅子與行人匹配，開始計時
                    if chair.last_updated_time is None:
                        chair.last_updated_time = current_time
                    elif current_time - chair.last_updated_time >= time_threshold:
                        # 達到閾值時間，更新狀態為 'in_use'
                        ChairService.update_chair_state(chair_id, 'in_use', cameraId)
                        ChairService.update_chair_last_updated_time(chair_id, current_time, cameraId)
                else:
                    # 沒有匹配到行人，重置計時
                    ChairService.update_chair_last_updated_time(chair_id, current_time, cameraId)

            elif chair.state == 'in_use':
                if not chair_matches.get(chair_id):
                    # 椅子未匹配到行人，開始計時
                    if chair.last_updated_time is None:
                        ChairService.update_chair_last_updated_time(chair_id, current_time, cameraId)
                    elif current_time - chair.last_updated_time >= time_threshold:
                        # 達到閾值時間，更新狀態為 'idle'
                        ChairService.update_chair_state(chair_id, 'idle', cameraId)
                        ChairService.update_chair_last_updated_time(chair_id, current_time, cameraId)
                else:
                    # 椅子仍然匹配到行人，重置計時
                    ChairService.update_chair_last_updated_time(chair_id, current_time, cameraId)
        
        return chairs
    
    def assign_chair_types(self, chairs, pillows, iou_threshold=0.3, distance_threshold=200):
        """
        根据座垫匹配最合适的椅子，并为椅子分配类型。每个椅子只能匹配一个座垫。
        如果椅子没有被设置类型，则默认类型为 None。
        """
        chairs_copy = chairs.copy()
        chair_type_map = dict()
        
        for pillow in pillows:
            best_match = None
            best_iou = 0
            best_distance = float('inf')
            best_chair_index = -1
            pillow_bbox = pillow['bbox']

            # 遍历所有椅子，找到与该座垫最匹配的椅子
            for i, chair in enumerate(chairs_copy):
                chair_bbox = chair['bbox']
                iou = utils.calculate_iou(chair_bbox, pillow_bbox)
                distance = utils.calculate_distance(chair_bbox, pillow_bbox)

                # 新增条件：检查座垫是否完全在椅子内
                if utils.is_A_fully_inside_B(pillow, chair):
                    iou = 1.0
                # 找到最好的匹配（最大IoU且距离最小）
                if iou > best_iou and distance < best_distance and iou >= iou_threshold:
                    best_iou = iou
                    best_distance = distance
                    best_match = chair
                    best_chair_index = i

            # 分配椅子类型
            if best_match and best_distance <= distance_threshold:
                # 将座垫的类别分配给最佳匹配的椅子
                chair_type_map[best_match['id']] = pillow['category']
                chairs_copy.pop(best_chair_index)
                
        # 遍历所有椅子，更新类型，如果没有匹配则设置为 None
        for chair in chairs:
            chair_id = chair['id']
            chair['type'] = chair_type_map.get(chair_id, None)  # 没有匹配的默认类型为 None

                    
        return chairs


    def find_best_match(self, chairs, person_outputs, iou_threshold):
        """
        根据行人匹配椅子。返回一个字典，表示每张椅子是否与行人匹配。
        椅子 ID 作为键，匹配结果 (True/False) 作为值。
        """
        matches = {}  # 记录椅子是否匹配到行人
        matched_chairs = set()  # 追踪已匹配的椅子

        # 遍历每个行人，寻找最合适的椅子匹配
        for person in person_outputs:
            best_match_chair = None
            best_iou = 0
            best_distance = float('inf')

            person_bbox = person['bbox']

            for i, chair in enumerate(chairs):
                if chair.chair_id in matched_chairs:
                    continue  # 已匹配的椅子不再参与匹配

                chair_bbox = eval(chair.position)
                iou = utils.calculate_iou(chair_bbox, person_bbox)
                distance = utils.calculate_distance(chair_bbox, person_bbox)
                # 根据 IoU 和距离选择最好的匹配
                if iou >= iou_threshold and (iou > best_iou or (iou == best_iou and distance < best_distance)):
                    best_iou = iou
                    best_distance = distance
                    best_match_chair = chair

            # 如果找到匹配的椅子，标记为已匹配
            if best_match_chair:
                matches[best_match_chair.chair_id] = True
                matched_chairs.add(best_match_chair.chair_id)  # 将匹配成功的椅子标记
            else:
                # 如果没有找到匹配的椅子，所有行人都没有匹配
                for chair in chairs:
                    if chair.chair_id not in matched_chairs:
                        matches[chair.chair_id] = False

        return matches