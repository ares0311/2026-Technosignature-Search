"""Tests for data_archival_log module."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.data_archival_log import (
    ALLOWED_DATA_ARCHIVAL_KINDS,
    ALLOWED_DATA_ARCHIVAL_STATUSES,
    DATA_ARCHIVAL_LOG_SCHEMA_VERSION,
    data_archival_summary,
    load_data_archival_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "data_archival_log.json"


def test_load_entries_no_error() -> None:
    entries = load_data_archival_entries()
    assert entries is not None


def test_load_entries_returns_five() -> None:
    entries = load_data_archival_entries()
    assert len(entries) == 5


def test_allowed_statuses_only() -> None:
    entries = load_data_archival_entries()
    for e in entries:
        assert e.status in ALLOWED_DATA_ARCHIVAL_STATUSES


def test_allowed_kinds_only() -> None:
    entries = load_data_archival_entries()
    for e in entries:
        assert e.archival_kind in ALLOWED_DATA_ARCHIVAL_KINDS


def test_all_required_fields_present() -> None:
    entries = load_data_archival_entries()
    for e in entries:
        assert e.entry_id
        assert e.candidate_id
        assert e.track
        assert e.archival_kind
        assert e.status


def test_summary_entry_count_five() -> None:
    summary = data_archival_summary()
    assert summary["entry_count"] == 5


def test_summary_archived_count() -> None:
    summary = data_archival_summary()
    assert summary["archived_count"] == 2


def test_summary_pending_count() -> None:
    summary = data_archival_summary()
    assert summary["pending_count"] == 1


def test_counts_by_kind_has_correct_keys() -> None:
    summary = data_archival_summary()
    by_kind = summary["counts_by_kind"]
    assert isinstance(by_kind, dict)
    for kind in by_kind:
        assert kind in ALLOWED_DATA_ARCHIVAL_KINDS


def test_counts_by_track_has_correct_keys() -> None:
    summary = data_archival_summary()
    by_track = summary["counts_by_track"]
    assert isinstance(by_track, dict)
    assert len(by_track) >= 1


def test_all_entries_have_entry_id() -> None:
    entries = load_data_archival_entries()
    for e in entries:
        assert e.entry_id


def test_all_entries_have_candidate_id() -> None:
    entries = load_data_archival_entries()
    for e in entries:
        assert e.candidate_id


def test_all_entries_have_track() -> None:
    entries = load_data_archival_entries()
    for e in entries:
        assert e.track


def test_entries_span_multiple_tracks() -> None:
    entries = load_data_archival_entries()
    tracks = {e.track for e in entries}
    assert len(tracks) >= 2


def test_entries_span_multiple_kinds() -> None:
    entries = load_data_archival_entries()
    kinds = {e.archival_kind for e in entries}
    assert len(kinds) >= 2


def test_summary_schema_version() -> None:
    summary = data_archival_summary()
    assert summary["schema_version"] == DATA_ARCHIVAL_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = data_archival_summary()
    assert "disclaimer" in summary
    assert summary["disclaimer"]


def test_disclaimer_no_detection_claim() -> None:
    summary = data_archival_summary()
    assert "not constitute a detection claim" in summary["disclaimer"]


def test_disclaimer_no_external_submission() -> None:
    summary = data_archival_summary()
    assert "does not authorize external submission" in summary["disclaimer"]


def test_disclaimer_operational() -> None:
    summary = data_archival_summary()
    assert "operational" in summary["disclaimer"]


def test_cli_data_archival_summary() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "data-archival-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["entry_count"] == 5


def test_validate_all_data_archival_gate() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "validate-all"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out.get("ok") is True
