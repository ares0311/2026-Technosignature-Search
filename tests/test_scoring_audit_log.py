"""Tests for scoring audit log module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.scoring_audit_log import (
    ALLOWED_AUDIT_EVENT_KINDS,
    SCORING_AUDIT_LOG_DISCLAIMER,
    SCORING_AUDIT_LOG_SCHEMA_VERSION,
    ScoringAuditEntry,
    load_scoring_audit_entries,
    scoring_audit_log_summary,
)


def test_load_entries_returns_list():
    result = load_scoring_audit_entries()
    assert isinstance(result, list)


def test_load_entries_returns_dataclass_instances():
    result = load_scoring_audit_entries()
    assert all(isinstance(e, ScoringAuditEntry) for e in result)


def test_fixture_has_five_entries():
    result = load_scoring_audit_entries()
    assert len(result) == 5


def test_event_kinds_valid():
    result = load_scoring_audit_entries()
    for e in result:
        assert e.event_kind in ALLOWED_AUDIT_EVENT_KINDS


def test_scores_in_range():
    result = load_scoring_audit_entries()
    for e in result:
        assert 0.0 <= e.score <= 1.0


def test_at_least_one_rescore():
    result = load_scoring_audit_entries()
    assert any(e.event_kind == "rescore" for e in result)


def test_at_least_one_initial_score():
    result = load_scoring_audit_entries()
    assert any(e.event_kind == "initial_score" for e in result)


def test_serving_id_non_empty():
    result = load_scoring_audit_entries()
    for e in result:
        assert len(e.serving_id) > 0


def test_as_dict_returns_expected_keys():
    e = load_scoring_audit_entries()[0]
    d = e.as_dict()
    assert "audit_id" in d
    assert "candidate_id" in d
    assert "model_id" in d
    assert "model_version" in d
    assert "event_kind" in d
    assert "score" in d
    assert "pathway" in d
    assert "serving_id" in d


def test_summary_returns_dict():
    result = scoring_audit_log_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = scoring_audit_log_summary()
    assert result["schema_version"] == SCORING_AUDIT_LOG_SCHEMA_VERSION


def test_summary_disclaimer():
    result = scoring_audit_log_summary()
    assert result["disclaimer"] == SCORING_AUDIT_LOG_DISCLAIMER
    assert "append-only" in result["disclaimer"].lower()


def test_summary_entry_count():
    result = scoring_audit_log_summary()
    assert result["entry_count"] == 5


def test_summary_unique_candidate_count():
    result = scoring_audit_log_summary()
    assert result["unique_candidate_count"] == 3


def test_summary_rescore_count():
    result = scoring_audit_log_summary()
    assert result["rescore_count"] == 1


def test_summary_by_event_kind():
    result = scoring_audit_log_summary()
    assert "initial_score" in result["by_event_kind"]
    assert "rescore" in result["by_event_kind"]
    assert "baseline_comparison" in result["by_event_kind"]


def test_summary_by_model_id():
    result = scoring_audit_log_summary()
    assert "mdl-001" in result["by_model_id"]
    assert "mdl-002" in result["by_model_id"]


def test_cli_scoring_audit_log_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "scoring-audit-log-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_scoring_audit_log_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "scoring-audit-log-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "entry_count" in data
    assert "unique_candidate_count" in data
    assert "rescore_count" in data
