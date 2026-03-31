<!-- 数据集管理 -->
<template>
  <div class="app-container">
    <!-- 内容区域 -->
    <el-card class="data-table">
      <template #header>
        <div class="card-header">
          <span>
            数据集管理列表
            <el-tooltip content="数据集管理列表">
              <QuestionFilled class="w-4 h-4 mx-1" />
            </el-tooltip>
          </span>
        </div>

        <!-- 搜索区域 -->
        <div v-show="visible" class="search-container">
          <el-form
            ref="queryFormRef"
            :model="queryFormData"
            label-suffix=":"
            :inline="true"
            @submit.prevent="handleQuery"
          >
            <el-form-item label="数据集名称" prop="name">
              <el-input v-model="queryFormData.name" placeholder="请输入数据集名称" clearable />
            </el-form-item>
            <el-form-item label="数据集版本号" prop="version">
              <el-input v-model="queryFormData.version" placeholder="请输入数据集版本号" clearable />
            </el-form-item>
            <el-form-item label="数据集来源" prop="source">
              <el-input v-model="queryFormData.source" placeholder="请输入数据集来源" clearable />
            </el-form-item>
            <el-form-item label="创建者" prop="created_by">
              <el-select
                v-model="queryFormData.created_by"
                placeholder="请选择创建者"
                clearable
                filterable
                style="width: 240px"
              >
                <el-option
                  v-for="user in userOptions"
                  :key="user.id"
                  :label="user.name"
                  :value="user.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="更新者" prop="updated_by">
              <el-select
                v-model="queryFormData.updated_by"
                placeholder="请选择更新者"
                clearable
                filterable
                style="width: 240px"
              >
                <el-option
                  v-for="user in userOptions"
                  :key="user.id"
                  :label="user.name"
                  :value="user.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item v-if="isExpand" prop="created_time" label="创建时间">
              <DatePicker
                v-model="createdDateRange"
                @update:model-value="handleCreatedDateRangeChange"
              />
            </el-form-item>
            <el-form-item v-if="isExpand" prop="updated_time" label="更新时间">
              <DatePicker
                v-model="updatedDateRange"
                @update:model-value="handleUpdatedDateRangeChange"
              />
            </el-form-item>
            <!-- 查询、重置、展开/收起按钮 -->
            <el-form-item>
              <el-button
                v-hasPerm="['module_smartlabel:datasets:query']"
                type="primary"
                icon="search"
                @click="handleQuery"
              >
                查询
              </el-button>
              <el-button
                v-hasPerm="['module_smartlabel:datasets:query']"
                icon="refresh"
                @click="handleResetQuery"
              >
                重置
              </el-button>
              <!-- 展开/收起 -->
              <template v-if="isExpandable">
                <el-link 
                  class="ml-3"
                  type="primary"
                  underline="never"
                  @click="isExpand = !isExpand"
                >
                  {{ isExpand ? "收起" : "展开" }}
                  <el-icon>
                    <template v-if="isExpand">
                      <ArrowUp />
                    </template>
                    <template v-else>
                      <ArrowDown />
                    </template>
                  </el-icon>
                </el-link>
              </template>
            </el-form-item>
          </el-form>
        </div>
      </template>

      <!-- 功能区域 -->
      <div class="data-table__toolbar">
        <div class="data-table__toolbar--left">
          <el-row :gutter="10">
            <el-col :span="1.5">
              <el-button
                v-hasPerm="['module_smartlabel:datasets:create']"
                type="success"
                icon="plus"
                @click="handleOpenDialog('create')"
              >
                新增
              </el-button>
            </el-col>
            <el-col :span="1.5">
              <el-button
                v-hasPerm="['module_smartlabel:datasets:delete']"
                type="danger"
                icon="delete"
                :disabled="selectIds.length === 0"
                @click="handleDelete(selectIds)"
              >
                批量删除
              </el-button>
            </el-col>
            <el-col :span="1.5">
              <span />
            </el-col>
          </el-row>
        </div>
        <div class="data-table__toolbar--right">
          <el-row :gutter="10">
            <el-col :span="1.5">
              <el-tooltip content="导入">
                <el-button
                  v-hasPerm="['module_smartlabel:datasets:import']"
                  type="success"
                  icon="upload"
                  circle
                  @click="handleOpenImportDialog"
                />
              </el-tooltip>
            </el-col>
            <el-col :span="1.5">
              <el-tooltip content="导出">
                <el-button
                  v-hasPerm="['module_smartlabel:datasets:export']"
                  type="warning"
                  icon="download"
                  circle
                  @click="handleOpenExportsModal"
                />
              </el-tooltip>
            </el-col>
            <el-col :span="1.5">
              <el-tooltip content="搜索显示/隐藏">
                <el-button
                  v-hasPerm="['*:*:*']"
                  type="info"
                  icon="search"
                  circle
                  @click="visible = !visible"
                />
              </el-tooltip>
            </el-col>
            <el-col :span="1.5">
              <el-tooltip content="刷新">
                <el-button
                  v-hasPerm="['module_smartlabel:datasets:query']"
                  type="primary"
                  icon="refresh"
                  circle
                  @click="handleRefresh"
                />
              </el-tooltip>
            </el-col>
            <el-col :span="1.5">
              <el-popover placement="bottom" trigger="click">
                <template #reference>
                  <el-button type="danger" icon="operation" circle></el-button>
                </template>
                <el-scrollbar max-height="350px">
                  <template v-for="column in tableColumns" :key="column.prop">
                    <el-checkbox v-if="column.prop" v-model="column.show" :label="column.label" />
                  </template>
                </el-scrollbar>
              </el-popover>
            </el-col>
          </el-row>
        </div>
      </div>

      <!-- 表格区域：系统配置列表 -->
      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="pageTableData"
        highlight-current-row
        class="data-table__content"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <template #empty>
          <el-empty :image-size="80" description="暂无数据" />
        </template>
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'selection')?.show"
          type="selection"
          min-width="55"
          align="center"
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'index')?.show"
          fixed
          label="序号"
          min-width="60"
        >
          <template #default="scope">
            {{ (queryFormData.page_no - 1) * queryFormData.page_size + scope.$index + 1 }}
          </template>
        </el-table-column>
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'name')?.show"
          label="数据集名称"
          prop="name"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'description')?.show"
          label="数据集描述"
          prop="description"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'version')?.show"
          label="数据集版本号"
          prop="version"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'source')?.show"
          label="数据集来源"
          prop="source"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'total_images')?.show"
          label="总共图片数"
          prop="total_images"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'created_by')?.show"
          label="创建者"
          prop="created_by"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'updated_by')?.show"
          label="更新者"
          prop="updated_by"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'created_time')?.show"
          label="创建时间"
          prop="created_time"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'updated_time')?.show"
          label="更新时间"
          prop="updated_time"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column
          v-if="tableColumns.find((col) => col.prop === 'operation')?.show"
          fixed="right"
          label="操作"
          align="center"
          min-width="180"
        >
          <template #default="scope">
            <el-button
              v-hasPerm="['module_smartlabel:datasets:detail']"
              type="info"
              size="small"
              link
              icon="document"
              @click="handleOpenDialog('detail', scope.row.id)"
            >
              详情
            </el-button>
            <el-button
              v-hasPerm="['module_smartlabel:datasets:update']"
              type="primary"
              size="small"
              link
              icon="edit"
              @click="handleOpenDialog('update', scope.row.id)"
            >
              编辑
            </el-button>
            <el-button
              v-hasPerm="['module_smartlabel:datasets:delete']"
              type="danger"
              size="small"
              link
              icon="delete"
              @click="handleDelete([scope.row.id])"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页区域 -->
      <template #footer>
        <pagination
          v-model:total="total"
          v-model:page="queryFormData.page_no"
          v-model:limit="queryFormData.page_size"
          @pagination="loadingData"
        />
      </template>
    </el-card>

    <!-- 弹窗区域 -->
    <el-dialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      @close="handleCloseDialog"
    >
      <!-- 详情 -->
      <template v-if="dialogVisible.type === 'detail'">
        <el-descriptions :column="4" border>
          <el-descriptions-item label="数据集ID" :span="2">
            {{ detailFormData.id }}
          </el-descriptions-item>
          <el-descriptions-item label="数据集名称" :span="2">
            {{ detailFormData.name }}
          </el-descriptions-item>
          <el-descriptions-item label="数据集描述" :span="2">
            {{ detailFormData.description }}
          </el-descriptions-item>
          <el-descriptions-item label="数据集版本号" :span="2">
            {{ detailFormData.version }}
          </el-descriptions-item>
          <el-descriptions-item label="数据集来源" :span="2">
            {{ detailFormData.source }}
          </el-descriptions-item>
          <el-descriptions-item label="总共图片数" :span="2">
            {{ detailFormData.total_images }}
          </el-descriptions-item>
          <el-descriptions-item label="创建者" :span="2">
            {{ detailFormData.created_by }}
          </el-descriptions-item>
          <el-descriptions-item label="更新者" :span="2">
            {{ detailFormData.updated_by }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ detailFormData.created_time }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间" :span="2">
            {{ detailFormData.updated_time }}
          </el-descriptions-item>
        </el-descriptions>
      </template>

      <!-- 新增、编辑表单 -->
      <template v-else>
        <el-form
          ref="dataFormRef"
          :model="formData"
          :rules="rules"
          label-suffix=":"
          label-width="auto"
          label-position="right"
        >
          <template v-if="dialogVisible.type === 'create'">
            <el-form-item label="导入格式" required>
              <el-row :gutter="12" class="w-full">
                <el-col :span="12">
                  <el-card
                    shadow="hover"
                    :class="{ 'is-active': importFormat === 'coco' }"
                    @click="setImportFormat('coco')"
                  >
                    <div class="format-title">COCO</div>
                    <div class="format-desc">包含图片与标注的 JSON 文件</div>
                  </el-card>
                </el-col>
                <el-col :span="12">
                  <el-card
                    shadow="hover"
                    :class="{ 'is-active': importFormat === 'voc' }"
                    @click="setImportFormat('voc')"
                  >
                    <div class="format-title">Pascal VOC</div>
                    <div class="format-desc">包含图片与标注的 XML 文件</div>
                  </el-card>
                </el-col>
                <el-col :span="12" class="mt-12px">
                  <el-card
                    shadow="hover"
                    :class="{ 'is-active': importFormat === 'yolo' }"
                    @click="setImportFormat('yolo')"
                  >
                    <div class="format-title">YOLO</div>
                    <div class="format-desc">TXT 标签与可选 YAML 类别</div>
                  </el-card>
                </el-col>
                <el-col :span="12" class="mt-12px">
                  <el-card
                    shadow="hover"
                    :class="{ 'is-active': importFormat === 'csv' }"
                    @click="setImportFormat('csv')"
                  >
                    <div class="format-title">CSV</div>
                    <div class="format-desc">表格标注与图片</div>
                  </el-card>
                </el-col>
              </el-row>
            </el-form-item>

            <el-form-item label="数据集名称" prop="name">
              <el-input v-model="formData.name" placeholder="请输入数据集名称" />
            </el-form-item>
            <el-form-item label="描述" prop="description">
              <el-input
                v-model="formData.description"
                :rows="4"
                :maxlength="200"
                show-word-limit
                type="textarea"
                placeholder="请输入描述（可选）"
              />
            </el-form-item>
            <el-form-item label="数据集版本号" prop="version">
              <el-input v-model="formData.version" placeholder="请输入数据集版本号（可选）" />
            </el-form-item>
            <el-form-item label="数据集来源" prop="source">
              <el-input v-model="formData.source" placeholder="请输入数据集来源（默认随导入格式）" />
            </el-form-item>
            <el-form-item label="数据划分" prop="split_type">
              <el-select v-model="cocoSplitType" placeholder="可选" clearable style="width: 100%">
                <el-option label="train" value="train" />
                <el-option label="val" value="val" />
                <el-option label="test" value="test" />
              </el-select>
            </el-form-item>
            <template v-if="importFormat === 'coco'">
              <el-form-item label="图片压缩包" required>
                <el-upload
                  v-model:file-list="cocoImagesZipFileList"
                  class="w-full"
                  accept=".zip"
                  :drag="true"
                  :limit="1"
                  :auto-upload="false"
                  :on-change="handleCocoImagesZipChange"
                  :on-remove="handleCocoImagesZipRemove"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">将 zip 拖到此处，或<em>点击上传</em></div>
                </el-upload>
              </el-form-item>
              <el-form-item label="标注文件" required>
                <el-upload
                  v-model:file-list="cocoAnnotationsFileList"
                  class="w-full"
                  accept=".json"
                  :drag="true"
                  :limit="1"
                  :auto-upload="false"
                  :on-change="handleCocoAnnotationsChange"
                  :on-remove="handleCocoAnnotationsRemove"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">将 annotations.json 拖到此处，或<em>点击上传</em></div>
                </el-upload>
              </el-form-item>
            </template>

            <template v-else-if="importFormat === 'voc'">
              <el-form-item label="图片压缩包" required>
                <el-upload
                  v-model:file-list="vocImagesZipFileList"
                  class="w-full"
                  accept=".zip"
                  :drag="true"
                  :limit="1"
                  :auto-upload="false"
                  :on-change="handleVocImagesZipChange"
                  :on-remove="handleVocImagesZipRemove"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">将 images.zip 拖到此处，或<em>点击上传</em></div>
                </el-upload>
              </el-form-item>
              <el-form-item label="标注压缩包" required>
                <el-upload
                  v-model:file-list="vocAnnotationsZipFileList"
                  class="w-full"
                  accept=".zip"
                  :drag="true"
                  :limit="1"
                  :auto-upload="false"
                  :on-change="handleVocAnnotationsZipChange"
                  :on-remove="handleVocAnnotationsZipRemove"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">将 annotations.zip(xml) 拖到此处，或<em>点击上传</em></div>
                </el-upload>
              </el-form-item>
            </template>

            <template v-else-if="importFormat === 'yolo'">
              <el-form-item label="图片压缩包" required>
                <el-upload
                  v-model:file-list="yoloImagesZipFileList"
                  class="w-full"
                  accept=".zip"
                  :drag="true"
                  :limit="1"
                  :auto-upload="false"
                  :on-change="handleYoloImagesZipChange"
                  :on-remove="handleYoloImagesZipRemove"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">将 images.zip 拖到此处，或<em>点击上传</em></div>
                </el-upload>
              </el-form-item>
              <el-form-item label="labels压缩包" required>
                <el-upload
                  v-model:file-list="yoloLabelsZipFileList"
                  class="w-full"
                  accept=".zip"
                  :drag="true"
                  :limit="1"
                  :auto-upload="false"
                  :on-change="handleYoloLabelsZipChange"
                  :on-remove="handleYoloLabelsZipRemove"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">将 labels.zip(txt) 拖到此处，或<em>点击上传</em></div>
                </el-upload>
              </el-form-item>
              <el-form-item label="data.yaml">
                <el-upload
                  v-model:file-list="yoloDataYamlFileList"
                  class="w-full"
                  accept=".yaml,.yml"
                  :drag="true"
                  :limit="1"
                  :auto-upload="false"
                  :on-change="handleYoloDataYamlChange"
                  :on-remove="handleYoloDataYamlRemove"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">将 data.yaml 拖到此处，或<em>点击上传</em></div>
                </el-upload>
              </el-form-item>
            </template>

            <template v-else-if="importFormat === 'csv'">
              <el-form-item label="图片压缩包" required>
                <el-upload
                  v-model:file-list="csvImagesZipFileList"
                  class="w-full"
                  accept=".zip"
                  :drag="true"
                  :limit="1"
                  :auto-upload="false"
                  :on-change="handleCsvImagesZipChange"
                  :on-remove="handleCsvImagesZipRemove"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">将 images.zip 拖到此处，或<em>点击上传</em></div>
                </el-upload>
              </el-form-item>
              <el-form-item label="标注文件" required>
                <el-upload
                  v-model:file-list="csvAnnotationsFileList"
                  class="w-full"
                  accept=".csv"
                  :drag="true"
                  :limit="1"
                  :auto-upload="false"
                  :on-change="handleCsvAnnotationsChange"
                  :on-remove="handleCsvAnnotationsRemove"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">将 annotations.csv 拖到此处，或<em>点击上传</em></div>
                </el-upload>
              </el-form-item>
            </template>
          </template>
          <template v-else>
            <el-form-item label="数据集 ID" prop="id" :required="false">
              <el-input v-model="formData.id" placeholder="数据集 ID" disabled />
            </el-form-item>
            <el-form-item label="数据集名称" prop="name" :required="false">
              <el-input v-model="formData.name" placeholder="请输入数据集名称" />
            </el-form-item>
            <el-form-item label="描述" prop="description">
              <el-input
                v-model="formData.description"
                :rows="4"
                :maxlength="100"
                show-word-limit
                type="textarea"
                placeholder="请输入描述"
              />
            </el-form-item>
            <el-form-item label="数据集版本号" prop="version" :required="false">
              <el-input v-model="formData.version" placeholder="请输入数据集版本号" />
            </el-form-item>
            <el-form-item label="数据集来源" prop="source" :required="false">
              <el-input v-model="formData.source" placeholder="请输入数据集来源" />
            </el-form-item>
            <el-form-item label="总共图片数" prop="total_images" :required="false">
              <el-input-number v-model="formData.total_images" :min="0" controls-position="right" />
            </el-form-item>
            <el-form-item label="创建者" prop="created_by" :required="false">
              <el-select
                v-model="formData.created_by"
                placeholder="请选择创建者"
                clearable
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="user in userOptions"
                  :key="user.id"
                  :label="user.name"
                  :value="user.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="更新者" prop="updated_by" :required="false">
              <el-select
                v-model="formData.updated_by"
                placeholder="请选择更新者"
                clearable
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="user in userOptions"
                  :key="user.id"
                  :label="user.name"
                  :value="user.id"
                />
              </el-select>
            </el-form-item>
          </template>
        </el-form>
      </template>

      <template #footer>
        <div class="dialog-footer">
          <!-- 详情弹窗不需要确定按钮的提交逻辑 -->
          <el-button @click="handleCloseDialog">取消</el-button>
          <el-button v-if="dialogVisible.type !== 'detail'" type="primary" @click="handleSubmit">
            确定
          </el-button>
          <el-button v-else type="primary" @click="handleCloseDialog">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 导入弹窗 -->
    <ImportModal
      v-model="importDialogVisible"
      :content-config="curdContentConfig"
      :loading="uploadLoading"
      @upload="handleUpload"
    />

    <!-- 导出弹窗 -->
    <ExportModal
      v-model="exportsDialogVisible"
      :content-config="curdContentConfig"
      :query-params="queryFormData"
      :page-data="pageTableData"
      :selection-data="selectionRows"
    />
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "Datasets",
  inheritAttrs: false,
});

