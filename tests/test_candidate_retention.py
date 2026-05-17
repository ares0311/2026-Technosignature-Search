"""Tests for candidate retention module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.candidate_retention import (
    ALLOWED_RETENTION_STATUSES,
    CANDIDATE_RETENTION_DISCLAIMER,
    CANDIDATE_RETENTION_SCHEMA_VERSION,
    CandidateRetentionRecord,
    candidate_retention_summary,
    load_retention_records,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_retention.json"


def test_load_retention_records_returns_list():
    result = load_retention_records()
    assert isinstance(result, list)


def test_load_retention_records_returns_dataclass_instances():
    result = load_retention_records()
    assert all(isinstance(r, CandidateRetentionRecord) for r in result)


def test_fixture_has_five_records():
    result = load_retention_records()
    assert len(result) == 5


def test_records_cover_all_three_tracks():
    result = load_retention_records()
    tracks = {r.track for r in result}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_retention_statuses_are_allowed():
    result = load_retention_records()
    for r in result:
        assert r.current_status in ALLOWED_RETENTION_STATUSES


def test_days_in_pipeline_non_negative():
    result = load_retention_records()
    for r in result:
        assert r.days_in_pipeline >= 0


def test_blocking_count_non_negative():
    result = load_retention_records()
    for r in result:
        assert r.blocking_count >= 0


def test_as_dict_returns_expected_keys():
    rec = load_retention_records()[0]
    d = rec.as_dict()
    assert "record_id" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "current_status" in d
    assert "days_in_pipeline" in d


def test_summary_schema_version():
    result = candidate_retention_summary()
    assert result["schema_version"] == CANDIDATE_RETENTION_SCHEMA_VERSION


def test_summary_disclaimer():
    result = candidate_retention_summary()
    assert result["disclaimer"] == CANDIDATE_RETENTION_DISCLAIMER
    assert "scheduling and provenance" in result["disclaimer"]


def test_summary_record_count():
    result = candidate_retention_summary()
    assert result["record_count"] == 5


def test_summary_active_count():
    result = candidate_retention_summary()
    # active, awaiting_epoch, under_review, escalated all count as "active"
    assert result["active_count"] == 4


def test_summary_archived_count():
    result = candidate_retention_summary()
    assert result["archived_count"] == 1


def test_summary_blocked_count():
    result = candidate_retention_summary()
    assert result["blocked_count"] == 3


def test_summary_average_days():
    result = candidate_retention_summary()
    assert result["average_days_in_pipeline"] > 0


def test_summary_max_days():
    result = candidate_retention_summary()
    assert result["max_days_in_pipeline"] == 51


def test_summary_by_track():
    result = candidate_retention_summary()
    assert result["by_track"]["radio"] == 2
    assert result["by_track"]["infrared"] == 2
    assert result["by_track"]["anomaly"] == 1


def test_summary_tracks_covered():
    result = candidate_retention_summary()
    assert set(result["tracks_covered"]) == {"radio", "infrared", "anomaly"}


def test_allowed_statuses_frozenset():
    assert "active" in ALLOWED_RETENTION_STATUSES
    assert "archived" in ALLOWED_RETENTION_STATUSES
    assert "escalated" in ALLOWED_RETENTION_STATUSES


def test_cli_retention_summary_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "candidate-retention-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_retention_summary_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "candidate-retention-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "record_count" in data
    assert "average_days_in_pipeline" in data


def test_cli_retention_summary_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "candidate-retention-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["record_count"] == 5
