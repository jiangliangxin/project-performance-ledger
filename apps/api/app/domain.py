from __future__ import annotations

from typing import Iterable

from .db import CooperationRecord, PayoutRecord


STATUS_LABELS = {
    "in_progress": "进行中",
    "cancelled": "已取消",
    "pending_publicity": "待公示",
    "pending_advance": "待公司预付款",
    "pending_full": "待公司全款",
    "pending_ratio": "待确认个人比例",
    "pending_payout": "待个人发放",
    "pending_first_payout": "待第一批发放",
    "partial_paid": "部分发放",
    "pending_final_payout": "待尾款发放",
    "settled": "已结清",
    "unknown_due": "应得金额待确认",
}

SUPPORTED_RULE_COMBINATIONS = {
    ("none", "single"),
    ("advance", "after_advance"),
    ("full", "single"),
    ("advance_and_full", "advance_then_full"),
}


def is_supported_rule_combination(collection_stage: str, payout_pattern: str) -> bool:
    return (collection_stage, payout_pattern) in SUPPORTED_RULE_COMBINATIONS


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def calculate_paid_total(payouts: Iterable[PayoutRecord]) -> int:
    return sum(item.amount_cents for item in payouts if not item.is_void)


def calculate_due_amount(record: CooperationRecord) -> int | None:
    if record.manual_due_amount_cents is not None:
        return record.manual_due_amount_cents
    standard = record.override_standard_cents
    if standard is None:
        standard = record.standard_performance_cents
    ratio = record.my_ratio_bps
    if standard is None or ratio is None:
        return None
    return (standard * ratio + 5000) // 10000


def calculate_current_status(record: CooperationRecord, payouts: Iterable[PayoutRecord]) -> str:
    if record.work_status == "cancelled":
        return "cancelled"
    if record.work_status != "completed":
        return "in_progress"
    if record.snapshot_publicity_required and record.publicity_status != "published":
        return "pending_publicity"

    payout_list = list(payouts)
    paid_total = calculate_paid_total(payout_list)
    due = calculate_due_amount(record)
    if due is None and paid_total > 0:
        return "pending_ratio"

    stage = record.snapshot_collection_stage
    if stage == "advance" and record.advance_received_date is None:
        return "pending_advance"
    if stage == "full" and record.full_received_date is None:
        return "pending_full"
    if stage == "advance_and_full" and record.advance_received_date is None:
        return "pending_advance"

    if due is None:
        return "pending_ratio"

    if record.snapshot_payout_pattern in {"after_advance", "advance_then_full"}:
        if paid_total == 0 and record.advance_received_date is not None:
            return "pending_first_payout"
        if record.snapshot_payout_pattern == "advance_then_full" and record.full_received_date is None:
            return "partial_paid" if paid_total > 0 else "pending_full"

    if paid_total == 0:
        return "pending_payout"
    if paid_total >= due:
        return "settled"
    if record.snapshot_payout_pattern == "advance_then_full" and record.full_received_date is not None:
        return "pending_final_payout"
    return "partial_paid"
