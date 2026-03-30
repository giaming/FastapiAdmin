# AI 管理模块本地生图接入技术实现文档（路径 A）

## 1. 背景与目标

在现有 AI 管理能力基础上，新增“AI 生图”模块，采用本地部署的生图引擎（ComfyUI 或 Stable Diffusion WebUI），由后端统一提供鉴权、权限控制、任务编排、参数校验、产物存储与查询接口。

### 1.1 目标

- 支持文生图（Text-to-Image）为第一期能力
- 支持任务异步执行、排队、状态查询、结果下载
- 支持权限点控制与审计（与系统 RBAC 体系一致）
- 支持本地文件落盘与可追溯元数据（任务参数、耗时、错误等）

### 1.2 非目标（第一期不做）

- 不接入任何云端 API
- 不在后端进程内直接集成 torch/diffusers（避免依赖与部署复杂度）
- 不做多机 GPU 调度与复杂计费
- 不做工作流可视化编辑器（可在后续迭代对接）

## 2. 现有系统能力复用点

### 2.1 插件路由与模块结构

后端支持插件模块自动发现与路由挂载，现有 AI 聊天模块已采用统一分层结构（controller/service/crud/model/schema/param）。

### 2.2 权限体系与菜单

系统已提供 RBAC 权限控制，菜单初始化数据中已存在 AI 管理相关节点，可按同样方式扩展“AI 生图”菜单与权限点。

### 2.3 任务调度

系统提供 APScheduler（AsyncIOScheduler）作为任务调度与执行能力，可用于执行生图任务（长耗时作业）。

### 2.4 文件存储

系统提供本地文件上传与静态目录存储能力，默认上传路径位于 `static/upload`，适用于生成图片落盘与管理。

## 3. 技术方案总览（路径 A）

### 3.1 核心思路

- 生图引擎作为本机独立服务运行（ComfyUI 或 WebUI），监听 `127.0.0.1` 或内网地址
- 后端将“生图”抽象为一种任务：创建任务 -> 投递执行 -> 获取进度/结果 -> 落盘 -> 查询/下载
- 后端对外暴露统一 API，前端只依赖后端，不直接访问引擎

### 3.2 引擎选型建议

第一期推荐 ComfyUI：

- API 化能力强，天然以“工作流”为单位，利于后续扩展到图生图、重绘等
- 与“模板化参数 + 工作流版本化”匹配度高

Stable Diffusion WebUI 可作为备选：

- 生态成熟、模型与插件丰富
- API 可用但参数与扩展兼容性差异较大，后端适配成本相对更高

### 3.3 与“本地不调 API”的边界说明

本方案不使用任何云端接口，但会通过 `localhost`/内网 HTTP 与本机引擎服务交互。对外（浏览器侧）不暴露引擎地址，安全边界仍由后端控制。

## 4. 模块与组件设计

### 4.1 后端新增模块结构（建议）

建议新增插件模块目录（示例）：

```txt
backend/app/plugin/module_ai_image/
├── controller.py
├── service.py
├── crud.py
├── model.py
├── schema.py
└── param.py
```

说明：

- 若希望“AI 生图”与“AI 聊天”同属一个模块前缀，也可以放在 `module_ai` 下新增 `image/` 子包；但从权限与演进角度，独立模块更清晰。

### 4.2 引擎适配层（抽象接口）

在 service 层引入“引擎适配器”概念，避免与某个引擎强耦合。

推荐抽象：

- `submit(job)`：提交任务，返回引擎侧 job_id
- `get_status(job_id)`：获取状态/进度
- `get_result(job_id)`：获取产物列表（图片/元数据）
- `cancel(job_id)`：取消任务（若引擎支持）

引擎实现：

- `ComfyUIAdapter`
- `WebUIAdapter`（可选）

### 4.3 任务执行模型

#### 4.3.1 数据库任务表（建议）

建议新增任务表 `ai_image_task`（不加外键约束，通过应用层保证一致性）：

