# -*- coding: utf-8 -*-

from pydantic import BaseModel, ConfigDict, Field
from fastapi import Query
from app.core.validator import DateTimeStr
from datetime import datetime
from app.core.validator import DateTimeStr
from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema, UserBySchema

class DatasetsCreateSchema(BaseModel):
    """
    数据集管理新增模型
    """
    dataset_id: int | None = Field(default=None, description='数据集 ID')
    name: str = Field(default=..., description='数据集名称')
    description: str | None = Field(default=None, max_length=255, description='数据集描述')
    version: str | None = Field(default=None, description='数据集版本号')
    source: str | None = Field(default=None, description='数据集来源')
    total_images: int | None = Field(default=0, description='总共图片数')
    created_by: int | None = Field(default=None, description='创建者')
    updated_by: int | None = Field(default=None, description='更新者')


class DatasetsUpdateSchema(DatasetsCreateSchema):
    """
    数据集管理更新模型
    """
    ...


class DatasetsOutSchema(DatasetsCreateSchema, BaseSchema, UserBySchema):
    """
    数据集管理响应模型
    """
    model_config = ConfigDict(from_attributes=True)


class DatasetsQueryParam:
    """数据集管理查询参数"""

    def __init__(
        self,
        name: str | None = Query(None, description="数据集名称"),
        version: str | None = Query(None, description="数据集版本号"),
        source: str | None = Query(None, description="数据集来源"),
        total_images: int | None = Query(None, description="总共图片数"),
        created_by: int | None = Query(None, description="创建者"),
        updated_by: int | None = Query(None, description="更新者"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
        updated_time: list[DateTimeStr] | None = Query(None, description="更新时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
    ) -> None:
        # 模糊查询字段
        self.name = (QueueEnum.like.value, name)
        # 精确查询字段
        if version:
            self.version = (QueueEnum.eq.value, version)
        # 精确查询字段
        if source:
            self.source = (QueueEnum.eq.value, source)
        # 精确查询字段
        if total_images:
            self.total_images = (QueueEnum.eq.value, total_images)
        # 精确查询字段
        if created_by:
            self.created_by = (QueueEnum.eq.value, created_by)
        # 精确查询字段
        if updated_by:
            self.updated_by = (QueueEnum.eq.value, updated_by)
        # 时间范围查询
        if created_time and len(created_time) == 2:
            self.created_time = (QueueEnum.between.value, (created_time[0], created_time[1]))
        if updated_time and len(updated_time) == 2:
            self.updated_time = (QueueEnum.between.value, (updated_time[0], updated_time[1]))
