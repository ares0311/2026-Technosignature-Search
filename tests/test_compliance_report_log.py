"""Tests for compliance_report_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.compliance_report_log import (
    ALLOWED_REPORT_KINDS,
    ALLOWED_REPORT_STATUSES,
    COMPLIANCE_REPORT_LOG_SCHEMA_VERSION,
    ComplianceReportEntry,
    compliance_report_summary,
    load_compliance_report_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "compliance_report_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == COMPLIANCE_REPORT_LOG_SCHEMA_VERSION


def test_fixture_report_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["report_kind"] in ALLOWED_REPORT_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_REPORT_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_compliance_report_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_compliance_report_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, ComplianceReportEntry)


def test_entry_ids_unique() -> None:
    entries = load_compliance_report_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_passed_entries_present() -> None:
    entries = load_compliance_report_entries(FIXTURE_PATH)
    assert any(e.status == "passed" for e in entries)


def test_failed_entries_present() -> None:
    entries = load_compliance_report_entries(FIXTURE_PATH)
    assert any(e.status == "failed" for e in entries)


def test_pending_entries_present() -> None:
    entries = load_compliance_report_entries(FIXTURE_PATH)
    assert any(e.status == "pending" for e in entries)


def test_waived_entries_present() -> None:
    entries = load_compliance_report_entries(FIXTURE_PATH)
    assert any(e.status == "waived" for e in entries)


def test_summary_entry_count() -> None:
    summary = compliance_report_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_passed_count() -> None:
    summary = compliance_report_summary(FIXTURE_PATH)
    assert summary["passed_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = compliance_report_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = compliance_report_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_REPORT_KINDS


def test_summary_by_status_keys() -> None:
    summary = compliance_report_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_REPORT_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = compliance_report_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = compliance_report_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_report_kind_raises() -> None:
    with pytest.raises(ValueError, match="report_kind"):
        ComplianceReportEntry(
            entry_id="x",
            report_kind="invalid_kind",
            status="passed",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        ComplianceReportEntry(
            entry_id="x",
            report_kind="internal_audit",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
