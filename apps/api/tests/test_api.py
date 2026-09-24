from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest

TEST_DATA_DIR = Path("/private/tmp/jizhang-api-tests")
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["JIZHANG_DATA_DIR"] = str(TEST_DATA_DIR)

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session as OrmSession

from app.db import SessionLocal, User, create_all
from app.domain import SUPPORTED_RULE_COMBINATIONS
from app.main import app
from app.security import hash_password
from app.config import Settings, settings

create_all()


def ensure_admin() -> None:
    create_all()
    db = SessionLocal()
    try:
        if not db.scalar(select(User).where(User.username == "test-admin")):
            db.add(User(username="test-admin", display_name="测试管理员", password_hash=hash_password("test-password"), role="admin", status="active"))
            db.commit()
    finally:
        db.close()


def test_health() -> None:
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_rate_limit_after_five_failed_attempts() -> None:
    suffix = uuid4().hex
    with TestClient(app) as client:
        failures = [
            client.post("/api/v1/auth/login", json={"username": f"unknown-{suffix}", "password": "incorrect-password"})
            for _ in range(5)
        ]
        assert all(response.status_code == 401 for response in failures)
        limited = client.post("/api/v1/auth/login", json={"username": f"unknown-{suffix}", "password": "incorrect-password"})
        assert limited.status_code == 429
        assert int(limited.headers["Retry-After"]) > 0


def test_production_settings_require_secure_cookies_and_reject_wildcard_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JIZHANG_DATA_DIR", str(TEST_DATA_DIR))
    monkeypatch.setenv("JIZHANG_ENV", "production")
    monkeypatch.setenv("JIZHANG_COOKIE_SECURE", "false")
    with pytest.raises(RuntimeError, match="JIZHANG_COOKIE_SECURE"):
        Settings()
    monkeypatch.setenv("JIZHANG_COOKIE_SECURE", "true")
    monkeypatch.setenv("JIZHANG_CORS_ORIGINS", "*")
    with pytest.raises(RuntimeError, match="CORS"):
        Settings()


def test_login_cookie_uses_secure_flag_when_enabled() -> None:
    ensure_admin()
    original_value = settings.cookie_secure
    settings.cookie_secure = True
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"})
            assert response.status_code == 200
            cookie = response.headers["set-cookie"].lower()
            assert "httponly" in cookie
            assert "secure" in cookie
            assert "samesite=lax" in cookie
    finally:
        settings.cookie_secure = original_value


def test_login_and_owner_scoped_record_flow() -> None:
    ensure_admin()
    with TestClient(app) as admin_client:
        login = admin_client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"})
        assert login.status_code == 200
        created_type = admin_client.post("/api/v1/project-types", json={"name": "测试评估"})
        assert created_type.status_code in {200, 409}
        project_type = admin_client.get("/api/v1/project-types").json()
        type_id = next(item["id"] for item in project_type if item["name"] == "测试评估")
        rule = admin_client.post(
            f"/api/v1/project-types/{type_id}/rules",
            json={
                "standard_performance_yuan": 8000,
                "default_ratio_percent": 100,
                "publicity_required": False,
                "collection_stage": "none",
                "payout_pattern": "single",
                "effective_from": "2026-01-01",
            },
        )
        assert rule.status_code in {200, 409}
        member = admin_client.post(
            "/api/v1/admin/users",
            json={"username": "test-member", "display_name": "测试成员", "password": "member-password", "role": "member"},
        )
        assert member.status_code in {200, 409}

        record = admin_client.post(
            "/api/v1/records",
            json={"company_name": "测试公司", "project_type_id": type_id, "record_date": "2026-09-20", "participation_mode": "exclusive"},
        )
        assert record.status_code == 200
        record_data = record.json()
        assert record_data["my_due_amount_yuan"] == 8000
        assert record_data["current_status"] == "in_progress"

        completed = admin_client.post(f"/api/v1/records/{record_data['id']}/complete", json={})
        assert completed.status_code == 200
        assert completed.json()["current_status"] == "pending_payout"
        payout = admin_client.post(f"/api/v1/records/{record_data['id']}/payouts", json={"amount_yuan": 8000, "batch_type": "manual"})
        assert payout.status_code == 200
        detail = admin_client.get(f"/api/v1/records/{record_data['id']}")
        assert detail.json()["current_status"] == "settled"
        exported = admin_client.get("/api/v1/exports/records.json")
        assert exported.status_code == 200
        assert any(item["id"] == record_data["id"] for item in exported.json()["records"])

    with TestClient(app) as member_client:
        login = member_client.post("/api/v1/auth/login", json={"username": "test-member", "password": "member-password"})
        assert login.status_code == 200
        assert member_client.get("/api/v1/records").json() == []
        assert member_client.get(f"/api/v1/records/{record_data['id']}").status_code == 404


