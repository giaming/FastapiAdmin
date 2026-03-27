# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class ProjectsModel(ModelMixin, UserMixin):
    """
    项目管理表
    """
    __tablename__: str = 'sl_projects'
    __table_args__: dict[str, str] = {'comment': '项目管理'}
    __loader_options__: list[str] = ["created_by", "updated_by"]

    name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='项目名称')
    setup_type: Mapped[str | None] = mapped_column(String(64), nullable=True, comment='项目类型')
    annotation_style_config: Mapped[str | None] = mapped_column(Text, nullable=True, comment='标注类型配置')
    owner_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment='所有者')

