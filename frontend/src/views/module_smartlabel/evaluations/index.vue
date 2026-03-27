<template>
  <div class="app-container">
    <!-- 搜索表单 -->
    <el-card shadow="never" class="search-wrapper">
      <el-form ref="searchFormRef" :inline="true" :model="queryParams">
        <el-form-item label="项目ID" prop="project_id">
          <el-input v-model="queryParams.project_id" placeholder="请输入项目ID" clearable />
        </el-form-item>
        <el-form-item label="用户ID" prop="user_id">
          <el-input v-model="queryParams.user_id" placeholder="请输入用户ID" clearable />
        </el-form-item>
        <el-form-item label="数据集ID" prop="dataset_id">
          <el-input v-model="queryParams.dataset_id" placeholder="请输入数据集ID" clearable />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="queryParams.status" placeholder="请选择状态" clearable>
            <el-option label="待处理" value="pending" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
          <el-button icon="Refresh" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作工具栏 -->
    <el-card shadow="never" class="table-wrapper">
      <template #header>
        <div class="flex justify-between items-center">
          <span class="font-bold">评估列表</span>
          <div>
            <el-button type="primary" icon="Plus" @click="handleAdd">触发新评估</el-button>
          </div>
        </div>
      </template>

      <!-- 数据表格 -->
      <el-table v-loading="loading" :data="tableData" border>
        <el-table-column label="ID" prop="id" width="80" align="center" />
        <el-table-column label="项目ID" prop="project_id" width="100" align="center" />
        <el-table-column label="用户ID" prop="user_id" width="100" align="center" />
        <el-table-column label="数据集ID" prop="dataset_id" width="100" align="center" />
        <el-table-column label="状态" prop="status" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="评估图像数" prop="total_images" width="120" align="center" />
        <el-table-column label="标注总数" prop="total_annotations" width="120" align="center" />
        <el-table-column label="平均IoU" prop="avg_iou" width="120" align="center">
          <template #default="scope">
            {{ scope.row.avg_iou ? scope.row.avg_iou.toFixed(4) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="类别匹配率" prop="class_match_rate" width="120" align="center">
          <template #default="scope">
            {{ scope.row.class_match_rate ? (scope.row.class_match_rate * 100).toFixed(2) + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="综合质量评分" prop="quality_score" width="120" align="center">
          <template #default="scope">
            {{ scope.row.quality_score ? scope.row.quality_score.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="完成时间" prop="evaluated_time" width="160" align="center" />
        <el-table-column label="操作" align="center" width="150" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="handleDetail(scope.row)">详情</el-button>
            <el-button type="primary" link @click="handleRetry(scope.row)">重跑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="flex justify-end mt-4">
        <el-pagination
          v-model:current-page="queryParams.page_no"
          v-model:page-size="queryParams.page_size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleQuery"
          @current-change="handleQuery"
        />
      </div>
    </el-card>

    <!-- 触发评估对话框 -->
    <el-dialog
      title="触发新评估"
      v-model="dialogVisible"
      width="500px"
      append-to-body
      @close="closeDialog"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-form-item label="项目ID" prop="project_id">
          <el-input-number v-model="formData.project_id" :min="1" class="w-full" />
        </el-form-item>
        <el-form-item label="用户ID" prop="user_id">
          <el-input-number v-model="formData.user_id" :min="1" class="w-full" />
        </el-form-item>
        <el-form-item label="数据集ID" prop="dataset_id">
          <el-input-number v-model="formData.dataset_id" :min="1" class="w-full" />
        </el-form-item>
        <el-form-item label="强制重跑" prop="force">
          <el-switch v-model="formData.force" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeDialog">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitLoading">确认</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog
      title="评估详情"
      v-model="detailVisible"
      width="800px"
      append-to-body
    >
      <div v-if="currentDetail">
        <el-descriptions border :column="2">
          <el-descriptions-item label="评估ID">{{ currentDetail.id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentDetail.status)">{{ currentDetail.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="项目ID">{{ currentDetail.project_id }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ currentDetail.user_id }}</el-descriptions-item>
          <el-descriptions-item label="总图像数">{{ currentDetail.total_images }}</el-descriptions-item>
          <el-descriptions-item label="总标注数">{{ currentDetail.total_annotations }}</el-descriptions-item>
          <el-descriptions-item label="平均IoU">{{ currentDetail.avg_iou?.toFixed(4) }}</el-descriptions-item>
          <el-descriptions-item label="质量分">{{ currentDetail.quality_score?.toFixed(2) }}</el-descriptions-item>
        </el-descriptions>
        
        <div v-if="currentDetail.error_message" class="mt-4 text-red-500">
          <div class="font-bold mb-2">错误信息：</div>
          <div class="whitespace-pre-wrap text-sm bg-gray-100 p-2 rounded">{{ currentDetail.error_message }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import EvaluationsAPI, { 
  EvaluationPageQuery, 
  EvaluationTable, 
  EvaluationTriggerForm 
} from '@/api/module_smartlabel/evaluations';

// 查询参数
const queryParams = reactive<EvaluationPageQuery>({
  page_no: 1,
  page_size: 10,
  project_id: undefined,
  user_id: undefined,
  dataset_id: undefined,
  status: undefined
});

const loading = ref(false);
const tableData = ref<EvaluationTable[]>([]);
const total = ref(0);

// 表单相关
const dialogVisible = ref(false);
const submitLoading = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive<EvaluationTriggerForm>({
  project_id: 1,
  user_id: 1,
  dataset_id: 1,
  force: false
});

const rules = reactive<FormRules>({
  project_id: [{ required: true, message: '请输入项目ID', trigger: 'blur' }],
  user_id: [{ required: true, message: '请输入用户ID', trigger: 'blur' }],
  dataset_id: [{ required: true, message: '请输入数据集ID', trigger: 'blur' }]
});

// 详情相关
const detailVisible = ref(false);
const currentDetail = ref<EvaluationTable | null>(null);

// 获取列表数据
const getList = async () => {
  loading.value = true;
  try {
    const res = await EvaluationsAPI.getEvaluationList(queryParams);
    if (res.code === 200 && res.data) {
      tableData.value = res.data.list;
      total.value = res.data.total;
    }
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 搜索
const handleQuery = () => {
  getList();
};

// 重置
const resetQuery = () => {
  queryParams.project_id = undefined;
  queryParams.user_id = undefined;
  queryParams.dataset_id = undefined;
  queryParams.status = undefined;
  queryParams.page_no = 1;
  handleQuery();
};

// 状态样式
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  };
  return map[status] || 'info';
};

// 新增触发
const handleAdd = () => {
  dialogVisible.value = true;
};

// 重跑
const handleRetry = (row: EvaluationTable) => {
  formData.project_id = row.project_id;
  formData.user_id = row.user_id;
  formData.dataset_id = row.dataset_id;
  formData.force = true;
  dialogVisible.value = true;
};

// 查看详情
const handleDetail = async (row: EvaluationTable) => {
  try {
    const res = await EvaluationsAPI.getEvaluationDetail(row.id);
    if (res.code === 200 && res.data) {
      currentDetail.value = res.data;
      detailVisible.value = true;
    }
  } catch (error) {
    console.error(error);
  }
};

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true;
      try {
        const res = await EvaluationsAPI.triggerEvaluation(formData);
        if (res.code === 200) {
          ElMessage.success('触发评估成功');
          dialogVisible.value = false;
          getList();
        }
      } catch (error) {
        console.error(error);
      } finally {
        submitLoading.value = false;
      }
    }
  });
};

// 关闭对话框
const closeDialog = () => {
  dialogVisible.value = false;
  if (formRef.value) {
    formRef.value.resetFields();
  }
};

onMounted(() => {
  getList();
});
</script>

<style scoped>
.search-wrapper {
  margin-bottom: 16px;
}
</style>