def test_deterministic_clipboard_import() -> None:
    ensure_admin()
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        created_type = client.post("/api/v1/project-types", json={"name": "导入测试类型"})
        assert created_type.status_code in {200, 409}
        type_id = next(item["id"] for item in client.get("/api/v1/project-types").json() if item["name"] == "导入测试类型")
        rule = client.post(
            f"/api/v1/project-types/{type_id}/rules",
            json={
                "standard_performance_yuan": 5000,
                "default_ratio_percent": 100,
                "publicity_required": False,
                "collection_stage": "none",
                "payout_pattern": "single",
                "effective_from": "2026-01-01",
            },
        )
        assert rule.status_code in {200, 409}
        headed_preview = client.post(
            "/api/v1/imports/preview",
            json={
                "source_type": "clipboard",
                "content": "公司名称\t项目类型\t记录日期\n带表头公司\t导入测试类型\t2026-09-20",
            },
        )
        assert headed_preview.status_code == 200
        assert headed_preview.json()["valid_count"] == 1
        assert headed_preview.json()["rows"][0]["company_name"] == "带表头公司"
        overflow_preview = client.post(
            "/api/v1/imports/preview",
            json={"source_type": "clipboard", "content": f"超大金额公司\t导入测试类型\t2026-09-20\t1e999"},
        )
        assert overflow_preview.status_code == 200
        assert any("绩效金额无法解析" in error for error in overflow_preview.json()["rows"][0]["errors"])
        content = "公司A\t导入测试类型\n公司B\t导入测试类型"
        preview = client.post("/api/v1/imports/preview", json={"source_type": "clipboard", "content": content})
        assert preview.status_code == 200
        assert preview.json()["valid_count"] == 2
        commit = client.post("/api/v1/imports/commit", json={"source_type": "clipboard", "content": content, "row_numbers": [1, 2]})
        assert commit.status_code == 200
        assert len(commit.json()["created_ids"]) == 2


def test_company_and_project_type_updates_reject_invalid_or_duplicate_values() -> None:
    ensure_admin()
    suffix = uuid4().hex[:10]
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        first_company = client.post("/api/v1/companies", json={"name": f"公司一-{suffix}"}).json()
        second_company = client.post("/api/v1/companies", json={"name": f"公司二-{suffix}"}).json()
        assert client.patch(f"/api/v1/companies/{first_company['id']}", json={"name": second_company["name"]}).status_code == 409
        assert client.patch(f"/api/v1/companies/{first_company['id']}", json={"status": "unknown"}).status_code == 400

        first_type = client.post("/api/v1/project-types", json={"name": f"类型一-{suffix}"}).json()
        second_type = client.post("/api/v1/project-types", json={"name": f"类型二-{suffix}"}).json()
        assert client.patch(f"/api/v1/project-types/{second_type['id']}", json={"name": first_type["name"]}).status_code == 409
        assert client.patch(f"/api/v1/project-types/{first_type['id']}", json={"status": "unknown"}).status_code == 400


