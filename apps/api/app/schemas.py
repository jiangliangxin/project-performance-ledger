from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class UserPublic(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    display_name: str
    role: str
    status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=200)
    display_name: str = Field(min_length=1, max_length=120)
    email: Optional[str] = None
    role: str = "member"


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    status: Optional[str] = None


class PasswordResetRequest(BaseModel):
    password: str = Field(min_length=8, max_length=200)


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    status: Optional[str] = None


class ProjectTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)


class ProjectTypeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=160)
    status: Optional[str] = None


class RuleCreate(BaseModel):
    standard_performance_yuan: float = Field(ge=0)
    default_ratio_percent: Optional[float] = Field(default=100, ge=0, le=100)
    publicity_required: bool = False
    collection_stage: str = "none"
    payout_pattern: str = "single"
    effective_from: date
    effective_to: Optional[date] = None
    source_note: Optional[str] = None


class RecordCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    project_type_id: str
    record_date: Optional[date] = None
    completion_date: Optional[date] = None
    participation_mode: str = "exclusive"
    my_ratio_percent: Optional[float] = Field(default=None, ge=0, le=100)
    override_standard_yuan: Optional[float] = Field(default=None, ge=0)
    override_reason: Optional[str] = Field(default=None, min_length=1, max_length=500)
    manual_due_yuan: Optional[float] = Field(default=None, ge=0)
    note: Optional[str] = None


class RecordUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    record_date: Optional[date] = None
    completion_date: Optional[date] = None
    work_status: Optional[str] = None
    participation_mode: Optional[str] = None
    my_ratio_percent: Optional[float] = Field(default=None, ge=0, le=100)
    override_standard_yuan: Optional[float] = Field(default=None, ge=0)
    manual_due_yuan: Optional[float] = Field(default=None, ge=0)
    reason: Optional[str] = Field(default=None, min_length=1, max_length=500)
    note: Optional[str] = None


class MilestoneRequest(BaseModel):
    occurred_date: Optional[date] = None


class MilestoneUpdateRequest(BaseModel):
    completion_date: Optional[date] = None
    publicity_date: Optional[date] = None
    advance_received_date: Optional[date] = None
    full_received_date: Optional[date] = None
    reason: str = Field(min_length=1, max_length=500)


class OverrideRequest(BaseModel):
    override_standard_yuan: Optional[float] = Field(default=None, ge=0)
    my_ratio_percent: Optional[float] = Field(default=None, ge=0, le=100)
    manual_due_yuan: Optional[float] = Field(default=None, ge=0)
    reason: str = Field(min_length=1, max_length=500)


class PayoutCreate(BaseModel):
    amount_yuan: float = Field(gt=0)
    received_date: Optional[date] = None
    batch_type: str = "manual"
    note: Optional[str] = None


class PayoutUpdate(BaseModel):
    amount_yuan: Optional[float] = Field(default=None, gt=0)
    received_date: Optional[date] = None
    batch_type: Optional[str] = None
    note: Optional[str] = None
    reason: str = Field(min_length=1, max_length=500)


class PayoutVoidRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class ImportRequest(BaseModel):
    source_type: str = "clipboard"
    content: str = Field(min_length=1, max_length=5_242_880)


class ImportCommitRequest(ImportRequest):
    row_numbers: List[int] = Field(min_length=1, max_length=10_000)


class ImportRow(BaseModel):
    row_number: int
    company_name: str = ""
    project_type_name: str = ""
    record_date: Optional[date] = None
    standard_performance_yuan: Optional[float] = None
    my_ratio_percent: Optional[float] = None
    matched_project_type_id: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ImportPreview(BaseModel):
    source_type: str
    delimiter: str
    has_header: bool
    rows: List[ImportRow]
    valid_count: int
    warning_count: int
    error_count: int


class DashboardSummary(BaseModel):
    project_count: int
    in_progress_count: int
    completed_count: int
    paid_total_cents: int
    due_total_cents: int
    outstanding_total_cents: int
    unknown_due_count: int
    status_counts: Dict[str, int]


class ApiMessage(BaseModel):
    message: str


def public_user(user: Any) -> UserPublic:
    return UserPublic.model_validate(user, from_attributes=True)
