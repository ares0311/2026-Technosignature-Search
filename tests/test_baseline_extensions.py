"""Tests for baseline eval extensions: rule fire rates, misclassification log,
performance history, drift check, and injection grid routing."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from techno_search.baseline_eval import (
    BASELINE_EVAL_DISCLAIMER,
    BASELINE_PERFORMANCE_HISTORY_SCHEMA_VERSION,
    baseline_pathway_drift_summary,
    baseline_performance_history_summary,
    evaluate_baseline,
)
from techno_search.baseline_model import ALL_BASELINE_RULES, RuleBasedBaselineClassifier
from techno_search.cli import main

# ---------------------------------------------------------------------------
# Step 1 — per-track accuracy
# ---------------------------------------------------------------------------


def test_evaluate_baseline_by_track_has_multiple_tracks():
    result = evaluate_baseline()
    track_accuracy = result["by_track_accuracy"]
    assert len(track_accuracy) >= 2, "Expected at least radio and infrared tracks"


def test_evaluate_baseline_per_track_accuracy_in_range():
    result = evaluate_baseline()
    for track, acc in result["by_track_accuracy"].items():
        assert 0.0 <= acc <= 1.0, f"Track {track} accuracy out of range: {acc}"


# ---------------------------------------------------------------------------
# Step 2 — rule fire rates
# ---------------------------------------------------------------------------


def test_evaluate_baseline_rule_fire_rates_all_rules_present():
    result = evaluate_baseline()
    fire_rates = result["rule_fire_rates"]
    for rule in ALL_BASELINE_RULES:
        assert rule in fire_rates, f"Missing rule in fire_rates: {rule}"


def test_evaluate_baseline_rule_fire_rates_values_in_range():
    result = evaluate_baseline()
    for rule, rate in result["rule_fire_rates"].items():
        assert 0.0 <= rate <= 1.0, f"Rule fire rate out of range for {rule}: {rate}"


def test_evaluate_baseline_false_positive_rule_fires_frequently():
    """The fp_prob >= 0.80 rule should fire for most calibration false-positives."""
    result = evaluate_baseline()
    fp_rule = "scores.false_positive_probability >= 0.80"
    rate = result["rule_fire_rates"].get(fp_rule, 0.0)
    assert rate > 0.0, "FP rule should fire on at least one case"


# ---------------------------------------------------------------------------
# Step 3 — misclassification log
# ---------------------------------------------------------------------------


def test_evaluate_baseline_misclassified_key_present():
    result = evaluate_baseline()
    assert "misclassified" in result
    assert "misclassified_count" in result


def test_evaluate_baseline_no_misclassifications_on_current_fixtures():
    result = evaluate_baseline()
    assert result["misclassified_count"] == 0, (
        f"Expected zero misclassifications, got: {result['misclassified']}"
    )


def test_evaluate_baseline_misclassified_structure():
    result = evaluate_baseline()
    for item in result["misclassified"]:
        assert "candidate_id" in item
        assert "expected_pathway" in item
        assert "predicted_pathway" in item
        assert "rule_trace" in item


# ---------------------------------------------------------------------------
# Step 4 — performance history fixture + summary
# ---------------------------------------------------------------------------


def test_baseline_performance_history_fixture_loads():
    history_path = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "baseline_performance_history.json"
    )
    with history_path.open() as f:
        data = json.load(f)
    assert data["schema_version"] == BASELINE_PERFORMANCE_HISTORY_SCHEMA_VERSION
    assert len(data["snapshots"]) >= 1


def test_baseline_performance_history_summary_snapshot_count():
    summary = baseline_performance_history_summary()
    assert summary["snapshot_count"] >= 1


def test_baseline_performance_history_summary_latest_accuracy():
    summary = baseline_performance_history_summary()
    acc = summary["latest_accuracy"]
    assert acc is not None
    assert 0.0 <= float(acc) <= 1.0


def test_baseline_performance_history_summary_disclaimer():
    summary = baseline_performance_history_summary()
    assert BASELINE_EVAL_DISCLAIMER in summary["disclaimer"]


def test_cli_baseline_performance_history_summary():
    out = StringIO()
    ret = main(["baseline-performance-history-summary"], stdout=out)
    assert ret == 0
    data = json.loads(out.getvalue())
    assert data["snapshot_count"] >= 1
    assert "latest_accuracy" in data


# ---------------------------------------------------------------------------
# Step 5 — synthetic injection grid for baseline routing
# ---------------------------------------------------------------------------


def _make_radio_packet(snr: float, drift_present: bool) -> dict:
    """Construct a synthetic scored radio packet at given SNR/drift level."""
    ts_interest = min(1.0, snr / 20.0)
    fp_prob = max(0.0, 1.0 - snr / 15.0) if drift_present else 0.95
    signal_conf = min(1.0, snr / 12.0) if drift_present else 0.10
    review_ready = min(1.0, snr / 18.0) if drift_present else 0.05
    return {
        "posterior": {
            "technosignature_interest": ts_interest,
            "natural_source": 0.0,
            "human_interference": 0.0,
            "instrumental_artifact": 0.0,
            "catalog_or_processing_error": 0.0,
            "known_object": 0.0,
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


def _make_ir_packet(ir_excess_strength: float) -> dict:
    """Construct a synthetic scored infrared excess packet."""
    ts_interest = min(1.0, ir_excess_strength * 0.8)
    fp_prob = max(0.0, 1.0 - ir_excess_strength * 0.7)
    signal_conf = min(1.0, ir_excess_strength * 0.9)
    review_ready = min(1.0, ir_excess_strength * 0.85)
    return {
        "posterior": {
            "technosignature_interest": ts_interest,
            "natural_source": 0.0,
            "human_interference": 0.0,
            "instrumental_artifact": 0.0,
            "catalog_or_processing_error": 0.0,
            "known_object": 0.0,
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


def test_injection_grid_high_snr_drift_not_false_positive():
    """High-SNR narrowband signal with drift should not route to do_not_submit_false_positive."""
    classifier = RuleBasedBaselineClassifier()
    for snr in (10.0, 15.0, 20.0):
        packet = _make_radio_packet(snr=snr, drift_present=True)
        result = classifier.predict(packet)
        assert result.predicted_pathway != "do_not_submit_false_positive", (
            f"SNR={snr} with drift should not be a false positive"
        )


def test_injection_grid_low_snr_no_drift_is_rfi_like():
    """Very low SNR with no drift should not route to candidate_review_packet."""
    classifier = RuleBasedBaselineClassifier()
    packet = _make_radio_packet(snr=1.0, drift_present=False)
    result = classifier.predict(packet)
    assert result.predicted_pathway != "candidate_review_packet", (
        "Very low SNR / no drift should not be candidate_review_packet"
    )


def test_injection_grid_strong_ir_excess_not_false_positive():
    """Strong IR excess should not route to do_not_submit_false_positive."""
    classifier = RuleBasedBaselineClassifier()
    packet = _make_ir_packet(ir_excess_strength=1.0)
    result = classifier.predict(packet)
    assert result.predicted_pathway != "do_not_submit_false_positive"


def test_injection_grid_weak_ir_excess_not_candidate_review():
    """Very weak IR excess (likely dust confusion) should not reach candidate_review_packet."""
    classifier = RuleBasedBaselineClassifier()
    packet = _make_ir_packet(ir_excess_strength=0.05)
    result = classifier.predict(packet)
    assert result.predicted_pathway != "candidate_review_packet"


# ---------------------------------------------------------------------------
# Step 9 — baseline drift check
# ---------------------------------------------------------------------------


def test_baseline_pathway_drift_zero_on_example_candidates():
    result = baseline_pathway_drift_summary()
    assert result["zero_drift"] is True, (
        f"Expected zero drift but got: {result['drift_cases']}"
    )


def test_baseline_pathway_drift_summary_structure():
    result = baseline_pathway_drift_summary()
    assert "candidates_checked" in result
    assert "drift_count" in result
    assert "drift_cases" in result
    assert result["candidates_checked"] >= 3


def test_baseline_pathway_drift_summary_disclaimer():
    result = baseline_pathway_drift_summary()
    assert BASELINE_EVAL_DISCLAIMER in result["disclaimer"]


def test_cli_baseline_pathway_drift_summary_exit_zero():
    out = StringIO()
    ret = main(["baseline-pathway-drift-summary"], stdout=out)
    assert ret == 0
    data = json.loads(out.getvalue())
    assert data["zero_drift"] is True


# ---------------------------------------------------------------------------
# Step 12 — baseline eval JSON schema
# ---------------------------------------------------------------------------


def test_baseline_eval_schema_in_schema_paths():
    out = StringIO()
    ret = main(["schema-paths"], stdout=out)
    assert ret == 0
    data = json.loads(out.getvalue())
    assert "baseline_eval" in data
    assert "baseline_performance_history" in data


def test_baseline_eval_schema_file_exists():
    schema_path = (
        Path(__file__).resolve().parents[1] / "schemas" / "baseline_eval.schema.json"
    )
    assert schema_path.exists()
    with schema_path.open() as f:
        schema = json.load(f)
    assert schema.get("title") == "BaselineEval"
    required = schema.get("required", [])
    for field in ("schema_version", "model_version", "disclaimer", "pathway_accuracy"):
        assert field in required


def test_baseline_performance_history_schema_file_exists():
    schema_path = (
        Path(__file__).resolve().parents[1]
        / "schemas"
        / "baseline_performance_history.schema.json"
    )
    assert schema_path.exists()
    with schema_path.open() as f:
        schema = json.load(f)
    assert schema.get("title") == "BaselinePerformanceHistory"
