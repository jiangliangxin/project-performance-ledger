from __future__ import annotations

import argparse
import getpass

import sys

from sqlalchemy import select

from .db import SessionLocal, User, utc_now
from .security import hash_password


def bump_revision(db) -> None:
    from .db import SystemMeta

    row = db.get(SystemMeta, "data_revision")
    if not row:
        db.add(SystemMeta(key="data_revision", value="1"))
    else:
        row.value = str(int(row.value) + 1)


def create_account(username: str, password: str, display_name: str, role: str) -> None:
    if len(password) < 8:
        raise SystemExit("密码至少需要 8 位")
    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.username == username)):
            raise SystemExit("用户名已存在")
        db.add(
            User(
                username=username,
                display_name=display_name,
                password_hash=hash_password(password),
                role=role,
                status="active",
                created_at=utc_now(),
            )
        )
        bump_revision(db)
        db.commit()
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="个人项目绩效收益记账系统管理命令")
    parser.add_argument("command", choices=["create-admin", "create-user"])
    parser.add_argument("--username", required=True)
    parser.add_argument("--display-name", default="")
    parser.add_argument("--password", default="")
    args = parser.parse_args()
    password = args.password or getpass.getpass("密码（至少8位）：")
    display_name = args.display_name or args.username
    role = "admin" if args.command == "create-admin" else "member"
    create_account(args.username.strip(), password, display_name.strip(), role)
    print(f"已创建{role}账号：{args.username}")


if __name__ == "__main__":
    main()
