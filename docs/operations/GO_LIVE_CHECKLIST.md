# 公网正式上线验收清单

本清单用于目标 Linux 服务器验收。本地 pytest、TestClient 和临时 SQLite 冒烟测试不能替代这些步骤；目前没有访问真实服务器、域名、证书或 Nginx/systemd 的权限。

## 1. 生产配置

- [ ] 将 `.env.example` 复制为 `/srv/jizhang/.env`，设置 `JIZHANG_ENV=production`、`JIZHANG_COOKIE_SECURE=true`、正式数据目录和备份目录。
- [ ] 使用唯一强管理员密码；`.env` 仅服务账号可读（建议 `chmod 600`），不得提交版本库。
- [ ] 同源 Nginx 部署无需跨域；如果设置 `JIZHANG_CORS_ORIGINS`，只列出真实可信的完整 Origin，不得使用 `*`。
- [ ] 确认 SQLite 数据库只有一个应用进程/worker，数据和备份目录均在持久化磁盘且不位于 Web 静态目录。

## 2. DNS、TLS、Nginx 和 systemd

- [ ] 子域名 A/AAAA 记录指向目标服务器；证书覆盖该域名且未过期。
- [ ] 根据实际域名替换 `deploy/nginx.conf.example` 中的 `server_name` 和证书路径。
- [ ] 安装服务后运行 `sudo systemd-analyze verify /etc/systemd/system/jizhang-api.service` 和 `sudo nginx -t`，两者均无错误。
- [ ] 启动服务并检查日志：`sudo systemctl enable --now jizhang-api`、`sudo systemctl status jizhang-api`、`sudo journalctl -u jizhang-api -n 100 --no-pager`。
- [ ] 确认 systemd `ExecStartPre` 的 `alembic upgrade head` 成功；FastAPI 仅监听 `127.0.0.1`，公网不能直接访问 8000 端口。
- [ ] Nginx 将 HTTP 重定向到 HTTPS，证书有效，静态页面和 `/api` 均由 HTTPS 域名访问。

## 3. 登录和权限

- [ ] `https://<正式域名>/api/v1/health` 返回 `{"status":"ok"}`；未登录访问 `/api/v1/records` 返回 401。
- [ ] 使用浏览器登录；开发者工具中会话 Cookie 带有 `HttpOnly`、`Secure`、`SameSite=Lax`，退出后 Cookie 失效。
- [ ] 连续 5 次输入错误密码后，第 6 次返回 429 和 `Retry-After`；15 分钟后可重新尝试。
- [ ] 在隔离验收账号下验证：管理员和成员都只能看到各自公司、记录、到账、Dashboard 和导出；成员不能访问管理员或其他成员的记录 ID。验收后禁用临时账号并归档测试记录。

## 4. 业务与导入

- [ ] 新建独享记录时默认采用项目类型价格和 100%；特殊价格需填写原因，历史调整可见。
- [ ] 验证完成、公示、预付款、全款与个人到账分别记录；纠正里程碑需要原因，个人到账错误采用“作废并重录”。
- [ ] 用非生产数据验证剪贴板和 `.xlsx` 导入：可选择有效行、错误行不可选；历史/批内重复仅提示，不自动合并；只写所选行。
- [ ] 验证项目类型价格规则和记录日期生效版本匹配；无适用规则的导入行不得提交。

## 5. 备份与恢复演练

- [ ] `sudo systemctl enable --now jizhang-backup.timer`；`systemctl list-timers` 显示每日北京时间 03:00 检查任务。
- [ ] 检查备份目录不可由 Nginx 访问；更改业务数据后产生新快照，无变化时不重复快照；超过 30 天的快照会清理。
- [ ] 创建独立演练目录并复制一份快照；恢复演练的备份目录也必须独立，避免覆盖生产备份状态文件：

  ```bash
  sudo install -d -o jizhang -m 700 /srv/jizhang/restore-drill/data /srv/jizhang/restore-drill/backups
  sudo -u jizhang cp /srv/jizhang/backups/jizhang-YYYYMMDD-HHMMSS.sqlite /srv/jizhang/restore-drill/backups/
  sudo -u jizhang env \
    JIZHANG_DATA_DIR=/srv/jizhang/restore-drill/data \
    JIZHANG_BACKUP_DIR=/srv/jizhang/restore-drill/backups \
    /srv/jizhang/apps/api/.venv/bin/python \
    /srv/jizhang/apps/api/scripts/restore_sqlite.py \
    /srv/jizhang/restore-drill/backups/jizhang-YYYYMMDD-HHMMSS.sqlite --confirm
  ```

- [ ] 对演练库执行 `sqlite3 /srv/jizhang/restore-drill/data/jizhang.sqlite 'PRAGMA integrity_check;'`，结果为 `ok`；使用演练配置启动临时应用并抽查项目、金额、到账和用户隔离。
- [ ] 确认恢复过程生成的恢复前安全副本和新的备份状态文件均可读；演练完成后再按组织的数据保留策略清理专用演练目录。
- [ ] 若必须恢复生产库：先停止 API，确认快照路径和当前数据库路径；脚本会在替换前保留安全副本。恢复后重新启动并抽查，再运行一次备份。

## 6. 上线判定

只有以上生产配置、HTTPS、认证与隔离、关键业务、每日备份和恢复演练全部通过，才可将该服务器判为完成上线验收。另行记录执行人、时间、证据截图/命令输出与快照文件名。

本地开发依赖安全扫描、第三方依赖漏洞扫描、渗透测试、真实公网链路和目标服务器恢复演练均未由当前代码测试覆盖；若公司安全要求较高，应在正式放入真实收益数据前安排独立安全检查。
