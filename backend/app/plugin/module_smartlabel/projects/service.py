# -*- coding: utf-8 -*-

import io
import pandas as pd
from fastapi import UploadFile

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_schema import BatchSetAvailable
from app.core.exceptions import CustomException
from app.core.logger import log
from app.utils.excel_util import ExcelUtil

from .crud import ProjectsCRUD
from .schema import (
    ProjectsCreateSchema,
    ProjectsUpdateSchema,
    ProjectsOutSchema,
    ProjectsQueryParam
)


class ProjectsService:
    """
    项目管理服务层
    """
    
    @classmethod
    async def detail_projects_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        详情
        
        参数:
        - auth: AuthSchema - 认证信息
        - id: int - 数据ID
        
        返回:
        - dict - 数据详情
        """
        obj = await ProjectsCRUD(auth).get_by_id_projects_crud(id=id)
        if not obj:
            raise CustomException(msg="该数据不存在")
        return ProjectsOutSchema.model_validate(obj).model_dump()
    
    @classmethod
    async def list_projects_service(cls, auth: AuthSchema, search: ProjectsQueryParam | None = None, order_by: list[dict] | None = None) -> list[dict]:
        """
        列表查询
        
        参数:
        - auth: AuthSchema - 认证信息
        - search: ProjectsQueryParam | None - 查询参数
        - order_by: list[dict] | None - 排序参数
        
        返回:
        - list[dict] - 数据列表
        """
        search_dict = search.__dict__ if search else None
        obj_list = await ProjectsCRUD(auth).list_projects_crud(search=search_dict, order_by=order_by)
        return [ProjectsOutSchema.model_validate(obj).model_dump() for obj in obj_list]

    @classmethod
    async def page_projects_service(cls, auth: AuthSchema, page_no: int, page_size: int, search: ProjectsQueryParam | None = None, order_by: list[dict] | None = None) -> dict:
        """
        分页查询（数据库分页）
        
        参数:
        - auth: AuthSchema - 认证信息
        - page_no: int - 页码
        - page_size: int - 每页数量
        - search: ProjectsQueryParam | None - 查询参数
        - order_by: list[dict] | None - 排序参数
        
        返回:
        - dict - 分页查询结果
        """
        search_dict = search.__dict__ if search else {}
        order_by_list = order_by or [{'id': 'asc'}]
        offset = (page_no - 1) * page_size
        result = await ProjectsCRUD(auth).page_projects_crud(
            offset=offset,
            limit=page_size,
            order_by=order_by_list,
            search=search_dict
        )
        return result
    
    @classmethod
    async def create_projects_service(cls, auth: AuthSchema, data: ProjectsCreateSchema) -> dict:
        """
        创建
        
        参数:
        - auth: AuthSchema - 认证信息
        - data: ProjectsCreateSchema - 创建数据
        
        返回:
        - dict - 创建结果
        """
        obj = await ProjectsCRUD(auth).create_projects_crud(data=data)
        return ProjectsOutSchema.model_validate(obj).model_dump()
    
    @classmethod
    async def update_projects_service(cls, auth: AuthSchema, id: int, data: ProjectsUpdateSchema) -> dict:
        """
        更新
        
        参数:
        - auth: AuthSchema - 认证信息
        - id: int - 数据ID
        - data: ProjectsUpdateSchema - 更新数据
        
        返回:
        - dict - 更新结果
        """
        # 检查数据是否存在
        obj = await ProjectsCRUD(auth).get_by_id_projects_crud(id=id)
        if not obj:
            raise CustomException(msg='更新失败，该数据不存在')
        
        # 检查唯一性约束
            
        obj = await ProjectsCRUD(auth).update_projects_crud(id=id, data=data)
        return ProjectsOutSchema.model_validate(obj).model_dump()
    
    @classmethod
    async def delete_projects_service(cls, auth: AuthSchema, ids: list[int]) -> None:
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
            obj = await ProjectsCRUD(auth).get_by_id_projects_crud(id=id)
            if not obj:
                raise CustomException(msg=f'删除失败，ID为{id}的数据不存在')
        await ProjectsCRUD(auth).delete_projects_crud(ids=ids)
    
    @classmethod
    async def set_available_projects_service(cls, auth: AuthSchema, data: BatchSetAvailable) -> None:
        """
        批量设置状态
        
        参数:
        - auth: AuthSchema - 认证信息
        - data: BatchSetAvailable - 批量设置状态数据
        
        返回:
        - None
        """
        await ProjectsCRUD(auth).set_available_projects_crud(ids=data.ids, status=data.status)
    
    @classmethod
    async def batch_export_projects_service(cls, obj_list: list[dict]) -> bytes:
        """
        批量导出
        
        参数:
        - obj_list: list[dict] - 数据列表
        
        返回:
        - bytes - 导出的Excel文件内容
        """
        mapping_dict = {
            'id': '项目ID',
            'name': '项目名称',
            'description': '项目描述',
            'setup_type': '项目类型',
            'annotation_style_config': '标注类型配置',
            'created_time': '创建时间',
            'updated_time': '更新时间',
            'owner_id': '所有者',
        }
        # 复制数据并转换状态
        data = obj_list.copy()
        for item in data:
            # 处理状态
            item["status"] = "启用" if item.get("status") == "0" else "停用"
            # 处理创建者
            creator_info = item.get("created_id")
            if isinstance(creator_info, dict):
                item["created_id"] = creator_info.get("name", "未知")
            else:
                item["created_id"] = "未知"

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)

    @classmethod
    async def batch_import_projects_service(cls, auth: AuthSchema, file: UploadFile, update_support: bool = False) -> str:
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
            '项目ID': 'id',
            '项目名称': 'name',
            '项目描述': 'description',
            '项目类型': 'setup_type',
            '标注类型配置': 'annotation_style_config',
            '创建时间': 'created_time',
            '更新时间': 'updated_time',
            '所有者': 'owner_id',
        }

        try:
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
                        "id": row['id'],
                        "name": row['name'],
                        "description": row['description'],
                        "setup_type": row['setup_type'],
                        "annotation_style_config": row['annotation_style_config'],
                        "created_time": row['created_time'],
                        "updated_time": row['updated_time'],
                        "owner_id": row['owner_id'],
                    }
                    # 使用CreateSchema做校验后入库
                    create_schema = ProjectsCreateSchema.model_validate(data)
                    
                    # 检查唯一性约束
                    
                    await ProjectsCRUD(auth).create_projects_crud(data=create_schema)
                    success_count += 1
                except Exception as e:
                    error_msgs.append(f"第{count}行: {str(e)}")
                    continue

            result = f"成功导入 {success_count} 条数据"
            if error_msgs:
                result += "\n错误信息:\n" + "\n".join(error_msgs)
            return result
            
        except Exception as e:
            log.error(f"批量导入失败: {str(e)}")
            raise CustomException(msg=f"导入失败: {str(e)}")
    
    @classmethod
    async def import_template_download_projects_service(cls) -> bytes:
        """
        下载导入模板
        
        返回:
        - bytes - Excel文件的二进制数据
        """
        header_list = [
            '项目ID',
            '项目名称',
            '项目描述',
            '项目类型',
            '标注类型配置',
            '创建时间',
            '更新时间',
            '所有者',
        ]
        selector_header_list = []
        option_list = []
        
        
        return ExcelUtil.get_excel_template(
            header_list=header_list,
            selector_header_list=selector_header_list,
            option_list=option_list
        )