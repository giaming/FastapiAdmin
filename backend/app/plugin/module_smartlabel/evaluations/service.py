import traceback
from datetime import datetime

from sqlalchemy import select

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.database import async_db_session

from .crud import EvaluationCRUD, EvaluationDetailCRUD
from .eval_algorithm import match_annotations
from .model import (
    AnnotationModel,
    EvaluationModel,
    GtAnnotationModel,
    ImageMappingModel,
    ImageModel,
)
from .schema import EvaluationCreateSchema, EvaluationTriggerSchema


class SmartLabelEvaluationService:
    def __init__(self, auth: AuthSchema | None = None) -> None:
        self.auth = auth
        if auth:
            self.eval_crud = EvaluationCRUD(auth=auth)

    async def trigger_evaluation(self, schema: EvaluationTriggerSchema) -> dict:
        if not schema.force:
            existing = await self.eval_crud.get_by_unique_key(
                project_id=schema.project_id,
                user_id=schema.user_id,
                dataset_id=schema.dataset_id,
                status_list=["pending", "running"],
            )
            if existing:
                return {
                    "evaluation_id": existing.id,
                    "status": existing.status,
                    "message": "Evaluation already in progress",
                }

        create_schema = EvaluationCreateSchema(
            project_id=schema.project_id,
            user_id=schema.user_id,
            dataset_id=schema.dataset_id,
            triggered_by=self.auth.user.id if self.auth else None,
            status="pending",
        )
        new_eval = await self.eval_crud.create(data=create_schema)
        return {
            "evaluation_id": new_eval.id,
            "status": "pending",
            "message": "Evaluation triggered successfully",
        }

    async def run_evaluation_job(self, evaluation_id: int) -> None:
        async with async_db_session() as session:
            try:
                stmt = select(EvaluationModel).where(EvaluationModel.id == evaluation_id)
                result = await session.execute(stmt)
                eval_record = result.scalars().first()
                if not eval_record:
                    return

                eval_record.status = "running"
                await session.flush()

                stmt = select(ImageModel).where(ImageModel.project_id == eval_record.project_id)
                images = (await session.execute(stmt)).scalars().all()
                total_images = len(images)

                if total_images == 0:
                    eval_record.status = "completed"
                    eval_record.error_message = "No images found for this project"
                    await session.commit()
                    return

                stmt = select(ImageMappingModel).where(
                    ImageMappingModel.project_id == eval_record.project_id,
                    ImageMappingModel.dataset_id == eval_record.dataset_id,
                )
                mappings = (await session.execute(stmt)).scalars().all()
                mapping_dict = {m.human_image_id: m.dataset_image_id for m in mappings}

                dataset_image_ids = list(mapping_dict.values())
                human_image_ids = list(mapping_dict.keys())

                if not mapping_dict:
                    eval_record.status = "completed"
                    eval_record.error_message = "No mappings found between project and dataset"
                    await session.commit()
                    return

                stmt = select(AnnotationModel).where(
                    AnnotationModel.user_id == eval_record.user_id,
                    AnnotationModel.image_id.in_(human_image_ids),
                )
                human_anns = (await session.execute(stmt)).scalars().all()

                stmt = select(GtAnnotationModel).where(
                    GtAnnotationModel.dataset_image_id.in_(dataset_image_ids),
                    GtAnnotationModel.is_reference == True,
                )
                gt_anns = (await session.execute(stmt)).scalars().all()

                human_anns_by_img: dict[int, list[dict]] = {}
                for ann in human_anns:
                    if ann.image_id is None:
                        continue
                    human_anns_by_img.setdefault(ann.image_id, []).append(
                        {
                            "annotation_id": ann.annotation_id,
                            "type": ann.type,
                            "class_name": ann.class_name,
                            "x": ann.x,
                            "y": ann.y,
                            "width": ann.width,
                            "height": ann.height,
                        }
                    )

                gt_anns_by_img: dict[int, list[dict]] = {}
                for ann in gt_anns:
                    gt_anns_by_img.setdefault(ann.dataset_image_id, []).append(
                        {
                            "id": ann.id,
                            "type": ann.type,
                            "class_name": ann.class_name,
                            "x": ann.x,
                            "y": ann.y,
                            "width": ann.width,
                            "height": ann.height,
                        }
                    )

                detail_crud = EvaluationDetailCRUD(session)
                await detail_crud.delete_by_evaluation_id(evaluation_id)

                all_details: list[dict] = []
                total_annotations = len(human_anns)

                for h_img_id, d_img_id in mapping_dict.items():
                    h_anns = human_anns_by_img.get(h_img_id, [])
                    g_anns = gt_anns_by_img.get(d_img_id, [])
                    if not h_anns or not g_anns:
                        continue

                    matched = match_annotations(h_anns, g_anns)
                    for match in matched:
                        match["evaluation_id"] = evaluation_id
                        match["human_image_id"] = h_img_id
                        match["dataset_image_id"] = d_img_id
                        all_details.append(match)

                batch_size = 1000
                for i in range(0, len(all_details), batch_size):
                    await detail_crud.batch_create(all_details[i : i + batch_size])

                avg_iou = sum(d["iou"] for d in all_details) / len(all_details) if all_details else 0.0
                class_match_rate = (
                    sum(1 for d in all_details if d["class_match"]) / len(all_details) if all_details else 0.0
                )
                quality_score = (
                    sum(d["single_quality_score"] for d in all_details) / len(all_details)
                    if all_details
                    else 0.0
                )

                eval_record.total_images = total_images
                eval_record.total_annotations = total_annotations
                eval_record.avg_iou = avg_iou
                eval_record.class_match_rate = class_match_rate
                eval_record.quality_score = quality_score
                eval_record.status = "completed"
                eval_record.evaluated_time = datetime.now()

                await session.commit()
            except Exception as e:
                await session.rollback()
                try:
                    stmt = select(EvaluationModel).where(EvaluationModel.id == evaluation_id)
                    eval_record = (await session.execute(stmt)).scalars().first()
                    if eval_record:
                        eval_record.status = "failed"
                        eval_record.error_message = str(e) + "\n" + traceback.format_exc()
                        await session.commit()
                except Exception:
                    pass


async def run_smartlabel_evaluation_job(evaluation_id: int) -> None:
    service = SmartLabelEvaluationService(auth=None)
    await service.run_evaluation_job(evaluation_id)
