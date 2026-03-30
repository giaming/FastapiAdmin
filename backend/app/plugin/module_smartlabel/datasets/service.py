# -*- coding: utf-8 -*-

import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path
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

            return DatasetsOutSchema.model_validate(dataset_obj).model_dump()
        except Exception:
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
