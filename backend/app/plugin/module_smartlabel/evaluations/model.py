import enum
from datetime import datetime

from sqlalchemy import (
    BIGINT,
    JSON,
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import MappedBase

# 导入已有的 DatasetsModel，避免重复定义
from app.plugin.module_smartlabel.datasets.model import DatasetsModel as DatasetModel


class DatasetImageModel(MappedBase):
    __tablename__: str = "sl_dataset_images"
    __table_args__: dict[str, str] = {"comment": "数据集图像表"}

    dataset_image_id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True, comment="数据集图像ID")
    dataset_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True, comment="所属数据集ID")
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False, comment="相对路径")
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True, comment="文件哈希")
    width: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="图像宽度")
    height: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="图像高度")
    split_type: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="数据划分：train/val/test")
    created_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, nullable=True, comment="创建时间")
    updated_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=True, comment="更新时间")


class GtAnnotationModel(MappedBase):
    __tablename__: str = "sl_gt_annotations"
    __table_args__: dict[str, str] = {"comment": "金标准标注表"}

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True, comment="主键ID")
    dataset_image_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True, comment="所属图像ID")
    type: Mapped[str] = mapped_column(String(64), nullable=False, comment="标注类型")
    class_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="类别名称")
    x: Mapped[float | None] = mapped_column(Float, nullable=True, comment="X坐标")
    y: Mapped[float | None] = mapped_column(Float, nullable=True, comment="Y坐标")
    width: Mapped[float | None] = mapped_column(Float, nullable=True, comment="宽度")
    height: Mapped[float | None] = mapped_column(Float, nullable=True, comment="高度")
    rotation: Mapped[float | None] = mapped_column(Float, default=0.0, nullable=True, comment="旋转角度")
    segmentation: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="分割数据")
    source: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="来源")
    confidence: Mapped[float | None] = mapped_column(Float, default=1.0, nullable=True, comment="置信度")
    is_reference: Mapped[bool | None] = mapped_column(Boolean, default=True, nullable=True, comment="是否作为参考标准")
    annotated_by: Mapped[int | None] = mapped_column(BIGINT, nullable=True, comment="标注者")
    reviewed_by: Mapped[int | None] = mapped_column(BIGINT, nullable=True, comment="审核者")
    review_status: Mapped[str | None] = mapped_column(String(32), default="approved", nullable=True, comment="审核状态")
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True, comment="审核备注")
    created_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, nullable=True, comment="创建时间")
    updated_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=True, comment="更新时间")


class EvaluationModel(MappedBase):
    __tablename__: str = "sl_evaluations"
    __table_args__: dict[str, str] = {"comment": "评估记录表"}

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True, comment="主键ID")
    project_id: Mapped[int] = mapped_column(BIGINT, nullable=False, comment="所属项目ID")
    user_id: Mapped[int] = mapped_column(BIGINT, nullable=False, comment="被评估学员ID")
    dataset_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True, comment="使用的数据集ID")
    triggered_by: Mapped[int | None] = mapped_column(BIGINT, nullable=True, comment="触发者ID")
    total_images: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="评估的图像总数")
    total_annotations: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="评估的标注总数")
    avg_iou: Mapped[float | None] = mapped_column(Float, nullable=True, comment="平均IoU")
    class_match_rate: Mapped[float | None] = mapped_column(Float, nullable=True, comment="类别匹配率")
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True, comment="综合质量评分")
    metrics_by_class: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="按类别统计指标")
    status: Mapped[str | None] = mapped_column(String(32), default="pending", nullable=True, comment="评估状态")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    evaluated_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, index=True, nullable=True, comment="评估完成时间")
    created_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, nullable=True, comment="创建时间")
    updated_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=True, comment="更新时间")


class EvaluationDetailModel(MappedBase):
    __tablename__: str = "sl_evaluation_details"
    __table_args__: dict[str, str] = {"comment": "评估详情表"}

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True, comment="主键ID")
    evaluation_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True, comment="所属评估记录ID")
    human_image_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True, comment="学员侧图像ID")
    dataset_image_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True, comment="数据集侧图像ID")
    human_annotation_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True, index=True, comment="学员标注ID")
    gt_annotation_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True, index=True, comment="金标准ID")
    iou: Mapped[float | None] = mapped_column(Float, nullable=True, comment="交并比")
    class_match: Mapped[bool | None] = mapped_column(Boolean, nullable=True, comment="类别是否匹配")
    bbox_diff_x: Mapped[float | None] = mapped_column(Float, nullable=True, comment="X坐标差异")
    bbox_diff_y: Mapped[float | None] = mapped_column(Float, nullable=True, comment="Y坐标差异")
    bbox_diff_width: Mapped[float | None] = mapped_column(Float, nullable=True, comment="宽度差异")
    bbox_diff_height: Mapped[float | None] = mapped_column(Float, nullable=True, comment="高度差异")
    single_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True, comment="单条质量分")


class ImageMappingModel(MappedBase):
    __tablename__: str = "sl_image_mappings"
    __table_args__: dict[str, str] = {"comment": "图像映射表"}

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True, comment="主键ID")
    project_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True, comment="项目ID")
    human_image_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True, comment="学员侧图像ID")
    dataset_id: Mapped[int] = mapped_column(BIGINT, nullable=False, comment="数据集ID")
    dataset_image_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True, comment="数据集侧图像ID")
    match_method: Mapped[str | None] = mapped_column(String(32), default="hash", nullable=True, comment="匹配方法")
    match_confidence: Mapped[float | None] = mapped_column(Float, default=1.0, nullable=True, comment="匹配置信度")
    is_locked: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True, comment="是否锁定")
    created_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, nullable=True, comment="创建时间")
    updated_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=True, comment="更新时间")


# 已有的相关的表映射（为查询准备）
class ImageModel(MappedBase):
    __tablename__: str = "sl_images"
    __table_args__: dict[str, str] = {"comment": "项目图像表"}

    image_id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True, comment="主键ID")
    project_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True, comment="所属项目ID")
    absolute_path: Mapped[str] = mapped_column(String(512), nullable=False, comment="绝对路径")
    width: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="宽度")
    height: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="高度")


class AnnotationModel(MappedBase):
    __tablename__: str = "sl_annotations"
    __table_args__: dict[str, str] = {"comment": "学员标注表"}

    annotation_id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True, comment="主键ID")
    image_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True, index=True, comment="图像ID")
    user_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True, index=True, comment="用户ID")
    type: Mapped[str] = mapped_column(String(64), nullable=False, comment="标注类型")
    class_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="类别名称")
    x: Mapped[float | None] = mapped_column(Float, nullable=True, comment="X坐标")
    y: Mapped[float | None] = mapped_column(Float, nullable=True, comment="Y坐标")
    width: Mapped[float | None] = mapped_column(Float, nullable=True, comment="宽度")
    height: Mapped[float | None] = mapped_column(Float, nullable=True, comment="高度")
    rotation: Mapped[float | None] = mapped_column(Float, default=0.0, nullable=True, comment="旋转角度")
    segmentation: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="分割数据")
