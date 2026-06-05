from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.audit_finding_log import (
    ALLOWED_AUDIT_FINDING_KINDS,
    ALLOWED_AUDIT_FINDING_STATUSES,
    AUDIT_FINDING_LOG_SCHEMA_VERSION,
    AuditFindingEntry,
    audit_finding_summary,
    load_audit_finding_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "audit_finding_log.json"


def test_schema_version() -> None:
    assert AUDIT_FINDING_LOG_SCHEMA_VERSION == "audit_finding_log_v1"


def test_allowed_audit_finding_kinds() -> None:
    assert "compliance_gap" in ALLOWED_AUDIT_FINDING_KINDS
    assert "configuration_issue" in ALLOWED_AUDIT_FINDING_KINDS
    assert "documentation_gap" in ALLOWED_AUDIT_FINDING_KINDS
    assert "process_gap" in ALLOWED_AUDIT_FINDING_KINDS
    assert "security_finding" in ALLOWED_AUDIT_FINDING_KINDS
    assert len(ALLOWED_AUDIT_FINDING_KINDS) == 5


def test_allowed_audit_finding_statuses() -> None:
    assert "accepted" in ALLOWED_AUDIT_FINDING_STATUSES
    assert "closed" in ALLOWED_AUDIT_FINDING_STATUSES
    assert "open" in ALLOWED_AUDIT_FINDING_STATUSES
    assert "remediated" in ALLOWED_AUDIT_FINDING_STATUSES
    assert len(ALLOWED_AUDIT_FINDING_STATUSES) == 4


def test_load_fixture_entries() -> None:
    entries = load_audit_finding_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_remediated_entries() -> None:
    entries = load_audit_finding_entries(FIXTURE_PATH)
    remediated = [e for e in entries if e.status == "remediated"]
    assert len(remediated) >= 2


def test_fixture_covers_all_statuses() -> None:
    entries = load_audit_finding_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert statuses == ALLOWED_AUDIT_FINDING_STATUSES


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_audit_finding_entries(FIXTURE_PATH)
    kinds = {e.finding_kind for e in entries}
    assert len(kinds) >= 4


def test_entry_fields_populated() -> None:
    entries = load_audit_finding_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.entry_id
        assert entry.finding_kind
        assert entry.status
        assert entry.audit_ref
        assert entry.description


def test_entry_is_frozen() -> None:
    entry = AuditFindingEntry(
        entry_id="af-x",
        finding_kind="process_gap",
        status="open",
        audit_ref="audit-x",
        description="Test description",
    )
    with pytest.raises(AttributeError):
        entry.status = "closed"  # type: ignore[misc]


def test_invalid_finding_kind_raises() -> None:
    with pytest.raises(ValueError, match="invalid finding_kind"):
        AuditFindingEntry(
            entry_id="af-bad",
            finding_kind="invalid_kind",
            status="open",
            audit_ref="audit-x",
            description="Description",
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        AuditFindingEntry(
            entry_id="af-bad",
            finding_kind="process_gap",
            status="invalid_status",
            audit_ref="audit-x",
            description="Description",
        )


def test_summary_entry_count() -> None:
    summary = audit_finding_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_remediated_count() -> None:
    summary = audit_finding_summary(FIXTURE_PATH)
    assert summary["remediated_count"] == 2


def test_summary_schema_version() -> None:
    summary = audit_finding_summary(FIXTURE_PATH)
    assert summary["schema_version"] == AUDIT_FINDING_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = audit_finding_summary(FIXTURE_PATH)
    assert "disclaimer" in summary
    assert "detection claim" in summary["disclaimer"]


def test_summary_kind_counts() -> None:
    summary = audit_finding_summary(FIXTURE_PATH)
    assert "kind_counts" in summary
    assert set(summary["kind_counts"].keys()) == ALLOWED_AUDIT_FINDING_KINDS


def test_summary_status_counts() -> None:
    summary = audit_finding_summary(FIXTURE_PATH)
    assert "status_counts" in summary
    assert set(summary["status_counts"].keys()) == ALLOWED_AUDIT_FINDING_STATUSES


def test_fixture_json_valid() -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "entries" in raw
    assert len(raw["entries"]) == 5


def test_validate_all_audit_finding_gate(tmp_path: Path) -> None:
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
