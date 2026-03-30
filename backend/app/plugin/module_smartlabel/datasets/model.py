# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import BigInteger, Integer, Text, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import MappedBase


class DatasetsModel(MappedBase):
    """
    数据集管理表
    """
    __tablename__: str = 'sl_datasets'
    __table_args__: dict[str, str] = {'comment': '数据集管理'}

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment='主键ID'
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True, comment='数据集名称')
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='数据集描述')
    version: Mapped[str | None] = mapped_column(String(64), nullable=True, comment='数据集版本号')
    source: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='数据集来源')
    total_images: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True, comment='总共图片数')
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment='创建者')
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment='更新者')
    created_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, nullable=True, comment='创建时间')
    updated_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=True, comment='更新时间')