import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox, type UploadFile, type UploadUserFile } from "element-plus";
import { QuestionFilled, ArrowUp, ArrowDown, UploadFilled } from "@element-plus/icons-vue";
import { formatToDateTime } from "@/utils/dateUtil";
import { useDictStore } from "@/store";
import { ResultEnum } from "@/enums/api/result.enum";
import DatePicker from "@/components/DatePicker/index.vue";
import type { IContentConfig } from "@/components/CURD/types";
import ImportModal from "@/components/CURD/ImportModal.vue";
import ExportModal from "@/components/CURD/ExportModal.vue";
import DatasetsAPI, {
  DatasetsPageQuery,
  DatasetsTable,
  DatasetsForm,
} from "@/api/module_smartlabel/datasets";
import { UserAPI } from "@/api/module_system/user";

const visible = ref(true);
const queryFormRef = ref();
const dataFormRef = ref();
const total = ref(0);
const selectIds = ref<number[]>([]);
const selectionRows = ref<DatasetsTable[]>([]);
const loading = ref(false);
const isExpand = ref(false);
const isExpandable = ref(true);

// 用户选项列表
const userOptions = ref<any[]>([]);

// 分页表单
const pageTableData = ref<DatasetsTable[]>([]);

// 表格列配置
const tableColumns = ref([
  { prop: "selection", label: "选择框", show: true },
  { prop: "index", label: "序号", show: true },
  { prop: "name", label: "数据集名称", show: true },
  { prop: "description", label: "数据集描述", show: true },
  { prop: "version", label: "数据集版本号", show: true },
  { prop: "source", label: "数据集来源", show: true },
  { prop: "total_images", label: "总共图片数", show: true },
  { prop: "created_by", label: "创建者", show: true },
  { prop: "updated_by", label: "更新者", show: true },
  { prop: "created_time", label: "创建时间", show: true },
  { prop: "updated_time", label: "更新时间", show: true },
  { prop: "operation", label: "操作", show: true },
]);