def test_advance_and_full_settlement_flow() -> None:
    ensure_admin()
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        created_type = client.post("/api/v1/project-types", json={"name": "阶段测试类型"})
        assert created_type.status_code in {200, 409}
        type_id = next(item["id"] for item in client.get("/api/v1/project-types").json() if item["name"] == "阶段测试类型")
        rule = client.post(
            f"/api/v1/project-types/{type_id}/rules",
            json={
                "standard_performance_yuan": 10000,
                "default_ratio_percent": 100,
                "publicity_required": True,
                "collection_stage": "advance_and_full",
                "payout_pattern": "advance_then_full",
                "effective_from": "2026-01-01",
            },
        )
        assert rule.status_code in {200, 409}
        record = client.post("/api/v1/records", json={"company_name": "阶段公司", "project_type_id": type_id, "record_date": "2026-09-20", "participation_mode": "exclusive"}).json()
        assert client.post(f"/api/v1/records/{record['id']}/complete", json={}).json()["current_status"] == "pending_publicity"
        assert client.post(f"/api/v1/records/{record['id']}/publish", json={}).json()["current_status"] == "pending_advance"
        assert client.post(f"/api/v1/records/{record['id']}/advance-received", json={}).json()["current_status"] == "pending_first_payout"
        assert client.post(f"/api/v1/records/{record['id']}/payouts", json={"amount_yuan": 3000, "batch_type": "advance"}).status_code == 200
        assert client.post(f"/api/v1/records/{record['id']}/full-received", json={}).json()["current_status"] == "pending_final_payout"
        assert client.post(f"/api/v1/records/{record['id']}/payouts", json={"amount_yuan": 7000, "batch_type": "final"}).status_code == 200
        assert client.get(f"/api/v1/records/{record['id']}").json()["current_status"] == "settled"


def test_import_validates_rows_warns_across_history_and_commits_only_selection() -> None:
    ensure_admin()
    suffix = uuid4().hex[:10]
    type_name = f"导入校验类型-{suffix}"
    historical_company = f"历史导入公司-{suffix}"
    repeated_company = f"批内重复公司-{suffix}"
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        project_type = client.post("/api/v1/project-types", json={"name": type_name}).json()
        rule = client.post(
            f"/api/v1/project-types/{project_type['id']}/rules",
            json={"standard_performance_yuan": 5000, "effective_from": "2020-01-01"},
        )
        assert rule.status_code == 200
        historical_record = client.post(
            "/api/v1/records",
            json={
                "company_name": historical_company,
                "project_type_id": project_type["id"],
                "record_date": "2025-01-01",
            },
        ).json()
        assert client.post(f"/api/v1/records/{historical_record['id']}/archive").status_code == 200
        content = (
            "合作公司\t项目类型\t记录日期\t绩效\t比例\n"
            f"{historical_company}\t{type_name}\t2026-09-22\t2000\t50%\n"
            f"错误金额公司-{suffix}\t{type_name}\t2026-09-22\t-50\t150%\n"
            f"{repeated_company}\t{type_name}\t2026-09-23\t2500\t50%\n"
            f"{repeated_company}\t{type_name}\t2026-09-24\t2500\t50%\n"
            f"无规则公司-{suffix}\t{type_name}\t2010-01-01\t1000\t50%"
        )
        preview = client.post("/api/v1/imports/preview", json={"source_type": "clipboard", "content": content})
        assert preview.status_code == 200
        preview_data = preview.json()
        assert (preview_data["valid_count"], preview_data["error_count"], preview_data["warning_count"]) == (3, 2, 2)
        assert "已有同公司、类型的历史记录" in "；".join(preview_data["rows"][0]["warnings"])
        assert "本批次第 4 行" in "；".join(preview_data["rows"][3]["warnings"])
        assert any("绩效金额不能小于 0" in error for error in preview_data["rows"][1]["errors"])
        assert any("个人比例必须在 0% 到 100% 之间" in error for error in preview_data["rows"][1]["errors"])
        assert any("没有匹配的项目类型绩效规则" in error for error in preview_data["rows"][4]["errors"])

        invalid_commit = client.post(
            "/api/v1/imports/commit",
            json={"source_type": "clipboard", "content": content, "row_numbers": [3]},
        )
        assert invalid_commit.status_code == 422
        assert client.get("/api/v1/records").json() == [] or all(
            not item["company_name"].startswith((historical_company, repeated_company))
            for item in client.get("/api/v1/records").json()
        )

        committed = client.post(
            "/api/v1/imports/commit",
            json={"source_type": "clipboard", "content": content, "row_numbers": [2, 4]},
        )
        assert committed.status_code == 200
        result = committed.json()
        assert len(result["created_ids"]) == 2
        assert len(result["skipped"]) == 3
        assert len(result["warnings"]) == 1
        duplicates = client.post(
            "/api/v1/records/duplicate-check",
            json={
                "company_name": historical_company,
                "project_type_id": project_type["id"],
                "record_date": "2029-01-01",
            },
        ).json()["duplicates"]
        assert len(duplicates) == 2


