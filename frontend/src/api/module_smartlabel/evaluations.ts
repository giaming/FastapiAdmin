import request from "@/utils/request";

const API_PATH = "/smartlabel/evaluations";

const EvaluationsAPI = {
  getEvaluationList(query: EvaluationPageQuery) {
    return request<ApiResponse<PageResult<EvaluationTable[]>>>({
      url: `${API_PATH}`,
      method: "get",
      params: query,
    });
  },

  getEvaluationDetail(id: number) {
    return request<ApiResponse<EvaluationTable>>({
      url: `${API_PATH}/${id}`,
      method: "get",
    });
  },

  triggerEvaluation(body: EvaluationTriggerForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/trigger`,
      method: "post",
      data: body,
    });
  },
};

export default EvaluationsAPI;

export interface EvaluationPageQuery extends PageQuery {
  project_id?: number;
  user_id?: number;
  dataset_id?: number;
  status?: string;
}

export interface EvaluationTable {
  id: number;
  project_id: number;
  user_id: number;
  dataset_id: number;
  triggered_by?: number;
  total_images?: number;
  total_annotations?: number;
  avg_iou?: number;
  class_match_rate?: number;
  quality_score?: number;
  metrics_by_class?: Record<string, any>;
  status: string;
  error_message?: string;
  evaluated_time?: string;
  created_time?: string;
  updated_time?: string;
}

export interface EvaluationConfigForm {
  iou_threshold?: number;
  strict_classmatch?: boolean;
  match_strategy?: string;
  w_iou?: number;
  w_class?: number;
}

export interface EvaluationTriggerForm {
  project_id: number;
  user_id: number;
  dataset_id: number;
  force?: boolean;
  config?: EvaluationConfigForm;
}
