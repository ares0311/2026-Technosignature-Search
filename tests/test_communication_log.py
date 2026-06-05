from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.communication_log import (
    ALLOWED_COMMUNICATION_KINDS,
    ALLOWED_COMMUNICATION_STATUSES,
    COMMUNICATION_LOG_SCHEMA_VERSION,
    CommunicationEntry,
    communication_summary,
    load_communication_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "communication_log.json"


def test_schema_version() -> None:
    assert COMMUNICATION_LOG_SCHEMA_VERSION == "communication_log_v1"


def test_allowed_communication_kinds() -> None:
    assert "broadcast" in ALLOWED_COMMUNICATION_KINDS
    assert "email_notification" in ALLOWED_COMMUNICATION_KINDS
    assert "escalation_notice" in ALLOWED_COMMUNICATION_KINDS
    assert "status_update" in ALLOWED_COMMUNICATION_KINDS
    assert "team_announcement" in ALLOWED_COMMUNICATION_KINDS
    assert len(ALLOWED_COMMUNICATION_KINDS) == 5


def test_allowed_communication_statuses() -> None:
    assert "delivered" in ALLOWED_COMMUNICATION_STATUSES
    assert "draft" in ALLOWED_COMMUNICATION_STATUSES
    assert "failed" in ALLOWED_COMMUNICATION_STATUSES
    assert "sent" in ALLOWED_COMMUNICATION_STATUSES
    assert len(ALLOWED_COMMUNICATION_STATUSES) == 4


def test_load_fixture_entries() -> None:
    entries = load_communication_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_delivered_entries() -> None:
    entries = load_communication_entries(FIXTURE_PATH)
    delivered = [e for e in entries if e.status == "delivered"]
    assert len(delivered) >= 2


def test_fixture_covers_all_statuses() -> None:
    entries = load_communication_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert statuses == ALLOWED_COMMUNICATION_STATUSES


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_communication_entries(FIXTURE_PATH)
    kinds = {e.communication_kind for e in entries}
    assert len(kinds) >= 4


def test_entry_fields_populated() -> None:
    entries = load_communication_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.entry_id
        assert entry.communication_kind
        assert entry.status
        assert entry.sender_id
        assert entry.subject


def test_entry_is_frozen() -> None:
    entry = CommunicationEntry(
        entry_id="comm-x",
        communication_kind="status_update",
        status="delivered",
        sender_id="sender-x",
        subject="Test subject",
    )
    with pytest.raises(AttributeError):
        entry.status = "failed"  # type: ignore[misc]


def test_invalid_communication_kind_raises() -> None:
    with pytest.raises(ValueError, match="invalid communication_kind"):
        CommunicationEntry(
            entry_id="comm-bad",
            communication_kind="invalid_kind",
            status="delivered",
            sender_id="sender-x",
            subject="Subject",
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        CommunicationEntry(
            entry_id="comm-bad",
            communication_kind="status_update",
            status="invalid_status",
            sender_id="sender-x",
            subject="Subject",
        )


def test_summary_entry_count() -> None:
    summary = communication_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_delivered_count() -> None:
    summary = communication_summary(FIXTURE_PATH)
    assert summary["delivered_count"] == 2


def test_summary_schema_version() -> None:
    summary = communication_summary(FIXTURE_PATH)
    assert summary["schema_version"] == COMMUNICATION_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = communication_summary(FIXTURE_PATH)
    assert "disclaimer" in summary
    assert "detection claim" in summary["disclaimer"]


def test_summary_kind_counts() -> None:
    summary = communication_summary(FIXTURE_PATH)
    assert "kind_counts" in summary
    assert set(summary["kind_counts"].keys()) == ALLOWED_COMMUNICATION_KINDS


def test_summary_status_counts() -> None:
    summary = communication_summary(FIXTURE_PATH)
    assert "status_counts" in summary
    assert set(summary["status_counts"].keys()) == ALLOWED_COMMUNICATION_STATUSES


def test_fixture_json_valid() -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "entries" in raw
    assert len(raw["entries"]) == 5


def test_validate_all_communication_gate(tmp_path: Path) -> None:
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
