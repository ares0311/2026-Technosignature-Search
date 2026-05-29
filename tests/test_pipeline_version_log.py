"""Tests for pipeline_version_log module."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.pipeline_version_log import (
    ALLOWED_PIPELINE_VERSION_KINDS,
    ALLOWED_PIPELINE_VERSION_STATUSES,
    PIPELINE_VERSION_LOG_SCHEMA_VERSION,
    load_pipeline_version_entries,
    pipeline_version_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pipeline_version_log.json"


def test_load_entries_no_error() -> None:
    entries = load_pipeline_version_entries()
    assert entries is not None


def test_load_entries_returns_five() -> None:
    entries = load_pipeline_version_entries()
    assert len(entries) == 5


def test_allowed_statuses_only() -> None:
    entries = load_pipeline_version_entries()
    for e in entries:
        assert e.status in ALLOWED_PIPELINE_VERSION_STATUSES


def test_allowed_kinds_only() -> None:
    entries = load_pipeline_version_entries()
    for e in entries:
        assert e.version_kind in ALLOWED_PIPELINE_VERSION_KINDS


def test_all_required_fields_present() -> None:
    entries = load_pipeline_version_entries()
    for e in entries:
        assert e.entry_id
        assert e.run_id
        assert e.version_kind
        assert e.status
        assert e.version_string


def test_summary_entry_count_five() -> None:
    summary = pipeline_version_summary()
    assert summary["entry_count"] == 5


def test_summary_active_count() -> None:
    summary = pipeline_version_summary()
    assert summary["active_count"] == 2


def test_summary_deprecated_count() -> None:
    summary = pipeline_version_summary()
    assert summary["deprecated_count"] == 1


def test_summary_superseded_count() -> None:
    summary = pipeline_version_summary()
    assert summary["superseded_count"] == 1


def test_summary_testing_count() -> None:
    summary = pipeline_version_summary()
    assert summary["testing_count"] == 1


def test_counts_by_kind_has_correct_keys() -> None:
    summary = pipeline_version_summary()
    by_kind = summary["counts_by_kind"]
    assert isinstance(by_kind, dict)
    for kind in by_kind:
        assert kind in ALLOWED_PIPELINE_VERSION_KINDS


def test_all_entries_have_entry_id() -> None:
    entries = load_pipeline_version_entries()
    for e in entries:
        assert e.entry_id


def test_all_entries_have_run_id() -> None:
    entries = load_pipeline_version_entries()
    for e in entries:
        assert e.run_id


def test_all_entries_have_version_string() -> None:
    entries = load_pipeline_version_entries()
    for e in entries:
        assert e.version_string


def test_entries_span_multiple_kinds() -> None:
    entries = load_pipeline_version_entries()
    kinds = {e.version_kind for e in entries}
    assert len(kinds) >= 2


def test_entries_span_multiple_statuses() -> None:
    entries = load_pipeline_version_entries()
    statuses = {e.status for e in entries}
    assert len(statuses) >= 2


def test_summary_schema_version() -> None:
    summary = pipeline_version_summary()
    assert summary["schema_version"] == PIPELINE_VERSION_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = pipeline_version_summary()
    assert "disclaimer" in summary
    assert summary["disclaimer"]


def test_disclaimer_no_detection_claim() -> None:
    summary = pipeline_version_summary()
    assert "not constitute a detection claim" in summary["disclaimer"]


def test_disclaimer_no_external_submission() -> None:
    summary = pipeline_version_summary()
    assert "does not authorize external submission" in summary["disclaimer"]


def test_disclaimer_reproducibility() -> None:
    summary = pipeline_version_summary()
    assert "reproducibility" in summary["disclaimer"]


def test_cli_pipeline_version_summary() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "pipeline-version-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["entry_count"] == 5


def test_validate_all_pipeline_version_gate() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "validate-all"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out.get("ok") is True
