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
    ALL_BASELINE_RULES,
    BASELINE_MODEL_VERSION,
    RuleBasedBaselineClassifier,
)
from techno_search.schemas import candidate_from_mapping
from techno_search.scoring import score_candidate

BASELINE_PERFORMANCE_HISTORY_SCHEMA_VERSION = "baseline_performance_history_v1"

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

    rule_fire_counts: dict[str, int] = {rule: 0 for rule in ALL_BASELINE_RULES}
    for r in results:
        for rule in r["rule_trace"]:
            if rule in rule_fire_counts:
                rule_fire_counts[rule] += 1
    rule_fire_rates = {
        rule: (count / total if total > 0 else 0.0)
        for rule, count in rule_fire_counts.items()
    }

    misclassified = [
        {
            "candidate_id": r["candidate_id"],
            "track": r["track"],
            "expected_pathway": r["expected_pathway"],
            "predicted_pathway": r["predicted_pathway"],
            "rule_trace": r["rule_trace"],
        }
        for r in results
        if not r["match"]
    ]

    # --- confusion matrix ---
    all_pathways = sorted(
        {r["expected_pathway"] for r in results}
        | {r["predicted_pathway"] for r in results}
    )
    confusion: dict[str, dict[str, int]] = {
        expected: {predicted: 0 for predicted in all_pathways}
        for expected in all_pathways
    }
    for r in results:
        confusion[r["expected_pathway"]][r["predicted_pathway"]] += 1

    per_pathway_precision: dict[str, float] = {}
    per_pathway_recall: dict[str, float] = {}
    per_pathway_f1: dict[str, float] = {}
    for pw in all_pathways:
        tp = confusion[pw][pw]
        fp = sum(confusion[other][pw] for other in all_pathways if other != pw)
        fn = sum(confusion[pw][other] for other in all_pathways if other != pw)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        per_pathway_precision[pw] = prec
        per_pathway_recall[pw] = rec
        per_pathway_f1[pw] = f1

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
        "rule_fire_rates": rule_fire_rates,
        "misclassified": misclassified,
        "misclassified_count": len(misclassified),
        "confusion_matrix": confusion,
        "per_pathway_precision": per_pathway_precision,
        "per_pathway_recall": per_pathway_recall,
        "per_pathway_f1": per_pathway_f1,
        "results": results,
    }


def _default_performance_history_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "baseline_performance_history.json"
    )


def baseline_performance_history_summary(
    history_path: Path | None = None,
) -> dict[str, Any]:
    """Summarise the append-only baseline performance history fixture."""
    path = history_path or _default_performance_history_path()
    if not path.exists():
        return {
            "schema_version": BASELINE_PERFORMANCE_HISTORY_SCHEMA_VERSION,
            "disclaimer": BASELINE_EVAL_DISCLAIMER,
            "snapshot_count": 0,
            "snapshots": [],
            "latest_accuracy": None,
        }
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    snapshots = data.get("snapshots", [])
    latest = snapshots[-1] if snapshots else {}
    return {
        "schema_version": BASELINE_PERFORMANCE_HISTORY_SCHEMA_VERSION,
        "disclaimer": BASELINE_EVAL_DISCLAIMER,
        "snapshot_count": len(snapshots),
        "snapshots": snapshots,
        "latest_accuracy": latest.get("pathway_accuracy"),
        "latest_model_version": latest.get("model_version"),
        "latest_snapshot_date": latest.get("snapshot_date"),
    }


def score_determinism_check(
    candidate_path: Path,
    runs: int = 3,
) -> dict[str, Any]:
    """Run score_candidate on the same input N times and assert identical outputs.

    Returns deterministic=True when all runs produce the same posterior, scores,
    and recommended_pathway. This is a local diagnostic only — it does not
    validate calibration quality or real-observation performance.
    """
    with candidate_path.open(encoding="utf-8") as handle:
        candidate_dict = json.load(handle)

    run_results: list[dict[str, Any]] = []
    for _ in range(runs):
        with suppress(Exception):
            candidate = candidate_from_mapping(candidate_dict)
            scored = score_candidate(candidate)
            packet = scored.as_dict()
            run_results.append(
                {
                    "posterior": packet.get("posterior", {}),
                    "scores": packet.get("scores", {}),
                    "recommended_pathway": packet.get("recommended_pathway", ""),
                }
            )

    if len(run_results) < runs:
        return {
            "schema_version": "score_determinism_v0",
            "disclaimer": BASELINE_EVAL_DISCLAIMER,
            "candidate_path": str(candidate_path),
            "runs_requested": runs,
            "runs_completed": len(run_results),
            "deterministic": False,
            "differing_fields": ["scoring_failed"],
        }

    differing: list[str] = []
    ref = run_results[0]
    for field in ("posterior", "scores", "recommended_pathway"):
        if any(r[field] != ref[field] for r in run_results[1:]):
            differing.append(field)

    return {
        "schema_version": "score_determinism_v0",
        "disclaimer": BASELINE_EVAL_DISCLAIMER,
        "candidate_path": str(candidate_path),
        "runs_requested": runs,
        "runs_completed": len(run_results),
        "deterministic": len(differing) == 0,
        "differing_fields": differing,
    }