def test_import_database_failure_rolls_back_all_selected_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    ensure_admin()
    suffix = uuid4().hex[:10]
    type_name = f"导入回滚类型-{suffix}"
    company_prefix = f"导入回滚公司-{suffix}"
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        project_type = client.post("/api/v1/project-types", json={"name": type_name}).json()
        rule = client.post(
            f"/api/v1/project-types/{project_type['id']}/rules",
            json={"standard_performance_yuan": 5000, "effective_from": "2020-01-01"},
        )
        assert rule.status_code == 200
        original_commit = OrmSession.commit

        def fail_commit(session: OrmSession) -> None:
            raise SQLAlchemyError("simulated commit failure")

        with monkeypatch.context() as patcher:
            patcher.setattr(OrmSession, "commit", fail_commit)
            response = client.post(
                "/api/v1/imports/commit",
                json={
                    "source_type": "clipboard",
                    "content": f"{company_prefix}-A\t{type_name}\n{company_prefix}-B\t{type_name}",
                    "row_numbers": [1, 2],
                },
            )
            assert response.status_code == 500
        assert OrmSession.commit is original_commit
        records = client.get("/api/v1/records").json()
        companies = client.get("/api/v1/companies").json()
        assert all(not item["company_name"].startswith(company_prefix) for item in records)
        assert all(not item["name"].startswith(company_prefix) for item in companies)


def test_import_file_commit_uses_selected_row_numbers() -> None:
    ensure_admin()
    suffix = uuid4().hex[:10]
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        project_type = client.post("/api/v1/project-types", json={"name": f"文件导入类型-{suffix}"}).json()
        rule = client.post(
            f"/api/v1/project-types/{project_type['id']}/rules",
            json={"standard_performance_yuan": 5000, "effective_from": "2020-01-01"},
        )
        assert rule.status_code == 200
        response = client.post(
            "/api/v1/imports/commit-file",
            files=[
                ("file", ("selected.csv", f"文件导入公司-{suffix}\t{project_type['name']}", "text/csv")),
                ("row_numbers", (None, "1")),
            ],
        )
        assert response.status_code == 200
        assert len(response.json()["created_ids"]) == 1


def test_import_file_upload_size_is_bounded() -> None:
    ensure_admin()
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        response = client.post(
            "/api/v1/imports/preview-file",
            files={"file": ("oversized.csv", b"x" * (5 * 1024 * 1024 + 1), "text/csv")},
        )
        assert response.status_code == 413


def test_rule_combinations_are_limited_to_supported_flows() -> None:
    assert SUPPORTED_RULE_COMBINATIONS == {
        ("none", "single"),
        ("advance", "after_advance"),
        ("full", "single"),
        ("advance_and_full", "advance_then_full"),
    }


def test_unknown_ratio_with_existing_payout_remains_pending_ratio() -> None:
    ensure_admin()
    suffix = uuid4().hex[:10]
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        project_type = client.post("/api/v1/project-types", json={"name": f"比例待确认类型-{suffix}"}).json()
        rule = client.post(
            f"/api/v1/project-types/{project_type['id']}/rules",
            json={"standard_performance_yuan": 10000, "effective_from": "2026-01-01"},
        )
        assert rule.status_code == 200
        record = client.post(
            "/api/v1/records",
            json={
                "company_name": f"待确认比例公司-{suffix}",
                "project_type_id": project_type["id"],
                "record_date": "2026-09-23",
                "participation_mode": "shared",
                "my_ratio_percent": None,
            },
        )
        assert record.status_code == 200
        record_id = record.json()["id"]
        assert client.post(f"/api/v1/records/{record_id}/complete", json={}).status_code == 200
        payout = client.post(
            f"/api/v1/records/{record_id}/payouts",
            json={"amount_yuan": 3000, "batch_type": "advance"},
        )
        assert payout.status_code == 200
        detail = client.get(f"/api/v1/records/{record_id}").json()
        assert detail["current_status"] == "pending_ratio"
        assert detail["my_due_amount_yuan"] is None
        assert detail["paid_total_yuan"] == 3000
        assert detail["outstanding_yuan"] is None


