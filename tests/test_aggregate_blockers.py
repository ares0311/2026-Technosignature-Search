"""Tests for aggregate_blockers module."""

from __future__ import annotations

import json
from io import StringIO

from techno_search.aggregate_blockers import (
    AGGREGATE_BLOCKERS_DISCLAIMER,
    aggregate_blockers_summary,
)
from techno_search.cli import main


def test_aggregate_blockers_summary_returns_dict():
    result = aggregate_blockers_summary()
    assert isinstance(result, dict)


def test_aggregate_blockers_summary_disclaimer():
    result = aggregate_blockers_summary()
    assert AGGREGATE_BLOCKERS_DISCLAIMER in result["disclaimer"]


def test_aggregate_blockers_summary_total_count():
    result = aggregate_blockers_summary()
    assert isinstance(result["total_blocker_count"], int)
    assert result["total_blocker_count"] >= 0


def test_aggregate_blockers_summary_by_source():
    result = aggregate_blockers_summary()
    assert isinstance(result["by_source"], dict)
    total = sum(result["by_source"].values())
    assert total == result["total_blocker_count"]


def test_aggregate_blockers_summary_by_track():
    result = aggregate_blockers_summary()
    assert isinstance(result["by_track"], dict)


def test_aggregate_blockers_summary_triage_count():
    result = aggregate_blockers_summary()
    assert isinstance(result["triage_blocker_count"], int)
    assert result["triage_blocker_count"] >= 0


def test_aggregate_blockers_summary_lifecycle_count():
    result = aggregate_blockers_summary()
    assert isinstance(result["lifecycle_blocker_count"], int)
    assert result["lifecycle_blocker_count"] >= 0


def test_aggregate_blockers_summary_observation_count():
    result = aggregate_blockers_summary()
    assert isinstance(result["observation_blocker_count"], int)
    assert result["observation_blocker_count"] >= 0


def test_aggregate_blockers_summary_handoff_count():
    result = aggregate_blockers_summary()
    assert isinstance(result["handoff_blocker_count"], int)
    assert result["handoff_blocker_count"] >= 0


def test_aggregate_blockers_summary_unique_candidate_count():
    result = aggregate_blockers_summary()
    assert isinstance(result["unique_candidate_count"], int)
    assert result["unique_candidate_count"] >= 0


def test_aggregate_blockers_candidates_with_blockers():
    result = aggregate_blockers_summary()
    assert isinstance(result["candidates_with_blockers"], list)
    assert len(result["candidates_with_blockers"]) == result["unique_candidate_count"]


def test_aggregate_blockers_blocker_list_structure():
    result = aggregate_blockers_summary()
    for blocker in result["blockers"]:
        assert "source" in blocker
        assert "candidate_id" in blocker
        assert "track" in blocker
        assert "blocking_reason" in blocker


def test_aggregate_blockers_source_counts_match_total():
    result = aggregate_blockers_summary()
    triage = result["triage_blocker_count"]
    lifecycle = result["lifecycle_blocker_count"]
    observation = result["observation_blocker_count"]
    handoff = result["handoff_blocker_count"]
    assert triage + lifecycle + observation + handoff == result["total_blocker_count"]


def test_cli_aggregate_blockers_summary_exits_zero():
    stdout = StringIO()
    exit_code = main(["aggregate-blockers-summary"], stdout=stdout)
    assert exit_code == 0


def test_cli_aggregate_blockers_summary_outputs_json():
    stdout = StringIO()
    main(["aggregate-blockers-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())
    assert "total_blocker_count" in result
    assert "by_source" in result
    assert "by_track" in result
    assert "disclaimer" in result
