from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.data_retention_log import (
    ALLOWED_DATA_RETENTION_KINDS,
    ALLOWED_DATA_RETENTION_STATUSES,
    DATA_RETENTION_LOG_SCHEMA_VERSION,
    DataRetentionEntry,
    data_retention_summary,
    load_data_retention_entries,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "data_retention_log.json"
)


def test_fixture_loads() -> None:
    entries = load_data_retention_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_schema_version() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == DATA_RETENTION_LOG_SCHEMA_VERSION


def test_entry_ids_unique() -> None:
    entries = load_data_retention_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_all_retention_kinds_valid() -> None:
    entries = load_data_retention_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.retention_kind in ALLOWED_DATA_RETENTION_KINDS


def test_all_statuses_valid() -> None:
    entries = load_data_retention_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.status in ALLOWED_DATA_RETENTION_STATUSES


def test_completed_count() -> None:
    entries = load_data_retention_entries(FIXTURE_PATH)
    completed = [e for e in entries if e.status == "completed"]
    assert len(completed) == 2


def test_pending_present() -> None:
    entries = load_data_retention_entries(FIXTURE_PATH)
    assert any(e.status == "pending" for e in entries)


def test_deferred_present() -> None:
    entries = load_data_retention_entries(FIXTURE_PATH)
    assert any(e.status == "deferred" for e in entries)


def test_failed_present() -> None:
    entries = load_data_retention_entries(FIXTURE_PATH)
    assert any(e.status == "failed" for e in entries)


def test_archive_transfer_kind_present() -> None:
    entries = load_data_retention_entries(FIXTURE_PATH)
    assert any(e.retention_kind == "archive_transfer" for e in entries)


def test_policy_review_kind_present() -> None:
    entries = load_data_retention_entries(FIXTURE_PATH)
    assert any(e.retention_kind == "policy_review" for e in entries)


def test_summary_entry_count() -> None:
    summary = data_retention_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_completed_count() -> None:
    summary = data_retention_summary(FIXTURE_PATH)
    assert summary["completed_count"] == 2


def test_summary_schema_version() -> None:
    summary = data_retention_summary(FIXTURE_PATH)
    assert summary["schema_version"] == DATA_RETENTION_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = data_retention_summary(FIXTURE_PATH)
    assert "operational provenance records" in summary["disclaimer"]


def test_summary_disclaimer_no_detection_claim() -> None:
    summary = data_retention_summary(FIXTURE_PATH)
    assert "detection claim" in summary["disclaimer"]


def test_dataclass_invalid_retention_kind() -> None:
    with pytest.raises(ValueError, match="retention_kind"):
        DataRetentionEntry(
            entry_id="x",
            retention_kind="invalid_kind",
            status="completed",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        DataRetentionEntry(
            entry_id="x",
            retention_kind="archive_transfer",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_frozen() -> None:
    entry = DataRetentionEntry(
        entry_id="x",
        retention_kind="deletion_scheduled",
        status="pending",
        actor_id="op",
        resource_id="res",
        timestamp_utc="2026-01-01T00:00:00Z",
        notes="",
    )
    with pytest.raises(AttributeError):
        entry.status = "completed"  # type: ignore[misc]


def test_allowed_kinds_completeness() -> None:
    assert "archive_transfer" in ALLOWED_DATA_RETENTION_KINDS
    assert "deletion_scheduled" in ALLOWED_DATA_RETENTION_KINDS
    assert "policy_review" in ALLOWED_DATA_RETENTION_KINDS
    assert "retention_expired" in ALLOWED_DATA_RETENTION_KINDS
    assert "retention_extended" in ALLOWED_DATA_RETENTION_KINDS


def test_allowed_statuses_completeness() -> None:
    assert "completed" in ALLOWED_DATA_RETENTION_STATUSES
    assert "deferred" in ALLOWED_DATA_RETENTION_STATUSES
    assert "failed" in ALLOWED_DATA_RETENTION_STATUSES
    assert "pending" in ALLOWED_DATA_RETENTION_STATUSES


def test_no_external_submission_in_disclaimer() -> None:
    summary = data_retention_summary(FIXTURE_PATH)
    assert "external submission" in summary["disclaimer"]
