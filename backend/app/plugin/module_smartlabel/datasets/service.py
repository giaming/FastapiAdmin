# -*- coding: utf-8 -*-

import asyncio
import hashlib
import io
import json
import mimetypes
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
import pandas as pd
from fastapi import UploadFile

from PIL import Image
from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.exceptions import CustomException
from app.config.setting import settings
from app.utils.excel_util import ExcelUtil

from .crud import DatasetsCRUD
from .schema import (
    DatasetsCreateSchema,
    DatasetsUpdateSchema,
    DatasetsOutSchema,
    DatasetsQueryParam
)


class DatasetsService:
    """
    数据集管理服务层
    """
    
    @classmethod
    async def detail_datasets_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        详情
        
        参数:
        - auth: AuthSchema - 认证信息
        - id: int - 数据ID
        
        返回:
        - dict - 数据详情
        """
        obj = await DatasetsCRUD(auth).get_by_id_datasets_crud(id=id)
        if not obj:
            raise CustomException(msg="该数据不存在")
        return DatasetsOutSchema.model_validate(obj).model_dump()
    
    @classmethod
    async def list_datasets_service(cls, auth: AuthSchema, search: DatasetsQueryParam | None = None, order_by: list[dict] | None = None) -> list[dict]:
        """
        列表查询
        
        参数:
        - auth: AuthSchema - 认证信息
        - search: DatasetsQueryParam | None - 查询参数
        - order_by: list[dict] | None - 排序参数
        
        返回:
        - list[dict] - 数据列表
        """
        search_dict = search.__dict__ if search else None
        obj_list = await DatasetsCRUD(auth).list_datasets_crud(search=search_dict, order_by=order_by)
        return [DatasetsOutSchema.model_validate(obj).model_dump() for obj in obj_list]

    @classmethod
    async def page_datasets_service(cls, auth: AuthSchema, page_no: int, page_size: int, search: DatasetsQueryParam | None = None, order_by: list[dict] | None = None) -> dict:
        """
        分页查询（数据库分页）
        
        参数:
        - auth: AuthSchema - 认证信息
        - page_no: int - 页码
        - page_size: int - 每页数量
        - search: DatasetsQueryParam | None - 查询参数
        - order_by: list[dict] | None - 排序参数
        
        返回:
        - dict - 分页查询结果
        """
        search_dict = search.__dict__ if search else {}
        order_by_list = order_by or [{'id': 'asc'}]
        offset = (page_no - 1) * page_size
        result = await DatasetsCRUD(auth).page_datasets_crud(
            offset=offset,
            limit=page_size,
            order_by=order_by_list,
            search=search_dict
        )
        return result
    
    @classmethod
    async def create_datasets_service(cls, auth: AuthSchema, data: DatasetsCreateSchema) -> dict:
        """
        创建
        
        参数:
        - auth: AuthSchema - 认证信息
        - data: DatasetsCreateSchema - 创建数据
        
        返回:
        - dict - 创建结果
        """
        if data.created_by is None:
            data.created_by = auth.user.id
        if data.updated_by is None:
            data.updated_by = auth.user.id
        obj = await DatasetsCRUD(auth).create_datasets_crud(data=data)
        return DatasetsOutSchema.model_validate(obj).model_dump()
    
    @classmethod
    async def update_datasets_service(cls, auth: AuthSchema, id: int, data: DatasetsUpdateSchema) -> dict:
        """
        更新
        
        参数:
        - auth: AuthSchema - 认证信息
        - id: int - 数据ID
        - data: DatasetsUpdateSchema - 更新数据
        
        返回:
        - dict - 更新结果
        """
        # 检查数据是否存在
        obj = await DatasetsCRUD(auth).get_by_id_datasets_crud(id=id)
        if not obj:
            raise CustomException(msg='更新失败，该数据不存在')
        
        # 检查唯一性约束
            
        if data.updated_by is None:
            data.updated_by = auth.user.id
        obj = await DatasetsCRUD(auth).update_datasets_crud(id=id, data=data)
        return DatasetsOutSchema.model_validate(obj).model_dump()
    
    @classmethod
    async def delete_datasets_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        """
        删除
        
        参数:
        - auth: AuthSchema - 认证信息
        - ids: list[int] - 数据ID列表
        
        返回:
        - None
        """
        if len(ids) < 1:
            raise CustomException(msg='删除失败，删除对象不能为空')
        for id in ids:
            obj = await DatasetsCRUD(auth).get_by_id_datasets_crud(id=id)
            if not obj:
                raise CustomException(msg=f'删除失败，ID为{id}的数据不存在')
        await DatasetsCRUD(auth).delete_datasets_crud(ids=ids)
    
    @classmethod
    @classmethod
    async def batch_export_datasets_service(cls, obj_list: list[dict]) -> bytes:
        """
        批量导出
        
        参数:
        - obj_list: list[dict] - 数据列表
        
        返回:
        - bytes - 导出的Excel文件内容
        """
        mapping_dict = {
            'id': '数据集ID',
            'name': '数据集名称',
            'description': '数据集描述',
            'version': '数据集版本号',
            'source': '数据集来源',
            'total_images': '总共图片数',
            'created_by': '创建者',
            'updated_by': '更新者',
            'created_time': '创建时间',
            'updated_time': '更新时间',
        }
        return ExcelUtil.export_list2excel(list_data=obj_list, mapping_dict=mapping_dict)

    @classmethod
    async def batch_import_datasets_service(cls, auth: AuthSchema, file: UploadFile, update_support: bool = False) -> str:
        """
        批量导入
        
        参数:
        - auth: AuthSchema - 认证信息
        - file: UploadFile - 上传的Excel文件
        - update_support: bool - 是否支持更新存在数据
        
        返回:
        - str - 导入结果信息
        """
        header_dict = {
            '数据集ID': 'id',
            '数据集名称': 'name',
            '数据集描述': 'description',
            '数据集版本号': 'version',
            '数据集来源': 'source',
            '总共图片数': 'total_images',
            '创建者': 'created_by',
            '更新者': 'updated_by',
        }

        try:
            def normalize(value):
                return None if pd.isna(value) else value

            # 读取Excel文件
            contents = await file.read()
            df = pd.read_excel(io.BytesIO(contents))
            await file.close()

            if df.empty:
                raise CustomException(msg="导入文件为空")

            # 检查表头是否完整
            missing_headers = [header for header in header_dict.keys() if header not in df.columns]
            if missing_headers:
                raise CustomException(msg=f"导入文件缺少必要的列: {', '.join(missing_headers)}")

            # 重命名列名
            df.rename(columns=header_dict, inplace=True)
            
            # 验证必填字段
            
            error_msgs = []
            success_count = 0
            count = 0
            
            for _index, row in df.iterrows():
                count += 1
                try:
                    data = {
                        "id": normalize(row.get('id')),
                        "name": row['name'],
                        "description": normalize(row.get('description')),
                        "version": normalize(row.get('version')),
                        "source": normalize(row.get('source')),
                        "total_images": normalize(row.get('total_images')),
                        "created_by": normalize(row.get('created_by')),
                        "updated_by": normalize(row.get('updated_by')),
                    }
                    # 使用CreateSchema做校验后入库
                    create_schema = DatasetsCreateSchema.model_validate(data)
                    
                    # 检查唯一性约束
                    
                    if update_support and create_schema.id is not None:
                        exists = await DatasetsCRUD(auth).get_by_id_datasets_crud(id=create_schema.id)
                        if exists:
                            update_schema = DatasetsUpdateSchema.model_validate(create_schema.model_dump())
                            await DatasetsCRUD(auth).update_datasets_crud(id=create_schema.id, data=update_schema)
                            success_count += 1
                            continue

                    await DatasetsCRUD(auth).create_datasets_crud(data=create_schema)
                    success_count += 1
                except Exception as e:
                    error_msgs.append(f"第{count}行: {str(e)}")
                    continue

            result = f"成功导入 {success_count} 条数据"
            if error_msgs:
                result += "\n错误信息:\n" + "\n".join(error_msgs)

            return result
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"导入失败: {e!s}")

    @classmethod
    async def import_coco_dataset_service(
        cls,
        auth: AuthSchema,
        name: str,
        description: str | None,
        version: str | None,
        source: str | None,
        split_type: str | None,
        images_zip: UploadFile,
        annotations_json: UploadFile,
    ) -> dict:
        from app.plugin.module_smartlabel.evaluations.model import DatasetImageModel, GtAnnotationModel
        from app.utils.minio_util import remove_objects_from_minio, upload_file_to_minio

        if not images_zip.filename or not images_zip.filename.lower().endswith(".zip"):
            raise CustomException(msg="图片文件必须为zip格式")
        if not annotations_json.filename or not annotations_json.filename.lower().endswith(".json"):
            raise CustomException(msg="标注文件必须为json格式")

        if images_zip.size and images_zip.size > 1024 * 1024 * 1024:
            raise CustomException(msg="图片zip过大，请分批导入")
        if annotations_json.size and annotations_json.size > 200 * 1024 * 1024:
            raise CustomException(msg="标注json过大，请分批导入")

        create_schema = DatasetsCreateSchema(
            name=name,
            description=description,
            version=version,
            source=source or "coco",
            total_images=0,
            created_by=auth.user.id if auth.user else None,
            updated_by=auth.user.id if auth.user else None,
        )

        dataset_obj = await DatasetsCRUD(auth).create_datasets_crud(data=create_schema)

        dataset_dir = settings.STATIC_ROOT.joinpath("datasets", str(dataset_obj.id))
        images_dir = dataset_dir.joinpath("images")
        images_dir.mkdir(parents=True, exist_ok=True)

        zip_path = dataset_dir.joinpath("images.zip")
        ann_path = dataset_dir.joinpath("annotations.json")

        use_minio = settings.DATASET_STORAGE_BACKEND == "minio"
        uploaded_keys: list[str] = []
        uploaded_key_set: set[str] = set()

        try:
            await _save_upload_file(images_zip, zip_path)
            await _save_upload_file(annotations_json, ann_path)

            extracted_paths = _safe_extract_zip(zip_path, images_dir)
            extracted_index = _build_basename_index(extracted_paths)

            coco = _load_json(ann_path)
            coco_images = coco.get("images") or []
            coco_annotations = coco.get("annotations") or []
            coco_categories = coco.get("categories") or []

            category_name_by_id: dict[int, str] = {}
            for c in coco_categories:
                try:
                    cid = int(c.get("id"))
                    cname = str(c.get("name") or "")
                    if cname:
                        category_name_by_id[cid] = cname
                except Exception:
                    continue

            if not isinstance(coco_images, list) or not coco_images:
                raise CustomException(msg="COCO标注文件缺少 images 列表")

            coco_image_id_to_row: dict[int, DatasetImageModel] = {}
            dataset_image_rows: list[DatasetImageModel] = []

            for img in coco_images:
                try:
                    coco_img_id = int(img.get("id"))
                except Exception:
                    continue
                file_name = str(img.get("file_name") or "").lstrip("/").replace("\\", "/")
                if not file_name or ".." in Path(file_name).parts:
                    raise CustomException(msg=f"非法图片路径: {file_name}")

                img_path = images_dir.joinpath(file_name)
                if not img_path.exists():
                    alt = extracted_index.get(Path(file_name).name)
                    if alt:
                        img_path = alt
                    else:
                        raise CustomException(msg=f"找不到图片文件: {file_name}")

                if use_minio:
                    object_key = f"{settings.MINIO_DATASET_PREFIX}/{dataset_obj.id}/images/{file_name}"
                    if object_key not in uploaded_key_set:
                        content_type = mimetypes.guess_type(file_name)[0]
                        key = await asyncio.to_thread(
                            upload_file_to_minio, img_path, object_key, content_type
                        )
                        uploaded_key_set.add(object_key)
                        uploaded_keys.append(key)

                width = img.get("width")
                height = img.get("height")
                if width is None or height is None:
                    try:
                        with Image.open(img_path) as im:
                            width, height = im.size
                    except Exception:
                        width, height = None, None

                file_hash = _sha256_file(img_path)

                row = DatasetImageModel(
                    dataset_id=int(dataset_obj.id),
                    relative_path=file_name,
                    file_hash=file_hash,
                    width=int(width) if width is not None else None,
                    height=int(height) if height is not None else None,
                    split_type=split_type,
                )
                dataset_image_rows.append(row)
                coco_image_id_to_row[coco_img_id] = row

            auth.db.add_all(dataset_image_rows)
            await auth.db.flush()

            coco_image_id_to_dataset_image_id: dict[int, int] = {}
            for coco_img_id, row in coco_image_id_to_row.items():
                coco_image_id_to_dataset_image_id[coco_img_id] = int(row.dataset_image_id)

            gt_rows: list[GtAnnotationModel] = []
            for ann in coco_annotations if isinstance(coco_annotations, list) else []:
                try:
                    coco_img_id = int(ann.get("image_id"))
                    dataset_image_id = coco_image_id_to_dataset_image_id.get(coco_img_id)
                    if not dataset_image_id:
                        continue
                    bbox = ann.get("bbox")
                    if not bbox or not isinstance(bbox, list) or len(bbox) < 4:
                        continue
                    x, y, w, h = bbox[:4]
                    x = float(x)
                    y = float(y)
                    w = float(w)
                    h = float(h)
                    cx = x + w / 2
                    cy = y + h / 2

                    category_id = ann.get("category_id")
                    class_name = None
                    try:
                        class_name = category_name_by_id.get(int(category_id)) if category_id is not None else None
                    except Exception:
                        class_name = None

                    segmentation = ann.get("segmentation")
                    is_reference = ann.get("is_reference")
                    if is_reference is None:
                        is_reference = True

                    gt_rows.append(
                        GtAnnotationModel(
                            dataset_image_id=dataset_image_id,
                            type="rect",
                            class_name=class_name,
                            x=cx,
                            y=cy,
                            width=w,
                            height=h,
                            rotation=0.0,
                            segmentation=segmentation if isinstance(segmentation, (list, dict)) else None,
                            source=source or "coco",
                            confidence=float(ann.get("score") or ann.get("confidence") or 1.0),
                            is_reference=bool(is_reference),
                            annotated_by=None,
                            reviewed_by=None,
                            review_status="approved",
                            review_notes=None,
                        )
                    )
                except Exception:
                    continue

            if gt_rows:
                auth.db.add_all(gt_rows)
                await auth.db.flush()

            dataset_obj.total_images = len(dataset_image_rows)
            await auth.db.flush()

            if use_minio:
                shutil.rmtree(images_dir, ignore_errors=True)

            return DatasetsOutSchema.model_validate(dataset_obj).model_dump()
        except Exception:
            if use_minio and uploaded_keys:
                await asyncio.to_thread(remove_objects_from_minio, uploaded_keys)
            shutil.rmtree(dataset_dir, ignore_errors=True)
            raise

    @classmethod
    async def import_voc_dataset_service(
        cls,
        auth: AuthSchema,
        name: str,
        description: str | None,
        version: str | None,
        source: str | None,
        split_type: str | None,
        images_zip: UploadFile,
        annotations_zip: UploadFile,
    ) -> dict:
        from app.plugin.module_smartlabel.evaluations.model import DatasetImageModel, GtAnnotationModel
        from app.utils.minio_util import remove_objects_from_minio, upload_file_to_minio

        if not images_zip.filename or not images_zip.filename.lower().endswith(".zip"):
            raise CustomException(msg="图片文件必须为zip格式")
        if not annotations_zip.filename or not annotations_zip.filename.lower().endswith(".zip"):
            raise CustomException(msg="标注文件必须为zip格式")

        create_schema = DatasetsCreateSchema(
            name=name,
            description=description,
            version=version,
            source=source or "voc",
            total_images=0,
            created_by=auth.user.id if auth.user else None,
            updated_by=auth.user.id if auth.user else None,
        )
        dataset_obj = await DatasetsCRUD(auth).create_datasets_crud(data=create_schema)

        dataset_dir = settings.STATIC_ROOT.joinpath("datasets", str(dataset_obj.id))
        images_dir = dataset_dir.joinpath("images")
        anns_dir = dataset_dir.joinpath("annotations")
        images_dir.mkdir(parents=True, exist_ok=True)
        anns_dir.mkdir(parents=True, exist_ok=True)

        zip_path = dataset_dir.joinpath("images.zip")
        ann_zip_path = dataset_dir.joinpath("annotations.zip")

        use_minio = settings.DATASET_STORAGE_BACKEND == "minio"
        uploaded_keys: list[str] = []
        uploaded_key_set: set[str] = set()

        try:
            await _save_upload_file(images_zip, zip_path)
            await _save_upload_file(annotations_zip, ann_zip_path)

            extracted_image_paths = _safe_extract_zip(zip_path, images_dir)
            extracted_ann_paths = _safe_extract_zip(ann_zip_path, anns_dir)
            extracted_image_index = _build_basename_index(extracted_image_paths)

            voc_items: list[dict[str, Any]] = []
            seen_file_names: set[str] = set()

            for xml_path in extracted_ann_paths:
                if not xml_path.is_file() or xml_path.suffix.lower() != ".xml":
                    continue
                try:
                    parsed = _parse_voc_xml(xml_path)
                except Exception:
                    continue

                file_name = str(parsed.get("file_name") or "").lstrip("/").replace("\\", "/")
                if not file_name or ".." in Path(file_name).parts:
                    continue
                if file_name in seen_file_names:
                    continue
                seen_file_names.add(file_name)

                img_path = images_dir.joinpath(file_name)
                if not img_path.exists():
                    alt = extracted_image_index.get(Path(file_name).name)
                    if alt:
                        img_path = alt
                    else:
                        raise CustomException(msg=f"找不到图片文件: {file_name}")

                width = parsed.get("width")
                height = parsed.get("height")
                if width is None or height is None:
                    try:
                        with Image.open(img_path) as im:
                            width, height = im.size
                    except Exception:
                        width, height = None, None

                if use_minio:
                    object_key = f"{settings.MINIO_DATASET_PREFIX}/{dataset_obj.id}/images/{file_name}"
                    if object_key not in uploaded_key_set:
                        content_type = mimetypes.guess_type(file_name)[0]
                        key = await asyncio.to_thread(
                            upload_file_to_minio, img_path, object_key, content_type
                        )
                        uploaded_key_set.add(object_key)
                        uploaded_keys.append(key)

                voc_items.append(
                    {
                        "file_name": file_name,
                        "img_path": img_path,
                        "width": width,
                        "height": height,
                        "objects": parsed.get("objects") or [],
                    }
                )

            if not voc_items:
                raise CustomException(msg="未找到可解析的VOC标注xml文件")

            dataset_image_rows: list[DatasetImageModel] = []
            for item in voc_items:
                img_path = item["img_path"]
                file_hash = _sha256_file(img_path)
                dataset_image_rows.append(
                    DatasetImageModel(
                        dataset_id=int(dataset_obj.id),
                        relative_path=str(item["file_name"]),
                        file_hash=file_hash,
                        width=int(item["width"]) if item.get("width") is not None else None,
                        height=int(item["height"]) if item.get("height") is not None else None,
                        split_type=split_type,
                    )
                )

            auth.db.add_all(dataset_image_rows)
            await auth.db.flush()

            file_name_to_dataset_image_id: dict[str, int] = {}
            for row in dataset_image_rows:
                file_name_to_dataset_image_id[str(row.relative_path)] = int(row.dataset_image_id)

            gt_rows: list[GtAnnotationModel] = []
            for item in voc_items:
                dataset_image_id = file_name_to_dataset_image_id.get(str(item["file_name"]))
                if not dataset_image_id:
                    continue
                for obj in item.get("objects") or []:
                    try:
                        class_name = obj.get("class_name")
                        bbox = obj.get("bbox") or {}
                        xmin = float(bbox.get("xmin"))
                        ymin = float(bbox.get("ymin"))
                        xmax = float(bbox.get("xmax"))
                        ymax = float(bbox.get("ymax"))
                        w = max(0.0, xmax - xmin)
                        h = max(0.0, ymax - ymin)
                        if w <= 0 or h <= 0:
                            continue
                        cx = xmin + w / 2
                        cy = ymin + h / 2
                        gt_rows.append(
                            GtAnnotationModel(
                                dataset_image_id=dataset_image_id,
                                type="rect",
                                class_name=str(class_name) if class_name else None,
                                x=cx,
                                y=cy,
                                width=w,
                                height=h,
                                rotation=0.0,
                                segmentation=None,
                                source=source or "voc",
                                confidence=1.0,
                                is_reference=True,
                                annotated_by=None,
                                reviewed_by=None,
                                review_status="approved",
                                review_notes=None,
                            )
                        )
                    except Exception:
                        continue

            if gt_rows:
                auth.db.add_all(gt_rows)
                await auth.db.flush()

            dataset_obj.total_images = len(dataset_image_rows)
            await auth.db.flush()

            if use_minio:
                shutil.rmtree(images_dir, ignore_errors=True)

            return DatasetsOutSchema.model_validate(dataset_obj).model_dump()
        except Exception:
            if use_minio and uploaded_keys:
                await asyncio.to_thread(remove_objects_from_minio, uploaded_keys)
            shutil.rmtree(dataset_dir, ignore_errors=True)
            raise

    @classmethod
    async def import_yolo_dataset_service(
        cls,
        auth: AuthSchema,
        name: str,
        description: str | None,
        version: str | None,
        source: str | None,
        split_type: str | None,
        images_zip: UploadFile,
        labels_zip: UploadFile,
        data_yaml: UploadFile | None,
    ) -> dict:
        from app.plugin.module_smartlabel.evaluations.model import DatasetImageModel, GtAnnotationModel
        from app.utils.minio_util import remove_objects_from_minio, upload_file_to_minio

        if not images_zip.filename or not images_zip.filename.lower().endswith(".zip"):
            raise CustomException(msg="图片文件必须为zip格式")
        if not labels_zip.filename or not labels_zip.filename.lower().endswith(".zip"):
            raise CustomException(msg="labels文件必须为zip格式")
        if data_yaml and data_yaml.filename and not data_yaml.filename.lower().endswith((".yaml", ".yml")):
            raise CustomException(msg="data.yaml 必须为 yaml 格式")

        create_schema = DatasetsCreateSchema(
            name=name,
            description=description,
            version=version,
            source=source or "yolo",
            total_images=0,
            created_by=auth.user.id if auth.user else None,
            updated_by=auth.user.id if auth.user else None,
        )
        dataset_obj = await DatasetsCRUD(auth).create_datasets_crud(data=create_schema)

        dataset_dir = settings.STATIC_ROOT.joinpath("datasets", str(dataset_obj.id))
        images_dir = dataset_dir.joinpath("images")
        labels_dir = dataset_dir.joinpath("labels")
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

        images_zip_path = dataset_dir.joinpath("images.zip")
        labels_zip_path = dataset_dir.joinpath("labels.zip")
        yaml_path = dataset_dir.joinpath("data.yaml") if data_yaml else None

        use_minio = settings.DATASET_STORAGE_BACKEND == "minio"
        uploaded_keys: list[str] = []
        uploaded_key_set: set[str] = set()

        try:
            await _save_upload_file(images_zip, images_zip_path)
            await _save_upload_file(labels_zip, labels_zip_path)
            if data_yaml and yaml_path is not None:
                await _save_upload_file(data_yaml, yaml_path)

            extracted_image_paths = _safe_extract_zip(images_zip_path, images_dir)
            extracted_label_paths = _safe_extract_zip(labels_zip_path, labels_dir)

            label_by_rel: dict[str, Path] = {}
            label_by_stem: dict[str, Path] = {}
            for p in extracted_label_paths:
                if not p.is_file() or p.suffix.lower() != ".txt":
                    continue
                try:
                    rel = p.resolve().relative_to(labels_dir.resolve()).as_posix()
                except Exception:
                    continue
                label_by_rel.setdefault(rel, p)
                label_by_stem.setdefault(p.stem, p)

            class_name_by_id: dict[int, str] = {}
            if yaml_path is not None and yaml_path.exists():
                try:
                    class_name_by_id = _parse_yolo_data_yaml(_load_text(yaml_path))
                except Exception:
                    class_name_by_id = {}

            image_items: list[dict[str, Any]] = []
            for p in extracted_image_paths:
                if not p.is_file() or not _is_image_file(p):
                    continue
                try:
                    rel = p.resolve().relative_to(images_dir.resolve()).as_posix()
                except Exception:
                    continue
                rel = rel.lstrip("/").replace("\\", "/")
                if not rel or ".." in PurePosixPath(rel).parts:
                    continue

                label_rel = str(PurePosixPath(rel).with_suffix(".txt"))
                label_path = label_by_rel.get(label_rel)
                if label_path is None:
                    label_path = label_by_stem.get(Path(rel).stem)

                width = None
                height = None
                try:
                    with Image.open(p) as im:
                        width, height = im.size
                except Exception:
                    width, height = None, None

                if use_minio:
                    object_key = f"{settings.MINIO_DATASET_PREFIX}/{dataset_obj.id}/images/{rel}"
                    if object_key not in uploaded_key_set:
                        content_type = mimetypes.guess_type(rel)[0]
                        key = await asyncio.to_thread(
                            upload_file_to_minio, p, object_key, content_type
                        )
                        uploaded_key_set.add(object_key)
                        uploaded_keys.append(key)

                image_items.append(
                    {
                        "relative_path": rel,
                        "img_path": p,
                        "label_path": label_path,
                        "width": width,
                        "height": height,
                    }
                )

            if not image_items:
                raise CustomException(msg="图片zip中未找到可用图片文件")

            dataset_image_rows: list[DatasetImageModel] = []
            for item in image_items:
                file_hash = _sha256_file(item["img_path"])
                dataset_image_rows.append(
                    DatasetImageModel(
                        dataset_id=int(dataset_obj.id),
                        relative_path=str(item["relative_path"]),
                        file_hash=file_hash,
                        width=int(item["width"]) if item.get("width") is not None else None,
                        height=int(item["height"]) if item.get("height") is not None else None,
                        split_type=split_type,
                    )
                )

            auth.db.add_all(dataset_image_rows)
            await auth.db.flush()

            rel_to_dataset_image_id: dict[str, int] = {}
            for row in dataset_image_rows:
                rel_to_dataset_image_id[str(row.relative_path)] = int(row.dataset_image_id)

            gt_rows: list[GtAnnotationModel] = []
            for item in image_items:
                rel = str(item["relative_path"])
                dataset_image_id = rel_to_dataset_image_id.get(rel)
                if not dataset_image_id:
                    continue
                label_path = item.get("label_path")
                if not label_path or not Path(label_path).exists():
                    continue
                img_w = item.get("width")
                img_h = item.get("height")
                if not img_w or not img_h:
                    continue
                for line in _load_text(Path(label_path)).splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    try:
                        cls_id = int(float(parts[0]))
                        cx = float(parts[1])
                        cy = float(parts[2])
                        w = float(parts[3])
                        h = float(parts[4])
                    except Exception:
                        continue
                    if 0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0 and 0.0 <= w <= 1.0 and 0.0 <= h <= 1.0:
                        cx *= float(img_w)
                        cy *= float(img_h)
                        w *= float(img_w)
                        h *= float(img_h)
                    if w <= 0 or h <= 0:
                        continue
                    class_name = class_name_by_id.get(cls_id) or f"class_{cls_id}"
                    gt_rows.append(
                        GtAnnotationModel(
                            dataset_image_id=dataset_image_id,
                            type="rect",
                            class_name=class_name,
                            x=cx,
                            y=cy,
                            width=w,
                            height=h,
                            rotation=0.0,
                            segmentation=None,
                            source=source or "yolo",
                            confidence=1.0,
                            is_reference=True,
                            annotated_by=None,
                            reviewed_by=None,
                            review_status="approved",
                            review_notes=None,
                        )
                    )

            if gt_rows:
                auth.db.add_all(gt_rows)
                await auth.db.flush()

            dataset_obj.total_images = len(dataset_image_rows)
            await auth.db.flush()

            if use_minio:
                shutil.rmtree(images_dir, ignore_errors=True)

            return DatasetsOutSchema.model_validate(dataset_obj).model_dump()
        except Exception:
            if use_minio and uploaded_keys:
                await asyncio.to_thread(remove_objects_from_minio, uploaded_keys)
            shutil.rmtree(dataset_dir, ignore_errors=True)
            raise

    @classmethod
    async def import_csv_dataset_service(
        cls,
        auth: AuthSchema,
        name: str,
        description: str | None,
        version: str | None,
        source: str | None,
        split_type: str | None,
        images_zip: UploadFile,
        annotations_csv: UploadFile,
    ) -> dict:
        from app.plugin.module_smartlabel.evaluations.model import DatasetImageModel, GtAnnotationModel
        from app.utils.minio_util import remove_objects_from_minio, upload_file_to_minio

        if not images_zip.filename or not images_zip.filename.lower().endswith(".zip"):
            raise CustomException(msg="图片文件必须为zip格式")
        if not annotations_csv.filename or not annotations_csv.filename.lower().endswith(".csv"):
            raise CustomException(msg="标注文件必须为csv格式")

        create_schema = DatasetsCreateSchema(
            name=name,
            description=description,
            version=version,
            source=source or "csv",
            total_images=0,
            created_by=auth.user.id if auth.user else None,
            updated_by=auth.user.id if auth.user else None,
        )
        dataset_obj = await DatasetsCRUD(auth).create_datasets_crud(data=create_schema)

        dataset_dir = settings.STATIC_ROOT.joinpath("datasets", str(dataset_obj.id))
        images_dir = dataset_dir.joinpath("images")
        images_dir.mkdir(parents=True, exist_ok=True)

        images_zip_path = dataset_dir.joinpath("images.zip")
        csv_path = dataset_dir.joinpath("annotations.csv")

        use_minio = settings.DATASET_STORAGE_BACKEND == "minio"
        uploaded_keys: list[str] = []
        uploaded_key_set: set[str] = set()

        try:
            await _save_upload_file(images_zip, images_zip_path)
            await _save_upload_file(annotations_csv, csv_path)

            extracted_image_paths = _safe_extract_zip(images_zip_path, images_dir)
            extracted_image_index = _build_basename_index(extracted_image_paths)

            df = _read_csv_any(csv_path)
            if df is None or df.empty:
                raise CustomException(msg="标注csv为空")

            df_columns = {str(c).strip().lower(): c for c in df.columns}

            def pick_col(candidates: list[str]) -> str | None:
                for c in candidates:
                    key = c.lower()
                    if key in df_columns:
                        return str(df_columns[key])
                return None

            col_file = pick_col(["file_name", "filename", "image", "image_path", "path", "relative_path"])
            if not col_file:
                raise CustomException(msg="标注csv缺少 file_name 列")

            col_class = pick_col(["class_name", "class", "label", "category", "name"])
            col_conf = pick_col(["confidence", "score", "prob"])
            col_seg = pick_col(["segmentation"])
            col_type = pick_col(["type"])
            col_is_ref = pick_col(["is_reference", "reference"])

            col_xmin = pick_col(["xmin", "x_min", "left"])
            col_ymin = pick_col(["ymin", "y_min", "top"])
            col_xmax = pick_col(["xmax", "x_max", "right"])
            col_ymax = pick_col(["ymax", "y_max", "bottom"])

            col_cx = pick_col(["cx", "center_x"])
            col_cy = pick_col(["cy", "center_y"])
            col_w = pick_col(["w", "width"])
            col_h = pick_col(["h", "height"])
            if col_cx is None and pick_col(["x"]) is not None:
                col_cx = pick_col(["x"])
            if col_cy is None and pick_col(["y"]) is not None:
                col_cy = pick_col(["y"])

            has_xyxy = all([col_xmin, col_ymin, col_xmax, col_ymax])
            has_cxcywh = all([col_cx, col_cy, col_w, col_h])
            if not has_xyxy and not has_cxcywh:
                raise CustomException(msg="标注csv缺少 bbox 列（xmin/ymin/xmax/ymax 或 cx/cy/width/height）")

            file_names: list[str] = []
            for v in df[col_file].tolist():
                s = str(v or "").strip().lstrip("/").replace("\\", "/")
                if not s or ".." in Path(s).parts:
                    continue
                file_names.append(s)

            if not file_names:
                raise CustomException(msg="标注csv缺少有效 file_name")

            unique_file_names: list[str] = []
            seen: set[str] = set()
            for fn in file_names:
                if fn in seen:
                    continue
                seen.add(fn)
                unique_file_names.append(fn)

            image_items: list[dict[str, Any]] = []
            for fn in unique_file_names:
                img_path = images_dir.joinpath(fn)
                if not img_path.exists():
                    alt = extracted_image_index.get(Path(fn).name)
                    if alt:
                        img_path = alt
                    else:
                        raise CustomException(msg=f"找不到图片文件: {fn}")

                width = None
                height = None
                try:
                    with Image.open(img_path) as im:
                        width, height = im.size
                except Exception:
                    width, height = None, None

                if use_minio:
                    object_key = f"{settings.MINIO_DATASET_PREFIX}/{dataset_obj.id}/images/{fn}"
                    if object_key not in uploaded_key_set:
                        content_type = mimetypes.guess_type(fn)[0]
                        key = await asyncio.to_thread(
                            upload_file_to_minio, img_path, object_key, content_type
                        )
                        uploaded_key_set.add(object_key)
                        uploaded_keys.append(key)

                image_items.append(
                    {
                        "file_name": fn,
                        "img_path": img_path,
                        "width": width,
                        "height": height,
                    }
                )

            dataset_image_rows: list[DatasetImageModel] = []
            for item in image_items:
                file_hash = _sha256_file(item["img_path"])
                dataset_image_rows.append(
                    DatasetImageModel(
                        dataset_id=int(dataset_obj.id),
                        relative_path=str(item["file_name"]),
                        file_hash=file_hash,
                        width=int(item["width"]) if item.get("width") is not None else None,
                        height=int(item["height"]) if item.get("height") is not None else None,
                        split_type=split_type,
                    )
                )

            auth.db.add_all(dataset_image_rows)
            await auth.db.flush()

            file_name_to_dataset_image_id: dict[str, int] = {}
            for row in dataset_image_rows:
                file_name_to_dataset_image_id[str(row.relative_path)] = int(row.dataset_image_id)

            gt_rows: list[GtAnnotationModel] = []
            for _, r in df.iterrows():
                try:
                    fn = str(r.get(col_file) or "").strip().lstrip("/").replace("\\", "/")
                    if not fn or ".." in Path(fn).parts:
                        continue
                    dataset_image_id = file_name_to_dataset_image_id.get(fn)
                    if not dataset_image_id:
                        continue

                    class_name = None
                    if col_class:
                        v = r.get(col_class)
                        if v is not None and str(v).strip() != "":
                            class_name = str(v).strip()

                    confidence = 1.0
                    if col_conf:
                        v = r.get(col_conf)
                        if v is not None and str(v).strip() != "":
                            confidence = float(v)

                    segmentation = None
                    if col_seg:
                        v = r.get(col_seg)
                        if v is not None and str(v).strip() != "":
                            try:
                                seg = json.loads(str(v))
                                if isinstance(seg, (list, dict)):
                                    segmentation = seg
                            except Exception:
                                segmentation = None

                    is_reference = True
                    if col_is_ref:
                        v = r.get(col_is_ref)
                        if v is not None and str(v).strip() != "":
                            is_reference = bool(int(v)) if str(v).strip().isdigit() else bool(v)

                    anno_type = "rect"
                    if col_type:
                        v = r.get(col_type)
                        if v is not None and str(v).strip() != "":
                            anno_type = str(v).strip()

                    if has_xyxy:
                        xmin = float(r.get(col_xmin))
                        ymin = float(r.get(col_ymin))
                        xmax = float(r.get(col_xmax))
                        ymax = float(r.get(col_ymax))
                        w = max(0.0, xmax - xmin)
                        h = max(0.0, ymax - ymin)
                        if w <= 0 or h <= 0:
                            continue
                        cx = xmin + w / 2
                        cy = ymin + h / 2
                    else:
                        cx = float(r.get(col_cx))
                        cy = float(r.get(col_cy))
                        w = float(r.get(col_w))
                        h = float(r.get(col_h))
                        if w <= 0 or h <= 0:
                            continue

                    gt_rows.append(
                        GtAnnotationModel(
                            dataset_image_id=dataset_image_id,
                            type=anno_type,
                            class_name=class_name,
                            x=cx,
                            y=cy,
                            width=w,
                            height=h,
                            rotation=0.0,
                            segmentation=segmentation,
                            source=source or "csv",
                            confidence=confidence,
                            is_reference=is_reference,
                            annotated_by=None,
                            reviewed_by=None,
                            review_status="approved",
                            review_notes=None,
                        )
                    )
                except Exception:
                    continue

            if gt_rows:
                auth.db.add_all(gt_rows)
                await auth.db.flush()

            dataset_obj.total_images = len(dataset_image_rows)
            await auth.db.flush()

            if use_minio:
                shutil.rmtree(images_dir, ignore_errors=True)

            return DatasetsOutSchema.model_validate(dataset_obj).model_dump()
        except Exception:
            if use_minio and uploaded_keys:
                await asyncio.to_thread(remove_objects_from_minio, uploaded_keys)
            shutil.rmtree(dataset_dir, ignore_errors=True)
            raise

    @classmethod
    async def import_template_download_datasets_service(cls) -> bytes:
        header_list = [
            "数据集ID",
            "数据集名称",
            "数据集描述",
            "数据集版本号",
            "数据集来源",
            "总共图片数",
            "创建者",
            "更新者",
        ]
        selector_header_list: list[str] = []
        option_list: list[dict] = []
        return ExcelUtil.get_excel_template(
            header_list=header_list,
            selector_header_list=selector_header_list,
            option_list=option_list,
        )


async def _save_upload_file(file: UploadFile, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    chunk_size = 8 * 1024 * 1024
    with target_path.open("wb") as f:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
    await file.seek(0)


def _safe_extract_zip(zip_path: Path, dest_dir: Path) -> list[Path]:
    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            if name.startswith("/") or name.startswith("..") or "/../" in name:
                raise CustomException(msg="zip内包含非法路径")
            out_path = dest_dir.joinpath(name)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            resolved_out = out_path.resolve()
            if not resolved_out.is_relative_to(dest_dir.resolve()):
                raise CustomException(msg="zip解压检测到路径穿越")
            with zf.open(info, "r") as src, resolved_out.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)
            extracted.append(resolved_out)
    return extracted


def _build_basename_index(paths: list[Path]) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for p in paths:
        if p.is_file():
            index.setdefault(p.name, p)
    return index


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8 * 1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise CustomException(msg="标注json格式不正确")
        return data
    except CustomException:
        raise
    except Exception as e:
        raise CustomException(msg=f"解析标注json失败: {e!s}")


def _load_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return path.read_text(errors="ignore")


def _read_csv_any(path: Path) -> pd.DataFrame:
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, encoding="utf-8", errors="ignore")


def _is_image_file(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}


def _parse_voc_xml(path: Path) -> dict[str, Any]:
    tree = ET.parse(path)
    root = tree.getroot()

    file_name = None
    fn = root.findtext("filename")
    if fn:
        file_name = str(fn).strip()

    width = None
    height = None
    size_el = root.find("size")
    if size_el is not None:
        w = size_el.findtext("width")
        h = size_el.findtext("height")
        try:
            width = int(float(w)) if w is not None else None
        except Exception:
            width = None
        try:
            height = int(float(h)) if h is not None else None
        except Exception:
            height = None

    objects: list[dict[str, Any]] = []
    for obj in root.findall("object"):
        name = obj.findtext("name")
        bnd = obj.find("bndbox")
        if bnd is None:
            continue
        try:
            xmin = float(bnd.findtext("xmin"))
            ymin = float(bnd.findtext("ymin"))
            xmax = float(bnd.findtext("xmax"))
            ymax = float(bnd.findtext("ymax"))
        except Exception:
            continue
        objects.append(
            {
                "class_name": str(name).strip() if name else None,
                "bbox": {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax},
            }
        )

    return {"file_name": file_name, "width": width, "height": height, "objects": objects}


def _parse_yolo_data_yaml(text: str) -> dict[int, str]:
    lines = [ln.rstrip() for ln in (text or "").splitlines() if ln.strip() and not ln.strip().startswith("#")]
    joined = "\n".join(lines)

    if "names:" not in joined:
        return {}

    idx = next((i for i, ln in enumerate(lines) if ln.strip().startswith("names:")), None)
    if idx is None:
        return {}

    after = lines[idx].split("names:", 1)[1].strip()
    if after.startswith("[") and after.endswith("]"):
        inner = after[1:-1].strip()
        if not inner:
            return {}
        parts = [p.strip().strip("'\"") for p in inner.split(",")]
        out: dict[int, str] = {}
        for i, name in enumerate(parts):
            if name:
                out[i] = name
        return out

    out: dict[int, str] = {}
    for ln in lines[idx + 1 :]:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("-"):
            name = s[1:].strip().strip("'\"")
            out[len(out)] = name
            continue
        if ":" in s:
            k, v = s.split(":", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k.isdigit() and v:
                out[int(k)] = v
                continue
            if k == "names":
                continue
        if not ln.startswith(" "):
            break
    return out