- `id`：主键
- `uuid`：全局唯一任务标识（对外返回）
- `user_id`：发起用户
- `engine_type`：`comfyui` / `webui`
- `engine_job_id`：引擎侧任务 id
- `workflow_id`：工作流模板 id（可选，ComfyUI 推荐）
- `prompt`：用户输入 prompt（可做脱敏与长度限制）
- `negative_prompt`：负向 prompt（可选）
- `params_json`：参数 JSON（steps/width/height/seed/sampler/cfg 等）
- `status`：`queued`/`running`/`success`/`failed`/`canceled`
- `progress`：0-100（可选）
- `result_files_json`：产物文件相对路径列表（JSON）
- `error_message`：失败原因（可截断长度）
- `started_time`/`finished_time`：执行时间
- `created_time`/`updated_time`：通用字段

索引建议：

- `(user_id, created_time)`：用户任务列表
- `(status, created_time)`：后台巡检/重试
- `uuid` 唯一

#### 4.3.2 执行与并发

单机 GPU 场景建议：

- 引擎侧通常自己有队列；后端仍需要做“入口限流 + 用户配额 + 最大并发”
- 最大并发建议配置化（如 1 或 2），避免 OOM 与系统雪崩

实现方式建议：

- 创建任务后落库为 `queued`
- 由调度器或后台 worker 拉取 `queued` 任务并提交到引擎
- 提交成功后写入 `engine_job_id`，状态置为 `running`
- 轮询更新进度并在完成时落盘产物、更新为 `success/failed`

### 4.4 文件落盘与访问策略

#### 4.4.1 落盘目录

建议统一落到后端静态目录下，示例：

- `backend/static/upload/ai_gen/{yyyy}/{mm}/{uuid}/`

落盘文件命名建议：

- `0001.png`、`0002.png`
- `metadata.json`（记录引擎返回的参数、seed、模型、耗时等）

#### 4.4.2 下载与访问

建议对外提供“受控下载”接口，避免直接暴露静态目录路径：

- `GET /ai-image/task/{uuid}/files`：返回文件列表（可带签名/临时 token）
- `GET /ai-image/task/{uuid}/download/{file}`：鉴权后下载

是否允许静态直链由安全策略决定：

- 若启用静态直链，应确保路径不可被枚举，并在返回链接时做权限校验

## 5. API 设计（建议）

统一前缀示例：`/api/v1/ai-image`

### 5.1 创建任务

`POST /ai-image/generate`

请求参数（示例）：

- `prompt`：必填
- `negative_prompt`：选填
- `width`/`height`：必填（白名单分辨率，如 512/768/1024 组合）
- `steps`：选填（范围限制）
- `seed`：选填
- `batch_size`：选填（范围限制）
- `workflow_id`：选填（ComfyUI 推荐用模板 ID）
- `engine_type`：选填（默认 comfyui）

返回（示例）：

- `task_uuid`
- `status=queued`

### 5.2 任务列表与详情

- `GET /ai-image/tasks`：分页列表，支持按状态过滤
- `GET /ai-image/task/{task_uuid}`：详情与当前进度

### 5.3 取消任务

`POST /ai-image/task/{task_uuid}/cancel`

说明：

- 若引擎支持 cancel，则调用引擎取消
- 若不支持，则后端标记取消并停止后续轮询；正在生成的任务由引擎自行结束或由运维处理

### 5.4 产物查询与下载

- `GET /ai-image/task/{task_uuid}/files`
- `GET /ai-image/task/{task_uuid}/download/{filename}`

### 5.5 进度推送（可选）

提供 WebSocket：

- `GET /api/v1/ai-image/ws?token=...`

推送消息示例：

- `{"task_uuid":"...","status":"running","progress":42}`
- `{"task_uuid":"...","status":"success","files":[...]}`

## 6. ComfyUI 对接设计（建议）

### 6.1 工作流模板管理

建议将 ComfyUI workflow 作为“模板”进行管理：

- 将 workflow JSON 存在数据库或配置目录
- `workflow_id` 映射到具体 JSON
- 允许在模板中预留变量（如 prompt、seed、width/height 等）
- 后端在提交前完成变量替换与参数白名单校验

