from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.getenv("JIZHANG_DATA_DIR", str(ROOT / "data"))).expanduser()
DB_PATH = DATA_DIR / "jizhang.sqlite"
BACKUP_DIR = Path(os.getenv("JIZHANG_BACKUP_DIR", str(ROOT / "backups"))).expanduser()
STATE_PATH = BACKUP_DIR / "backup-state.json"
BEIJING_TZ = ZoneInfo("Asia/Shanghai")
BACKUP_NAME = re.compile(r"jizhang-\d{8}-\d{6}(?:-\d{6})?\.sqlite")


def validate(path: Path) -> None:
    connection = sqlite3.connect(str(path))
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not result or result[0] != "ok":
            raise RuntimeError(f"SQLite integrity_check 失败：{result}")
        if "system_meta" not in tables:
            raise RuntimeError("备份缺少 system_meta 表，不是有效的绩效台账数据库")
    finally:
        connection.close()


def snapshot(source_path: Path, destination_path: Path) -> None:
    source = sqlite3.connect(str(source_path))
    destination = sqlite3.connect(str(destination_path))
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    os.chmod(destination_path, 0o600)


def restore_backup(
    backup_path: Path,
    database_path: Path,
    backup_dir: Path,
    state_path: Optional[Path] = None,
) -> Optional[Path]:
    backup = backup_path.resolve(strict=True)
    backup_root = backup_dir.resolve(strict=True)
    database = database_path.resolve()
    if backup.parent != backup_root or not BACKUP_NAME.fullmatch(backup.name):
        raise ValueError("只允许从配置的备份目录恢复标准命名的 jizhang 时间戳快照")
    if backup == database:
        raise ValueError("备份文件不能与当前数据库路径相同")
    validate(backup)
    database.parent.mkdir(parents=True, exist_ok=True)

    safety_copy: Optional[Path] = None
    if database.exists():
        connection = sqlite3.connect(str(database))
        try:
            checkpoint = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            if checkpoint and checkpoint[0] != 0:
                raise RuntimeError("当前数据库仍有活动连接；请先停止 API 服务")
        finally:
            connection.close()
        timestamp = datetime.now(BEIJING_TZ).strftime("%Y%m%d-%H%M%S-%f")
        safety_copy = backup_root / f"jizhang-pre-restore-{timestamp}.sqlite"
        snapshot(database, safety_copy)
        validate(safety_copy)

    descriptor, temporary_name = tempfile.mkstemp(prefix="jizhang-restore-", suffix=".sqlite.tmp", dir=database.parent)
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        snapshot(backup, temporary_path)
        validate(temporary_path)
        if state_path:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {"revision": "restore-pending", "backup": backup.name, "created_at": datetime.now(BEIJING_TZ).isoformat()},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        for suffix in ("-wal", "-shm"):
            sidecar = Path(f"{database}{suffix}")
            if sidecar.exists():
                sidecar.unlink()
        os.replace(temporary_path, database)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return safety_copy


def main() -> int:
    parser = argparse.ArgumentParser(description="从已验证的 SQLite 快照恢复绩效台账数据库")
    parser.add_argument("backup", type=Path, help="备份目录下的 jizhang-YYYYMMDD-HHMMSS.sqlite")
    parser.add_argument("--confirm", action="store_true", help="确认替换当前数据库文件")
    args = parser.parse_args()
    if not args.confirm:
        parser.error("恢复会替换当前数据库；确认 API 服务已停止后，请追加 --confirm")
    try:
        safety_copy = restore_backup(args.backup, DB_PATH, BACKUP_DIR, STATE_PATH)
    except (OSError, sqlite3.Error, RuntimeError, ValueError) as error:
        parser.exit(1, f"恢复失败：{error}\n")
    print(f"数据库已从快照恢复：{args.backup}")
    if safety_copy:
        print(f"恢复前安全副本：{safety_copy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
