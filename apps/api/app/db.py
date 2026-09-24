from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.utcnow()


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@event.listens_for(engine, "connect")
def configure_sqlite(dbapi_connection: Any, _connection_record: Any) -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


class User(Base):
    __tablename__ = "app_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="member")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    normalized_name: Mapped[str] = mapped_column(String(200), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class ProjectType(Base):
    __tablename__ = "project_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_by: Mapped[str] = mapped_column(ForeignKey("app_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class ProjectTypeRule(Base):
    __tablename__ = "project_type_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_type_id: Mapped[str] = mapped_column(ForeignKey("project_types.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    standard_performance_cents: Mapped[int] = mapped_column(BigInteger)
    default_ratio_bps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=10000)
    publicity_required: Mapped[bool] = mapped_column(Boolean, default=False)
    collection_stage: Mapped[str] = mapped_column(String(30), default="none")
    payout_pattern: Mapped[str] = mapped_column(String(30), default="single")
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class CooperationRecord(Base):
    __tablename__ = "cooperation_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    project_type_id: Mapped[str] = mapped_column(ForeignKey("project_types.id"), index=True)
    rule_id: Mapped[Optional[str]] = mapped_column(ForeignKey("project_type_rules.id"), nullable=True)
    record_date: Mapped[date] = mapped_column(Date, index=True)
    work_status: Mapped[str] = mapped_column(String(30), default="in_progress")
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    publicity_status: Mapped[str] = mapped_column(String(30), default="not_applicable")
    publicity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    advance_received_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    full_received_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    participation_mode: Mapped[str] = mapped_column(String(20), default="exclusive")
    my_ratio_bps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    standard_performance_cents: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    override_standard_cents: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    manual_due_amount_cents: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    snapshot_publicity_required: Mapped[bool] = mapped_column(Boolean, default=False)
    snapshot_collection_stage: Mapped[str] = mapped_column(String(30), default="none")
    snapshot_payout_pattern: Mapped[str] = mapped_column(String(30), default="single")
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class PayoutRecord(Base):
    __tablename__ = "payout_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    cooperation_record_id: Mapped[str] = mapped_column(ForeignKey("cooperation_records.id"), index=True)
    batch_type: Mapped[str] = mapped_column(String(20), default="manual")
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    received_date: Mapped[date] = mapped_column(Date)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_void: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class PerformanceChange(Base):
    __tablename__ = "performance_changes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    cooperation_record_id: Mapped[str] = mapped_column(ForeignKey("cooperation_records.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(40))
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(20))
    parser_mode: Mapped[str] = mapped_column(String(30), default="deterministic")
    mapping_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="preview")
    created_record_ids_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_summary_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class SystemMeta(Base):
    __tablename__ = "system_meta"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


def create_all() -> None:
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
