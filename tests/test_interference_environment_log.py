"""Tests for interference_environment_log module."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.interference_environment_log import (
    ALLOWED_INTERFERENCE_KINDS,
    ALLOWED_INTERFERENCE_STATUSES,
    INTERFERENCE_ENVIRONMENT_LOG_SCHEMA_VERSION,
    interference_environment_summary,
    load_interference_environment_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "interference_environment_log.json"


def test_load_entries_no_error() -> None:
    entries = load_interference_environment_entries()
    assert entries is not None


def test_load_entries_returns_five() -> None:
    entries = load_interference_environment_entries()
    assert len(entries) == 5


def test_allowed_statuses_only() -> None:
    entries = load_interference_environment_entries()
    for e in entries:
        assert e.status in ALLOWED_INTERFERENCE_STATUSES


def test_allowed_kinds_only() -> None:
    entries = load_interference_environment_entries()
    for e in entries:
        assert e.interference_kind in ALLOWED_INTERFERENCE_KINDS


def test_all_required_fields_present() -> None:
    entries = load_interference_environment_entries()
    for e in entries:
        assert e.entry_id
        assert e.run_id
        assert e.interference_kind
        assert e.status


def test_summary_entry_count_five() -> None:
    summary = interference_environment_summary()
    assert summary["entry_count"] == 5


def test_summary_assessed_count() -> None:
    summary = interference_environment_summary()
    assert summary["assessed_count"] == 2


def test_summary_flagged_count() -> None:
    summary = interference_environment_summary()
    assert summary["flagged_count"] == 1


def test_summary_cleared_count() -> None:
    summary = interference_environment_summary()
    assert summary["cleared_count"] == 1


def test_summary_inconclusive_count() -> None:
    summary = interference_environment_summary()
    assert summary["inconclusive_count"] == 1


def test_counts_by_kind_has_correct_keys() -> None:
    summary = interference_environment_summary()
    by_kind = summary["counts_by_kind"]
    assert isinstance(by_kind, dict)
    for kind in by_kind:
        assert kind in ALLOWED_INTERFERENCE_KINDS


def test_all_entries_have_entry_id() -> None:
    entries = load_interference_environment_entries()
    for e in entries:
        assert e.entry_id


def test_all_entries_have_run_id() -> None:
    entries = load_interference_environment_entries()
    for e in entries:
        assert e.run_id


def test_entries_span_multiple_kinds() -> None:
    entries = load_interference_environment_entries()
    kinds = {e.interference_kind for e in entries}
    assert len(kinds) >= 2


def test_entries_span_multiple_statuses() -> None:
    entries = load_interference_environment_entries()
    statuses = {e.status for e in entries}
    assert len(statuses) >= 2


def test_summary_schema_version() -> None:
    summary = interference_environment_summary()
    assert summary["schema_version"] == INTERFERENCE_ENVIRONMENT_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = interference_environment_summary()
    assert "disclaimer" in summary
    assert summary["disclaimer"]


def test_disclaimer_no_detection_claim() -> None:
    summary = interference_environment_summary()
    assert "not constitute a detection claim" in summary["disclaimer"]


def test_disclaimer_no_external_submission() -> None:
    summary = interference_environment_summary()
    assert "does not authorize external submission" in summary["disclaimer"]


def test_disclaimer_operational() -> None:
    summary = interference_environment_summary()
    assert "operational" in summary["disclaimer"]


def test_cli_interference_environment_summary() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "interference-environment-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["entry_count"] == 5


def test_validate_all_interference_environment_gate() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "validate-all"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out.get("ok") is True
