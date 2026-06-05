from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.change_request_log import (
    ALLOWED_CHANGE_REQUEST_KINDS,
    ALLOWED_CHANGE_REQUEST_STATUSES,
    CHANGE_REQUEST_LOG_SCHEMA_VERSION,
    ChangeRequestEntry,
    change_request_summary,
    load_change_request_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "change_request_log.json"


def test_schema_version() -> None:
    assert CHANGE_REQUEST_LOG_SCHEMA_VERSION == "change_request_log_v1"


def test_allowed_change_request_kinds() -> None:
    assert "emergency_change" in ALLOWED_CHANGE_REQUEST_KINDS
    assert "normal_change" in ALLOWED_CHANGE_REQUEST_KINDS
    assert "routine_change" in ALLOWED_CHANGE_REQUEST_KINDS
    assert "standard_change" in ALLOWED_CHANGE_REQUEST_KINDS
    assert "urgent_change" in ALLOWED_CHANGE_REQUEST_KINDS
    assert len(ALLOWED_CHANGE_REQUEST_KINDS) == 5


def test_allowed_change_request_statuses() -> None:
    assert "approved" in ALLOWED_CHANGE_REQUEST_STATUSES
    assert "cancelled" in ALLOWED_CHANGE_REQUEST_STATUSES
    assert "pending_review" in ALLOWED_CHANGE_REQUEST_STATUSES
    assert "rejected" in ALLOWED_CHANGE_REQUEST_STATUSES
    assert len(ALLOWED_CHANGE_REQUEST_STATUSES) == 4


def test_load_fixture_entries() -> None:
    entries = load_change_request_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_approved_entries() -> None:
    entries = load_change_request_entries(FIXTURE_PATH)
    approved = [e for e in entries if e.status == "approved"]
    assert len(approved) >= 2


def test_fixture_covers_all_statuses() -> None:
    entries = load_change_request_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert statuses == ALLOWED_CHANGE_REQUEST_STATUSES


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_change_request_entries(FIXTURE_PATH)
    kinds = {e.change_kind for e in entries}
    assert len(kinds) >= 4


def test_entry_fields_populated() -> None:
    entries = load_change_request_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.entry_id
        assert entry.change_kind
        assert entry.status
        assert entry.requestor_id
        assert entry.description


def test_entry_is_frozen() -> None:
    entry = ChangeRequestEntry(
        entry_id="cr-x",
        change_kind="normal_change",
        status="approved",
        requestor_id="req-x",
        description="Test description",
    )
    with pytest.raises(AttributeError):
        entry.status = "cancelled"  # type: ignore[misc]


def test_invalid_change_kind_raises() -> None:
    with pytest.raises(ValueError, match="invalid change_kind"):
        ChangeRequestEntry(
            entry_id="cr-bad",
            change_kind="invalid_kind",
            status="approved",
            requestor_id="req-x",
            description="Description",
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        ChangeRequestEntry(
            entry_id="cr-bad",
            change_kind="normal_change",
            status="invalid_status",
            requestor_id="req-x",
            description="Description",
        )


def test_summary_entry_count() -> None:
    summary = change_request_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_approved_count() -> None:
    summary = change_request_summary(FIXTURE_PATH)
    assert summary["approved_count"] == 2


def test_summary_schema_version() -> None:
    summary = change_request_summary(FIXTURE_PATH)
    assert summary["schema_version"] == CHANGE_REQUEST_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = change_request_summary(FIXTURE_PATH)
    assert "disclaimer" in summary
    assert "detection claim" in summary["disclaimer"]


def test_summary_kind_counts() -> None:
    summary = change_request_summary(FIXTURE_PATH)
    assert "kind_counts" in summary
    assert set(summary["kind_counts"].keys()) == ALLOWED_CHANGE_REQUEST_KINDS


def test_summary_status_counts() -> None:
    summary = change_request_summary(FIXTURE_PATH)
    assert "status_counts" in summary
    assert set(summary["status_counts"].keys()) == ALLOWED_CHANGE_REQUEST_STATUSES


def test_fixture_json_valid() -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "entries" in raw
    assert len(raw["entries"]) == 5


def test_validate_all_change_request_gate(tmp_path: Path) -> None:
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
