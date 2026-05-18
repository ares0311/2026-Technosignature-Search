from __future__ import annotations

import json
from pathlib import Path

from techno_search.candidate_rescore import (
    ALLOWED_RESCORE_TRIGGERS,
    CANDIDATE_RESCORE_DISCLAIMER,
    CANDIDATE_RESCORE_SCHEMA_VERSION,
    RescoreEvent,
    candidate_rescore_summary,
    load_rescore_events,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_rescore.json"


def test_schema_version():
    assert CANDIDATE_RESCORE_SCHEMA_VERSION == "candidate_rescore_v1"


def test_disclaimer_present():
    assert len(CANDIDATE_RESCORE_DISCLAIMER) > 20
    assert "provenance" in CANDIDATE_RESCORE_DISCLAIMER.lower()


def test_disclaimer_no_discovery_claim():
    lower = CANDIDATE_RESCORE_DISCLAIMER.lower()
    assert "discovery" not in lower or "no re-score" in lower


def test_allowed_triggers():
    assert "new_model_registered" in ALLOWED_RESCORE_TRIGGERS
    assert "operator_request" in ALLOWED_RESCORE_TRIGGERS
    assert "drift_detected" in ALLOWED_RESCORE_TRIGGERS
    assert "model_version_change" in ALLOWED_RESCORE_TRIGGERS


def test_load_rescore_events_returns_list():
    events = load_rescore_events(FIXTURE_PATH)
    assert isinstance(events, list)


def test_load_rescore_events_count():
    events = load_rescore_events(FIXTURE_PATH)
    assert len(events) == 4


def test_rescore_event_fields():
    events = load_rescore_events(FIXTURE_PATH)
    e = events[0]
    assert isinstance(e, RescoreEvent)
    assert e.rescore_id == "rs-001"
    assert e.candidate_id == "radio-clean-candidate"
    assert e.prior_model_id == "mdl-001"
    assert e.new_model_id == "mdl-002"
    assert 0.0 <= e.prior_score <= 1.0
    assert 0.0 <= e.new_score <= 1.0


def test_rescore_event_as_dict():
    events = load_rescore_events(FIXTURE_PATH)
    d = events[0].as_dict()
    assert "rescore_id" in d
    assert "prior_pathway" in d
    assert "new_pathway" in d
    assert "trigger" in d


def test_pathway_change_detected():
    events = load_rescore_events(FIXTURE_PATH)
    pathway_changes = [e for e in events if e.prior_pathway != e.new_pathway]
    assert len(pathway_changes) == 1
    assert pathway_changes[0].rescore_id == "rs-002"


def test_all_triggers_valid():
    events = load_rescore_events(FIXTURE_PATH)
    for e in events:
        assert e.trigger in ALLOWED_RESCORE_TRIGGERS


def test_scores_in_range():
    events = load_rescore_events(FIXTURE_PATH)
    for e in events:
        assert 0.0 <= e.prior_score <= 1.0
        assert 0.0 <= e.new_score <= 1.0


def test_summary_event_count():
    summary = candidate_rescore_summary(FIXTURE_PATH)
    assert summary["event_count"] == 4


def test_summary_unique_candidate_count():
    summary = candidate_rescore_summary(FIXTURE_PATH)
    assert summary["unique_candidate_count"] == 3


def test_summary_pathway_change_count():
    summary = candidate_rescore_summary(FIXTURE_PATH)
    assert summary["pathway_change_count"] == 1


def test_summary_by_trigger():
    summary = candidate_rescore_summary(FIXTURE_PATH)
    bt = summary["by_trigger"]
    assert bt["new_model_registered"] == 2
    assert bt["operator_request"] == 1
    assert bt["drift_detected"] == 1


def test_summary_max_score_delta():
    summary = candidate_rescore_summary(FIXTURE_PATH)
    assert summary["max_score_delta"] > 0.0


def test_summary_schema_version():
    summary = candidate_rescore_summary(FIXTURE_PATH)
    assert summary["schema_version"] == "candidate_rescore_v1"


def test_summary_disclaimer():
    summary = candidate_rescore_summary(FIXTURE_PATH)
    assert len(summary["disclaimer"]) > 20


def test_fixture_json_valid():
    data = json.loads(FIXTURE_PATH.read_text())
    assert "rescore_events" in data
    assert len(data["rescore_events"]) >= 4


def test_fixture_required_fields():
    data = json.loads(FIXTURE_PATH.read_text())
    required = {
        "rescore_id", "candidate_id", "prior_model_id", "new_model_id",
        "prior_score", "new_score", "prior_pathway", "new_pathway",
        "trigger", "serving_id", "event_utc",
    }
    for entry in data["rescore_events"]:
        for field in required:
            assert field in entry, f"Missing {field} in {entry.get('rescore_id')}"


def test_no_invalid_triggers_in_fixture():
    data = json.loads(FIXTURE_PATH.read_text())
    for entry in data["rescore_events"]:
        assert entry["trigger"] in ALLOWED_RESCORE_TRIGGERS
