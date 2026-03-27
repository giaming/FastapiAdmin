# -*- coding: utf-8 -*-

from pydantic import BaseModel, ConfigDict, Field
from fastapi import Query
from app.core.validator import DateTimeStr
from datetime import datetime
from app.core.validator import DateTimeStr
from app.common.enums import QueueEnum
from app.core.base_schema import BaseSchema, UserBySchema

class ProjectsCreateSchema(BaseModel):
    """
    项目管理新增模型
    """
    name: str = Field(default=..., description='项目名称')
    description: str | None = Field(default=None, max_length=255, description='项目描述')
    setup_type: str = Field(default=..., description='项目类型')
    annotation_style_config: str | None = Field(default=None, description='标注类型配置')
    owner_id: int = Field(default=..., description='所有者')


class ProjectsUpdateSchema(ProjectsCreateSchema):
    """
    项目管理更新模型
    """
    ...


class ProjectsOutSchema(ProjectsCreateSchema, BaseSchema, UserBySchema):
    """
    项目管理响应模型
    """
    model_config = ConfigDict(from_attributes=True)


class ProjectsQueryParam:
    """项目管理查询参数"""

    def __init__(
        self,
        name: str | None = Query(None, description="项目名称"),
        description: str | None = Query(None, description="项目描述"),
        setup_type: str | None = Query(None, description="项目类型"),
        annotation_style_config: str | None = Query(None, description="标注类型配置"),
        owner_id: int | None = Query(None, description="所有者"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
        updated_time: list[DateTimeStr] | None = Query(None, description="更新时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
    ) -> None:
        # 模糊查询字段
        self.name = (QueueEnum.like.value, name)
        # 模糊查询字段
        self.description = (QueueEnum.like.value, description)
        # 精确查询字段
        if setup_type:
            self.setup_type = (QueueEnum.eq.value, setup_type)
        # 精确查询字段
        if annotation_style_config:
            self.annotation_style_config = (QueueEnum.eq.value, annotation_style_config)
        # 精确查询字段
        if owner_id:
            self.owner_id = (QueueEnum.eq.value, owner_id)
        # 时间范围查询
        if created_time and len(created_time) == 2:
            self.created_time = (QueueEnum.between.value, (created_time[0], created_time[1]))
        if updated_time and len(updated_time) == 2:
            self.updated_time = (QueueEnum.between.value, (updated_time[0], updated_time[1]))
