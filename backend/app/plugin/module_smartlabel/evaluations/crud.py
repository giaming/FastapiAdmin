from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_crud import CRUDBase

from .model import (
    EvaluationDetailModel,
    EvaluationModel,
)
from .schema import (
    EvaluationCreateSchema,
    EvaluationOutSchema,
    EvaluationUpdateSchema,
)


class EvaluationCRUD(CRUDBase[EvaluationModel, EvaluationCreateSchema, EvaluationUpdateSchema]):
    """评估记录数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=EvaluationModel, auth=auth)

    async def get_by_id_crud(self, id: int) -> EvaluationModel | None:
        return await self.get(id=id)

    async def get_by_unique_key(self, project_id: int, user_id: int, dataset_id: int, status_list: list[str]) -> EvaluationModel | None:
        """根据联合键查找特定状态的评估记录"""
        stmt = select(self.model).where(
            self.model.project_id == project_id,
            self.model.user_id == user_id,
            self.model.dataset_id == dataset_id,
            self.model.status.in_(status_list)
        ).order_by(self.model.id.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict] | None = None,
    ) -> Sequence[EvaluationModel]:
        return await self.list(search=search, order_by=order_by)

    async def create_crud(self, data: EvaluationCreateSchema) -> EvaluationModel | None:
        return await self.create(data=data)

    async def update_crud(self, id: int, data: EvaluationUpdateSchema) -> EvaluationModel | None:
        return await self.update(id=id, data=data)

    async def delete_crud(self, ids: list[int]) -> None:
        # 注意业务上应该先删除 details
        return await self.delete(ids=ids)

    async def page_crud(
        self,
        offset: int,
        limit: int,
        order_by: list[dict] | None = None,
        search: dict | None = None,
    ) -> dict:
        order_by_list = order_by or [{"id": "desc"}]
        search_dict = search or {}
        return await self.page(
            offset=offset,
            limit=limit,
            order_by=order_by_list,
            search=search_dict,
            out_schema=EvaluationOutSchema,
        )


class EvaluationDetailCRUD:
    """评估详情数据层（不使用CRUDBase，因为不需要通用鉴权和软删除等）"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.model = EvaluationDetailModel

    async def delete_by_evaluation_id(self, evaluation_id: int) -> None:
        """根据评估ID删除所有明细"""
        stmt = delete(self.model).where(self.model.evaluation_id == evaluation_id)
        await self.db.execute(stmt)
        await self.db.flush()

    async def batch_create(self, records: list[dict]) -> None:
        """批量插入明细"""
        if not records:
            return
        
        # 将字典转换为模型实例
        instances = [self.model(**record) for record in records]
        self.db.add_all(instances)
        await self.db.flush()