// 导出列（不含选择/序号/操作）
const exportColumns = [
  { prop: "name", label: "数据集名称" },
  { prop: "description", label: "数据集描述" },
  { prop: "version", label: "数据集版本号" },
  { prop: "source", label: "数据集来源" },
  { prop: "total_images", label: "总共图片数" },
  { prop: "created_by", label: "创建者" },
  { prop: "updated_by", label: "更新者" },
  { prop: "created_time", label: "创建时间" },
  { prop: "updated_time", label: "更新时间" },
];

// 导入/导出配置
const curdContentConfig = {
  permPrefix: "module_smartlabel:datasets",
  cols: exportColumns as any,
  importTemplate: () => DatasetsAPI.downloadTemplateDatasets(),
  exportsAction: async (params: any) => {
    const query: any = { ...params };
    query.page_no = 1;
    query.page_size = 9999;
    const all: any[] = [];
    while (true) {
      const res = await DatasetsAPI.listDatasets(query);
      const items = res.data?.data?.items || [];
      const total = res.data?.data?.total || 0;
      all.push(...items);
      if (all.length >= total || items.length === 0) break;
      query.page_no += 1;
    }
    return all;
  },
} as unknown as IContentConfig;

// 详情表单
const detailFormData = ref<DatasetsTable>({});
// 日期范围临时变量
const createdDateRange = ref<[Date, Date] | []>([]);
// 更新时间范围临时变量
const updatedDateRange = ref<[Date, Date] | []>([]);

