from __future__ import annotations

import json
from pathlib import Path

from techno_search.candidate_comparison import (
    ALLOWED_COMPARISON_STATUSES,
    CANDIDATE_COMPARISON_DISCLAIMER,
    CANDIDATE_COMPARISON_SCHEMA_VERSION,
    CandidateComparisonRecord,
    candidate_comparison_summary,
    load_comparison_records,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_comparisons.json"


def test_schema_version():
    assert CANDIDATE_COMPARISON_SCHEMA_VERSION == "candidate_comparison_v1"


def test_disclaimer_present():
    assert len(CANDIDATE_COMPARISON_DISCLAIMER) > 20
    assert "scheduling" in CANDIDATE_COMPARISON_DISCLAIMER.lower()


def test_disclaimer_no_authorization():
    lower = CANDIDATE_COMPARISON_DISCLAIMER.lower()
    assert "does not authorize external submission" in lower


def test_allowed_statuses():
    assert "ranked" in ALLOWED_COMPARISON_STATUSES
    assert "tied" in ALLOWED_COMPARISON_STATUSES
    assert "inconclusive" in ALLOWED_COMPARISON_STATUSES
    assert "insufficient_data" in ALLOWED_COMPARISON_STATUSES


def test_load_returns_list():
    records = load_comparison_records(FIXTURE_PATH)
    assert isinstance(records, list)


def test_load_count():
    records = load_comparison_records(FIXTURE_PATH)
    assert len(records) == 4


def test_record_fields():
    records = load_comparison_records(FIXTURE_PATH)
    r = records[0]
    assert isinstance(r, CandidateComparisonRecord)
    assert r.comparison_id == "cmp-001"
    assert r.comparison_status == "ranked"
    assert isinstance(r.candidate_ids, list)
    assert len(r.candidate_ids) == 2
    assert isinstance(r.scores, dict)
    assert isinstance(r.pathways, dict)


def test_record_as_dict():
    records = load_comparison_records(FIXTURE_PATH)
    d = records[0].as_dict()
    assert "comparison_id" in d
    assert "candidate_ids" in d
    assert "comparison_status" in d
    assert "scores" in d
    assert "pathways" in d
    assert "top_candidate_id" in d


def test_ranked_record_has_top_candidate():
    records = load_comparison_records(FIXTURE_PATH)
    ranked = [r for r in records if r.comparison_status == "ranked"]
    for r in ranked:
        assert len(r.top_candidate_id) > 0


def test_tied_record_top_candidate_empty():
    records = load_comparison_records(FIXTURE_PATH)
    tied = [r for r in records if r.comparison_status == "tied"]
    assert len(tied) >= 1
    assert tied[0].top_candidate_id == ""


def test_insufficient_data_record_empty_scores():
    records = load_comparison_records(FIXTURE_PATH)
    insuf = [r for r in records if r.comparison_status == "insufficient_data"]
    assert len(insuf) >= 1
    assert insuf[0].scores == {}


def test_all_statuses_valid():
    records = load_comparison_records(FIXTURE_PATH)
    for r in records:
        assert r.comparison_status in ALLOWED_COMPARISON_STATUSES


def test_summary_record_count():
    summary = candidate_comparison_summary(FIXTURE_PATH)
    assert summary["record_count"] == 4


def test_summary_ranked_count():
    summary = candidate_comparison_summary(FIXTURE_PATH)
    assert summary["ranked_count"] == 2


def test_summary_tied_count():
    summary = candidate_comparison_summary(FIXTURE_PATH)
    assert summary["tied_count"] == 1


def test_summary_insufficient_count():
    summary = candidate_comparison_summary(FIXTURE_PATH)
    assert summary["insufficient_data_count"] == 1


def test_summary_by_status():
    summary = candidate_comparison_summary(FIXTURE_PATH)
    bs = summary["by_status"]
    assert bs["ranked"] == 2
    assert bs["tied"] == 1
    assert bs["insufficient_data"] == 1


def test_summary_top_candidates():
    summary = candidate_comparison_summary(FIXTURE_PATH)
    tops = summary["top_candidate_ids"]
    assert "radio-clean-candidate" in tops or "anomaly-clean-candidate" in tops


def test_summary_disclaimer():
    summary = candidate_comparison_summary(FIXTURE_PATH)
    assert len(summary["disclaimer"]) > 20


def test_fixture_json_valid():
    data = json.loads(FIXTURE_PATH.read_text())
    assert "candidate_comparisons" in data
    assert len(data["candidate_comparisons"]) >= 4


def test_fixture_required_fields():
    data = json.loads(FIXTURE_PATH.read_text())
    required = {
        "comparison_id", "candidate_ids", "comparison_status",
        "scores", "pathways", "top_candidate_id", "comparison_utc",
    }
    for entry in data["candidate_comparisons"]:
        for f in required:
            assert f in entry, f"Missing {f} in {entry.get('comparison_id')}"
