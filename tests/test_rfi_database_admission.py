"""Tests for RFI database admission guardrails."""
from __future__ import annotations

import json
from pathlib import Path

from techno_search.rfi_database_admission import (
    ALLOWED_RFI_DATABASE_ADMISSION_STATUSES,
    RFI_DATABASE_ADMISSION_DISCLAIMER,
    RFI_DATABASE_ADMISSION_SCHEMA_VERSION,
    load_rfi_database_admission_records,
    rfi_database_admission_summary,
    validate_rfi_database_admission_records,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "rfi_database_admission.json"


def test_load_admission_records_returns_fixture_records() -> None:
    records = load_rfi_database_admission_records()
    assert len(records) == 5
    assert records[0].source_id == "rfi-admit-synthetic-v0"


def test_summary_counts_statuses_and_authorization() -> None:
    summary = rfi_database_admission_summary()
    assert summary["schema_version"] == RFI_DATABASE_ADMISSION_SCHEMA_VERSION
    assert summary["record_count"] == 5
    assert summary["blocked_count"] == 3
    assert summary["synthetic_only_count"] == 1
    assert summary["real_data_authorized_count"] == 0
    assert summary["total_blocker_count"] == 7


def test_summary_disclaimer_is_conservative() -> None:
    summary = rfi_database_admission_summary()
    assert summary["disclaimer"] == RFI_DATABASE_ADMISSION_DISCLAIMER
    assert "do not ingest real monitoring data" in summary["disclaimer"]
    assert "authorize external submission" in summary["disclaimer"]


def test_fixture_statuses_are_allowed() -> None:
    for record in load_rfi_database_admission_records():
        assert record.admission_status in ALLOWED_RFI_DATABASE_ADMISSION_STATUSES


def test_validation_accepts_default_fixture() -> None:
    validation = validate_rfi_database_admission_records(
        load_rfi_database_admission_records()
    )
    assert validation["ok"] is True
    assert validation["issue_count"] == 0


def test_validation_rejects_real_authorization_without_reviews(tmp_path: Path) -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    data["rfi_database_admission_records"][1]["real_data_authorized"] = True
    path = tmp_path / "bad_admission.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    summary = rfi_database_admission_summary(path)
    assert summary["validation_ok"] is False
    assert "real data authorization requires all reviews" in summary["validation_issues"][0]


def test_validation_rejects_synthetic_real_authorization_conflict(tmp_path: Path) -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    data["rfi_database_admission_records"][0]["real_data_authorized"] = True
    path = tmp_path / "synthetic_conflict.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    summary = rfi_database_admission_summary(path)
    assert summary["validation_ok"] is False
    assert "synthetic-only" in summary["validation_issues"][0]


def test_custom_path_argument() -> None:
    records = load_rfi_database_admission_records(FIXTURE_PATH)
    summary = rfi_database_admission_summary(FIXTURE_PATH)
    assert len(records) == 5
    assert summary["validation_ok"] is True