// 处理创建时间范围变化
function handleCreatedDateRangeChange(range: [Date, Date]) {
  createdDateRange.value = range;
  if (range && range.length === 2) {
    queryFormData.created_time = [formatToDateTime(range[0]), formatToDateTime(range[1])];
  } else {
    queryFormData.created_time = undefined;
  }
}

// 处理更新时间范围变化
function handleUpdatedDateRangeChange(range: [Date, Date]) {
  updatedDateRange.value = range;
  if (range && range.length === 2) {
    queryFormData.updated_time = [formatToDateTime(range[0]), formatToDateTime(range[1])];
  } else {
    queryFormData.updated_time = undefined;
  }
}

// 加载用户列表
async function loadUserOptions() {
  try {
    // 分页加载所有用户（每页 100 条）
    const allUsers: any[] = [];
    let page = 1;
    const pageSize = 100;
    
    while (true) {
      const query: any = { page_no: page, page_size: pageSize };
      // 只查询启用状态的用户
      query.status = '0';
      console.log('[数据集管理] 开始加载用户列表，查询参数:', query);
      
      const response = await UserAPI.listUser(query);
      const users = response.data.data.items || [];
      console.log('[数据集管理] 第', page, '页用户响应:', users);
      allUsers.push(...users);
      
      // 如果返回的数量小于分页大小，说明已经加载完所有用户
      if (users.length < pageSize) {
        break;
      }
      page++;
    }
    
    userOptions.value = allUsers;
    console.log('[数据集管理] 加载完成，用户选项数量:', userOptions.value.length, '用户选项:', userOptions.value);
  } catch (error: any) {
    console.error('[数据集管理] 加载用户列表失败:', error);
  }
}

