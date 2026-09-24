# 进度日志

## 会话：2026-09-20

### 阶段 1：需求与发现
- **状态：** complete
- **开始时间：** 2026-09-20
- 执行的操作：
  - 读取 planning-with-files-zh 技能规则。
  - 检查工作目录和现有代码文件。
  - 确认以 PRD、CONTEXT 和 ADR 作为方案基线。
- 创建/修改的文件：
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### 阶段 2：规划与结构
- **状态：** complete
- 执行的操作：
  - 评估了企业化方案和个人 MVP 的复杂度。
  - 核对 Vue、FastAPI、Docker Compose、PostgreSQL 和 SQLite 官方资料。
  - 将架构收敛为 Vue + FastAPI + SQLite 轻量单体。
- 创建/修改的文件：
  - `DEVELOPMENT_PLAN_ENTERPRISE_REFERENCE.md`
  - `DEVELOPMENT_PLAN.md`

### 阶段 3：方案文档
- **状态：** complete
- 执行的操作：
  - 编写轻量版架构、数据模型、API、导入、测试和分阶段开发方案。
  - 记录 SQLite 到 PostgreSQL 的升级条件。
- 创建/修改的文件：
  - `DEVELOPMENT_PLAN.md`

### 阶段 4：审查与验证
- **状态：** complete
- 执行的操作：
  - 核对主方案没有把 PostgreSQL、Nginx、Redis、消息队列或组织权限作为第一版前置依赖。
  - 修正无公司收款要求的一次发放类型的当前节点计算。
  - 统一金额字段使用 BIGINT 分值，导入提交路径和轻量数据模型。
  - 检查 PRD、CONTEXT、ADR 和主开发方案文件均存在且非空。
- 创建/修改的文件：
  - `DEVELOPMENT_PLAN.md`
  - `task_plan.md`
  - `progress.md`

### 阶段 5：确认后的方案同步
- **状态：** complete
- 执行的操作：
  - 根据用户确认，将范围从单用户调整为管理员创建的少量成员账号；
  - 明确普通成员只能访问自己的合作记录，管理员可查看全部记录；
  - 将公网部署定为 Nginx + systemd + FastAPI + SQLite，Docker 保留为可选方式；
  - 增加每日检查数据版本、变化后备份、保留 30 天的备份方案；
  - 更新 PRD、CONTEXT、开发方案和 ADR。
- 创建/修改的文件：
  - `PRD.md`
  - `CONTEXT.md`
  - `DEVELOPMENT_PLAN.md`
  - `findings.md`
  - `task_plan.md`
  - `docs/adr/0004-single-user-first-with-an-ownership-boundary.md`
  - `docs/adr/0005-small-team-accounts-with-owner-scoped-data.md`

### 阶段 6：最终一致性检查
- **状态：** complete
- 执行的操作：
  - 检查旧的“单用户登录”“未来再使用 Nginx”等表述已清除；
  - 确认所有方案文档均存在且非空；
  - 确认新增管理员/成员、owner 隔离、Nginx/systemd、变更后备份和 30 天保留规则已在主要文档中一致出现。
- 测试结果：文档静态检查通过；未执行应用构建或运行测试，因为当前仓库尚无应用代码。

## 会话：应用开发启动

### 阶段 6：MVP 应用开发
- **状态：** complete
- 执行的操作：
  - 用户明确要求开始开发；
  - 重新读取当前任务计划、发现和进度；
  - 将任务计划切换到应用开发阶段。
- 已完成：创建工程骨架、认证、用户隔离、规则、记录、到账、导入、Dashboard、备份和部署示例。

### 阶段 7：验证与交付
- **状态：** complete
- 验证结果：
  - 后端 `pytest`：4 passed；
  - Alembic `check`：No new upgrade operations detected；
  - Python compileall：通过；
  - 前端 `npm run build`：类型检查和 Vite 生产构建通过；
  - SQLite 变更检测备份：首次生成、无变化跳过均通过；
  - Uvicorn 真实端口启动：受当前沙箱禁止监听本地端口影响，未完成；接口已用 TestClient 验证。
- 交付文件：
  - `apps/api/`：FastAPI、模型、迁移、测试和备份脚本；
  - `apps/web/`：Vue 前端和生产构建；
  - `deploy/`：systemd、备份定时任务和 Nginx 示例；
  - `README.md`：本地启动和部署说明。

