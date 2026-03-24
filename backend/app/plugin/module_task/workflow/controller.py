from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.request import PaginationService
from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.logger import log
from app.core.router_class import OperationLogRoute

from .schema import WorkflowCreateSchema, WorkflowOutSchema, WorkflowQueryParam, WorkflowUpdateSchema
from .service import WorkflowService

WorkflowRouter = APIRouter(route_class=OperationLogRoute, prefix="/workflow", tags=["工作流管理"])


@WorkflowRouter.get(
    "/list",
    summary="查询工作流列表",
    description="查询工作流列表",
    response_model=ResponseSchema[list[WorkflowOutSchema]],
)
async def get_workflow_list_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[WorkflowQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_task:workflow:query"]))],
) -> JSONResponse:
    """
    查询工作流列表

    参数:
    - page (PaginationQueryParam): 分页查询参数模型
    - search (WorkflowQueryParam): 查询参数模型
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含分页后的工作流列表
    """
    result_dict_list = await WorkflowService.get_workflow_list_service(auth=auth, search=search)
    result_dict = await PaginationService.paginate(
        data_list=result_dict_list,
        page_no=page.page_no,
        page_size=page.page_size,
    )
    log.info("查询工作流列表成功")
    return SuccessResponse(data=result_dict, msg="查询工作流列表成功")


@WorkflowRouter.get(
    "/detail/{id}",
    summary="获取工作流详情",
    description="获取工作流详情",
    response_model=ResponseSchema[WorkflowOutSchema],
)
async def get_workflow_detail_controller(
    id: Annotated[int, Path(description="工作流 ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_task:workflow:detail"]))],
) -> JSONResponse:
    """
    获取工作流详情

    参数:
    - id (int): 工作流 ID
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含工作流详情
    """
    result_dict = await WorkflowService.get_workflow_detail_service(id=id, auth=auth)
    log.info(f"获取工作流详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取工作流详情成功")


@WorkflowRouter.post(
    "/create",
    summary="创建工作流",
    description="创建工作流",
    response_model=ResponseSchema[WorkflowOutSchema],
)
async def create_workflow_controller(
    data: Annotated[WorkflowCreateSchema, Body(description="工作流创建数据")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_task:workflow:create"]))],
) -> JSONResponse:
    """
    创建工作流

    参数:
    - data (WorkflowCreateSchema): 工作流创建数据
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含创建的工作流详情
    """
    result_dict = await WorkflowService.create_workflow_service(auth=auth, data=data)
    log.info("创建工作流成功")
    return SuccessResponse(data=result_dict, msg="创建工作流成功")


@WorkflowRouter.put(
    "/update/{id}",
    summary="更新工作流",
    description="更新工作流",
    response_model=ResponseSchema[WorkflowOutSchema],
)
async def update_workflow_controller(
    id: Annotated[int, Path(description="工作流 ID")],
    data: Annotated[WorkflowUpdateSchema, Body(description="工作流更新数据")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_task:workflow:update"]))],
) -> JSONResponse:
    """
    更新工作流

    参数:
    - id (int): 工作流 ID
    - data (WorkflowUpdateSchema): 工作流更新数据
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含更新的工作流详情
    """
    result_dict = await WorkflowService.update_workflow_service(id=id, auth=auth, data=data)
    log.info(f"更新工作流成功 {id}")
    return SuccessResponse(data=result_dict, msg="更新工作流成功")


@WorkflowRouter.delete(
    "/delete",
    summary="删除工作流",
    description="删除工作流",
    response_model=ResponseSchema[None],
)
async def delete_workflow_controller(
    ids: Annotated[list[int], Body(description="工作流 ID 列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_task:workflow:delete"]))],
) -> JSONResponse:
    """
    删除工作流

    参数:
    - ids (list[int]): 工作流 ID 列表
    - auth (AuthSchema): 认证信息模型
    """
    await WorkflowService.delete_workflow_service(auth=auth, ids=ids)
    log.info(f"删除工作流成功：{ids}")
    return SuccessResponse(msg="删除工作流成功")