// 分页查询参数
const queryFormData = reactive<DatasetsPageQuery>({
  page_no: 1,
  page_size: 10,
  name: undefined,
  version: undefined,
  source: undefined,
  total_images: undefined,
  created_by: undefined,
  updated_by: undefined,
  created_time: undefined,
  updated_time: undefined,
});

// 编辑表单
const formData = reactive<DatasetsForm>({
  id: undefined,
  name: undefined,
  description: undefined,
  version: undefined,
  source: undefined,
  total_images: undefined,
  created_by: undefined,
  updated_by: undefined,
});

const cocoSplitType = ref<string | undefined>(undefined);
type ImportFormat = "coco" | "voc" | "yolo" | "csv";
const importFormat = ref<ImportFormat>("coco");
const cocoImagesZipFileList = ref<UploadUserFile[]>([]);
const cocoAnnotationsFileList = ref<UploadUserFile[]>([]);
const cocoImagesZipRaw = ref<File | null>(null);
const cocoAnnotationsRaw = ref<File | null>(null);

const vocImagesZipFileList = ref<UploadUserFile[]>([]);
const vocAnnotationsZipFileList = ref<UploadUserFile[]>([]);
const vocImagesZipRaw = ref<File | null>(null);
const vocAnnotationsZipRaw = ref<File | null>(null);

