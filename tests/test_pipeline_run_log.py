"""Tests for pipeline_run_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.pipeline_run_log import (
    ALLOWED_RUN_KINDS,
    ALLOWED_RUN_STATUSES,
    PIPELINE_RUN_LOG_DISCLAIMER,
    PIPELINE_RUN_LOG_SCHEMA_VERSION,
    load_pipeline_run_entries,
    pipeline_run_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pipeline_run_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_pipeline_run_entries()
    assert len(entries) == 5


def test_all_run_kinds_present() -> None:
    entries = load_pipeline_run_entries()
    kinds = {e.run_kind for e in entries}
    assert "full_pipeline" in kinds
    assert "partial_rerun" in kinds
    assert "test_run" in kinds
    assert "recovery_run" in kinds


def test_all_statuses_present() -> None:
    entries = load_pipeline_run_entries()
    statuses = {e.status for e in entries}
    assert "completed" in statuses
    assert "failed" in statuses
    assert "aborted" in statuses
    assert "paused" in statuses


def test_summary_entry_count_five() -> None:
    summary = pipeline_run_log_summary()
    assert summary["entry_count"] == 5


def test_completed_count_is_two() -> None:
    summary = pipeline_run_log_summary()
    assert summary["completed_count"] == 2


def test_failed_count_is_one() -> None:
    summary = pipeline_run_log_summary()
    assert summary["failed_count"] == 1


def test_counts_by_status_covers_present_statuses() -> None:
    summary = pipeline_run_log_summary()
    by_status = summary["counts_by_status"]
    assert "completed" in by_status
    assert "failed" in by_status
    assert "aborted" in by_status
    assert "paused" in by_status


def test_counts_by_kind_covers_expected_kinds() -> None:
    summary = pipeline_run_log_summary()
    by_kind = summary["counts_by_kind"]
    assert "full_pipeline" in by_kind
    assert "partial_rerun" in by_kind
    assert "test_run" in by_kind
    assert "recovery_run" in by_kind


def test_schema_version() -> None:
    summary = pipeline_run_log_summary()
    assert summary["schema_version"] == PIPELINE_RUN_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = pipeline_run_log_summary()
    assert "reproducibility records" in summary["disclaimer"]
    assert summary["disclaimer"] == PIPELINE_RUN_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = pipeline_run_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_run_kinds_has_five_members() -> None:
    assert len(ALLOWED_RUN_KINDS) == 5


def test_allowed_run_statuses_has_five_members() -> None:
    assert len(ALLOWED_RUN_STATUSES) == 5


def test_fixture_run_kinds_in_allowed() -> None:
    entries = load_pipeline_run_entries()
    for e in entries:
        assert e.run_kind in ALLOWED_RUN_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_pipeline_run_entries()
    for e in entries:
        assert e.status in ALLOWED_RUN_STATUSES


def test_completed_at_nullable() -> None:
    entries = load_pipeline_run_entries()
    prl001 = next(e for e in entries if e.entry_id == "prl-001")
    assert prl001.completed_at == "2026-01-10T10:30:00Z"
    prl003 = next(e for e in entries if e.entry_id == "prl-003")
    assert prl003.completed_at is None


def test_candidate_count_nullable() -> None:
    entries = load_pipeline_run_entries()
    prl001 = next(e for e in entries if e.entry_id == "prl-001")
    assert prl001.candidate_count == 10
    prl004 = next(e for e in entries if e.entry_id == "prl-004")
    assert prl004.candidate_count is None


def test_as_dict_returns_required_keys() -> None:
    entries = load_pipeline_run_entries()
    d = entries[0].as_dict()
    for key in ("entry_id", "run_id", "run_kind", "status",
                "started_by", "started_at", "completed_at",
                "candidate_count", "notes"):
        assert key in d


def test_custom_path_argument() -> None:
    entries = load_pipeline_run_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = pipeline_run_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_full_pipeline_count_is_two() -> None:
    summary = pipeline_run_log_summary()
    assert summary["counts_by_kind"].get("full_pipeline", 0) == 2