def baseline_pathway_drift_summary(
    example_candidates_dir: Path | None = None,
) -> dict[str, Any]:
    """Compare scoring-model recommended_pathway vs baseline predicted_pathway.

    Returns drift_cases for any disagreements and a drift_count.
    Zero drift means the baseline faithfully mirrors the scoring model on all
    committed example candidates.
    """
    examples_dir = example_candidates_dir or _default_example_candidates_dir()
    classifier = RuleBasedBaselineClassifier()
    drift_cases: list[dict[str, Any]] = []
    checked = 0

    if examples_dir.exists():
        for candidate_path in sorted(examples_dir.glob("*.json")):
            with candidate_path.open(encoding="utf-8") as handle:
                candidate_dict = json.load(handle)
            with suppress(Exception):
                candidate = candidate_from_mapping(candidate_dict)
                scored = score_candidate(candidate)
                packet = scored.as_dict()
                result = classifier.predict(packet)
                scoring_pathway = scored.recommended_pathway.value
                baseline_pathway = result.predicted_pathway
                checked += 1
                if scoring_pathway != baseline_pathway:
                    drift_cases.append(
                        {
                            "candidate_id": candidate.candidate_id,
                            "track": candidate.track.value,
                            "scoring_model_pathway": scoring_pathway,
                            "baseline_pathway": baseline_pathway,
                            "rule_trace": result.rule_trace,
                        }
                    )

    return {
        "schema_version": "baseline_drift_v0",
        "disclaimer": BASELINE_EVAL_DISCLAIMER,
        "candidates_checked": checked,
        "drift_count": len(drift_cases),
        "drift_cases": drift_cases,
        "zero_drift": len(drift_cases) == 0,
    }


def classifier_rule_coverage_summary(
    calibration_fixture_path: Path | None = None,
    example_candidates_dir: Path | None = None,
) -> dict[str, Any]:
    """Report which baseline classifier rules fire across all evaluation cases.

    Returns per-rule fire counts and a coverage fraction (fraction of rules that
    fire at least once). This is a local diagnostic only — not a claim about
    real-observation coverage or detection performance.
    """

    eval_result = evaluate_baseline(calibration_fixture_path, example_candidates_dir)
    rule_fire_rates: dict[str, float] = eval_result.get("rule_fire_rates", {})
    total_cases = int(eval_result.get("total_cases", 0))

    rules_fired_at_least_once = sorted(
        rule for rule, rate in rule_fire_rates.items() if rate > 0.0
    )
    rules_never_fired = sorted(
        rule for rule, rate in rule_fire_rates.items() if rate == 0.0
    )
    total_rules = len(ALL_BASELINE_RULES)
    fired_count = len(rules_fired_at_least_once)
    coverage_fraction = fired_count / total_rules if total_rules > 0 else 0.0

    return {
        "schema_version": "classifier_rule_coverage_v0",
        "disclaimer": BASELINE_EVAL_DISCLAIMER,
        "total_rules": total_rules,
        "rules_fired_count": fired_count,
        "rules_never_fired_count": len(rules_never_fired),
        "coverage_fraction": round(coverage_fraction, 4),
        "evaluation_case_count": total_cases,
        "rules_fired_at_least_once": rules_fired_at_least_once,
        "rules_never_fired": rules_never_fired,
        "rule_fire_rates": dict(sorted(rule_fire_rates.items())),
    }


def _default_route_coverage_fixture_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "route_coverage_fixtures.json"
    )


def route_coverage_summary(
    calibration_fixture_path: Path | None = None,
    example_candidates_dir: Path | None = None,
    route_coverage_fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Check that all Pathway enum values have calibration fixture coverage."""

    from techno_search.schemas import Pathway

    eval_result = evaluate_baseline(calibration_fixture_path, example_candidates_dir)
    results: list[dict[str, Any]] = list(eval_result.get("results", []))
    all_pathways = {p.value for p in Pathway}

    rc_path = route_coverage_fixture_path or _default_route_coverage_fixture_path()
    if rc_path.exists():
        classifier = RuleBasedBaselineClassifier()
        with rc_path.open(encoding="utf-8") as handle:
            rc_data = json.load(handle)
        for fixture in rc_data.get("fixtures", []):
            candidate_dict = fixture.get("candidate", {})
            if not candidate_dict:
                continue
            with suppress(Exception):
                route_result = _score_and_predict(candidate_dict, classifier)
                declared_pathway = str(
                    fixture.get("expected_pathway", route_result["expected_pathway"])
                )
                if declared_pathway in all_pathways:
                    route_result["scoring_model_pathway"] = route_result[
                        "expected_pathway"
                    ]
                    route_result["expected_pathway"] = declared_pathway
                    route_result["match"] = (
                        route_result["predicted_pathway"] == declared_pathway
                    )
                results.append(route_result)

    covered_pathways = {r["expected_pathway"] for r in results}
    uncovered_pathways = sorted(all_pathways - covered_pathways)

    by_pathway: dict[str, int] = {}
    for r in results:
        pw = r["expected_pathway"]
        by_pathway[pw] = by_pathway.get(pw, 0) + 1

    return {
        "schema_version": "route_coverage_v1",
        "disclaimer": BASELINE_EVAL_DISCLAIMER,
        "total_pathway_values": len(all_pathways),
        "covered_pathway_count": len(covered_pathways),
        "uncovered_pathway_count": len(uncovered_pathways),
        "uncovered_pathways": uncovered_pathways,
        "covered_pathways": sorted(covered_pathways),
        "by_pathway_case_count": dict(sorted(by_pathway.items())),
        "full_coverage": len(uncovered_pathways) == 0,
    }
