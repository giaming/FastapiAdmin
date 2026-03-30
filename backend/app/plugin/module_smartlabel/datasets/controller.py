# -*- coding: utf-8 -*-

from fastapi import APIRouter, Body, Depends, File, Form, Path, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse

from app.common.response import SuccessResponse, StreamResponse
from app.core.dependencies import AuthPermission
from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_params import PaginationQueryParam
from app.utils.common_util import bytes2file_response
from app.core.logger import log

from .service import DatasetsService
from .schema import DatasetsCreateSchema, DatasetsUpdateSchema, DatasetsQueryParam

DatasetsRouter = APIRouter(prefix='/datasets', tags=["数据集管理模块"]) 

@DatasetsRouter.get(
    "/detail/{id}",
    summary="获取数据集管理详情",
    description="获取数据集管理详情"
)
async def get_datasets_detail_controller(
    id: int = Path(..., description="ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:datasets:detail"]))
) -> JSONResponse:
    """
    获取数据集管理详情接口
    
    参数:
    - id: int - 数据ID
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含数据集管理详情的JSON响应
    """
    result_dict = await DatasetsService.detail_datasets_service(auth=auth, id=id)
    log.info(f"获取数据集管理详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取数据集管理详情成功")

@DatasetsRouter.get(
    "/list",
    summary="查询数据集管理列表",
    description="查询数据集管理列表"
)
async def get_datasets_list_controller(
    page: PaginationQueryParam = Depends(),
    search: DatasetsQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:datasets:query"]))
) -> JSONResponse:
    """
    查询数据集管理列表接口（数据库分页）
    
    参数:
    - page: PaginationQueryParam - 分页参数
    - search: DatasetsQueryParam - 查询参数
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含数据集管理列表的JSON响应
    """
    result_dict = await DatasetsService.page_datasets_service(
        auth=auth,
        page_no=page.page_no if page.page_no is not None else 1,
        page_size=page.page_size if page.page_size is not None else 10,
        search=search,
        order_by=page.order_by
    )
    log.info("查询数据集管理列表成功")
    return SuccessResponse(data=result_dict, msg="查询数据集管理列表成功")

@DatasetsRouter.post(
    "/create",
    summary="创建数据集管理",
    description="创建数据集管理"
)
async def create_datasets_controller(
    data: DatasetsCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:datasets:create"]))
) -> JSONResponse:
    """
    创建数据集管理接口
    
    参数:
    - data: DatasetsCreateSchema - 创建数据
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含创建数据集管理结果的JSON响应
    """
    result_dict = await DatasetsService.create_datasets_service(auth=auth, data=data)
    log.info("创建数据集管理成功")
    return SuccessResponse(data=result_dict, msg="创建数据集管理成功")


@DatasetsRouter.post(
    "/import/coco",
    summary="上传COCO数据集并创建",
    description="上传COCO数据集并创建（包含图片zip与annotations.json）",
)
async def import_coco_datasets_controller(
    name: str = Form(..., description="数据集名称"),
    description: str | None = Form(None, description="数据集描述"),
    version: str | None = Form(None, description="数据集版本号"),
    source: str | None = Form("coco", description="数据集来源"),
    split_type: str | None = Form(None, description="数据划分：train/val/test"),
    images_zip: UploadFile = File(..., description="图片zip包"),
    annotations_json: UploadFile = File(..., description="COCO标注json文件"),
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:datasets:create"])),
) -> JSONResponse:
    result_dict = await DatasetsService.import_coco_dataset_service(
        auth=auth,
        name=name,
        description=description,
        version=version,
        source=source,
        split_type=split_type,
        images_zip=images_zip,
        annotations_json=annotations_json,
    )
    log.info("上传COCO数据集并创建成功")
    return SuccessResponse(data=result_dict, msg="上传COCO数据集并创建成功")

@DatasetsRouter.put(
    "/update/{id}",
    summary="修改数据集管理",
    description="修改数据集管理"
)
async def update_datasets_controller(
    data: DatasetsUpdateSchema,
    id: int = Path(..., description="ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:datasets:update"]))
) -> JSONResponse:
    """
    修改数据集管理接口
    
    参数:
    - id: int - 数据ID
    - data: DatasetsUpdateSchema - 更新数据
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含修改数据集管理结果的JSON响应
    """
    result_dict = await DatasetsService.update_datasets_service(auth=auth, id=id, data=data)
    log.info("修改数据集管理成功")
    return SuccessResponse(data=result_dict, msg="修改数据集管理成功")

@DatasetsRouter.delete(
    "/delete",
    summary="删除数据集管理",
    description="删除数据集管理"
)
async def delete_datasets_controller(
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:datasets:delete"]))
) -> JSONResponse:
    """
    删除数据集管理接口
    
    参数:
    - ids: list[int] - 数据ID列表
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含删除数据集管理结果的JSON响应
    """
    await DatasetsService.delete_datasets_service(auth=auth, ids=ids)
    log.info(f"删除数据集管理成功: {ids}")
    return SuccessResponse(msg="删除数据集管理成功")

@DatasetsRouter.patch(
    '/export',
    summary="导出数据集管理",
    description="导出数据集管理"
)
async def export_datasets_list_controller(
    search: DatasetsQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:datasets:export"]))
) -> StreamingResponse:
    """
    导出数据集管理接口
    
    参数:
    - search: DatasetsQueryParam - 查询参数
    - auth: AuthSchema - 认证信息
    
    返回:
    - StreamingResponse - 包含导出数据集管理数据的流式响应
    """
    result_dict_list = await DatasetsService.list_datasets_service(search=search, auth=auth)
    export_result = await DatasetsService.batch_export_datasets_service(obj_list=result_dict_list)
    log.info('导出数据集管理成功')
    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=sl_datasets.xlsx'}
    )

@DatasetsRouter.post(
    '/import',
    summary="导入数据集管理",
    description="导入数据集管理"
)
async def import_datasets_list_controller(
    file: UploadFile,
    auth: AuthSchema = Depends(AuthPermission(["module_smartlabel:datasets:import"]))
) -> JSONResponse:
    """
    导入数据集管理接口
    
    参数:
    - file: UploadFile - 上传的Excel文件
    - auth: AuthSchema - 认证信息
    
    返回:
    - JSONResponse - 包含导入数据集管理结果的JSON响应
    """
    batch_import_result = await DatasetsService.batch_import_datasets_service(file=file, auth=auth, update_support=True)
    log.info("导入数据集管理成功")
    return SuccessResponse(data=batch_import_result, msg="导入数据集管理成功")

@DatasetsRouter.post(
    '/download/template',
    summary="获取数据集管理导入模板",
    description="获取数据集管理导入模板",
    dependencies=[Depends(AuthPermission(["module_smartlabel:datasets:download"]))]
)
async def export_datasets_template_controller() -> StreamingResponse:
    """
    获取数据集管理导入模板接口
    
    返回:
    - StreamingResponse - 包含数据集管理导入模板的流式响应
    """
    import_template_result = await DatasetsService.import_template_download_datasets_service()
    log.info('获取数据集管理导入模板成功')
    return StreamResponse(
        data=bytes2file_response(import_template_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=sl_datasets_template.xlsx'}
    )
