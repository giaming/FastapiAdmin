import request from "@/utils/request";

const API_PATH = "/smartlabel/projects";

const ProjectsAPI = {
  // 列表查询
  listProjects(query: ProjectsPageQuery) {
    return request<ApiResponse<PageResult<ProjectsTable[]>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  // 详情查询
  detailProjects(id: number) {
    return request<ApiResponse<ProjectsTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  // 新增
  createProjects(body: ProjectsForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  // 修改（带主键）
  updateProjects(id: number, body: ProjectsForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  // 删除（支持批量）
  deleteProjects(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: ids,
    });
  },

  // 批量启用/停用
  batchProjects(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/available/setting`,
      method: "patch",
      data: body,
    });
  },

  // 导出
  exportProjects(query: ProjectsPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: "post",
      data: query,
      responseType: "blob",
    });
  },

  // 下载导入模板
  downloadTemplateProjects() {
    return request<Blob>({
      url: `${API_PATH}/download/template`,
      method: "post",
      responseType: "blob",
    });
  },

  // 导入
  importProjects(body: FormData) {
    return request<ApiResponse>({
      url: `${API_PATH}/import`,
      method: "post",
      data: body,
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

export default ProjectsAPI;

// ------------------------------
// TS 类型声明
// ------------------------------

// 列表查询参数
export interface ProjectsPageQuery extends PageQuery {
  name?: string;
  setup_type?: string;
  annotation_style_config?: string;
  owner_id?: string;
  created_time?: string[];
  updated_time?: string[];
}

// 列表展示项
export interface ProjectsTable extends BaseType {
  name?: string;
  setup_type?: string;
  annotation_style_config?: string;
  owner_id?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
}

// 新增/修改/详情表单参数
export interface ProjectsForm extends BaseFormType {
  name?: string;
  setup_type?: string;
  annotation_style_config?: string;
  owner_id?: string;
}