### 6.2 提交与轮询策略

推荐做法：

- 提交后拿到引擎 job_id
- 使用轮询获取状态/进度
- 完成后拉取输出图片并拷贝到后端落盘目录

轮询频率建议：

- running：1-2 秒一次（可配置）
- 成功/失败：立即停止轮询
- 超时：配置化（例如 10-30 分钟），超时标记 failed 并记录错误

## 7. 安全与合规

### 7.1 鉴权与权限点

建议新增权限点（示例）：

- `module_ai_image:task:create`
- `module_ai_image:task:query`
- `module_ai_image:task:detail`
- `module_ai_image:task:cancel`
- `module_ai_image:file:query`
- `module_ai_image:file:download`

菜单挂载到“AI 管理”下或独立一级菜单按产品策略决定。

### 7.2 参数白名单与资源保护

必须做的限制：

- prompt/negative_prompt 长度限制与内容审计（至少做长度与字符集限制）
- width/height/steps/batch_size 的上限与组合白名单
- 单用户并发与频率限制
- 全局最大并发（GPU 保护）
- 输出目录与文件名严格由服务端生成，禁止客户端指定任意路径

### 7.3 引擎服务安全

- 引擎监听地址建议限制为 `127.0.0.1` 或内网，禁止公网暴露
- 引擎与后端之间建议放置在同一宿主机或同一私有网络
- 若必须跨主机访问，建议加内网 ACL 与专用网络隔离

## 8. 配置与部署

### 8.1 后端配置项（建议新增）

- `AI_IMAGE_ENGINE_TYPE`：默认 `comfyui`
- `COMFYUI_BASE_URL`：如 `http://127.0.0.1:8188`
- `WEBUI_BASE_URL`：如 `http://127.0.0.1:7860`
- `AI_IMAGE_MAX_CONCURRENCY`：全局最大并发
- `AI_IMAGE_POLL_INTERVAL_MS`：轮询间隔
- `AI_IMAGE_TASK_TIMEOUT_SEC`：任务超时
- `AI_IMAGE_OUTPUT_DIR`：产物落盘根目录（默认 `static/upload/ai_gen`）

### 8.2 运行形态建议

推荐部署拓扑：

- 后端服务：FastAPI
- 生图引擎：ComfyUI（独立进程或容器）
- GPU 驱动：宿主机安装 CUDA/驱动（容器通过 nvidia-container-runtime 访问 GPU）
- 数据库与 Redis：按现有部署方式

## 9. 可观测性与运维

### 9.1 日志

- 任务创建/取消/完成记录操作日志
- 引擎交互失败记录错误码、耗时与截断后的响应（避免写入敏感信息）

### 9.2 指标（可选）

- 队列长度、成功率、平均耗时、失败原因分类、GPU 并发占用（可用 nvidia-smi 采集）

### 9.3 巡检与补偿

建议增加后台巡检：

- `running` 超时任务标记失败并告警
- 引擎 job_id 不存在时的失败归因
- 产物缺失时的重试/失败处理

## 10. 测试策略

### 10.1 单元测试

- 参数校验（分辨率、steps、batch_size 等）
- 权限校验（不同权限点访问控制）
- 路径生成与落盘安全（防路径穿越）

### 10.2 集成测试

- 在本机启动 ComfyUI（可用最小工作流）
- 提交任务 -> 查询进度 -> 获取结果 -> 下载校验

### 10.3 压测与边界

- 并发提交（验证限流与排队）
- 超时任务（验证失败落库与可见性）
- 引擎不可用（验证降级与错误提示）

## 11. 迭代路线建议

### 11.1 第一阶段（MVP）

- 文生图任务创建、列表、详情、下载
- 基础并发限制与超时
- ComfyUI 单一模板工作流

### 11.2 第二阶段（可用性增强）

- WebSocket 进度推送
- 取消任务
- 多模板工作流与版本管理

### 11.3 第三阶段（能力扩展）

- 图生图、局部重绘、ControlNet 等
- 多机/多 GPU 调度与队列化（如引入专门 worker）

