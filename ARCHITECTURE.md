# AE WPM 技术架构（汇报版）

> 基于当前代码和部署文档整理；“演进建议”是建议方向，不代表已实现。

## 一、项目概览

AE WPM 是迁移项目全生命周期管理门户，覆盖**迁移申请、评估、商业案例、审批及执行跟踪**。

当前采用**前后端分离的模块化单体架构**：Vue 3 前端、Django REST API 后端、SQL Server 生产数据库。生产运行于 Windows，由 Apache 统一提供 HTTPS、静态页面和 API 反向代理。

## 二、系统架构

### Overall

![AE WPM 系统架构 Overall 图](./architecture-system-overall.svg)

### 详细版

![AE WPM 系统架构详细图](./architecture-system-detailed.svg)

**主要组件**

| 层 | 当前技术与职责 |
|---|---|
| 前端 | Vue 3、Vue Router、MDS；负责业务页面、表单及项目工作区。 |
| 接入 | Apache 处理 HTTPS、SPA 静态资源和 `/api` 反向代理。 |
| 后端 | Django 5、DRF；按业务路由、视图、服务和模型组织，作为一个后端应用部署。 |
| 数据与集成 | Django ORM；生产 SQL Server、开发 SQLite；集成 Entra ID、SendGrid 和 LLM API。 |

开发环境使用 Vite `3002`，本地 Django `8001` 与 SQLite；生产后端只监听本机 `8000`，不应直接对外开放。详见 [DEPLOYMENT.md](./DEPLOYMENT.md)。

## 三、核心业务流程

### Overall

![AE WPM 核心业务流程 Overall 图](./architecture-business-flow-overall.svg)

### 详细版

![AE WPM 核心业务流程详细图](./architecture-business-flow-detailed.svg)

详细版按项目生命周期展示五个阶段及其交付物；阶段清单依据提供的流程参考，具体功能和状态以项目配置及系统实际实现为准。

各工作区以项目记录或 `migration_request_id` 关联。主要业务域包括：

- **项目与评估：** Intake、Opportunity Assessment、Scope Statement。
- **项目准备：** Project Charter、资源、访问准备、利益相关方及人员咨询。
- **财务与审批：** Business Case、成本费率、角色审批与审批状态。
- **跟踪与管理：** Gantt、Migration Dashboard、BPM ROFO/Actual。
- **主数据：** 产品归属、GSC 站点、服务目录、工作时间及访问配置。

项目、评估、审批等数据由 Django ORM 管理；部分灵活工作区使用 JSON 字段，并在部分记录中保留 revision 或审计信息。附件通过 Django `FileField` 处理。

## 四、关键技术路径

- **登录与权限：** 前端通过 Entra ID 登录并附带身份相关请求头；后端按项目申请人/团队、Super Admin 或主数据访问配置进行授权。
- **邮件：** 后端调用 SendGrid 发送通知。
- **AI 问答：** Django 先抽取查询条件、读取业务数据，再调用 LLM 生成回答；仓库另有 Dify 文件解析 helper，但不是聊天主链路。
- **部署：** Apache 提供用户入口并转发 API；Waitress 承载 Django；生产数据保存在 SQL Server。开发使用 Vite、Django 和 SQLite。

## 五、建议的演进重点

1. **先加固身份边界：** 当前后端身份 helper 会读取 JWT 载荷及 `X-User-Email`，但 helper 本身没有验证 JWT 签名、issuer 或 audience。应确认上游是否已验证；若没有，应在后端增加标准验证，并限制 mock 身份仅用于受控开发环境。
2. **提升数据可靠性：** 明确附件的生产存储、备份与恢复；统一跨工作区的审计和并发编辑规则，并加强 SQL Server 迁移验证。
3. **完善发布运维：** 逐步自动化测试、迁移审批、备份确认、健康检查和回滚验证；补齐 API、数据库及邮件/LLM 外部依赖的监控。
4. **暂缓为拆分而拆分：** 目前模块化单体与业务形态匹配。先强化模块边界；只有在规模、团队或独立扩缩容需求明确后，再评估微服务。

## 汇报结论

**当前方向是“前后端分离 + 模块化单体 + Windows 集中部署”。** 建议按“身份安全 → 数据可靠 → 发布可运维 → 按需扩展”的顺序演进，现阶段优先把现有平台做稳，而不是先引入微服务复杂度。

**代码参考：** [README.md](./README.md)、[backend/config/settings.py](./backend/config/settings.py)、[backend/api/models.py](./backend/api/models.py)、[frontend/src/router/index.js](./frontend/src/router/index.js)、[backend/api/permissions/attributes_access.py](./backend/api/permissions/attributes_access.py)。