def test_financial_edits_require_a_reason_and_keep_history() -> None:
    ensure_admin()
    suffix = uuid4().hex
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        project_type = client.post("/api/v1/project-types", json={"name": f"金额调整-{suffix}"}).json()
        rule = client.post(
            f"/api/v1/project-types/{project_type['id']}/rules",
            json={"standard_performance_yuan": 8000, "effective_from": "2026-01-01"},
        )
        assert rule.status_code == 200
        record = client.post(
            "/api/v1/records",
            json={
                "company_name": f"金额调整公司-{suffix}",
                "project_type_id": project_type["id"],
                "record_date": "2026-09-23",
                "override_standard_yuan": 10000,
                "override_reason": "本项目特殊标准",
                "manual_due_yuan": 9000,
            },
        )
        assert record.status_code == 200
        record_id = record.json()["id"]
        assert record.json()["my_due_amount_yuan"] == 9000
        assert client.patch(
            f"/api/v1/records/{record_id}", json={"override_standard_yuan": None, "manual_due_yuan": None}
        ).status_code == 400
        updated = client.patch(
            f"/api/v1/records/{record_id}",
            json={"override_standard_yuan": None, "manual_due_yuan": None, "reason": "撤销特殊调整"},
        )
        assert updated.status_code == 200
        assert updated.json()["standard_performance_yuan"] == 8000
        assert updated.json()["my_due_amount_yuan"] == 8000
        history = client.get(f"/api/v1/records/{record_id}/performance-changes")
        assert history.status_code == 200
        assert [item["field_name"] for item in history.json()].count("standard") == 2
        assert [item["field_name"] for item in history.json()].count("due_amount") == 2
        assert {item["reason"] for item in history.json()} == {"本项目特殊标准", "撤销特殊调整"}
        assert client.patch(f"/api/v1/records/{record_id}", json={"participation_mode": "shared"}).status_code == 400
        shared = client.patch(
            f"/api/v1/records/{record_id}",
            json={"participation_mode": "shared", "reason": "确认多人分配"},
        )
        assert shared.status_code == 200
        zero = client.patch(
            f"/api/v1/records/{record_id}",
            json={"override_standard_yuan": 0, "reason": "本项目特殊标准为0"},
        )
        assert zero.status_code == 200
        assert zero.json()["standard_performance_yuan"] == 0


def test_due_amount_rounds_half_up_to_integer_cents() -> None:
    ensure_admin()
    suffix = uuid4().hex
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        project_type = client.post("/api/v1/project-types", json={"name": f"金额舍入-{suffix}"}).json()
        rule = client.post(
            f"/api/v1/project-types/{project_type['id']}/rules",
            json={"standard_performance_yuan": 0.01, "effective_from": "2026-01-01"},
        )
        assert rule.status_code == 200
        record = client.post(
            "/api/v1/records",
            json={
                "company_name": f"舍入公司-{suffix}",
                "project_type_id": project_type["id"],
                "record_date": "2026-09-23",
                "participation_mode": "shared",
                "my_ratio_percent": 50,
            },
        )
        assert record.status_code == 200
        assert record.json()["my_due_amount_yuan"] == 0.01


