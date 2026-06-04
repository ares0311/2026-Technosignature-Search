from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.configuration_change_log import (
    ALLOWED_CONFIGURATION_CHANGE_KINDS,
    ALLOWED_CONFIGURATION_CHANGE_STATUSES,
    CONFIGURATION_CHANGE_LOG_SCHEMA_VERSION,
    ConfigurationChangeEntry,
    configuration_change_summary,
    load_configuration_change_entries,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "configuration_change_log.json"
)


def test_fixture_loads() -> None:
    entries = load_configuration_change_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_schema_version() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == CONFIGURATION_CHANGE_LOG_SCHEMA_VERSION


def test_entry_ids_unique() -> None:
    entries = load_configuration_change_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_all_change_kinds_valid() -> None:
    entries = load_configuration_change_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.change_kind in ALLOWED_CONFIGURATION_CHANGE_KINDS


def test_all_statuses_valid() -> None:
    entries = load_configuration_change_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.status in ALLOWED_CONFIGURATION_CHANGE_STATUSES


def test_applied_count() -> None:
    entries = load_configuration_change_entries(FIXTURE_PATH)
    applied = [e for e in entries if e.status == "applied"]
    assert len(applied) == 2


def test_reverted_present() -> None:
    entries = load_configuration_change_entries(FIXTURE_PATH)
    assert any(e.status == "reverted" for e in entries)


def test_pending_present() -> None:
    entries = load_configuration_change_entries(FIXTURE_PATH)
    assert any(e.status == "pending" for e in entries)


def test_failed_present() -> None:
    entries = load_configuration_change_entries(FIXTURE_PATH)
    assert any(e.status == "failed" for e in entries)


def test_rollback_kind_present() -> None:
    entries = load_configuration_change_entries(FIXTURE_PATH)
    assert any(e.change_kind == "rollback" for e in entries)


def test_parameter_update_kind_present() -> None:
    entries = load_configuration_change_entries(FIXTURE_PATH)
    assert any(e.change_kind == "parameter_update" for e in entries)


def test_summary_entry_count() -> None:
    summary = configuration_change_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_applied_count() -> None:
    summary = configuration_change_summary(FIXTURE_PATH)
    assert summary["applied_count"] == 2


def test_summary_schema_version() -> None:
    summary = configuration_change_summary(FIXTURE_PATH)
    assert summary["schema_version"] == CONFIGURATION_CHANGE_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = configuration_change_summary(FIXTURE_PATH)
    assert "operational provenance records" in summary["disclaimer"]


def test_summary_disclaimer_no_detection_claim() -> None:
    summary = configuration_change_summary(FIXTURE_PATH)
    assert "detection claim" in summary["disclaimer"]


def test_dataclass_invalid_change_kind() -> None:
    with pytest.raises(ValueError, match="change_kind"):
        ConfigurationChangeEntry(
            entry_id="x",
            change_kind="invalid_kind",
            status="applied",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        ConfigurationChangeEntry(
            entry_id="x",
            change_kind="parameter_update",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_frozen() -> None:
    entry = ConfigurationChangeEntry(
        entry_id="x",
        change_kind="version_pin",
        status="pending",
        actor_id="op",
        resource_id="res",
        timestamp_utc="2026-01-01T00:00:00Z",
        notes="",
    )
    with pytest.raises(AttributeError):
        entry.status = "applied"  # type: ignore[misc]


def test_allowed_kinds_completeness() -> None:
    assert "parameter_update" in ALLOWED_CONFIGURATION_CHANGE_KINDS
    assert "profile_switch" in ALLOWED_CONFIGURATION_CHANGE_KINDS
    assert "rollback" in ALLOWED_CONFIGURATION_CHANGE_KINDS
    assert "template_apply" in ALLOWED_CONFIGURATION_CHANGE_KINDS
    assert "version_pin" in ALLOWED_CONFIGURATION_CHANGE_KINDS


def test_allowed_statuses_completeness() -> None:
    assert "applied" in ALLOWED_CONFIGURATION_CHANGE_STATUSES
    assert "failed" in ALLOWED_CONFIGURATION_CHANGE_STATUSES
    assert "pending" in ALLOWED_CONFIGURATION_CHANGE_STATUSES
    assert "reverted" in ALLOWED_CONFIGURATION_CHANGE_STATUSES


def test_no_external_submission_in_disclaimer() -> None:
    summary = configuration_change_summary(FIXTURE_PATH)
    assert "external submission" in summary["disclaimer"]