const yoloImagesZipFileList = ref<UploadUserFile[]>([]);
const yoloLabelsZipFileList = ref<UploadUserFile[]>([]);
const yoloDataYamlFileList = ref<UploadUserFile[]>([]);
const yoloImagesZipRaw = ref<File | null>(null);
const yoloLabelsZipRaw = ref<File | null>(null);
const yoloDataYamlRaw = ref<File | null>(null);

const csvImagesZipFileList = ref<UploadUserFile[]>([]);
const csvAnnotationsFileList = ref<UploadUserFile[]>([]);
const csvImagesZipRaw = ref<File | null>(null);
const csvAnnotationsRaw = ref<File | null>(null);

// 定义初始表单数据常量
const initialFormData: Omit<DatasetsForm, 'id'> = {
  name: undefined,
  description: undefined,
  version: undefined,
  source: undefined,
  total_images: undefined,
  created_by: undefined,
  updated_by: undefined,
};

// 字典仓库与需要加载的字典类型
const dictStore = useDictStore();
const dictTypes: any = [
];

// 弹窗状态
const dialogVisible = reactive({
  title: "",
  visible: false,
  type: "create" as "create" | "update" | "detail",
});

// 表单验证规则
const rules = reactive({
  id: [{ required: false, message: "请输入数据集ID", trigger: "blur" }],
  name: [{ required: true, message: "请输入数据集名称", trigger: "blur" }],
  description: [{ required: false, message: "请输入数据集描述", trigger: "blur" }],
  version: [{ required: false, message: "请输入数据集版本号", trigger: "blur" }],
  source: [{ required: false, message: "请输入数据集来源", trigger: "blur" }],
  total_images: [{ required: false, message: "请输入总共图片数", trigger: "blur" }],
  created_by: [{ required: false, message: "请输入创建者", trigger: "blur" }],
  updated_by: [{ required: false, message: "请输入更新者", trigger: "blur" }],
});

const handleCocoImagesZipChange = (file: UploadFile, fileList: UploadUserFile[]) => {
  cocoImagesZipRaw.value = (file.raw as File) || null;
  cocoImagesZipFileList.value = fileList;
};

const handleCocoImagesZipRemove = () => {
  cocoImagesZipRaw.value = null;
  cocoImagesZipFileList.value = [];
};

const handleCocoAnnotationsChange = (file: UploadFile, fileList: UploadUserFile[]) => {
  cocoAnnotationsRaw.value = (file.raw as File) || null;
  cocoAnnotationsFileList.value = fileList;
};

const handleCocoAnnotationsRemove = () => {
  cocoAnnotationsRaw.value = null;
  cocoAnnotationsFileList.value = [];
};

const handleVocImagesZipChange = (file: UploadFile, fileList: UploadUserFile[]) => {
  vocImagesZipRaw.value = (file.raw as File) || null;
  vocImagesZipFileList.value = fileList;
};

const handleVocImagesZipRemove = () => {
  vocImagesZipRaw.value = null;
  vocImagesZipFileList.value = [];
};

const handleVocAnnotationsZipChange = (file: UploadFile, fileList: UploadUserFile[]) => {
  vocAnnotationsZipRaw.value = (file.raw as File) || null;
  vocAnnotationsZipFileList.value = fileList;
};

const handleVocAnnotationsZipRemove = () => {
  vocAnnotationsZipRaw.value = null;
  vocAnnotationsZipFileList.value = [];
};

const handleYoloImagesZipChange = (file: UploadFile, fileList: UploadUserFile[]) => {
  yoloImagesZipRaw.value = (file.raw as File) || null;
  yoloImagesZipFileList.value = fileList;
};

const handleYoloImagesZipRemove = () => {
  yoloImagesZipRaw.value = null;
  yoloImagesZipFileList.value = [];
};

const handleYoloLabelsZipChange = (file: UploadFile, fileList: UploadUserFile[]) => {
  yoloLabelsZipRaw.value = (file.raw as File) || null;
  yoloLabelsZipFileList.value = fileList;
};

