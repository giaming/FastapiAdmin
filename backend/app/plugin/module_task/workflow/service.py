from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.exceptions import CustomException

from .crud import WorkflowCRUD
from .schema import (
    WorkflowCreateSchema,
    WorkflowOutSchema,
    WorkflowQueryParam,
    WorkflowUpdateSchema,
)


class WorkflowService:
    """工作流管理服务层"""

    @classmethod
    async def get_workflow_list_service(
        cls,
        auth: AuthSchema,
        search: WorkflowQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None,
    ) -> list[dict]:
        """
        获取工作流列表

        参数:
        - auth (AuthSchema): 认证信息模型
        - search (WorkflowQueryParam | None): 查询参数模型
        - order_by (list[dict[str, str]] | None): 排序参数列表

        返回:
        - list[dict]: 工作流详情字典列表
        """
        obj_list = await WorkflowCRUD(auth).get_obj_list_crud(search=search.__dict__, order_by=order_by)
        return [WorkflowOutSchema.model_validate(obj).model_dump() for obj in obj_list]

    @classmethod
    async def get_workflow_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        获取工作流详情

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 工作流 ID

        返回:
        - dict: 工作流详情字典
        """
        obj = await WorkflowCRUD(auth).get_obj_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg="工作流不存在")
        return WorkflowOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def create_workflow_service(cls, auth: AuthSchema, data: WorkflowCreateSchema) -> dict:
        """
        创建工作流

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (WorkflowCreateSchema): 工作流创建模型

        返回:
        - dict: 工作流详情字典
        """
        exist_obj = await WorkflowCRUD(auth).get(code=data.code)
        if exist_obj:
            raise CustomException(msg="创建失败，该流程编码已存在")

        obj = await WorkflowCRUD(auth).create_obj_crud(data=data)
        if not obj:
            raise CustomException(msg="创建失败")
        return WorkflowOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def update_workflow_service(cls, auth: AuthSchema, id: int, data: WorkflowUpdateSchema) -> dict:
        """
        更新工作流

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 工作流 ID
        - data (WorkflowUpdateSchema): 工作流更新模型

        返回:
        - dict: 工作流详情字典
        """
        exist_obj = await WorkflowCRUD(auth).get_obj_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg="更新失败，该工作流不存在")

        # 检查编码是否被其他工作流使用
        other_obj = await WorkflowCRUD(auth).get(code=data.code)
        if other_obj and other_obj.id != id:
            raise CustomException(msg="更新失败，该流程编码已被使用")

        obj = await WorkflowCRUD(auth).update_obj_crud(id=id, data=data)
        if not obj:
            raise CustomException(msg="更新失败")
        return WorkflowOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def delete_workflow_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        """
        删除工作流

        参数:
        - auth (AuthSchema): 认证信息模型
        - ids (list[int]): 工作流 ID 列表
        """
        if len(ids) < 1:
            raise CustomException(msg="删除失败，删除对象不能为空")

        for id in ids:
            exist_obj = await WorkflowCRUD(auth).get_obj_by_id_crud(id=id)
            if not exist_obj:
                raise CustomException(msg="删除失败，该工作流不存在")

        await WorkflowCRUD(auth).delete_obj_crud(ids=ids)
