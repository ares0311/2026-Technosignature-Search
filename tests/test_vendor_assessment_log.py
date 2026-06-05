from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.vendor_assessment_log import (
    ALLOWED_VENDOR_ASSESSMENT_KINDS,
    ALLOWED_VENDOR_ASSESSMENT_STATUSES,
    VENDOR_ASSESSMENT_LOG_SCHEMA_VERSION,
    VendorAssessmentEntry,
    load_vendor_assessment_entries,
    vendor_assessment_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "vendor_assessment_log.json"


def test_schema_version() -> None:
    assert VENDOR_ASSESSMENT_LOG_SCHEMA_VERSION == "vendor_assessment_log_v1"


def test_allowed_vendor_assessment_kinds() -> None:
    assert "financial_review" in ALLOWED_VENDOR_ASSESSMENT_KINDS
    assert "performance_review" in ALLOWED_VENDOR_ASSESSMENT_KINDS
    assert "risk_review" in ALLOWED_VENDOR_ASSESSMENT_KINDS
    assert "security_review" in ALLOWED_VENDOR_ASSESSMENT_KINDS
    assert "technical_review" in ALLOWED_VENDOR_ASSESSMENT_KINDS
    assert len(ALLOWED_VENDOR_ASSESSMENT_KINDS) == 5


def test_allowed_vendor_assessment_statuses() -> None:
    assert "accepted" in ALLOWED_VENDOR_ASSESSMENT_STATUSES
    assert "completed" in ALLOWED_VENDOR_ASSESSMENT_STATUSES
    assert "in_progress" in ALLOWED_VENDOR_ASSESSMENT_STATUSES
    assert "rejected" in ALLOWED_VENDOR_ASSESSMENT_STATUSES
    assert len(ALLOWED_VENDOR_ASSESSMENT_STATUSES) == 4


def test_load_fixture_entries() -> None:
    entries = load_vendor_assessment_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_completed_entries() -> None:
    entries = load_vendor_assessment_entries(FIXTURE_PATH)
    completed = [e for e in entries if e.status == "completed"]
    assert len(completed) >= 2


def test_fixture_covers_all_statuses() -> None:
    entries = load_vendor_assessment_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert statuses == ALLOWED_VENDOR_ASSESSMENT_STATUSES


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_vendor_assessment_entries(FIXTURE_PATH)
    kinds = {e.assessment_kind for e in entries}
    assert len(kinds) >= 4


def test_entry_fields_populated() -> None:
    entries = load_vendor_assessment_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.entry_id
        assert entry.assessment_kind
        assert entry.status
        assert entry.vendor_id
        assert entry.description


def test_entry_is_frozen() -> None:
    entry = VendorAssessmentEntry(
        entry_id="va-x",
        assessment_kind="performance_review",
        status="completed",
        vendor_id="vendor-x",
        description="Test description",
    )
    with pytest.raises(AttributeError):
        entry.status = "rejected"  # type: ignore[misc]


def test_invalid_assessment_kind_raises() -> None:
    with pytest.raises(ValueError, match="invalid assessment_kind"):
        VendorAssessmentEntry(
            entry_id="va-bad",
            assessment_kind="invalid_kind",
            status="completed",
            vendor_id="vendor-x",
            description="Description",
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        VendorAssessmentEntry(
            entry_id="va-bad",
            assessment_kind="performance_review",
            status="invalid_status",
            vendor_id="vendor-x",
            description="Description",
        )


def test_summary_entry_count() -> None:
    summary = vendor_assessment_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_completed_count() -> None:
    summary = vendor_assessment_summary(FIXTURE_PATH)
    assert summary["completed_count"] == 2


def test_summary_schema_version() -> None:
    summary = vendor_assessment_summary(FIXTURE_PATH)
    assert summary["schema_version"] == VENDOR_ASSESSMENT_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = vendor_assessment_summary(FIXTURE_PATH)
    assert "disclaimer" in summary
    assert "detection claim" in summary["disclaimer"]


def test_summary_kind_counts() -> None:
    summary = vendor_assessment_summary(FIXTURE_PATH)
    assert "kind_counts" in summary
    assert set(summary["kind_counts"].keys()) == ALLOWED_VENDOR_ASSESSMENT_KINDS


def test_summary_status_counts() -> None:
    summary = vendor_assessment_summary(FIXTURE_PATH)
    assert "status_counts" in summary
    assert set(summary["status_counts"].keys()) == ALLOWED_VENDOR_ASSESSMENT_STATUSES


def test_fixture_json_valid() -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "entries" in raw
    assert len(raw["entries"]) == 5


def test_validate_all_vendor_assessment_gate(tmp_path: Path) -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "validate-all"],
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert result.returncode == 0
