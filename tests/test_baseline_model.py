"""Tests for the interpretable rule-based baseline classifier."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from techno_search.baseline_eval import BASELINE_EVAL_DISCLAIMER, evaluate_baseline
from techno_search.baseline_model import (
    BASELINE_MODEL_DISCLAIMER,
    BASELINE_MODEL_VERSION,
    RuleBasedBaselineClassifier,
    predict_pathway,
)
from techno_search.cli import main
from techno_search.schemas import candidate_from_mapping
from techno_search.scoring import score_candidate


def _make_scored_packet(
    *,
    ts_interest: float = 0.0,
    fp_prob: float = 1.0,
    signal_conf: float = 0.0,
    review_ready: float = 0.0,
    known_object: float = 0.0,
) -> dict:
    return {
        "posterior": {
            "technosignature_interest": ts_interest,
            "natural_source": 0.0,
            "human_interference": 0.0,
            "instrumental_artifact": 0.0,
            "catalog_or_processing_error": 0.0,
            "known_object": known_object,
            "noise_or_low_confidence": 0.0,
        },
        "scores": {
            "false_positive_probability": fp_prob,
            "signal_reality_confidence": signal_conf,
            "novelty_score": 0.0,
            "followup_value": 0.0,
            "review_readiness": review_ready,
        },
    }


def test_baseline_known_object_routing():
    packet = _make_scored_packet(known_object=0.90, fp_prob=0.1)
    result = predict_pathway(packet)
    assert result.predicted_pathway == "known_object_annotation"
    assert "posterior.known_object >= 0.80" in result.rule_trace


def test_baseline_false_positive_routing():
    packet = _make_scored_packet(fp_prob=0.90, known_object=0.0)
    result = predict_pathway(packet)
    assert result.predicted_pathway == "do_not_submit_false_positive"
    assert "scores.false_positive_probability >= 0.80" in result.rule_trace


def test_baseline_candidate_review_packet_routing():
    packet = _make_scored_packet(
        ts_interest=0.70,
        fp_prob=0.20,
        signal_conf=0.80,
        review_ready=0.80,
        known_object=0.05,
    )
    result = predict_pathway(packet)
    assert result.predicted_pathway == "candidate_review_packet"
    assert "posterior.technosignature_interest >= 0.60" in result.rule_trace


def test_baseline_human_review_queue_routing():
    packet = _make_scored_packet(
        ts_interest=0.30,
        fp_prob=0.50,
        signal_conf=0.50,
        review_ready=0.40,
        known_object=0.0,
    )
    result = predict_pathway(packet)
    assert result.predicted_pathway == "human_review_queue"


def test_baseline_github_reproducibility_only_routing():
    packet = _make_scored_packet(
        ts_interest=0.10,
        fp_prob=0.75,
        signal_conf=0.20,
        review_ready=0.10,
        known_object=0.0,
    )
    result = predict_pathway(packet)
    assert result.predicted_pathway == "github_reproducibility_only"


def test_baseline_rule_trace_nonempty():
    packet = _make_scored_packet(fp_prob=0.95)
    result = predict_pathway(packet)
    assert len(result.rule_trace) >= 1


def test_baseline_model_version():
    packet = _make_scored_packet()
    result = predict_pathway(packet)
    assert result.model_version == BASELINE_MODEL_VERSION


def test_baseline_disclaimer():
    packet = _make_scored_packet()
    result = predict_pathway(packet)
    assert BASELINE_MODEL_DISCLAIMER in result.disclaimer


def test_baseline_rule_coverage_between_zero_and_one():
    for fp in (0.0, 0.5, 0.9, 1.0):
        packet = _make_scored_packet(fp_prob=fp)
        result = predict_pathway(packet)
        assert 0.0 <= result.rule_coverage <= 1.0


def test_baseline_routes_calibration_false_positives():
    """All calibration false-positives should route to do_not_submit_false_positive."""
    import json as _json
    cal_path = (
        Path(__file__).resolve().parent / "fixtures" / "calibration_false_positives.json"
    )
    with cal_path.open() as f:
        cal_data = _json.load(f)
    classifier = RuleBasedBaselineClassifier()
    for fixture in cal_data.get("fixtures", []):
        candidate_dict = fixture.get("candidate", {})
        if not candidate_dict:
            continue
        candidate = candidate_from_mapping(candidate_dict)
        scored = score_candidate(candidate)
        packet = scored.as_dict()
        result = classifier.predict(packet)
        assert result.predicted_pathway == "do_not_submit_false_positive", (
            f"Expected false positive for {fixture.get('name')}, "
            f"got {result.predicted_pathway}"
        )


def test_baseline_routes_clean_example_candidates():
    """Clean example candidates should not route to false_positive."""
    import json as _json
    examples_dir = Path(__file__).resolve().parents[1] / "examples" / "candidates"
    classifier = RuleBasedBaselineClassifier()
    for candidate_path in sorted(examples_dir.glob("*.json")):
        with candidate_path.open() as f:
            candidate_dict = _json.load(f)
        candidate = candidate_from_mapping(candidate_dict)
        scored = score_candidate(candidate)
        packet = scored.as_dict()
        result = classifier.predict(packet)
        assert result.predicted_pathway != "do_not_submit_false_positive", (
            f"{candidate_path.name} should not route to false positive"
        )


def test_evaluate_baseline_accuracy():
    result = evaluate_baseline()
    assert result["total_cases"] >= 3
    assert result["pathway_accuracy"] >= 0.80
    assert 0.0 <= result["false_positive_recall"] <= 1.0
    assert 0.0 <= result["candidate_precision"] <= 1.0
    assert result["disclaimer"] == BASELINE_EVAL_DISCLAIMER


def test_evaluate_baseline_by_track_coverage():
    result = evaluate_baseline()
    track_accuracy = result["by_track_accuracy"]
    assert len(track_accuracy) >= 1


def test_cli_baseline_eval_summary():
    out = StringIO()
    ret = main(["baseline-eval-summary"], stdout=out)
    assert ret == 0
    data = json.loads(out.getvalue())
    assert data["pathway_accuracy"] >= 0.80
    assert BASELINE_EVAL_DISCLAIMER in data["disclaimer"]
    assert "model_version" in data
    assert "total_cases" in data
    assert data["total_cases"] >= 3
