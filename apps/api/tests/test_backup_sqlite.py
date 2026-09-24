from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import backup_sqlite
import restore_sqlite


BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def create_database(path: Path, value: str) -> None:
    connection = sqlite3.connect(str(path))
    try:
        connection.execute("CREATE TABLE system_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute("INSERT INTO system_meta (key, value) VALUES ('data_revision', ?)", (value,))
        connection.commit()
    finally:
        connection.close()


def read_revision(path: Path) -> str:
    connection = sqlite3.connect(str(path))
    try:
        return connection.execute("SELECT value FROM system_meta WHERE key='data_revision'").fetchone()[0]
    finally:
        connection.close()


def test_backup_rotation_uses_thirty_days_not_file_count(tmp_path: Path, monkeypatch) -> None:
    now = datetime(2026, 9, 23, 12, 0, tzinfo=BEIJING_TZ)
    old_backup = tmp_path / "jizhang-older.sqlite"
    recent_backup = tmp_path / "jizhang-recent.sqlite"
    old_backup.touch()
    recent_backup.touch()
    old_time = (now - timedelta(days=31)).timestamp()
    recent_time = (now - timedelta(days=29)).timestamp()
    import os

    os.utime(old_backup, (old_time, old_time))
    os.utime(recent_backup, (recent_time, recent_time))
    monkeypatch.setattr(backup_sqlite, "BACKUP_DIR", tmp_path)

    backup_sqlite.rotate(now)

    assert not old_backup.exists()
    assert recent_backup.exists()


def test_backup_is_created_only_when_revision_changes(tmp_path: Path, monkeypatch, capsys) -> None:
    database = tmp_path / "jizhang.sqlite"
    backup_dir = tmp_path / "backups"
    state = backup_dir / "backup-state.json"
    create_database(database, "1")
    monkeypatch.setattr(backup_sqlite, "DB_PATH", database)
    monkeypatch.setattr(backup_sqlite, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(backup_sqlite, "STATE_PATH", state)

    assert backup_sqlite.main() == 0
    first_snapshot = list(backup_dir.glob("jizhang-*.sqlite"))
    assert len(first_snapshot) == 1
    assert backup_sqlite.main() == 0
    assert list(backup_dir.glob("jizhang-*.sqlite")) == first_snapshot
    assert "数据版本未变化" in capsys.readouterr().out

    connection = sqlite3.connect(str(database))
    try:
        connection.execute("UPDATE system_meta SET value='2' WHERE key='data_revision'")
        connection.commit()
    finally:
        connection.close()
    assert backup_sqlite.main() == 0
    assert len(list(backup_dir.glob("jizhang-*.sqlite"))) == 2


def test_restore_validates_snapshot_and_preserves_pre_restore_copy(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    database = tmp_path / "data" / "jizhang.sqlite"
    database.parent.mkdir()
    backup = backup_dir / "jizhang-20260923-120000.sqlite"
    create_database(database, "before")
    create_database(backup, "restored")
    state = backup_dir / "backup-state.json"

    safety_copy = restore_sqlite.restore_backup(backup, database, backup_dir, state)

    assert read_revision(database) == "restored"
    assert safety_copy is not None and safety_copy.exists()
    assert read_revision(safety_copy) == "before"
    assert '"revision": "restore-pending"' in state.read_text(encoding="utf-8")
