"""Tests for pipeline_checkpoint_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.pipeline_checkpoint_log import (
    ALLOWED_CHECKPOINT_KINDS,
    ALLOWED_CHECKPOINT_STATUSES,
    PIPELINE_CHECKPOINT_LOG_DISCLAIMER,
    PIPELINE_CHECKPOINT_LOG_SCHEMA_VERSION,
    load_pipeline_checkpoint_entries,
    pipeline_checkpoint_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pipeline_checkpoint_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_pipeline_checkpoint_entries()
    assert len(entries) == 5


def test_all_checkpoint_kinds_present() -> None:
    entries = load_pipeline_checkpoint_entries()
    kinds = {e.checkpoint_kind for e in entries}
    assert "stage_start" in kinds
    assert "stage_complete" in kinds
    assert "recovery_point" in kinds
    assert "validation_gate" in kinds
    assert "end_of_run" in kinds


def test_all_statuses_present() -> None:
    entries = load_pipeline_checkpoint_entries()
    statuses = {e.status for e in entries}
    assert "saved" in statuses
    assert "restored" in statuses
    assert "expired" in statuses
    assert "invalidated" in statuses


def test_summary_entry_count_five() -> None:
    summary = pipeline_checkpoint_log_summary()
    assert summary["entry_count"] == 5


def test_saved_count_is_two() -> None:
    summary = pipeline_checkpoint_log_summary()
    assert summary["saved_count"] == 2


def test_restored_count_is_one() -> None:
    summary = pipeline_checkpoint_log_summary()
    assert summary["restored_count"] == 1


def test_counts_by_status_covers_all_four() -> None:
    summary = pipeline_checkpoint_log_summary()
    by_status = summary["counts_by_status"]
    assert set(by_status.keys()) == {"saved", "restored", "expired", "invalidated"}


def test_counts_by_kind_covers_all_five() -> None:
    summary = pipeline_checkpoint_log_summary()
    by_kind = summary["counts_by_kind"]
    assert len(by_kind) == 5


def test_schema_version() -> None:
    summary = pipeline_checkpoint_log_summary()
    assert summary["schema_version"] == PIPELINE_CHECKPOINT_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_reproducibility() -> None:
    summary = pipeline_checkpoint_log_summary()
    assert "reproducibility records" in summary["disclaimer"]
    assert summary["disclaimer"] == PIPELINE_CHECKPOINT_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = pipeline_checkpoint_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_checkpoint_kinds_has_five_members() -> None:
    assert len(ALLOWED_CHECKPOINT_KINDS) == 5


def test_allowed_checkpoint_statuses_has_four_members() -> None:
    assert len(ALLOWED_CHECKPOINT_STATUSES) == 4


def test_fixture_checkpoint_kinds_in_allowed() -> None:
    entries = load_pipeline_checkpoint_entries()
    for e in entries:
        assert e.checkpoint_kind in ALLOWED_CHECKPOINT_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_pipeline_checkpoint_entries()
    for e in entries:
        assert e.status in ALLOWED_CHECKPOINT_STATUSES


def test_candidate_count_nullable() -> None:
    entries = load_pipeline_checkpoint_entries()
    pck001 = next(e for e in entries if e.entry_id == "pck-001")
    assert pck001.candidate_count == 12
    pck003 = next(e for e in entries if e.entry_id == "pck-003")
    assert pck003.candidate_count is None


def test_as_dict_returns_required_keys() -> None:
    entries = load_pipeline_checkpoint_entries()
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "run_id" in d
    assert "checkpoint_kind" in d
    assert "status" in d
    assert "stage_name" in d
    assert "checkpointed_by" in d
    assert "checkpointed_at" in d
    assert "candidate_count" in d
    assert "notes" in d


def test_custom_path_argument() -> None:
    entries = load_pipeline_checkpoint_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = pipeline_checkpoint_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_multiple_run_ids_present() -> None:
    entries = load_pipeline_checkpoint_entries()
    run_ids = {e.run_id for e in entries}
    assert len(run_ids) >= 2


def test_end_of_run_entry_invalidated() -> None:
    entries = load_pipeline_checkpoint_entries()
    pck005 = next(e for e in entries if e.entry_id == "pck-005")
    assert pck005.checkpoint_kind == "end_of_run"
    assert pck005.status == "invalidated"
