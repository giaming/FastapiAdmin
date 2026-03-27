import request from "@/utils/request";

const API_PATH = "/smartlabel/datasets";

const DatasetsAPI = {
  // 列表查询
  listDatasets(query: DatasetsPageQuery) {
    return request<ApiResponse<PageResult<DatasetsTable[]>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  // 详情查询
  detailDatasets(id: number) {
    return request<ApiResponse<DatasetsTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  // 新增
  createDatasets(body: DatasetsForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  // 修改（带主键）
  updateDatasets(id: number, body: DatasetsForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  // 删除（支持批量）
  deleteDatasets(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: ids,
    });
  },

  // 批量启用/停用
  batchDatasets(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/available/setting`,
      method: "patch",
      data: body,
    });
  },

  // 导出
  exportDatasets(query: DatasetsPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: "post",
      data: query,
      responseType: "blob",
    });
  },

  // 下载导入模板
  downloadTemplateDatasets() {
    return request<Blob>({
      url: `${API_PATH}/download/template`,
      method: "post",
      responseType: "blob",
    });
  },

  // 导入
  importDatasets(body: FormData) {
    return request<ApiResponse>({
      url: `${API_PATH}/import`,
      method: "post",
      data: body,
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

export default DatasetsAPI;

// ------------------------------
// TS 类型声明
// ------------------------------

// 列表查询参数
export interface DatasetsPageQuery extends PageQuery {
  name?: string;
  version?: string;
  source?: string;
  total_images?: string;
  created_by?: string;
  updated_by?: string;
  created_time?: string[];
  updated_time?: string[];
}

// 列表展示项
export interface DatasetsTable extends BaseType {
  dataset_id?: number;
  name?: string;
  version?: string;
  source?: string;
  total_images?: string;
  created_by?: string;
  updated_by?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
}

// 新增/修改/详情表单参数
export interface DatasetsForm extends BaseFormType {
  dataset_id?: number;
  name?: string;
  version?: string;
  source?: string;
  total_images?: string;
  created_by?: string;
  updated_by?: string;
}