## 测试结果
| 测试 | 输入 | 预期结果 | 实际结果 | 状态 |
|------|------|---------|---------|------|
| 文档基线检查 | PRD/CONTEXT/ADR | 文件存在且可读取 | 已确认 | 通过 |
| 轻量架构静态检查 | 小团队低并发范围 vs DEVELOPMENT_PLAN.md | 无强制 PostgreSQL/Redis/队列 | 已确认 | 通过 |
| 方案一致性检查 | PRD/CONTEXT/ADR/开发方案 | 预付款、全款、未知比例和规则版本一致 | 已确认 | 通过 |
| 后端业务流程测试 | 登录、用户隔离、规则、单批次和分阶段到账 | 4 个测试通过 | 已确认 | 通过 |
| 数据库迁移检查 | Alembic metadata 与 migration | 无新增迁移操作 | 已确认 | 通过 |
| 前端生产构建 | `npm run build` | vue-tsc 和 Vite 构建成功 | 已确认 | 通过 |
| 备份脚本 | 数据版本变化/不变化 | 分别生成/跳过备份 | 已确认 | 通过 |

## 错误日志
| 时间戳 | 错误 | 尝试次数 | 解决方案 |
|--------|------|---------|---------|
| 2026-09-20 | Python `compileall` 写入 macOS 受限缓存目录被拒绝 | 1 | 使用任务专用字节码缓存目录重试 |
| 2026-09-20 | `npm install` 长时间无输出 | 1 | 停止无反馈进程，保留代码并稍后用受控方式验证依赖 |
| 2026-09-20 | `uv sync` 默认使用受限缓存目录 | 1 | 改用任务专用 `UV_CACHE_DIR` 临时路径 |
| 2026-09-20 | SQLAlchemy 在 Python 3.9 下无法解析模型中的 `str | None` | 1 | 改为 `typing.Optional`，API 模块导入验证通过 |
| 2026-09-20 | 系统 Python 缺少 `hashlib.scrypt` | 1 | 改为 PBKDF2-HMAC-SHA256，登录测试通过 |
| 2026-09-20 | 登录接口响应参数被 FastAPI 当作查询参数 | 1 | 使用 `Response` 类型注入，接口测试通过 |
| 2026-09-20 | SQLite 临时备份文件 URI 校验失败 | 1 | 改为显式文件路径连接，备份测试通过 |
| 2026-09-20 | 清理后的空 SQLite 数据库未执行迁移时 Alembic check 报 target not up to date | 1 | 执行 upgrade head 后 check 通过，并清理测试数据库 |
| 2026-09-20 | 沙箱禁止 Uvicorn 绑定本地 8000 端口 | 1 | 使用 TestClient 完成 API 验证；真实服务器监听需在用户服务器执行 |

## 五问重启检查
| 问题 | 答案 |
|------|------|
| 我在哪里？ | 阶段 7：验证与交付完成 |
| 我要去哪里？ | 进入用户服务器部署和后续迭代 |
| 目标是什么？ | 交付可运行的 MVP 账本系统 |
| 我学到了什么？ | 见 findings.md |
| 我做了什么？ | 已完成 MVP 应用、迁移、测试和部署示例 |

---
*每个阶段完成后或遇到错误时更新此文件*

## 会话：2026-09-23 上线准备审计

### 阶段 8：上线准备审计
- **状态：** complete，用户已确认业务边界
- **审计范围：** PRD/CONTEXT/ADR 对照、业务状态计算、导入、权限、绩效调整与纠错、认证、备份、部署模板、自动化验证。
- **执行结果：**
  - 审计开始时仓库位于 main 分支、HEAD 为 641c1c8，工作区干净。
  - 后端 pytest：4 passed。
  - 前端 npm run build：通过。
  - Python compileall：通过。
  - 在 /private/tmp 的隔离数据库执行 Alembic upgrade/check：通过。
  - 状态探针复现“advance_and_full + single”在没有全款时仍可显示 settled。
  - 导入解析探针确认负金额和超过100%的比例可通过解析；导入路径缺少对应业务范围校验。
  - 未访问真实公网服务器；没有进行浏览器端到端、目标机 Nginx/systemd、渗透、依赖漏洞扫描或恢复演练。
- **主要结论：** MVP 核心链路和架构已具备；当前不应直接作为公网多人生产账本上线。P1/P2 证据、源码定位和建议见 findings.md 的“2026-09-23 上线准备审计”。
- **用户已确认：** 管理员仅访问本人记录；导入可选有效行且整批事务提交；V1 不建取消状态、使用归档；比例/应得未知时即使已有到账也保持待确认比例。
- **本轮修改：** 仅更新 task_plan.md、findings.md、progress.md 审计记录；没有修改应用代码。

