def compute_iou(box1: dict, box2: dict) -> float:
    """计算两个矩形框的IoU"""
    x1_1, y1_1 = box1['x'] - box1['width'] / 2, box1['y'] - box1['height'] / 2
    x2_1, y2_1 = box1['x'] + box1['width'] / 2, box1['y'] + box1['height'] / 2

    x1_2, y1_2 = box2['x'] - box2['width'] / 2, box2['y'] - box2['height'] / 2
    x2_2, y2_2 = box2['x'] + box2['width'] / 2, box2['y'] + box2['height'] / 2

    inter_x1 = max(x1_1, x1_2)
    inter_y1 = max(y1_1, y1_2)
    inter_x2 = min(x2_1, x2_2)
    inter_y2 = min(y2_1, y2_2)

    if inter_x1 < inter_x2 and inter_y1 < inter_y2:
        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        box1_area = box1['width'] * box1['height']
        box2_area = box2['width'] * box2['height']
        union_area = box1_area + box2_area - inter_area
        return inter_area / union_area if union_area > 0 else 0.0
    return 0.0

def match_annotations(
    human_anns: list[dict], 
    gt_anns: list[dict], 
    iou_threshold: float = 0.5,
    strict_classmatch: bool = True,
    w_iou: float = 0.8,
    w_class: float = 0.2
) -> list[dict]:
    """匹配标注并计算评估详情
    返回匹配结果列表，未匹配的不返回
    要求 class_match=1 且 iou>=threshold
    """
    matched_details = []
    used_gt_indices = set()

    for h_ann in human_anns:
        best_iou = 0.0
        best_gt_idx = -1
        
        # 如果不是 rect 类型，暂时跳过计算（v1 仅支持 rect）
        if h_ann.get('type') != 'rect':
            continue

        for i, gt_ann in enumerate(gt_anns):
            if i in used_gt_indices:
                continue
            
            if gt_ann.get('type') != 'rect':
                continue

            # 类别匹配检查
            class_match = (h_ann.get('class_name') == gt_ann.get('class_name'))
            if strict_classmatch and not class_match:
                continue

            iou = compute_iou(h_ann, gt_ann)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = i

        # 根据业务口径：要求 class_match=1, 只统计 iou>=threshold，未匹配不写入 details
        if best_iou >= iou_threshold and best_gt_idx != -1:
            gt_ann = gt_anns[best_gt_idx]
            used_gt_indices.add(best_gt_idx)
            
            single_score = (w_iou * best_iou + w_class * 1.0) * 100
            
            matched_details.append({
                'human_annotation_id': h_ann.get('id') or h_ann.get('annotation_id'),
                'gt_annotation_id': gt_ann.get('id'),
                'iou': best_iou,
                'class_match': True,
                'bbox_diff_x': h_ann.get('x', 0) - gt_ann.get('x', 0),
                'bbox_diff_y': h_ann.get('y', 0) - gt_ann.get('y', 0),
                'bbox_diff_width': h_ann.get('width', 0) - gt_ann.get('width', 0),
                'bbox_diff_height': h_ann.get('height', 0) - gt_ann.get('height', 0),
                'single_quality_score': single_score
            })

    return matched_details