const handleYoloLabelsZipRemove = () => {
  yoloLabelsZipRaw.value = null;
  yoloLabelsZipFileList.value = [];
};

const handleYoloDataYamlChange = (file: UploadFile, fileList: UploadUserFile[]) => {
  yoloDataYamlRaw.value = (file.raw as File) || null;
  yoloDataYamlFileList.value = fileList;
};

const handleYoloDataYamlRemove = () => {
  yoloDataYamlRaw.value = null;
  yoloDataYamlFileList.value = [];
};

const handleCsvImagesZipChange = (file: UploadFile, fileList: UploadUserFile[]) => {
  csvImagesZipRaw.value = (file.raw as File) || null;
  csvImagesZipFileList.value = fileList;
};

const handleCsvImagesZipRemove = () => {
  csvImagesZipRaw.value = null;
  csvImagesZipFileList.value = [];
};

const handleCsvAnnotationsChange = (file: UploadFile, fileList: UploadUserFile[]) => {
  csvAnnotationsRaw.value = (file.raw as File) || null;
  csvAnnotationsFileList.value = fileList;
};

const handleCsvAnnotationsRemove = () => {
  csvAnnotationsRaw.value = null;
  csvAnnotationsFileList.value = [];
};

function resetImportFiles() {
  cocoImagesZipRaw.value = null;
  cocoAnnotationsRaw.value = null;
  cocoImagesZipFileList.value = [];
  cocoAnnotationsFileList.value = [];

  vocImagesZipRaw.value = null;
  vocAnnotationsZipRaw.value = null;
  vocImagesZipFileList.value = [];
  vocAnnotationsZipFileList.value = [];

  yoloImagesZipRaw.value = null;
  yoloLabelsZipRaw.value = null;
  yoloDataYamlRaw.value = null;
  yoloImagesZipFileList.value = [];
  yoloLabelsZipFileList.value = [];
  yoloDataYamlFileList.value = [];

  csvImagesZipRaw.value = null;
  csvAnnotationsRaw.value = null;
  csvImagesZipFileList.value = [];
  csvAnnotationsFileList.value = [];
}

function setImportFormat(fmt: ImportFormat) {
  if (importFormat.value !== fmt) {
    resetImportFiles();
  }
  importFormat.value = fmt;
  if (!formData.source) {
    formData.source = fmt;
  }
}

// 导入弹窗显示状态
const importDialogVisible = ref(false);
const uploadLoading = ref(false);

// 导出弹窗显示状态
const exportsDialogVisible = ref(false);

// 打开导入弹窗
function handleOpenImportDialog() {
  importDialogVisible.value = true;
}

// 打开导出弹窗
function handleOpenExportsModal() {
  exportsDialogVisible.value = true;
}

// 列表刷新
async function handleRefresh() {
  await loadingData();
}

// 加载表格数据
async function loadingData() {
  loading.value = true;
  try {
    const response = await DatasetsAPI.listDatasets(queryFormData);
    pageTableData.value = response.data.data.items;
    total.value = response.data.data.total;
  } catch (error: any) {
    console.error(error);
  } finally {
    loading.value = false;
  }
}

// 查询（重置页码后获取数据）
async function handleQuery() {
  queryFormData.page_no = 1;
  loadingData();
}

// 选择创建人后触发查询
function handleConfirm() {
  handleQuery();
}

// 重置查询
async function handleResetQuery() {
  queryFormRef.value.resetFields();
  queryFormData.page_no = 1;
  // 重置日期范围选择器
  createdDateRange.value = [];
  updatedDateRange.value = [];
  queryFormData.created_time = undefined;
  queryFormData.updated_time = undefined;
  loadingData();
}

// 重置表单
async function resetForm() {
  if (dataFormRef.value) {
    dataFormRef.value.resetFields();
    dataFormRef.value.clearValidate();
  }
  // 完全重置 formData 为初始状态（不含 id）
  Object.assign(formData, initialFormData);
  formData.id = undefined;
  cocoSplitType.value = undefined;
  importFormat.value = "coco";
  resetImportFiles();
}

// 行复选框选中项变化
async function handleSelectionChange(selection: any) {
  selectIds.value = selection.map((item: any) => item.id);
  selectionRows.value = selection;
}

// 关闭弹窗
async function handleCloseDialog() {
  dialogVisible.visible = false;
  resetForm();
}

// 打开弹窗
async function handleOpenDialog(type: "create" | "update" | "detail", id?: number) {
  dialogVisible.type = type;
  if (id) {
    const response = await DatasetsAPI.detailDatasets(id);
    if (type === "detail") {
      dialogVisible.title = "详情";
      Object.assign(detailFormData.value, response.data.data);
    } else if (type === "update") {
      dialogVisible.title = "修改";
      Object.assign(formData, response.data.data);
    }
  } else {
    dialogVisible.title = "新增数据集";
    // 新增时只需要重置表单字段，id 保持 undefined
    Object.assign(formData, initialFormData);
    formData.id = undefined;
    cocoSplitType.value = undefined;
    importFormat.value = "coco";
    resetImportFiles();
  }
  dialogVisible.visible = true;
}

