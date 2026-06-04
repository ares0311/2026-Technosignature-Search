from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.compliance_audit_log import (
    ALLOWED_COMPLIANCE_AUDIT_KINDS,
    ALLOWED_COMPLIANCE_AUDIT_STATUSES,
    COMPLIANCE_AUDIT_LOG_DISCLAIMER,
    COMPLIANCE_AUDIT_LOG_SCHEMA_VERSION,
    ComplianceAuditEntry,
    compliance_audit_summary,
    load_compliance_audit_entries,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "compliance_audit_log.json"
)


def test_allowed_kinds_not_empty() -> None:
    assert len(ALLOWED_COMPLIANCE_AUDIT_KINDS) > 0


def test_allowed_statuses_not_empty() -> None:
    assert len(ALLOWED_COMPLIANCE_AUDIT_STATUSES) > 0


def test_expected_kinds_present() -> None:
    assert "data_handling" in ALLOWED_COMPLIANCE_AUDIT_KINDS
    assert "access_policy" in ALLOWED_COMPLIANCE_AUDIT_KINDS
    assert "retention_policy" in ALLOWED_COMPLIANCE_AUDIT_KINDS
    assert "security_policy" in ALLOWED_COMPLIANCE_AUDIT_KINDS
    assert "operational_policy" in ALLOWED_COMPLIANCE_AUDIT_KINDS


def test_expected_statuses_present() -> None:
    assert "passed" in ALLOWED_COMPLIANCE_AUDIT_STATUSES
    assert "failed" in ALLOWED_COMPLIANCE_AUDIT_STATUSES
    assert "under_review" in ALLOWED_COMPLIANCE_AUDIT_STATUSES
    assert "waived" in ALLOWED_COMPLIANCE_AUDIT_STATUSES


def test_schema_version_string() -> None:
    assert isinstance(COMPLIANCE_AUDIT_LOG_SCHEMA_VERSION, str)
    assert len(COMPLIANCE_AUDIT_LOG_SCHEMA_VERSION) > 0


def test_disclaimer_string() -> None:
    assert isinstance(COMPLIANCE_AUDIT_LOG_DISCLAIMER, str)
    assert "does not" in COMPLIANCE_AUDIT_LOG_DISCLAIMER


def test_entry_valid_construction() -> None:
    entry = ComplianceAuditEntry(
        entry_id="ca-test-001",
        audit_kind="data_handling",
        status="passed",
        actor_id="operator-x",
        resource_id="candidate-store",
        timestamp_utc="2026-06-01T00:00:00Z",
        notes=None,
    )
    assert entry.entry_id == "ca-test-001"
    assert entry.audit_kind == "data_handling"
    assert entry.status == "passed"


def test_entry_invalid_kind_raises() -> None:
    with pytest.raises(ValueError, match="audit_kind"):
        ComplianceAuditEntry(
            entry_id="ca-bad",
            audit_kind="unknown_kind",
            status="passed",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_entry_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        ComplianceAuditEntry(
            entry_id="ca-bad",
            audit_kind="data_handling",
            status="unknown_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_load_fixture_returns_entries() -> None:
    entries = load_compliance_audit_entries(FIXTURE_PATH)
    assert len(entries) >= 1


def test_fixture_has_expected_count() -> None:
    entries = load_compliance_audit_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_passed_entries() -> None:
    entries = load_compliance_audit_entries(FIXTURE_PATH)
    passed = [e for e in entries if e.status == "passed"]
    assert len(passed) >= 1


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_compliance_audit_entries(FIXTURE_PATH)
    kinds = {e.audit_kind for e in entries}
    assert len(kinds) >= 3


def test_summary_schema_version() -> None:
    summary = compliance_audit_summary(FIXTURE_PATH)
    assert summary["schema_version"] == COMPLIANCE_AUDIT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = compliance_audit_summary(FIXTURE_PATH)
    assert "does not" in summary["disclaimer"]


def test_summary_entry_count() -> None:
    summary = compliance_audit_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_passed_count() -> None:
    summary = compliance_audit_summary(FIXTURE_PATH)
    assert summary["passed_count"] >= 1


def test_summary_by_kind() -> None:
    summary = compliance_audit_summary(FIXTURE_PATH)
    assert isinstance(summary["by_kind"], dict)
    assert len(summary["by_kind"]) >= 1


def test_summary_by_status() -> None:
    summary = compliance_audit_summary(FIXTURE_PATH)
    assert isinstance(summary["by_status"], dict)
    assert "passed" in summary["by_status"]


def test_fixture_json_parseable() -> None:
    raw = json.loads(FIXTURE_PATH.read_text())
    assert "entries" in raw
    assert raw["schema_version"] == COMPLIANCE_AUDIT_LOG_SCHEMA_VERSION
