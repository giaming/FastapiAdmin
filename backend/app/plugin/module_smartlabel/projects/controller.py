# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, UploadFile, Body, Path, Query
from fastapi.responses import StreamingResponse, JSONResponse

from app.common.response import SuccessResponse, StreamResponse
from app.core.dependencies import AuthPermission
from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_params import PaginationQueryParam
from app.utils.common_util import bytes2file_response
from app.core.logger import log
from app.core.base_schema import BatchSetAvailable

from .service import ProjectsService
from .schema import ProjectsCreateSchema, ProjectsUpdateSchema, ProjectsQueryParam

ProjectsRouter = APIRouter(prefix='/projects', tags=["项目管理模块"]) 

@ProjectsRouter.get(
    "/detail/{id}",
    summary="获取项目管理详情",
    description="获取项目管理详情"
)
async def get_projects_detail_controller(
    id: int = Path(..., description="ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:projects:query"]))
) -> JSONResponse:
    """
    获取项目管理详情接口
    
    参数:
    - id: int - 数据ID
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含项目管理详情的JSON响应
    """
    result_dict = await ProjectsService.detail_projects_service(auth=auth, id=id)
    log.info(f"获取项目管理详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取项目管理详情成功")

@ProjectsRouter.get(
    "/list",
    summary="查询项目管理列表",
    description="查询项目管理列表"
)
async def get_projects_list_controller(
    page: PaginationQueryParam = Depends(),
    search: ProjectsQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:projects:query"]))
) -> JSONResponse:
    """
    查询项目管理列表接口（数据库分页）
    
    参数:
    - page: PaginationQueryParam - 分页参数
    - search: ProjectsQueryParam - 查询参数
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含项目管理列表的JSON响应
    """
    result_dict = await ProjectsService.page_projects_service(
        auth=auth,
        page_no=page.page_no if page.page_no is not None else 1,
        page_size=page.page_size if page.page_size is not None else 10,
        search=search,
        order_by=page.order_by
    )
    log.info("查询项目管理列表成功")
    return SuccessResponse(data=result_dict, msg="查询项目管理列表成功")

@ProjectsRouter.post(
    "/create",
    summary="创建项目管理",
    description="创建项目管理"
)
async def create_projects_controller(
    data: ProjectsCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:projects:create"]))
) -> JSONResponse:
    """
    创建项目管理接口
    
    参数:
    - data: ProjectsCreateSchema - 创建数据
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含创建项目管理结果的JSON响应
    """
    result_dict = await ProjectsService.create_projects_service(auth=auth, data=data)
    log.info("创建项目管理成功")
    return SuccessResponse(data=result_dict, msg="创建项目管理成功")

@ProjectsRouter.put(
    "/update/{id}",
    summary="修改项目管理",
    description="修改项目管理"
)
async def update_projects_controller(
    data: ProjectsUpdateSchema,
    id: int = Path(..., description="ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:projects:update"]))
) -> JSONResponse:
    """
    修改项目管理接口
    
    参数:
    - id: int - 数据ID
    - data: ProjectsUpdateSchema - 更新数据
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含修改项目管理结果的JSON响应
    """
    result_dict = await ProjectsService.update_projects_service(auth=auth, id=id, data=data)
    log.info("修改项目管理成功")
    return SuccessResponse(data=result_dict, msg="修改项目管理成功")

@ProjectsRouter.delete(
    "/delete",
    summary="删除项目管理",
    description="删除项目管理"
)
async def delete_projects_controller(
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:projects:delete"]))
) -> JSONResponse:
    """
    删除项目管理接口
    
    参数:
    - ids: list[int] - 数据ID列表
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含删除项目管理结果的JSON响应
    """
    await ProjectsService.delete_projects_service(auth=auth, ids=ids)
    log.info(f"删除项目管理成功: {ids}")
    return SuccessResponse(msg="删除项目管理成功")

@ProjectsRouter.patch(
    "/available/setting",
    summary="批量修改项目管理状态",
    description="批量修改项目管理状态"
)
async def batch_set_available_projects_controller(
    data: BatchSetAvailable,
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:projects:patch"]))
) -> JSONResponse:
    """
    批量修改项目管理状态接口
    
    参数:
    - data: BatchSetAvailable - 批量修改状态数据
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含批量修改项目管理状态结果的JSON响应
    """
    await ProjectsService.set_available_projects_service(auth=auth, data=data)
    log.info(f"批量修改项目管理状态成功: {data.ids}")
    return SuccessResponse(msg="批量修改项目管理状态成功")

@ProjectsRouter.post(
    '/export',
    summary="导出项目管理",
    description="导出项目管理"
)
async def export_projects_list_controller(
    search: ProjectsQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:projects:export"]))
) -> StreamingResponse:
    """
    导出项目管理接口
    
    参数:
    - search: ProjectsQueryParam - 查询参数
    - auth: AuthSchema - 认证信息
    
    返回:
    - StreamingResponse - 包含导出项目管理数据的流式响应
    """
    result_dict_list = await ProjectsService.list_projects_service(search=search, auth=auth)
    export_result = await ProjectsService.batch_export_projects_service(obj_list=result_dict_list)
    log.info('导出项目管理成功')
    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=sl_projects.xlsx'}
    )

@ProjectsRouter.post(
    '/import',
    summary="导入项目管理",
    description="导入项目管理"
)
async def import_projects_list_controller(
    file: UploadFile,
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:projects:import"]))
) -> JSONResponse:
    """
    导入项目管理接口
    
    参数:
    - file: UploadFile - 上传的Excel文件
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含导入项目管理结果的JSON响应
    """
    batch_import_result = await ProjectsService.batch_import_projects_service(file=file, auth=auth, update_support=True)
    log.info("导入项目管理成功")
    return SuccessResponse(data=batch_import_result, msg="导入项目管理成功")

@ProjectsRouter.post(
    '/download/template',
    summary="获取项目管理导入模板",
    description="获取项目管理导入模板",
    dependencies=[Depends(AuthPermission(["module_smartlabel:projects:download"]))]
)
async def export_projects_template_controller() -> StreamingResponse:
    """
    获取项目管理导入模板接口
    
    返回:
    - StreamingResponse - 包含项目管理导入模板的流式响应
    """
    import_template_result = await ProjectsService.import_template_download_projects_service()
    log.info('获取项目管理导入模板成功')
    return StreamResponse(
        data=bytes2file_response(import_template_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=sl_projects_template.xlsx'}
    )