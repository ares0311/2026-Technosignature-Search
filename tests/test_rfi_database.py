"""Tests for site-specific RFI database guardrails."""
from __future__ import annotations

import json
from pathlib import Path

from techno_search.rfi_database import (
    ALLOWED_RFI_REVIEW_STATUSES,
    ALLOWED_RFI_SOURCE_CLASSES,
    RFI_DATABASE_DISCLAIMER,
    RFI_DATABASE_SCHEMA_VERSION,
    load_rfi_database_records,
    rfi_database_matches,
    rfi_database_summary,
    validate_rfi_database_records,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "rfi_database.json"


def test_load_rfi_database_records_returns_fixture_entries() -> None:
    records = load_rfi_database_records()
    assert len(records) == 5
    assert records[0].entry_id == "rfi-db-001"


def test_summary_counts_review_statuses_and_synthetic_records() -> None:
    summary = rfi_database_summary()
    assert summary["schema_version"] == RFI_DATABASE_SCHEMA_VERSION
    assert summary["record_count"] == 5
    assert summary["active_count"] == 4
    assert summary["reviewed_count"] == 3
    assert summary["provisional_count"] == 1
    assert summary["synthetic_count"] == 5
    assert summary["real_record_count"] == 0


def test_summary_disclaimer_is_conservative() -> None:
    summary = rfi_database_summary()
    assert summary["disclaimer"] == RFI_DATABASE_DISCLAIMER
    assert "false-positive screening aids" in summary["disclaimer"]
    assert "do not calibrate scoring thresholds" in summary["disclaimer"]
    assert "discoveries" in summary["disclaimer"]


def test_fixture_values_are_allowed() -> None:
    for record in load_rfi_database_records():
        assert record.source_class in ALLOWED_RFI_SOURCE_CLASSES
        assert record.review_status in ALLOWED_RFI_REVIEW_STATUSES


def test_validation_accepts_default_fixture() -> None:
    validation = validate_rfi_database_records(load_rfi_database_records())
    assert validation["ok"] is True
    assert validation["issue_count"] == 0
    assert validation["issues"] == []


def test_validation_reports_invalid_frequency_range(tmp_path: Path) -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    data["rfi_database_entries"][0]["frequency_high_hz"] = 1.0
    path = tmp_path / "bad_rfi_database.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    summary = rfi_database_summary(path)
    assert summary["validation_ok"] is False
    assert summary["validation_issue_count"] == 1
    assert "frequency_high_hz" in summary["validation_issues"][0]


def test_validation_reports_missing_provenance(tmp_path: Path) -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    data["rfi_database_entries"][0]["provenance"] = ""
    path = tmp_path / "missing_provenance.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    summary = rfi_database_summary(path)
    assert summary["validation_ok"] is False
    assert "provenance is required" in summary["validation_issues"][0]


def test_frequency_match_returns_active_non_rejected_entries() -> None:
    matches = rfi_database_matches(1_575_420_000.0)
    assert [match.entry_id for match in matches] == ["rfi-db-001"]


def test_inactive_deprecated_entry_is_not_matched() -> None:
    matches = rfi_database_matches(100_000_000.0)
    assert matches == []


def test_custom_path_argument() -> None:
    records = load_rfi_database_records(FIXTURE_PATH)
    summary = rfi_database_summary(FIXTURE_PATH)
    assert len(records) == 5
    assert summary["validation_ok"] is True
