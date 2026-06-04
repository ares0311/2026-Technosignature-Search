from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.problem_management_log import (
    ALLOWED_PROBLEM_MANAGEMENT_KINDS,
    ALLOWED_PROBLEM_MANAGEMENT_STATUSES,
    PROBLEM_MANAGEMENT_LOG_SCHEMA_VERSION,
    ProblemManagementEntry,
    load_problem_management_entries,
    problem_management_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "problem_management_log.json"
)


def test_fixture_loads() -> None:
    entries = load_problem_management_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_schema_version() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == PROBLEM_MANAGEMENT_LOG_SCHEMA_VERSION


def test_entry_ids_unique() -> None:
    entries = load_problem_management_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_all_problem_kinds_valid() -> None:
    entries = load_problem_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.problem_kind in ALLOWED_PROBLEM_MANAGEMENT_KINDS


def test_all_statuses_valid() -> None:
    entries = load_problem_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.status in ALLOWED_PROBLEM_MANAGEMENT_STATUSES


def test_resolved_count() -> None:
    entries = load_problem_management_entries(FIXTURE_PATH)
    resolved = [e for e in entries if e.status == "resolved"]
    assert len(resolved) == 2


def test_under_investigation_present() -> None:
    entries = load_problem_management_entries(FIXTURE_PATH)
    assert any(e.status == "under_investigation" for e in entries)


def test_identified_present() -> None:
    entries = load_problem_management_entries(FIXTURE_PATH)
    assert any(e.status == "identified" for e in entries)


def test_closed_present() -> None:
    entries = load_problem_management_entries(FIXTURE_PATH)
    assert any(e.status == "closed" for e in entries)


def test_infrastructure_kind_present() -> None:
    entries = load_problem_management_entries(FIXTURE_PATH)
    assert any(e.problem_kind == "infrastructure" for e in entries)


def test_software_kind_present() -> None:
    entries = load_problem_management_entries(FIXTURE_PATH)
    assert any(e.problem_kind == "software" for e in entries)


def test_summary_entry_count() -> None:
    summary = problem_management_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_resolved_count() -> None:
    summary = problem_management_summary(FIXTURE_PATH)
    assert summary["resolved_count"] == 2


def test_summary_schema_version() -> None:
    summary = problem_management_summary(FIXTURE_PATH)
    assert summary["schema_version"] == PROBLEM_MANAGEMENT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = problem_management_summary(FIXTURE_PATH)
    assert "operational provenance records" in summary["disclaimer"]


def test_summary_disclaimer_no_detection_claim() -> None:
    summary = problem_management_summary(FIXTURE_PATH)
    assert "detection claim" in summary["disclaimer"]


def test_dataclass_invalid_problem_kind() -> None:
    with pytest.raises(ValueError, match="problem_kind"):
        ProblemManagementEntry(
            entry_id="x",
            problem_kind="invalid_kind",
            status="resolved",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        ProblemManagementEntry(
            entry_id="x",
            problem_kind="infrastructure",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes="",
        )


def test_dataclass_frozen() -> None:
    entry = ProblemManagementEntry(
        entry_id="x",
        problem_kind="software",
        status="identified",
        actor_id="op",
        resource_id="res",
        timestamp_utc="2026-01-01T00:00:00Z",
        notes="",
    )
    with pytest.raises(AttributeError):
        entry.status = "resolved"  # type: ignore[misc]


def test_allowed_kinds_completeness() -> None:
    assert "hardware" in ALLOWED_PROBLEM_MANAGEMENT_KINDS
    assert "infrastructure" in ALLOWED_PROBLEM_MANAGEMENT_KINDS
    assert "process" in ALLOWED_PROBLEM_MANAGEMENT_KINDS
    assert "security" in ALLOWED_PROBLEM_MANAGEMENT_KINDS
    assert "software" in ALLOWED_PROBLEM_MANAGEMENT_KINDS


def test_allowed_statuses_completeness() -> None:
    assert "closed" in ALLOWED_PROBLEM_MANAGEMENT_STATUSES
    assert "identified" in ALLOWED_PROBLEM_MANAGEMENT_STATUSES
    assert "resolved" in ALLOWED_PROBLEM_MANAGEMENT_STATUSES
    assert "under_investigation" in ALLOWED_PROBLEM_MANAGEMENT_STATUSES


def test_no_external_submission_in_disclaimer() -> None:
    summary = problem_management_summary(FIXTURE_PATH)
    assert "external submission" in summary["disclaimer"]
