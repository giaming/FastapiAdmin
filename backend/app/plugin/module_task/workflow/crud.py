from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_crud import CRUDBase

from .model import WorkflowModel
from .schema import (
    WorkflowCreateSchema,
    WorkflowUpdateSchema,
)


class WorkflowCRUD(CRUDBase[WorkflowModel, WorkflowCreateSchema, WorkflowUpdateSchema]):
    """工作流数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化工作流 CRUD

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        self.auth = auth
        super().__init__(model=WorkflowModel, auth=auth)

    async def get_obj_by_id_crud(self, id: int) -> WorkflowModel | None:
        """
        获取工作流详情

        参数:
        - id (int): 工作流 ID

        返回:
        - WorkflowModel | None: 工作流模型，如果不存在则为 None
        """
        return await self.get(id=id)

    async def get_obj_list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[WorkflowModel]:
        """
        获取工作流列表

        参数:
        - search (dict | None): 查询参数字典
        - order_by (list[dict[str, str]] | None): 排序参数列表

        返回:
        - list[WorkflowModel]: 工作流模型序列
        """
        return await self.list(search=search, order_by=order_by)

    async def create_obj_crud(self, data: WorkflowCreateSchema) -> WorkflowModel | None:
        """
        创建工作流

        参数:
        - data (WorkflowCreateSchema): 创建工作流模型

        返回:
        - WorkflowModel | None: 创建的工作流模型，如果创建失败则为 None
        """
        return await self.create(data=data)

    async def update_obj_crud(self, id: int, data: WorkflowUpdateSchema) -> WorkflowModel | None:
        """
        更新工作流

        参数:
        - id (int): 工作流 ID
        - data (WorkflowUpdateSchema): 更新工作流模型

        返回:
        - WorkflowModel | None: 更新后的工作流模型，如果更新失败则为 None
        """
        return await self.update(id=id, data=data)

    async def delete_obj_crud(self, ids: list[int]) -> None:
        """
        删除工作流

        参数:
        - ids (list[int]): 工作流 ID 列表
        """
        return await self.delete(ids=ids)