## 会话：2026-09-23 上线整改

### 阶段 9：上线整改实施
- **状态：** in_progress
- **用户目标：** 先设计整改顺序并开始修复已审计的问题。
- **已确认决策：** 管理员只看本人业务数据；导入预览选择有效行并以单事务提交；V1 用归档、不用取消状态；比例未知时状态保持待确认比例，即使已有到账。
- **整改顺序：** 权限隔离 → 结算状态与规则校验 → 导入校验和选择 → 纠错/绩效审计 → 公网安全、迁移、备份恢复 → 全量回归。
- **当前动作：** 第一项代码修复已收敛为 owner-only；已移除管理员对他人公司、记录、到账和聚合查询的 owner-scope 旁路，待添加反向越权回归并运行。
- **工作区检查：** 上一轮的 `findings.md`、`progress.md`、`task_plan.md` 变更保留；本次没有应用代码改动。仓库未提供 `.codegraph/` 索引或额外 `AGENTS.md` 文件。
- **权限修复进展：** 增加管理员访问成员公司、记录、到账、Dashboard 和导出数据的反向越权测试；定向测试 `1 passed`。首次 pytest 因默认 uv 缓存目录无读取权限失败，改用 `/private/tmp/jizhang-uv-cache` 后通过。
- **第二阶段实现：** 状态机对未知应得且已有到账改为 `pending_ratio`；服务端仅接受开发方案中的四种结算组合，规则页不再为新规则提供语义不清的 `manual` 选项（历史标签保留）。
- **回归结果：** 状态、规则组合和权限新增 API 测试后，后端全套 `pytest -q`：8 passed。
- **导入阶段进展：** 后端预览已加入 5 MB/1 万行限制、Excel 解压上限、金额/比例/规则校验及跨日期历史/批内重复提示；提交改为必须传所选行号，预检后单事务写入并整体回滚。前端粘贴/文件均可选择有效行，待完善测试和构建。
- **导入阶段回归：** 新增三条 API 回归（历史含归档记录/批内重复、无效行拒绝、只提交勾选行、文件 multipart 行号）；定向运行 3 passed。`npm run build` 的 vue-tsc 与 Vite 构建通过。
- **归档与纠错阶段：** API 新增归档记录筛选、恢复和里程碑日期更正；编辑可显式清空金额/比例，财务调整必须提供原因，并提供单条绩效调整历史查询。详情页增加节点日期表单、调整历史、到账作废入口；到账纠错采用作废后重录以保留原记录。归档列表支持恢复，历史金额/到账事实不因归档改变。
- **阶段回归：** 后端全套测试 14 passed；前端 `npm run build` 的类型检查和生产构建通过。到账直接 PATCH 也要求原因并记入历史，作废要求原因且不可重复作废。公网/备份整改待处理。

### 阶段 9：本地整改收尾与回归
- **状态：** complete；目标服务器验收仍待执行
- **额外走查修复：**
  - 导入器增加“公司名称”表头别名，并增加对应回归测试，修复与导入页面示例不匹配的问题；
  - 公司/项目类型 API 限制状态枚举，改名时拦截重复目标，拒绝空白名称；
  - systemd API 服务统一使用 `apps/api/.venv`，并将工作目录设为 `apps/api`，保证 Alembic 的 `prepend_sys_path=.` 可正确导入 `app`；同步更新备份、恢复命令路径。
- **最终验证：**
  - 后端 `.venv/bin/python -m pytest -q`：24 passed；
  - 前端 `npm run build`：vue-tsc 与 Vite 生产构建通过；
  - Python `compileall`：通过；
  - 隔离 SQLite `alembic upgrade head` 与 `alembic check`：通过，No new upgrade operations detected；
  - 本地 production Secure Cookie 配置检查、备份与恢复逻辑测试通过；`git diff --check` 通过；
  - 新增验证：登录 Cookie 实际带有 `HttpOnly`、`Secure`、`SameSite=Lax`；超出 5 MB 的导入文件返回 413；
  - 未访问实际公网服务器；浏览器端到端、DNS/TLS/Nginx/systemd 实机验证、定时器检查、生产数据恢复演练以及外部安全/依赖漏洞扫描仍未完成。
- **验证命令纠正：** 一次从仓库根目录运行后端测试和 Alembic 时 `app` 导入路径不匹配；一次 `uv run` 编译尝试使用了受限默认缓存。改从 `apps/api` 使用已安装虚拟环境后，验证通过；没有因此改动应用逻辑。
