# 个人项目绩效收益记账系统开发方案（轻量版）

版本：V1.2  
对应 PRD：`PRD.md` V1.2  
适用范围：个人起步、最多约 4～5 人低并发、公网私有部署  
原则：先把业务链路和数据隔离做对，再为未来扩展保留边界，不提前建设企业级基础设施。

> `DEVELOPMENT_PLAN_ENTERPRISE_REFERENCE.md` 保留了企业化扩展参考，但不作为第一版开发标准。

## 1. 结论：第一版不需要复杂技术栈

第一版推荐：

```text
Vue 3 + TypeScript + Vite
            ↓
FastAPI 单体服务
            ↓
SQLite 文件数据库
```

生产环境使用已有 Nginx：

```text
浏览器 → HTTPS → Nginx
                    ├── Vue 构建产物
                    └── /api/* → FastAPI → SQLite
```

第一版暂时不需要：

- PostgreSQL；
- Redis；
- 消息队列；
- 对象存储；
- Kubernetes；
- 微服务；
- 通用工作流引擎；
- 细粒度组织权限系统；
- 独立的通用事件溯源系统。

SQLite 官方文档将单文件、易部署列为其优势，同时也明确其并发写入能力不适合高并发场景。因此它适合当前最多约 4～5 人、低频写入的台账系统；未来如果出现高并发写入、多实例部署或共享协作，再迁移 PostgreSQL，而不是现在提前承担运维成本。[SQLite Appropriate Uses](https://www.sqlite.org/whentouse.html)

## 2. 推荐技术栈

### 2.1 前端

| 领域 | 选择 | 第一版用途 |
|---|---|---|
| 框架 | Vue 3 | 页面和业务组件 |
| 语言 | TypeScript | 约束金额、状态、导入数据 |
| 构建 | Vite | 开发服务器和生产构建 |
| 路由 | Vue Router | Dashboard、列表、详情、规则管理 |
| UI | Element Plus 或同类成熟组件库 | 表格、表单、抽屉、日期选择器 |
| 状态 | 少量 Pinia + composables | 只保存会话和筛选，不复制全部服务端数据 |
| 导入 | `xlsx` 或同类解析库 | 解析 Excel/CSV/剪贴板 |
| 测试 | Vitest + Vue Test Utils | 计算和组件测试 |

第一版不引入图表库也可以。Dashboard 先用数字卡片、状态分组和简单表格；需要趋势图时再加入 ECharts。

### 2.2 后端

| 领域 | 选择 | 第一版用途 |
|---|---|---|
| API | FastAPI | 提供业务 API 和 OpenAPI |
| ORM | SQLAlchemy 2 | 访问 SQLite，保留未来迁移能力 |
| Schema | Pydantic | 请求、响应和导入校验 |
| 数据库迁移 | Alembic | 管理表结构变化 |
| 测试 | pytest | 领域计算、API 和数据库测试 |
| 依赖管理 | `pyproject.toml` + uv 或等价方案 | 锁定 Python 依赖 |

### 2.3 基础设施

开发环境只需要：

```text
Node.js
Python
SQLite
```

生产环境可选：

```text
一台服务器
Nginx
一个由 systemd 管理的 FastAPI 进程
一个 SQLite 数据文件
一个备份目录
```

默认直接在服务器虚拟环境中运行，不要求 Docker。若服务器已有统一 Docker 运维规范，可以使用 Docker Compose，但 SQLite 数据库和备份必须通过宿主机目录挂载，不能放在容器临时层。

## 3. 代码结构

推荐从一个仓库开始：

```text
jizhang/
├── apps/
│   ├── web/
│   │   ├── src/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── features/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── records/
│   │   │   │   ├── project-types/
│   │   │   │   └── imports/
│   │   │   ├── router/
│   │   │   ├── stores/
│   │   │   └── styles/
│   │   └── package.json
│   └── api/
│       ├── app/
│       │   ├── core/
│       │   ├── db/
│       │   ├── auth/
│       │   ├── companies/
│       │   ├── project_types/
│       │   ├── records/
│       │   ├── settlement/
│       │   ├── payouts/
│       │   ├── imports/
│       │   └── dashboard/
│       ├── migrations/
│       ├── tests/
│       └── pyproject.toml
├── data/
│   └── .gitkeep
├── docs/
├── scripts/
├── .env.example
└── README.md
```

后端每个业务模块保持简单的四层：

```text
router → service → repository → database
          ↓
       domain functions
```

状态计算和金额计算必须放在可独立测试的 domain functions 中，不写在 Vue 页面或 API 路由里。

## 4. MVP 数据模型

第一版建设最小账号和角色关系，但不建设组织/工作空间成员关系和通用事件系统，只保留未来扩展最有价值的字段。

### 4.1 `app_users`

公网部署时必须登录。第一版不开放公开注册，由管理员创建成员账号。

```text
id UUID PK
username TEXT UNIQUE
email TEXT NULL UNIQUE
display_name TEXT
password_hash TEXT
role TEXT                    -- admin / member
status TEXT                  -- active / disabled
created_at TIMESTAMPTZ
last_login_at TIMESTAMPTZ NULL
```

权限边界：

- `admin` 可以管理账号和共享项目类型/规则，但只能查看和修改自己的公司、合作记录、到账、导入结果及聚合数据；
- `member` 只能查看和修改自己的公司、合作记录、到账和导入结果；
- 普通成员不能通过公开注册加入系统；
- 所有业务查询都必须按当前用户身份过滤，不能只依赖前端隐藏。

公网部署始终启用登录，支持管理员和普通成员账号；不提供公开注册。

### 4.2 `companies`

```text
id UUID PK
owner_id UUID FK
name TEXT
normalized_name TEXT
status TEXT                  -- active / archived
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

不把公司名称作为全局唯一键，避免同名公司或名称变更造成误合并。

### 4.3 `project_types`

```text
id UUID PK
name TEXT
status TEXT                  -- active / archived
created_by UUID FK
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

第一版项目类型和规则由管理员统一维护，所有成员可选择使用；合作记录仍然按 `owner_id` 隔离。记录保存规则快照，管理员后续改价不会影响历史记录。

### 4.4 `project_type_rules`

```text
id UUID PK
project_type_id UUID FK
version_no INTEGER
standard_performance_cents BIGINT
default_ratio_bps INTEGER NULL
publicity_required BOOLEAN NULL
collection_stage TEXT        -- none / advance / full / advance_and_full
payout_pattern TEXT          -- single / after_advance / advance_then_full；manual 仅兼容旧规则，新建时拒绝
effective_from DATE
effective_to DATE NULL
is_active BOOLEAN
source_note TEXT NULL
created_at TIMESTAMPTZ
```

同一类型的旧规则不修改，新增规则版本。

### 4.5 `cooperation_records`

```text
id UUID PK
owner_id UUID FK
company_id UUID FK
project_type_id UUID FK
rule_id UUID FK NULL
record_date DATE
work_status TEXT             -- in_progress / completed (历史 cancelled 值只读兼容)
completion_date DATE NULL
publicity_status TEXT        -- not_applicable / pending / published
publicity_date DATE NULL
advance_received_date DATE NULL
full_received_date DATE NULL
participation_mode TEXT      -- exclusive / shared
my_ratio_bps INTEGER NULL
standard_performance_cents BIGINT NULL
my_due_amount_cents BIGINT NULL
override_reason TEXT NULL
snapshot_publicity_required BOOLEAN NULL
snapshot_collection_stage TEXT NULL
snapshot_payout_pattern TEXT NULL
archived_at TIMESTAMPTZ NULL
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

说明：

- `standard_performance_cents` 是创建时规则快照；
- `my_ratio_bps` 为空表示比例未知，不表示0%；
- `my_due_amount_cents` 为空表示本人应得未知；
- `advance_received_date` 和 `full_received_date` 只代表公司收款节点，不代表个人到账；
- 不设置公司收款金额字段；
- 不对公司+类型+日期设置唯一约束，只做重复提示。

### 4.6 `payout_records`

第一版不单独建设 `payout_batches` 表，实际到账记录直接带批次类型：

```text
id UUID PK
owner_id UUID FK
cooperation_record_id UUID FK
batch_type TEXT               -- advance / final / manual / unknown
amount_cents BIGINT
received_date DATE
note TEXT NULL
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

预付款后的第一笔到账可以标记为 `advance`，全款后的到账可以标记为 `final`；比例未知不影响实际金额录入。

### 4.7 `performance_changes`

记录会影响收益结果的人工调整，以及关键里程碑和个人到账的更正/作废：

```text
id UUID PK
owner_id UUID FK
cooperation_record_id UUID FK
field_name TEXT              -- standard / ratio / due_amount / flow
old_value JSON
new_value JSON
reason TEXT
created_at TIMESTAMPTZ
```

金额/比例调整必须提交原因；明确传 `null` 表示清除覆盖值，与字段未传区分。更正完成、公示、预付款、全款日期及编辑/作废到账也必须带原因并进入该记录的历史查询。

### 4.8 `import_batches`

```text
id UUID PK
owner_id UUID FK
source_type TEXT              -- xlsx / csv / clipboard
parser_mode TEXT
mapping JSON
status TEXT                   -- preview / committed / rolled_back / failed
created_record_ids JSON
error_summary JSON
created_at TIMESTAMPTZ
```

第一版不必把每一行原始数据永久保存；预览数据保存在前端，提交时由后端重新校验。若需要撤销，`created_record_ids` 足以支持撤销本批新增数据。

### 4.9 `system_meta`

用于记录备份判断所需的系统级数据版本，不承载业务明细：

```text
key TEXT PK                  -- data_revision
value TEXT
updated_at TIMESTAMPTZ
```

每次成功提交业务写入时递增 `data_revision`，每日备份任务与上次备份版本比较，只有发生变化时才生成新的 SQLite 备份。

## 5. 业务计算

### 5.1 金额

```text
effective_standard = record.override_standard ?? record.standard_performance
effective_ratio = record.my_ratio ?? rule.default_ratio

if manual_due_amount exists:
    my_due = manual_due_amount
else if effective_standard and effective_ratio are known:
    my_due = round(effective_standard * effective_ratio / 10000)
else:
    my_due = NULL

paid_total = SUM(payout_records.amount_cents)

if my_due is NULL:
    outstanding = NULL
else:
    outstanding = max(my_due - paid_total, 0)
```

约定：

- 10000 基点 = 100%；
- 未知使用 `NULL`；
- 金额使用分，不使用浮点；
- 到账金额大于应得金额时允许保存，但显示异常提示。

### 5.2 当前节点

状态计算函数只依赖合作记录、规则快照和到账记录：

```text
calculate_current_node(record, rule, payouts)
```

判断顺序：

1. 历史数据若保留旧 `cancelled` 值，仅兼容显示；新建/编辑不允许写入；归档不属于工作/结算状态；
2. 未完成 → 进行中；
3. 需要公示且未公示 → 待公示；
4. 已有个人到账但比例/应得未知 → 待确认个人比例，展示已到账且待到账未知；
5. 要求预付款但没有预付款日期 → 待公司预付款；
6. 要求全款但没有全款日期 → 待公司全款；
7. 无个人到账且比例/应得未知 → 待确认个人比例；
8. `single` 模式已满足完成/公示条件且没有到账 → 待个人发放；
9. 预付款已到但还没有第一笔到账 → 待第一批发放；
10. 全款已到且已到账小于应得 → 待尾款发放；
11. 已到账大于0但小于应得 → 部分发放；
12. 已到账大于等于应得 → 已结清。

`current_node` 不作为唯一事实写死在数据库中，由服务端计算后返回。这样补录日期或到账记录后，状态会自动更新。

### 5.3 项目类型规则

第一版支持四类规则组合：

| `collection_stage` | `payout_pattern` | 含义 |
|---|---|---|
| none | single | 完成/公示条件满足后一次发放 |
| advance | after_advance | 公司预付款后发放 |
| full | single | 公司全款后发放 |
| advance_and_full | advance_then_full | 预付款后部分发放，全款后发放剩余 |

如果未来出现其他组合，再扩展枚举，不引入自由流程编辑器。

## 6. API 设计

统一前缀：`/api/v1`。

### 6.1 通用约定

- ID 使用 UUID；
- 日期使用 `YYYY-MM-DD`；
- 金额使用 `*_cents` 整数；
- 未知使用 `null`；
- 列表支持 `page`、`page_size`、`q` 和状态筛选；
- 错误格式统一；
- 后端重新校验所有金额、比例、日期和类型值。

所有业务 API 都要求登录。服务端从会话中取得当前用户，不接受前端传入的 `owner_id` 作为权限依据。

### 6.2 认证和账号管理

```text
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
POST /api/v1/admin/users
GET  /api/v1/admin/users
PATCH /api/v1/admin/users/{id}
POST /api/v1/admin/users/{id}/reset-password
```

第一版只支持管理员创建账号、禁用账号和重置密码，不实现公开注册、邮箱验证和短信验证。所有角色仅访问自己的业务数据；管理员额外管理账号和共享类型规则。生产环境通过 `JIZHANG_ENV=production` 强制启用 `HttpOnly`、`Secure` Cookie，且不接受通配 CORS 来源。登录对同一来源/账号 15 分钟限 5 次失败；这项内存限速仅适用于单进程。

### 6.3 合作公司

```text
GET   /api/v1/companies
POST  /api/v1/companies
PATCH /api/v1/companies/{id}
POST  /api/v1/companies/{id}/archive
```

### 6.4 项目类型和规则

```text
GET   /api/v1/project-types
POST  /api/v1/project-types
PATCH /api/v1/project-types/{id}
GET   /api/v1/project-types/{id}/rules
POST  /api/v1/project-types/{id}/rules
POST  /api/v1/project-types/{id}/archive
```

规则创建时校验版本号和生效日期，不能直接修改已经使用过的旧规则。

### 6.5 合作记录

```text
GET   /api/v1/records
POST  /api/v1/records/duplicate-check
POST  /api/v1/records
GET   /api/v1/records/{id}
PATCH /api/v1/records/{id}
GET   /api/v1/records/{id}/performance-changes
PATCH /api/v1/records/{id}/milestones
POST  /api/v1/records/{id}/complete
POST  /api/v1/records/{id}/publish
POST  /api/v1/records/{id}/override
POST  /api/v1/records/{id}/archive
POST  /api/v1/records/{id}/unarchive
```

重复检查只返回提示，不阻止创建。

### 6.6 公司收款和个人到账

```text
POST  /api/v1/records/{id}/advance-received
POST  /api/v1/records/{id}/full-received
GET   /api/v1/records/{id}/payouts
POST  /api/v1/records/{id}/payouts
PATCH /api/v1/payouts/{id}
POST  /api/v1/payouts/{id}/void
```

`advance-received` 和 `full-received` 不携带公司收款金额，只携带日期和备注。

### 6.7 Dashboard、导入和导出

```text
GET  /api/v1/dashboard/summary
POST /api/v1/imports/preview
POST /api/v1/imports/preview-file
POST /api/v1/imports/commit
POST /api/v1/imports/commit-file
GET  /api/v1/exports/records.csv
GET  /api/v1/exports/records.json
```

导入预览不写入业务表；提交时在一个 SQLite 事务中完成。实际接口为 `/imports/preview`、`/imports/preview-file`、`/imports/commit` 和 `/imports/commit-file`；提交必须附带用户选择的行号，后端重新解析校验，错误行不可选。历史重复与批内重复只警告、不自动合并。V1 暂无批次浏览/整批撤销入口。

## 7. 前端页面

### 7.1 页面路由

```text
/dashboard
/records
/records/new
/records/:id
/project-types
/project-types/:id
/imports
/settings
```

### 7.2 Dashboard

第一版不用图表也可以，优先展示：

- 进行中；
- 待公示；
- 待公司预付款/全款；
- 待第一批发放；
- 待尾款发放；
- 部分发放；
- 已结清；
- 已到账总额；
- 待到账总额。

### 7.3 合作记录列表

核心字段：

```text
合作公司 / 项目类型 / 记录日期 / 当前节点 / 我的应得 / 已到账 / 待到账
```

筛选：公司、类型、年度、工作状态、公示状态、公司收款状态、当前节点。

### 7.4 合作记录详情

```text
合作公司和类型
规则摘要
金额摘要
完成/公示/预付款/全款节点
到账记录
人工调整历史
```

### 7.5 项目类型管理

列表展示：

```text
类型名称 / 当前规则版本 / 标准绩效 / 是否公示 / 收款节点 / 发放模式
```

编辑已有规则时强制创建新版本。

## 8. 导入方案

### 8.1 解析位置

```text
剪贴板文本或 Excel/CSV 文件提交到 API 确定性解析
        ↓
返回解析预览，用户选择有效行
        ↓
后端重新解析、校验和匹配规则
        ↓
SQLite 单事务写入所选记录
```

导入不调用 AI。上传文件限制为 5 MB，XLSX 展开数据限制为 25 MB，最多 1 万行；每次提交整体成功或整体回滚。

### 8.2 支持模式

1. 无表头时按固定列顺序读取：合作公司、项目类型、可选记录日期、标准绩效覆盖、个人比例；
2. 带支持表头别名时按字段解析；
3. 自动识别制表符、逗号或分号，不提供自定义分隔符和任意字段映射；
4. 未来再评估多工作表导入。

### 8.3 校验

- 公司名称为空：错误；
- 项目类型为空或找不到记录日期适用规则：错误，不可提交；
- 日期无法解析：错误；
- 金额必须是非负有效数；比例必须在 0–100 之间；
- 类型规则未匹配：错误，不可提交；
- 已有相同公司和类型记录：警告，不自动合并；
- 批次内相同公司和类型：警告，不自动合并；
- 用户未勾选的有效行不写入；
- 提交失败：整批回滚。

## 9. 认证、备份和部署

### 9.1 认证

公网部署始终启用登录：

- 初始化一个管理员账号；
- 管理员创建和禁用成员账号；
- 只保留 `admin` 和 `member` 两种角色；
- 所有角色只看自己的业务数据；
- 管理员额外管理账号和共享项目类型规则；
- 不开放完全公开注册；
- 密码重置先由管理员在后台或服务器命令完成，不引入邮箱和短信服务。

权限必须在后端查询层执行。前端隐藏菜单不构成权限控制。

### 9.2 本地开发

```text
前端：npm run dev
后端：uv run fastapi dev app/main.py
数据库：data/jizhang.sqlite
```

开发阶段允许前后端两个进程，生产阶段由 Nginx 托管 `web/dist`，并将 `/api` 反向代理到 FastAPI。

### 9.3 生产部署

默认生产形态：

```text
Nginx
├── /srv/jizhang/web/dist
└── /api/* → 127.0.0.1:8000

systemd
└── jizhang-api.service → FastAPI

/srv/jizhang/data/jizhang.sqlite
/srv/jizhang/backups/
```

Nginx 只负责 HTTPS、静态文件和 API 反向代理，FastAPI 不直接暴露公网端口。systemd 在启动 API 前执行 `alembic upgrade head`；应用启动过程不运行 `create_all()`。生产服务仅使用一个 Uvicorn worker，以匹配 SQLite 和进程内登录限速边界。Docker Compose 保留为可选部署方式；如果使用 Docker，必须将 `data/` 和 `backups/` 绑定到宿主机。

### 9.4 备份

必须提供：

- 每日定时检查数据库是否发生变化；
- 有变化时使用 SQLite backup API 生成新备份；
- 无变化时不重复生成备份文件；
- 每日即使没有业务变化也清理超过 30 天的备份；
- 备份目录不允许被 Nginx 直接访问；
- 支持从备份恢复；恢复前必须停止 API，并自动生成恢复前安全副本；
- 恢复源和恢复临时文件均校验 SQLite 完整性；恢复后人工登录抽查项目、金额和到账；
- 提供 CSV/JSON 导出作为人工数据出口。

建议在 `system_meta` 中维护一个随业务事务递增的 `data_revision`：

```text
定时任务读取 data_revision
    ↓
与上次备份记录比较
    ↓
没有变化：跳过
有变化：SQLite backup API → 临时文件 → integrity_check → 原子重命名
```

备份时间按 `Asia/Shanghai（UTC+8）` 运行。仅保存在同一台服务器可以防止误操作和程序故障，但不能防止服务器磁盘整体损坏，这是当前低成本部署下的已知风险。

不建议直接复制正在写入的 SQLite 文件，备份脚本应使用 SQLite backup API。

## 10. 测试方案

### 10.1 领域测试

至少覆盖：

| 场景 | 结果 |
|---|---|
| 新建记录 | 进行中 |
| 完成但要求公示 | 待公示 |
| 已公示但未收预付款 | 待公司预付款 |
| 预付款已收但没有第一笔到账 | 待第一批发放 |
| 第一笔已到账但未收全款 | 已部分发放/待全款 |
| 全款已收且已到账少于应得 | 待尾款发放 |
| 比例未知 | 待确认个人比例 |
| 已到账等于应得 | 已结清 |
| 修改类型规则 | 历史记录不变化 |
| 预览导入 | 不写正式业务表 |
| 导入提交失败 | 整批回滚 |

### 10.2 前后端测试

- FastAPI API 集成测试；
- Vue 表单、金额和状态组件测试；
- 导入预览测试；
- Playwright 跑一条完整发放链路；
- 前端类型检查、lint、build；
- 后端 pytest 和迁移测试。

## 11. 开发顺序

### 阶段 0：最小工程骨架

- 创建 Vue/Vite 和 FastAPI 项目；
- SQLite 连接和 Alembic；
- 基础布局、路由和错误处理；
- `.env.example` 和 README；
- 领域金额/比例工具函数。

完成标准：空库可以启动，前后端可以互相请求。

### 阶段 1：项目类型规则

- 合作公司；
- 项目类型；
- 规则版本；
- 标准绩效、公示、收款节点、发放模式；
- 规则摘要。

完成标准：可以维护一条类型规则，并创建新版本而不影响旧版本。

### 阶段 2：合作记录

- 快速新增；
- 北京时间默认记录日期；
- 重复提示；
- 规则快照；
- 独享比例100%；
- 多人比例未知/具体比例；
- 人工覆盖和历史。

完成标准：只填写公司和类型即可创建一条可追踪记录。

### 阶段 3：流程和到账

- 完成、公示、预付款、全款；
- 当前节点计算；
- 多笔个人到账；
- 已到账和待到账；
- 预付款部分发放链路。

完成标准：跑通“完成 → 公示 → 预付款 → 第一笔到账 → 全款 → 尾款到账”。

### 阶段 4：Dashboard 和导入

- 首页状态卡片；
- 列表筛选；
- 详情时间线；
- Excel/CSV/剪贴板预览；
- 选择有效行后原子提交（提交失败整批回滚）；
- CSV/JSON 导出。

完成标准：可以批量录入并从首页找到所有未结清记录。

### 阶段 5：账号、私有部署和备份

- 管理员初始化；
- 管理员创建、禁用和重置成员账号；
- 后端按用户隔离查询和修改；
- Nginx HTTPS、静态文件和 API 反向代理；
- systemd 管理 FastAPI；
- 数据有变化时才生成每日 SQLite 备份；
- 保留 30 天备份并验证恢复；
- 发布说明和完整回归测试。

完成标准：管理员可以创建成员，成员只能看到自己的数据，部署后可以按 README 恢复系统和数据。

## 12. 何时升级到 PostgreSQL/企业架构

满足以下任一条件再升级：

- 用户数量或写入并发明显增长；
- 需要跨用户共享和协作数据；
- 需要组织、成员和更细的权限；
- 需要多实例部署；
- 需要后台异步处理大批量导入；
- 需要附件、对象存储或通知中心；
- 需要高可用和集中式备份。

升级顺序建议：

```text
SQLite → PostgreSQL
小团队用户 → 组织/成员/工作空间
单进程 → 多实例 API
同步导入 → 后台任务
简单到账记录 → 独立发放批次/事件表
```

金额计算、规则快照、状态计算和 API 语义不应因数据库迁移而改变。

## 13. 第一版完成标准

- 个人可以在一分钟内创建一条合作记录；
- 项目类型可以带出标准绩效和流程；
- 同公司同类型重复时有提示但不会自动合并；
- 完成、公示、预付款、全款和个人到账互不混淆；
- 预付款后的实际到账可以先录入，比例未知也不报错；
- 类型规则改版不会改变历史记录；
- Excel/剪贴板导入先预览再写入；
- Dashboard 能区分进行中、待公示、待收款、待发放、部分发放和已结清；
- 数据可以导出和恢复；
- 不引入当前不需要的 PostgreSQL、Redis、队列、AI 或细粒度企业权限系统；Nginx 已作为公网部署基础设施使用。
