from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"


class Settings:
    def __init__(self) -> None:
        self.environment = os.getenv("JIZHANG_ENV", "development").strip().lower()
        if self.environment not in {"development", "production"}:
            raise RuntimeError("JIZHANG_ENV 只能是 development 或 production")
        self.is_production = self.environment == "production"
        data_dir_value = os.getenv("JIZHANG_DATA_DIR")
        self.data_dir = Path(data_dir_value).expanduser() if data_dir_value else DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        database_url = os.getenv("JIZHANG_DATABASE_URL")
        self.database_url = database_url or f"sqlite:///{self.data_dir / 'jizhang.sqlite'}"
        default_origins = "" if self.is_production else "http://localhost:5173"
        origins = os.getenv("JIZHANG_CORS_ORIGINS", default_origins)
        self.cors_origins = [item.strip() for item in origins.split(",") if item.strip()]
        secure_default = "true" if self.is_production else "false"
        self.cookie_secure = os.getenv("JIZHANG_COOKIE_SECURE", secure_default).strip().lower() == "true"
        if self.is_production and not self.cookie_secure:
            raise RuntimeError("公网生产环境必须启用 JIZHANG_COOKIE_SECURE=true")
        if self.is_production and "*" in self.cors_origins:
            raise RuntimeError("公网生产环境不能使用通配 CORS 来源")
        self.cookie_name = os.getenv("JIZHANG_COOKIE_NAME", "jizhang_session")
        self.session_days = int(os.getenv("JIZHANG_SESSION_DAYS", "7"))
        self.backup_dir = Path(os.getenv("JIZHANG_BACKUP_DIR", str(PROJECT_ROOT / "backups"))).expanduser()
        self.initial_admin_username = os.getenv("JIZHANG_INITIAL_ADMIN_USERNAME", "")
        self.initial_admin_password = os.getenv("JIZHANG_INITIAL_ADMIN_PASSWORD", "")
        self.initial_admin_name = os.getenv("JIZHANG_INITIAL_ADMIN_NAME", "系统管理员")


settings = Settings()
