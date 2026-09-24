# 个人项目绩效收益记账系统

当前实现采用：

```text
Vue 3 + TypeScript + Vite
            ↓ /api
FastAPI + SQLAlchemy
            ↓
SQLite
```

支持的第一版能力：

- 管理员初始化和成员账号管理；
- 成员数据按账号隔离；
- 公司、项目类型和规则版本；
- 合作记录、完成、公示、公司预付款/全款；
- 个人多批次到账；
- Dashboard 状态和金额统计；
- Excel/CSV/剪贴板确定性导入；
- CSV/JSON 导出；
- 每日数据变化检测备份脚本。

## 项目文档

- [产品需求文档](docs/product/PRD.md)
- [业务上下文与领域术语](docs/architecture/CONTEXT.md)
- [当前轻量开发方案](docs/development/DEVELOPMENT_PLAN.md)
- [企业化扩展历史参考](docs/reference/DEVELOPMENT_PLAN_ENTERPRISE_REFERENCE.md)
- [公网部署验收清单](docs/operations/GO_LIVE_CHECKLIST.md)
- [架构决策记录](docs/adr/)

## 本地启动

### 后端

```bash
cd apps/api
uv sync
uv run alembic upgrade head
cd ../..
JIZHANG_INITIAL_ADMIN_USERNAME=admin \
JIZHANG_INITIAL_ADMIN_PASSWORD='change-this-password' \
uv run --project apps/api uvicorn app.main:app --app-dir apps/api --reload --port 8000
```

如果数据库已经创建过，修改初始管理员环境变量不会覆盖现有账号。也可以使用管理命令创建账号：

```bash
cd apps/api
uv run python -m app.cli create-admin --username admin
```

### 前端

```bash
cd apps/web
npm install
npm run dev
```

打开 `http://localhost:5173`。

## 备份

数据库默认位于 `data/jizhang.sqlite`。备份脚本会读取 `system_meta.data_revision`：

```bash
uv run --project apps/api python apps/api/scripts/backup_sqlite.py
```

有业务数据变化时才会创建备份，按北京时间每日检查。备份文件应放在 Nginx 不可访问的目录，并定期验证恢复。

备份脚本按数据库 `data_revision` 跳过无变化数据，备份完成后执行 SQLite `integrity_check`。旧快照按文件修改时间保留 30 天，不再按“30 份”计算。备份与数据库在同一服务器，不能覆盖整机/磁盘故障风险；需要时应另行配置离机副本。

恢复演练/恢复步骤（先停止 API，防止运行中的 SQLite 连接继续写入）：

```bash
sudo systemctl stop jizhang-api
/srv/jizhang/apps/api/.venv/bin/python /srv/jizhang/apps/api/scripts/restore_sqlite.py /srv/jizhang/backups/jizhang-YYYYMMDD-HHMMSS.sqlite --confirm
sudo systemctl start jizhang-api
```

恢复脚本只接受备份目录下符合命名格式的快照，会校验数据库并在替换前生成一份带 `pre-restore` 标记的当前库安全副本。执行后应登录检查几条记录和到账数据；发生问题时停止服务，再用安全副本恢复。恢复会替换当前数据库文件，必须确认备份文件和目标路径后再执行。

## 生产部署原则

- Nginx 提供 HTTPS、Vue 静态文件和 `/api` 反向代理；
- FastAPI 由 systemd 管理，不直接暴露公网端口；
- SQLite 和备份目录必须是宿主机持久化目录；
- 默认运行一个 FastAPI 实例；
- 设置 `JIZHANG_ENV=production`；此时缺省启用 Secure Cookie，显式关闭将阻止应用启动，CORS 不允许通配来源；当前同源 Nginx 部署不需要额外开放跨域来源；
- FastAPI 启动前由 systemd `ExecStartPre` 执行 `alembic upgrade head`；应用运行期不调用 `create_all()`，防止跳过版本化迁移；
- 登录对同一来源/账号实施 15 分钟 5 次失败限速；当前部署必须保持单实例/单 worker，限速状态位于进程内存，不能声称跨多实例共享；
- 使用强管理员密码，不把 `.env` 提交到仓库。

当前仓库只包含 MVP 应用实现和部署基础文件，不包含真实生产域名、证书和服务器凭据。

## 许可证

本项目基于 MIT License 开源，详见 [LICENSE](LICENSE)。
