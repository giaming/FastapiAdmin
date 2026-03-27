from dataclasses import dataclass
from typing import Any

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema
from app.core.validator import DateTimeStr


class EvaluationConfigSchema(BaseModel):
    """评估配置模型"""
    iou_threshold: float = Field(default=0.5, description="IoU阈值")
    strict_classmatch: bool = Field(default=True, description="严格匹配类别")
    match_strategy: str = Field(default="greedy", description="匹配策略")
    w_iou: float = Field(default=0.8, description="IoU权重")
    w_class: float = Field(default=0.2, description="类别权重")


class EvaluationTriggerSchema(BaseModel):
    """触发评估请求模型"""
    project_id: int = Field(..., description="所属项目ID")
    user_id: int = Field(..., description="被评估学员ID")
    dataset_id: int = Field(..., description="使用的数据集ID")
    force: bool = Field(default=False, description="是否强制重新评估")
    config: EvaluationConfigSchema | None = Field(default=None, description="评估配置")


class EvaluationCreateSchema(BaseModel):
    """评估记录创建模型"""
    project_id: int
    user_id: int
    dataset_id: int
    triggered_by: int | None = None
    status: str = "pending"


class EvaluationUpdateSchema(BaseModel):
    """评估记录更新模型"""
    status: str | None = None
    total_images: int | None = None
    total_annotations: int | None = None
    avg_iou: float | None = None
    class_match_rate: float | None = None
    quality_score: float | None = None
    metrics_by_class: dict[str, Any] | None = None
    error_message: str | None = None
    evaluated_time: Any | None = None


class EvaluationOutSchema(BaseModel):
    """评估记录响应模型"""
    id: int
    project_id: int
    user_id: int
    dataset_id: int
    triggered_by: int | None
    total_images: int | None
    total_annotations: int | None
    avg_iou: float | None
    class_match_rate: float | None
    quality_score: float | None
    metrics_by_class: dict[str, Any] | None
    status: str
    error_message: str | None
    evaluated_time: Any | None
    created_time: Any | None
    updated_time: Any | None

    model_config = ConfigDict(from_attributes=True)


@dataclass
class EvaluationQueryParam:
    """评估查询参数"""

    def __init__(
        self,
        project_id: int | None = Query(None, description="项目ID"),
        user_id: int | None = Query(None, description="用户ID"),
        dataset_id: int | None = Query(None, description="数据集ID"),
        status: str | None = Query(None, description="状态"),
    ) -> None:
        if project_id:
            self.project_id = (QueueEnum.eq.value, project_id)
        if user_id:
            self.user_id = (QueueEnum.eq.value, user_id)
        if dataset_id:
            self.dataset_id = (QueueEnum.eq.value, dataset_id)
        if status:
            self.status = (QueueEnum.eq.value, status)


class EvaluationDetailOutSchema(BaseModel):
    """评估详情响应模型"""
    id: int
    evaluation_id: int
    human_image_id: int | None
    dataset_image_id: int | None
    human_annotation_id: int | None
    gt_annotation_id: int | None
    iou: float | None
    class_match: bool | None
    bbox_diff_x: float | None
    bbox_diff_y: float | None
    bbox_diff_width: float | None
    bbox_diff_height: float | None
    single_quality_score: float | None

    model_config = ConfigDict(from_attributes=True)


@dataclass
class EvaluationDetailQueryParam:
    """评估详情查询参数"""

    def __init__(
        self,
        evaluation_id: int = Query(..., description="评估ID"),
        human_image_id: int | None = Query(None, description="人类图像ID"),
    ) -> None:
        self.evaluation_id = (QueueEnum.eq.value, evaluation_id)
        if human_image_id:
            self.human_image_id = (QueueEnum.eq.value, human_image_id)
