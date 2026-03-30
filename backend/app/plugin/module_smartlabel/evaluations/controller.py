from typing import Annotated

from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.logger import log
from app.core.router_class import OperationLogRoute

from .crud import EvaluationCRUD
from .schema import (
    EvaluationOutSchema,
    EvaluationQueryParam,
    EvaluationTriggerSchema,
)
from .service import SmartLabelEvaluationService, run_smartlabel_evaluation_job

SmartLabelRouter = APIRouter(route_class=OperationLogRoute, prefix="/evaluations", tags=["SmartLabel 评估模块"])


@SmartLabelRouter.post(
    "/trigger",
    summary="触发全量评估",
    description="触发按项目的全量评估任务",
    response_model=ResponseSchema[dict],
)
async def trigger_evaluation_controller(
    data: EvaluationTriggerSchema,
    auth: Annotated[AuthSchema, Depends(AuthPermission())],
) -> JSONResponse:
    """触发全量评估"""
    service = SmartLabelEvaluationService(auth=auth)
    result = await service.trigger_evaluation(data)

    if result.get("status") == "pending":
        from datetime import datetime, timedelta

        from apscheduler.triggers.date import DateTrigger

        from app.core.ap_scheduler import SchedulerUtil, scheduler

        if not SchedulerUtil.is_running():
            SchedulerUtil.start()

        evaluation_id = result["evaluation_id"]
        job_id = f"smartlabel_eval_{evaluation_id}"
        trigger = DateTrigger(run_date=datetime.now() + timedelta(seconds=0.1), timezone="Asia/Shanghai")
        try:
            scheduler.add_job(
                func=run_smartlabel_evaluation_job,
                trigger=trigger,
                kwargs={"evaluation_id": evaluation_id},
                id=job_id,
                name=f"SmartLabel 评估 ({evaluation_id})",
                jobstore="default",
                executor="default",
                max_instances=1,
                replace_existing=True,
            )
        except Exception:
            log.error("添加 SmartLabel 评估任务失败", exc_info=True)

    log.info(f"触发评估任务：project_id={data.project_id}, status={result['status']}")
    return SuccessResponse(data=result, msg="触发评估任务成功")


@SmartLabelRouter.get(
    "",
    summary="查询评估列表",
    description="分页查询评估记录",
    response_model=ResponseSchema[list[EvaluationOutSchema]],
)
async def get_evaluations_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[EvaluationQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission())],
) -> JSONResponse:
    """查询评估列表"""
    crud = EvaluationCRUD(auth=auth)
    # 将 dataclass 转换为字典用于查询
    search_dict = {k: getattr(search, k) for k in search.__dict__ if hasattr(search, k)}
    
    result_dict = await crud.page_crud(
        offset=page.page_no,
        limit=page.page_size,
        search=search_dict,
        order_by=page.order_by,
    )
    return SuccessResponse(data=result_dict, msg="查询评估列表成功")


@SmartLabelRouter.get(
    "/{id}",
    summary="查询评估详情汇总",
    description="查询评估记录汇总信息",
    response_model=ResponseSchema[EvaluationOutSchema],
)
async def get_evaluation_detail_controller(
    id: Annotated[int, Path(description="评估 ID")],
    auth: Annotated[AuthSchema, Depends(AuthPermission())],
) -> JSONResponse:
    """查询评估详情汇总"""
    crud = EvaluationCRUD(auth=auth)
    result = await crud.get_by_id_crud(id=id)
    if not result:
        return SuccessResponse(code=404, msg="评估记录不存在")
    return SuccessResponse(data=EvaluationOutSchema.model_validate(result).model_dump(), msg="查询评估详情成功")
