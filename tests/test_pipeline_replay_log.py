from __future__ import annotations

from techno_search.pipeline_replay_log import (
    ALLOWED_REPLAY_OUTCOMES,
    PIPELINE_REPLAY_DISCLAIMER,
    PIPELINE_REPLAY_SCHEMA_VERSION,
    PipelineReplayEntry,
    load_replay_entries,
    pipeline_replay_summary,
)


def test_schema_version() -> None:
    assert PIPELINE_REPLAY_SCHEMA_VERSION == "pipeline_replay_log_v1"


def test_disclaimer_append_only() -> None:
    assert "append-only" in PIPELINE_REPLAY_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in PIPELINE_REPLAY_DISCLAIMER


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in PIPELINE_REPLAY_DISCLAIMER


def test_disclaimer_no_packet_modification() -> None:
    assert "does not modify committed candidate packets" in PIPELINE_REPLAY_DISCLAIMER


def test_allowed_outcomes() -> None:
    assert "score_matched" in ALLOWED_REPLAY_OUTCOMES
    assert "score_diverged" in ALLOWED_REPLAY_OUTCOMES
    assert "config_mismatch" in ALLOWED_REPLAY_OUTCOMES
    assert "replay_error" in ALLOWED_REPLAY_OUTCOMES


def test_load_entries_count() -> None:
    entries = load_replay_entries()
    assert len(entries) == 4


def test_load_entries_types() -> None:
    entries = load_replay_entries()
    for e in entries:
        assert isinstance(e, PipelineReplayEntry)


def test_first_entry_fields() -> None:
    entries = load_replay_entries()
    e = entries[0]
    assert e.replay_id == "rpl-001"
    assert e.candidate_id == "radio-clean-candidate"
    assert e.original_config_id == "pcfg-001"
    assert e.replay_config_id == "pcfg-001"
    assert e.original_score == 0.88
    assert e.replayed_score == 0.88
    assert e.outcome == "score_matched"
    assert e.score_delta == 0.0


def test_score_diverged_entry() -> None:
    entries = load_replay_entries()
    diverged = [e for e in entries if e.outcome == "score_diverged"]
    assert len(diverged) == 1
    d = diverged[0]
    assert d.replay_id == "rpl-002"
    assert d.score_delta == -0.04


def test_config_mismatch_entry() -> None:
    entries = load_replay_entries()
    mismatched = [e for e in entries if e.outcome == "config_mismatch"]
    assert len(mismatched) == 1
    assert mismatched[0].replay_id == "rpl-004"


def test_score_matched_entries() -> None:
    entries = load_replay_entries()
    matched = [e for e in entries if e.outcome == "score_matched"]
    assert len(matched) == 2


def test_as_dict_keys() -> None:
    entries = load_replay_entries()
    d = entries[0].as_dict()
    expected = {
        "replay_id", "candidate_id", "original_config_id", "replay_config_id",
        "original_score", "replayed_score", "outcome", "score_delta",
        "replay_utc", "notes",
    }
    assert set(d.keys()) == expected


def test_as_dict_values_match() -> None:
    entries = load_replay_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["replay_id"] == e.replay_id
    assert d["original_score"] == e.original_score
    assert d["outcome"] == e.outcome


def test_summary_entry_count() -> None:
    s = pipeline_replay_summary()
    assert s["entry_count"] == 4


def test_summary_matched_count() -> None:
    s = pipeline_replay_summary()
    assert s["matched_count"] == 2


def test_summary_diverged_count() -> None:
    s = pipeline_replay_summary()
    assert s["diverged_count"] == 1


def test_summary_by_outcome() -> None:
    s = pipeline_replay_summary()
    bo = s["by_outcome"]
    assert bo.get("score_matched", 0) == 2
    assert bo.get("score_diverged", 0) == 1
    assert bo.get("config_mismatch", 0) == 1


def test_summary_mean_abs_delta() -> None:
    s = pipeline_replay_summary()
    assert s["mean_abs_score_delta"] >= 0.0


def test_summary_max_abs_delta() -> None:
    s = pipeline_replay_summary()
    assert s["max_abs_score_delta"] >= s["mean_abs_score_delta"]


def test_summary_schema_version() -> None:
    s = pipeline_replay_summary()
    assert s["schema_version"] == PIPELINE_REPLAY_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = pipeline_replay_summary()
    assert "disclaimer" in s
    assert "append-only" in s["disclaimer"]