def test_milestone_dates_can_be_corrected_and_cleared_with_history() -> None:
    ensure_admin()
    suffix = uuid4().hex
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        project_type = client.post("/api/v1/project-types", json={"name": f"节点更正-{suffix}"}).json()
        rule = client.post(
            f"/api/v1/project-types/{project_type['id']}/rules",
            json={
                "standard_performance_yuan": 8000,
                "publicity_required": True,
                "collection_stage": "advance_and_full",
                "payout_pattern": "advance_then_full",
                "effective_from": "2026-01-01",
            },
        )
        assert rule.status_code == 200
        record = client.post(
            "/api/v1/records",
            json={"company_name": f"节点公司-{suffix}", "project_type_id": project_type["id"], "record_date": "2026-09-23"},
        ).json()
        record_id = record["id"]
        first = client.patch(
            f"/api/v1/records/{record_id}/milestones",
            json={
                "completion_date": "2026-09-10",
                "publicity_date": "2026-09-11",
                "advance_received_date": "2026-09-12",
                "full_received_date": "2026-09-13",
                "reason": "按实际资料录入",
            },
        )
        assert first.status_code == 200
        assert first.json()["work_status"] == "completed"
        assert client.patch(
            f"/api/v1/records/{record_id}",
            json={"completion_date": "2026-09-09", "reason": "尝试绕过节点历史"},
        ).status_code == 400
        assert client.post(
            f"/api/v1/records/{record_id}/complete", json={"occurred_date": "2026-09-09"}
        ).status_code == 400
        assert client.post(
            f"/api/v1/records/{record_id}/publish", json={"occurred_date": "2026-09-08"}
        ).status_code == 400
        assert client.post(
            f"/api/v1/records/{record_id}/advance-received", json={"occurred_date": "2026-09-07"}
        ).status_code == 400
        assert client.post(
            f"/api/v1/records/{record_id}/full-received", json={"occurred_date": "2026-09-06"}
        ).status_code == 400
        corrected = client.patch(
            f"/api/v1/records/{record_id}/milestones",
            json={
                "completion_date": None,
                "publicity_date": None,
                "advance_received_date": None,
                "full_received_date": None,
                "reason": "撤销错误日期",
            },
        )
        assert corrected.status_code == 200
        assert corrected.json()["work_status"] == "in_progress"
        assert corrected.json()["completion_date"] is None
        assert corrected.json()["publicity_status"] == "pending"
        assert corrected.json()["advance_received_date"] is None
        assert corrected.json()["full_received_date"] is None
        history = client.get(f"/api/v1/records/{record_id}/performance-changes").json()
        assert len(history) == 8
        assert {item["reason"] for item in history} == {"按实际资料录入", "撤销错误日期"}


def test_archive_can_be_restored_without_changing_financial_facts() -> None:
    ensure_admin()
    suffix = uuid4().hex
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        project_type = client.post("/api/v1/project-types", json={"name": f"归档测试-{suffix}"}).json()
        rule = client.post(
            f"/api/v1/project-types/{project_type['id']}/rules",
            json={"standard_performance_yuan": 8000, "effective_from": "2026-01-01"},
        )
        assert rule.status_code == 200
        record = client.post(
            "/api/v1/records",
            json={"company_name": f"归档公司-{suffix}", "project_type_id": project_type["id"], "record_date": "2026-09-23"},
        ).json()
        record_id = record["id"]
        assert client.post(f"/api/v1/records/{record_id}/archive").status_code == 200
        assert all(item["id"] != record_id for item in client.get("/api/v1/records").json())
        archived_rows = client.get("/api/v1/records", params={"archived": "true"}).json()
        assert any(item["id"] == record_id for item in archived_rows)
        archived_detail = client.get(f"/api/v1/records/{record_id}").json()
        assert archived_detail["archived_at"] is not None
        assert archived_detail["my_due_amount_yuan"] == record["my_due_amount_yuan"]
        assert client.post(f"/api/v1/records/{record_id}/unarchive").status_code == 200
        restored = client.get(f"/api/v1/records/{record_id}").json()
        assert restored["archived_at"] is None
        assert restored["my_due_amount_yuan"] == record["my_due_amount_yuan"]


