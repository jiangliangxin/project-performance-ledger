from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.getenv("JIZHANG_DATA_DIR", str(ROOT / "data"))).expanduser()
DB_PATH = DATA_DIR / "jizhang.sqlite"
BACKUP_DIR = Path(os.getenv("JIZHANG_BACKUP_DIR", str(ROOT / "backups"))).expanduser()
STATE_PATH = BACKUP_DIR / "backup-state.json"
BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def read_revision() -> str:
    connection = sqlite3.connect(str(DB_PATH))
    try:
        row = connection.execute("SELECT value FROM system_meta WHERE key = 'data_revision'").fetchone()
        return row[0] if row else "0"
    finally:
        connection.close()


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def validate(path: Path) -> None:
    connection = sqlite3.connect(str(path))
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise RuntimeError(f"SQLite integrity_check 失败：{result}")
    finally:
        connection.close()


def rotate(now: Optional[datetime] = None) -> None:
    cutoff = ((now or datetime.now(BEIJING_TZ)) - timedelta(days=30)).timestamp()
    for backup in BACKUP_DIR.glob("jizhang-*.sqlite"):
        if backup.stat().st_mtime < cutoff:
            backup.unlink()


def main() -> int:
    if not DB_PATH.exists():
        print(f"数据库不存在，跳过备份：{DB_PATH}")
        return 0
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    rotate()
    revision = read_revision()
    state = load_state()
    if state.get("revision") == revision:
        print(f"数据版本未变化（{revision}），跳过备份")
        return 0

    timestamp = datetime.now(BEIJING_TZ).strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"jizhang-{timestamp}.sqlite"
    if target.exists():
        timestamp = datetime.now(BEIJING_TZ).strftime("%Y%m%d-%H%M%S-%f")
        target = BACKUP_DIR / f"jizhang-{timestamp}.sqlite"
    file_descriptor, temporary_name = tempfile.mkstemp(prefix="jizhang-", suffix=".sqlite.tmp", dir=BACKUP_DIR)
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        source = sqlite3.connect(str(DB_PATH))
        destination = sqlite3.connect(str(temporary_path))
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()
        validate(temporary_path)
        temporary_path.replace(target)
        STATE_PATH.write_text(
            json.dumps({"revision": revision, "backup": target.name, "created_at": datetime.now(BEIJING_TZ).isoformat()}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        rotate()
        print(f"已创建备份：{target}")
        return 0
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


if __name__ == "__main__":
    sys.exit(main())
