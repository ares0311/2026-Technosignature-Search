from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.procurement_log import (
    ALLOWED_PROCUREMENT_KINDS,
    ALLOWED_PROCUREMENT_STATUSES,
    PROCUREMENT_LOG_SCHEMA_VERSION,
    ProcurementEntry,
    load_procurement_entries,
    procurement_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "procurement_log.json"


def test_schema_version() -> None:
    assert PROCUREMENT_LOG_SCHEMA_VERSION == "procurement_log_v1"


def test_allowed_procurement_kinds() -> None:
    assert "contract_renewal" in ALLOWED_PROCUREMENT_KINDS
    assert "emergency_procurement" in ALLOWED_PROCUREMENT_KINDS
    assert "framework_order" in ALLOWED_PROCUREMENT_KINDS
    assert "purchase_order" in ALLOWED_PROCUREMENT_KINDS
    assert "requisition" in ALLOWED_PROCUREMENT_KINDS
    assert len(ALLOWED_PROCUREMENT_KINDS) == 5


def test_allowed_procurement_statuses() -> None:
    assert "approved" in ALLOWED_PROCUREMENT_STATUSES
    assert "cancelled" in ALLOWED_PROCUREMENT_STATUSES
    assert "completed" in ALLOWED_PROCUREMENT_STATUSES
    assert "pending" in ALLOWED_PROCUREMENT_STATUSES
    assert len(ALLOWED_PROCUREMENT_STATUSES) == 4


def test_load_fixture_entries() -> None:
    entries = load_procurement_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_completed_entries() -> None:
    entries = load_procurement_entries(FIXTURE_PATH)
    completed = [e for e in entries if e.status == "completed"]
    assert len(completed) >= 2


def test_fixture_covers_all_statuses() -> None:
    entries = load_procurement_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert statuses == ALLOWED_PROCUREMENT_STATUSES


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_procurement_entries(FIXTURE_PATH)
    kinds = {e.procurement_kind for e in entries}
    assert len(kinds) >= 4


def test_entry_fields_populated() -> None:
    entries = load_procurement_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.entry_id
        assert entry.procurement_kind
        assert entry.status
        assert entry.requester_id
        assert entry.description


def test_entry_is_frozen() -> None:
    entry = ProcurementEntry(
        entry_id="proc-x",
        procurement_kind="purchase_order",
        status="completed",
        requester_id="req-x",
        description="Test description",
    )
    with pytest.raises(AttributeError):
        entry.status = "cancelled"  # type: ignore[misc]


def test_invalid_procurement_kind_raises() -> None:
    with pytest.raises(ValueError, match="invalid procurement_kind"):
        ProcurementEntry(
            entry_id="proc-bad",
            procurement_kind="invalid_kind",
            status="completed",
            requester_id="req-x",
            description="Description",
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        ProcurementEntry(
            entry_id="proc-bad",
            procurement_kind="purchase_order",
            status="invalid_status",
            requester_id="req-x",
            description="Description",
        )


def test_summary_entry_count() -> None:
    summary = procurement_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_completed_count() -> None:
    summary = procurement_summary(FIXTURE_PATH)
    assert summary["completed_count"] == 2


def test_summary_schema_version() -> None:
    summary = procurement_summary(FIXTURE_PATH)
    assert summary["schema_version"] == PROCUREMENT_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = procurement_summary(FIXTURE_PATH)
    assert "disclaimer" in summary
    assert "detection claim" in summary["disclaimer"]


def test_summary_kind_counts() -> None:
    summary = procurement_summary(FIXTURE_PATH)
    assert "kind_counts" in summary
    assert set(summary["kind_counts"].keys()) == ALLOWED_PROCUREMENT_KINDS


def test_summary_status_counts() -> None:
    summary = procurement_summary(FIXTURE_PATH)
    assert "status_counts" in summary
    assert set(summary["status_counts"].keys()) == ALLOWED_PROCUREMENT_STATUSES


def test_fixture_json_valid() -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "entries" in raw
    assert len(raw["entries"]) == 5


def test_validate_all_procurement_gate(tmp_path: Path) -> None:
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