def test_payout_corrections_keep_history_and_require_reasons() -> None:
    ensure_admin()
    suffix = uuid4().hex
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        project_type = client.post("/api/v1/project-types", json={"name": f"到账更正-{suffix}"}).json()
        rule = client.post(
            f"/api/v1/project-types/{project_type['id']}/rules",
            json={"standard_performance_yuan": 8000, "effective_from": "2026-01-01"},
        )
        assert rule.status_code == 200
        record = client.post(
            "/api/v1/records",
            json={"company_name": f"到账公司-{suffix}", "project_type_id": project_type["id"], "record_date": "2026-09-23"},
        ).json()
        payout = client.post(
            f"/api/v1/records/{record['id']}/payouts",
            json={"amount_yuan": 1000, "received_date": "2026-09-20", "batch_type": "manual"},
        ).json()
        assert client.patch(f"/api/v1/payouts/{payout['id']}", json={"amount_yuan": 1200}).status_code == 422
        updated = client.patch(
            f"/api/v1/payouts/{payout['id']}",
            json={"amount_yuan": 1200, "reason": "更正到账金额"},
        )
        assert updated.status_code == 200
        assert updated.json()["amount_yuan"] == 1200
        assert client.post(f"/api/v1/payouts/{payout['id']}/void").status_code == 422
        voided = client.post(
            f"/api/v1/payouts/{payout['id']}/void",
            json={"reason": "原记录批次记错，按正确记录重录"},
        )
        assert voided.status_code == 200
        detail = client.get(f"/api/v1/records/{record['id']}").json()
        assert detail["payouts"][0]["is_void"] is True
        assert detail["paid_total_yuan"] == 0
        history = client.get(f"/api/v1/records/{record['id']}/performance-changes").json()
        assert {item["field_name"] for item in history} == {"payout_amount", "payout_void"}
        assert {item["reason"] for item in history} == {"更正到账金额", "原记录批次记错，按正确记录重录"}


def test_unsupported_collection_and_payout_combination_is_rejected() -> None:
    ensure_admin()
    suffix = uuid4().hex[:10]
    with TestClient(app) as client:
        assert client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        project_type = client.post("/api/v1/project-types", json={"name": f"非法规则类型-{suffix}"}).json()
        response = client.post(
            f"/api/v1/project-types/{project_type['id']}/rules",
            json={
                "standard_performance_yuan": 10000,
                "collection_stage": "advance_and_full",
                "payout_pattern": "single",
                "effective_from": "2026-01-01",
            },
        )
        assert response.status_code == 400


def test_admin_cannot_access_member_business_records() -> None:
    ensure_admin()
    suffix = uuid4().hex[:10]
    company_name = f"成员私有公司-{suffix}"
    with TestClient(app) as admin_client:
        assert admin_client.post("/api/v1/auth/login", json={"username": "test-admin", "password": "test-password"}).status_code == 200
        project_type = admin_client.post("/api/v1/project-types", json={"name": f"私有隔离类型-{suffix}"}).json()
        rule = admin_client.post(
            f"/api/v1/project-types/{project_type['id']}/rules",
            json={"standard_performance_yuan": 5000, "effective_from": "2026-01-01"},
        )
        assert rule.status_code == 200
        member_response = admin_client.post(
            "/api/v1/admin/users",
            json={"username": f"private-{suffix}", "display_name": "隔离测试成员", "password": "member-password"},
        )
        assert member_response.status_code == 200
        admin_count_before = admin_client.get("/api/v1/dashboard/summary").json()["project_count"]

        with TestClient(app) as member_client:
            assert member_client.post(
                "/api/v1/auth/login",
                json={"username": f"private-{suffix}", "password": "member-password"},
            ).status_code == 200
            record = member_client.post(
                "/api/v1/records",
                json={"company_name": company_name, "project_type_id": project_type["id"], "record_date": "2026-09-23"},
            )
            assert record.status_code == 200
            record_id = record.json()["id"]
            payout = member_client.post(
                f"/api/v1/records/{record_id}/payouts",
                json={"amount_yuan": 1000, "batch_type": "manual"},
            )
            assert payout.status_code == 200
            payout_id = payout.json()["id"]

        assert admin_client.get(f"/api/v1/records/{record_id}").status_code == 404
        assert admin_client.patch(f"/api/v1/records/{record_id}", json={"note": "越权修改"}).status_code == 404
        assert admin_client.get("/api/v1/records").json() == [] or all(
            item["id"] != record_id for item in admin_client.get("/api/v1/records").json()
        )
        assert all(item["name"] != company_name for item in admin_client.get("/api/v1/companies").json())
        assert admin_client.patch(f"/api/v1/payouts/{payout_id}", json={"amount_yuan": 9000, "reason": "越权修改"}).status_code == 404
        assert admin_client.post(f"/api/v1/payouts/{payout_id}/void", json={"reason": "越权作废"}).status_code == 404
        assert admin_client.get("/api/v1/dashboard/summary").json()["project_count"] == admin_count_before
        assert company_name not in admin_client.get("/api/v1/exports/records.csv").text
        assert company_name not in admin_client.get("/api/v1/exports/records.json").text
