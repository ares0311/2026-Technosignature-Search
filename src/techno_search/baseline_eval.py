"""Baseline evaluation harness for Milestone 10 scaffolding.

Evaluates RuleBasedBaselineClassifier against synthetic injection-recovery
and calibration false-positive fixtures. Results are local synthetic
diagnostics only — not calibrated survey metrics or detection claims.
"""

from __future__ import annotations

import json
from contextlib import suppress
from pathlib import Path
from typing import Any

from techno_search.baseline_model import (
    BASELINE_MODEL_VERSION,
    RuleBasedBaselineClassifier,
)
from techno_search.schemas import candidate_from_mapping
from techno_search.scoring import score_candidate

BASELINE_EVAL_DISCLAIMER = (
    "Baseline evaluation results are local synthetic diagnostics only. "
    "They are not calibrated survey sensitivity estimates, detection claims, "
    "discoveries, or external validation. Accuracy metrics are computed against "
    "synthetic fixtures and have no statistical meaning for real observations."
)


def _default_calibration_fixture_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "calibration_false_positives.json"
    )


def _default_example_candidates_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "examples" / "candidates"


def _score_and_predict(
    candidate_dict: dict[str, Any],
    classifier: RuleBasedBaselineClassifier,
) -> dict[str, Any]:
    candidate = candidate_from_mapping(candidate_dict)
    scored = score_candidate(candidate)
    packet = scored.as_dict()
    result = classifier.predict(packet)
    return {
        "candidate_id": candidate.candidate_id,
        "track": candidate.track.value,
        "expected_pathway": str(scored.recommended_pathway.value),
        "predicted_pathway": result.predicted_pathway,
        "match": result.predicted_pathway == scored.recommended_pathway.value,
        "rule_trace": result.rule_trace,
        "rule_coverage": result.rule_coverage,
    }


def evaluate_baseline(
    calibration_fixture_path: Path | None = None,
    example_candidates_dir: Path | None = None,
) -> dict[str, Any]:
    classifier = RuleBasedBaselineClassifier()
    results: list[dict[str, Any]] = []

    cal_path = calibration_fixture_path or _default_calibration_fixture_path()
    if cal_path.exists():
        with cal_path.open(encoding="utf-8") as handle:
            cal_data = json.load(handle)
        for fixture in cal_data.get("fixtures", []):
            candidate_dict = fixture.get("candidate", {})
            if not candidate_dict:
                continue
            with suppress(Exception):
                results.append(_score_and_predict(candidate_dict, classifier))

    examples_dir = example_candidates_dir or _default_example_candidates_dir()
    if examples_dir.exists():
        for candidate_path in sorted(examples_dir.glob("*.json")):
            with candidate_path.open(encoding="utf-8") as handle:
                candidate_dict = json.load(handle)
            with suppress(Exception):
                results.append(_score_and_predict(candidate_dict, classifier))

    total = len(results)
    correct = sum(1 for r in results if r["match"])
    pathway_accuracy = correct / total if total > 0 else 0.0

    false_positive_results = [
        r for r in results if r["expected_pathway"] == "do_not_submit_false_positive"
    ]
    fp_total = len(false_positive_results)
    fp_correct = sum(1 for r in false_positive_results if r["match"])
    false_positive_recall = fp_correct / fp_total if fp_total > 0 else 0.0

    candidate_results = [
        r for r in results if r["predicted_pathway"] == "candidate_review_packet"
    ]
    cp_total = len(candidate_results)
    cp_correct = sum(1 for r in candidate_results if r["match"])
    candidate_precision = cp_correct / cp_total if cp_total > 0 else 0.0

    mean_rule_coverage = (
        sum(r["rule_coverage"] for r in results) / total if total > 0 else 0.0
    )

    by_track: dict[str, dict[str, int]] = {}
    for r in results:
        track = r["track"]
        if track not in by_track:
            by_track[track] = {"total": 0, "correct": 0}
        by_track[track]["total"] += 1
        if r["match"]:
            by_track[track]["correct"] += 1

    track_accuracy = {
        track: (counts["correct"] / counts["total"] if counts["total"] > 0 else 0.0)
        for track, counts in by_track.items()
    }

    return {
        "schema_version": "baseline_eval_v0",
        "model_version": BASELINE_MODEL_VERSION,
        "disclaimer": BASELINE_EVAL_DISCLAIMER,
        "total_cases": total,
        "correct_predictions": correct,
        "pathway_accuracy": pathway_accuracy,
        "false_positive_recall": false_positive_recall,
        "candidate_precision": candidate_precision,
        "mean_rule_coverage": mean_rule_coverage,
        "by_track_accuracy": track_accuracy,
        "results": results,
    }
