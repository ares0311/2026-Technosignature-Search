"""Tests for candidate lifecycle schema, loader, summary, and CLI."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from techno_search.candidate_lifecycle import (
    ALLOWED_LIFECYCLE_STAGES,
    CANDIDATE_LIFECYCLE_DISCLAIMER,
    CANDIDATE_LIFECYCLE_SCHEMA_VERSION,
    candidate_lifecycle_summary,
    load_lifecycle_entries,
)
from techno_search.cli import main


def test_lifecycle_fixture_loads():
    entries = load_lifecycle_entries()
    assert len(entries) >= 3


def test_lifecycle_fixture_all_stages_valid():
    entries = load_lifecycle_entries()
    for entry in entries:
        assert entry.stage in ALLOWED_LIFECYCLE_STAGES, f"Unknown stage: {entry.stage}"


def test_lifecycle_fixture_tracks_covered():
    entries = load_lifecycle_entries()
    tracks = {e.track for e in entries}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_lifecycle_summary_entry_count():
    summary = candidate_lifecycle_summary()
    assert summary["entry_count"] >= 3


def test_lifecycle_summary_by_stage_present():
    summary = candidate_lifecycle_summary()
    assert len(summary["by_stage"]) >= 1


def test_lifecycle_summary_by_track_has_three_tracks():
    summary = candidate_lifecycle_summary()
    assert len(summary["tracks_covered"]) >= 3


def test_lifecycle_summary_disclaimer():
    summary = candidate_lifecycle_summary()
    assert CANDIDATE_LIFECYCLE_DISCLAIMER in summary["disclaimer"]


def test_lifecycle_summary_schema_version():
    summary = candidate_lifecycle_summary()
    assert summary["schema_version"] == CANDIDATE_LIFECYCLE_SCHEMA_VERSION


def test_cli_candidate_lifecycle_summary_exit_zero():
    out = StringIO()
    ret = main(["candidate-lifecycle-summary"], stdout=out)
    assert ret == 0
    data = json.loads(out.getvalue())
    assert data["entry_count"] >= 3


def test_cli_candidate_lifecycle_summary_disclaimer():
    out = StringIO()
    main(["candidate-lifecycle-summary"], stdout=out)
    data = json.loads(out.getvalue())
    assert CANDIDATE_LIFECYCLE_DISCLAIMER in data["disclaimer"]


def test_lifecycle_schema_in_schema_paths():
    out = StringIO()
    ret = main(["schema-paths"], stdout=out)
    assert ret == 0
    data = json.loads(out.getvalue())
    assert "candidate_lifecycle" in data


def test_lifecycle_schema_file_exists():
    schema_path = (
        Path(__file__).resolve().parents[1] / "schemas" / "candidate_lifecycle.schema.json"
    )
    assert schema_path.exists()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema.get("title") == "CandidateLifecycle"
    required = schema.get("required", [])
    for field in ("schema_version", "disclaimer", "entries"):
        assert field in required