// 提交表单（防抖）
async function handleSubmit() {
  // 表单校验
  dataFormRef.value.validate(async (valid: any) => {
    if (valid) {
      loading.value = true;
      // 根据弹窗传入的参数 (deatil\create\update) 判断走什么逻辑
      const submitData = { ...formData };
      // 新增时不需要提交 id 字段
      if (dialogVisible.type === 'create') {
        delete submitData.id;
      }
      const id = formData.id;
      if (id) {
        try {
          await DatasetsAPI.updateDatasets(id, { id, ...submitData });
          dialogVisible.visible = false;
          resetForm();
          handleCloseDialog();
          handleResetQuery();
        } catch (error: any) {
          console.error(error);
        } finally {
          loading.value = false;
        }
      } else {
        try {
          const fd = new FormData();
          fd.append("name", String(submitData.name || ""));
          if (submitData.description) fd.append("description", String(submitData.description));
          if (submitData.version) fd.append("version", String(submitData.version));
          fd.append("source", String(submitData.source || importFormat.value));
          if (cocoSplitType.value) fd.append("split_type", cocoSplitType.value);

          if (importFormat.value === "coco") {
            if (!cocoImagesZipRaw.value) {
              ElMessage.error("请上传图片zip包");
              loading.value = false;
              return;
            }
            if (!cocoAnnotationsRaw.value) {
              ElMessage.error("请上传标注json文件");
              loading.value = false;
              return;
            }
            fd.append("images_zip", cocoImagesZipRaw.value);
            fd.append("annotations_json", cocoAnnotationsRaw.value);
            await DatasetsAPI.importCocoDataset(fd);
          } else if (importFormat.value === "voc") {
            if (!vocImagesZipRaw.value) {
              ElMessage.error("请上传图片zip包");
              loading.value = false;
              return;
            }
            if (!vocAnnotationsZipRaw.value) {
              ElMessage.error("请上传标注xml zip包");
              loading.value = false;
              return;
            }
            fd.append("images_zip", vocImagesZipRaw.value);
            fd.append("annotations_zip", vocAnnotationsZipRaw.value);
            await DatasetsAPI.importVocDataset(fd);
          } else if (importFormat.value === "yolo") {
            if (!yoloImagesZipRaw.value) {
              ElMessage.error("请上传图片zip包");
              loading.value = false;
              return;
            }
            if (!yoloLabelsZipRaw.value) {
              ElMessage.error("请上传labels zip包");
              loading.value = false;
              return;
            }
            fd.append("images_zip", yoloImagesZipRaw.value);
            fd.append("labels_zip", yoloLabelsZipRaw.value);
            if (yoloDataYamlRaw.value) fd.append("data_yaml", yoloDataYamlRaw.value);
            await DatasetsAPI.importYoloDataset(fd);
          } else if (importFormat.value === "csv") {
            if (!csvImagesZipRaw.value) {
              ElMessage.error("请上传图片zip包");
              loading.value = false;
              return;
            }
            if (!csvAnnotationsRaw.value) {
              ElMessage.error("请上传标注csv文件");
              loading.value = false;
              return;
            }
            fd.append("images_zip", csvImagesZipRaw.value);
            fd.append("annotations_csv", csvAnnotationsRaw.value);
            await DatasetsAPI.importCsvDataset(fd);
          }

          dialogVisible.visible = false;
          resetForm();
          handleCloseDialog();
          handleResetQuery();
        } catch (error: any) {
          console.error(error);
        } finally {
          loading.value = false;
        }
      }
    }
  });
}

// 删除、批量删除
async function handleDelete(ids: number[]) {
  ElMessageBox.confirm("确认删除该项数据?", "警告", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(async () => {
      try {
        loading.value = true;
        await DatasetsAPI.deleteDatasets(ids);
        handleResetQuery();
      } catch (error: any) {
        console.error(error);
      } finally {
        loading.value = false;
      }
    })
    .catch(() => {
      ElMessageBox.close();
    });
}

// 处理上传
const handleUpload = async (formData: FormData) => {
  try {
    uploadLoading.value = true;
    const response = await DatasetsAPI.importDatasets(formData);
    if (response.data.code === ResultEnum.SUCCESS) {
      ElMessage.success(`${response.data.msg}，${response.data.data}`);
      importDialogVisible.value = false;
      await handleQuery();
    }
  } catch (error: any) {
    console.error(error);
  } finally {
    uploadLoading.value = false;
  }
};

onMounted(async () => {
  // 预加载字典数据
  if (dictTypes.length > 0) {
    await dictStore.getDict(dictTypes);
  }
  // 加载用户列表
  await loadUserOptions();
  loadingData();
});
</script>

<style lang="scss" scoped>
.format-title {
  font-weight: 600;
  font-size: 16px;
}

.format-desc {
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.is-active {
  border-color: var(--el-color-primary);
}
</style>
