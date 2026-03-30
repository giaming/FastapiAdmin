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
          <el-select v-model="queryParams.status" placeholder="请选择状态" clearable style="min-width: 120px;">
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
          <el-select
            v-model="formData.project_id"
            class="w-full"
            filterable
            remote
            clearable
            :remote-method="fetchProjects"
            :loading="projectLoading"
            placeholder="请选择项目（可输入项目名称搜索）"
          >
            <el-option
              v-for="item in projectOptions"
              :key="item.id"
              :label="`${item.name}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="用户ID" prop="user_id">
          <el-select
            v-model="formData.user_id"
            class="w-full"
            filterable
            remote
            clearable
            :remote-method="fetchUsers"
            :loading="userLoading"
            placeholder="请选择用户（可输入用户名/姓名搜索）"
          >
            <el-option
              v-for="item in userOptions"
              :key="item.id"
              :label="item.label"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数据集ID" prop="dataset_id">
          <el-select
            v-model="formData.dataset_id"
            class="w-full"
            filterable
            remote
            clearable
            :remote-method="fetchDatasets"
            :loading="datasetLoading"
            placeholder="请选择数据集（可输入数据集名称搜索）"
          >
            <el-option
              v-for="item in datasetOptions"
              :key="item.id"
              :label="`${item.name}`"
              :value="item.id"
            />
          </el-select>
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
} from '@/api/module_smartlabel/evaluations';
import ProjectsAPI, { type ProjectsTable } from '@/api/module_smartlabel/projects';
import DatasetsAPI, { type DatasetsTable } from '@/api/module_smartlabel/datasets';
import UserAPI, { type UserInfo } from '@/api/module_system/user';

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
const formData = reactive<{
  project_id: number | undefined;
  user_id: number | undefined;
  dataset_id: number | undefined;
  force: boolean;
}>({
  project_id: undefined,
  user_id: undefined,
  dataset_id: undefined,
  force: false,
});

const rules = reactive<FormRules>({
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  user_id: [{ required: true, message: '请选择用户', trigger: 'change' }],
  dataset_id: [{ required: true, message: '请选择数据集', trigger: 'change' }]
});

type IdNameOption = { id: number; name: string };
type UserOption = { id: number; label: string };

const projectLoading = ref(false);
const datasetLoading = ref(false);
const userLoading = ref(false);

const projectOptions = ref<IdNameOption[]>([]);
const datasetOptions = ref<IdNameOption[]>([]);
const userOptions = ref<UserOption[]>([]);

const fetchProjects = async (keyword: string) => {
  projectLoading.value = true;
  try {
    const res = await ProjectsAPI.listProjects({
      page_no: 1,
      page_size: 50,
      name: keyword?.trim() || undefined,
    });
    projectOptions.value = ((res.data.data?.items || []) as ProjectsTable[])
      .map((p) => ({ id: Number(p.id), name: String(p.name ?? '') }))
      .filter((p) => Number.isFinite(p.id) && p.name);
  } finally {
    projectLoading.value = false;
  }
};

const fetchDatasets = async (keyword: string) => {
  datasetLoading.value = true;
  try {
    const res = await DatasetsAPI.listDatasets({
      page_no: 1,
      page_size: 50,
      name: keyword?.trim() || undefined,
    } as any);
    datasetOptions.value = ((res.data.data?.items || []) as DatasetsTable[])
      .map((d) => ({ id: Number(d.id), name: String(d.name ?? '') }))
      .filter((d) => Number.isFinite(d.id) && d.name);
  } finally {
    datasetLoading.value = false;
  }
};

const fetchUsers = async (keyword: string) => {
  userLoading.value = true;
  try {
    const q = keyword?.trim() || undefined;
    const res = await UserAPI.listUser({
      page_no: 1,
      page_size: 50,
      name: q,
      username: q,
      status: '0',
    } as any);
    userOptions.value = ((res.data.data?.items || []) as UserInfo[])
      .map((u) => {
        const id = Number(u.id);
        const username = u.username ? String(u.username) : '';
        const name = u.name ? String(u.name) : '';
        const labelBase = name || username || `用户 ${id}`;
        const label = `${labelBase}${username && name && username !== name ? `（${username}）` : ''}`;
        return { id, label };
      })
      .filter((u) => Number.isFinite(u.id));
  } finally {
    userLoading.value = false;
  }
};

const ensureProjectOption = async (id?: number) => {
  if (!id || projectOptions.value.some((o) => o.id === id)) return;
  const res = await ProjectsAPI.detailProjects(id);
  const p: any = res.data.data;
  if (!p) return;
  projectOptions.value.unshift({ id: Number(p.id), name: String(p.name ?? '') });
};

const ensureDatasetOption = async (id?: number) => {
  if (!id || datasetOptions.value.some((o) => o.id === id)) return;
  const res = await DatasetsAPI.detailDatasets(id);
  const d: any = res.data.data;
  if (!d) return;
  datasetOptions.value.unshift({ id: Number(d.id), name: String(d.name ?? '') });
};

const ensureUserOption = async (id?: number) => {
  if (!id || userOptions.value.some((o) => o.id === id)) return;
  const res = await UserAPI.detailUser(id);
  const u: any = res.data.data;
  if (!u) return;
  const username = u.username ? String(u.username) : '';
  const name = u.name ? String(u.name) : '';
  const labelBase = name || username || `用户 ${id}`;
  const label = `${labelBase}${username && name && username !== name ? `（${username}）` : ''}`;
  userOptions.value.unshift({ id: Number(u.id), label });
};

const initTriggerOptions = async () => {
  await Promise.all([fetchProjects(''), fetchDatasets(''), fetchUsers('')]);
  await Promise.all([
    ensureProjectOption(formData.project_id),
    ensureDatasetOption(formData.dataset_id),
    ensureUserOption(formData.user_id),
  ]);
};

// 详情相关
const detailVisible = ref(false);
const currentDetail = ref<EvaluationTable | null>(null);

// 获取列表数据
const getList = async () => {
  loading.value = true;
  try {
    const res = await EvaluationsAPI.getEvaluationList(queryParams);
    tableData.value = res.data.data?.items || [];
    total.value = res.data.data?.total || 0;
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
type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger';
const getStatusType = (status: string): TagType => {
  const map: Record<string, TagType> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
  };
  return map[status] || 'info';
};

// 新增触发
const handleAdd = () => {
  dialogVisible.value = true;
  formData.project_id = undefined;
  formData.user_id = undefined;
  formData.dataset_id = undefined;
  formData.force = false;
  initTriggerOptions();
};

// 重跑
const handleRetry = (row: EvaluationTable) => {
  formData.project_id = row.project_id;
  formData.user_id = row.user_id;
  formData.dataset_id = row.dataset_id;
  formData.force = true;
  dialogVisible.value = true;
  initTriggerOptions();
};

// 查看详情
const handleDetail = async (row: EvaluationTable) => {
  try {
    const res = await EvaluationsAPI.getEvaluationDetail(row.id);
    currentDetail.value = res.data.data;
    detailVisible.value = true;
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
        await EvaluationsAPI.triggerEvaluation({
          project_id: formData.project_id!,
          user_id: formData.user_id!,
          dataset_id: formData.dataset_id!,
          force: formData.force,
        });
        dialogVisible.value = false;
        getList();
      } catch (error) {
        console.error(error);
        ElMessage.error('触发评估失败');
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
