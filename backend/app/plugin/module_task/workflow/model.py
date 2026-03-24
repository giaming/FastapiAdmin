from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class WorkflowModel(ModelMixin, UserMixin):
    """
    工作流模型
    """

    __tablename__: str = "task_workflow"
    __table_args__: dict[str, str] = {"comment": "工作流表"}
    __loader_options__: list[str] = ["created_by", "updated_by"]

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="流程名称")
    code: Mapped[str] = mapped_column(String(64), nullable=False, comment="流程编码")
    status: Mapped[str] = mapped_column(String(32), nullable=False, comment="流程状态")
    nodes: Mapped[dict] = mapped_column(JSON, nullable=False, comment="节点数据 (JSON 格式)")
    edges: Mapped[dict] = mapped_column(JSON, nullable=False, comment="连线数据 (JSON 格式)")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注/描述")
