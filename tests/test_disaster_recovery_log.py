from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.disaster_recovery_log import (
    ALLOWED_DISASTER_RECOVERY_KINDS,
    ALLOWED_DISASTER_RECOVERY_STATUSES,
    DISASTER_RECOVERY_LOG_DISCLAIMER,
    DISASTER_RECOVERY_LOG_SCHEMA_VERSION,
    DisasterRecoveryEntry,
    disaster_recovery_summary,
    load_disaster_recovery_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "disaster_recovery_log.json"


def test_allowed_kinds_not_empty() -> None:
    assert len(ALLOWED_DISASTER_RECOVERY_KINDS) > 0


def test_allowed_statuses_not_empty() -> None:
    assert len(ALLOWED_DISASTER_RECOVERY_STATUSES) > 0


def test_expected_kinds_present() -> None:
    assert "backup_restore" in ALLOWED_DISASTER_RECOVERY_KINDS
    assert "failover" in ALLOWED_DISASTER_RECOVERY_KINDS
    assert "recovery_test" in ALLOWED_DISASTER_RECOVERY_KINDS
    assert "redundancy_check" in ALLOWED_DISASTER_RECOVERY_KINDS
    assert "business_continuity_drill" in ALLOWED_DISASTER_RECOVERY_KINDS


def test_expected_statuses_present() -> None:
    assert "completed" in ALLOWED_DISASTER_RECOVERY_STATUSES
    assert "failed" in ALLOWED_DISASTER_RECOVERY_STATUSES
    assert "in_progress" in ALLOWED_DISASTER_RECOVERY_STATUSES
    assert "scheduled" in ALLOWED_DISASTER_RECOVERY_STATUSES


def test_schema_version_string() -> None:
    assert isinstance(DISASTER_RECOVERY_LOG_SCHEMA_VERSION, str)
    assert len(DISASTER_RECOVERY_LOG_SCHEMA_VERSION) > 0


def test_disclaimer_string() -> None:
    assert isinstance(DISASTER_RECOVERY_LOG_DISCLAIMER, str)
    assert "does not" in DISASTER_RECOVERY_LOG_DISCLAIMER


def test_entry_valid_construction() -> None:
    entry = DisasterRecoveryEntry(
        entry_id="dr-test-001",
        recovery_kind="recovery_test",
        status="completed",
        actor_id="operator-x",
        resource_id="pipeline-v1",
        timestamp_utc="2026-06-01T00:00:00Z",
        notes=None,
    )
    assert entry.entry_id == "dr-test-001"
    assert entry.recovery_kind == "recovery_test"
    assert entry.status == "completed"


def test_entry_invalid_kind_raises() -> None:
    with pytest.raises(ValueError, match="recovery_kind"):
        DisasterRecoveryEntry(
            entry_id="dr-bad",
            recovery_kind="unknown_kind",
            status="completed",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_entry_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        DisasterRecoveryEntry(
            entry_id="dr-bad",
            recovery_kind="failover",
            status="unknown_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_load_fixture_returns_entries() -> None:
    entries = load_disaster_recovery_entries(FIXTURE_PATH)
    assert len(entries) >= 1


def test_fixture_has_expected_count() -> None:
    entries = load_disaster_recovery_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_completed_entries() -> None:
    entries = load_disaster_recovery_entries(FIXTURE_PATH)
    completed = [e for e in entries if e.status == "completed"]
    assert len(completed) >= 1


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_disaster_recovery_entries(FIXTURE_PATH)
    kinds = {e.recovery_kind for e in entries}
    assert len(kinds) >= 3


def test_summary_schema_version() -> None:
    summary = disaster_recovery_summary(FIXTURE_PATH)
    assert summary["schema_version"] == DISASTER_RECOVERY_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = disaster_recovery_summary(FIXTURE_PATH)
    assert "does not" in summary["disclaimer"]


def test_summary_entry_count() -> None:
    summary = disaster_recovery_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_completed_count() -> None:
    summary = disaster_recovery_summary(FIXTURE_PATH)
    assert summary["completed_count"] >= 1


def test_summary_by_kind() -> None:
    summary = disaster_recovery_summary(FIXTURE_PATH)
    assert isinstance(summary["by_kind"], dict)
    assert len(summary["by_kind"]) >= 1


def test_summary_by_status() -> None:
    summary = disaster_recovery_summary(FIXTURE_PATH)
    assert isinstance(summary["by_status"], dict)
    assert "completed" in summary["by_status"]


def test_fixture_json_parseable() -> None:
    raw = json.loads(FIXTURE_PATH.read_text())
    assert "entries" in raw
    assert raw["schema_version"] == DISASTER_RECOVERY_LOG_SCHEMA_VERSION
