"""Tests for baseline confusion matrix and score determinism checker."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

from techno_search.baseline_eval import BASELINE_EVAL_DISCLAIMER, evaluate_baseline
from techno_search.cli import main

# ---------------------------------------------------------------------------
# Confusion matrix
# ---------------------------------------------------------------------------


def test_confusion_matrix_keys_present():
    result = evaluate_baseline()
    assert "confusion_matrix" in result
    assert "per_pathway_precision" in result
    assert "per_pathway_recall" in result
    assert "per_pathway_f1" in result


def test_confusion_matrix_pathways_consistent():
    result = evaluate_baseline()
    matrix = result["confusion_matrix"]
    precision = result["per_pathway_precision"]
    recall = result["per_pathway_recall"]
    f1 = result["per_pathway_f1"]
    assert set(matrix.keys()) == set(precision.keys()) == set(recall.keys()) == set(f1.keys())


def test_confusion_matrix_values_non_negative():
    result = evaluate_baseline()
    for row in result["confusion_matrix"].values():
        for count in row.values():
            assert count >= 0


def test_confusion_matrix_row_sums_match_total():
    result = evaluate_baseline()
    matrix = result["confusion_matrix"]
    total_from_matrix = sum(
        count for row in matrix.values() for count in row.values()
    )
    assert total_from_matrix == result["total_cases"]


def test_per_pathway_precision_in_range():
    result = evaluate_baseline()
    for pw, prec in result["per_pathway_precision"].items():
        assert 0.0 <= prec <= 1.0, f"Precision out of range for {pw}: {prec}"


def test_per_pathway_recall_in_range():
    result = evaluate_baseline()
    for pw, rec in result["per_pathway_recall"].items():
        assert 0.0 <= rec <= 1.0, f"Recall out of range for {pw}: {rec}"


def test_per_pathway_f1_in_range():
    result = evaluate_baseline()
    for pw, f1 in result["per_pathway_f1"].items():
        assert 0.0 <= f1 <= 1.0, f"F1 out of range for {pw}: {f1}"


def test_baseline_confusion_matrix_cli_exit_zero():
    out = StringIO()
    ret = main(["baseline-confusion-matrix-summary"], stdout=out)
    assert ret == 0


def test_baseline_confusion_matrix_cli_has_disclaimer():
    out = StringIO()
    main(["baseline-confusion-matrix-summary"], stdout=out)
    import json
    data = json.loads(out.getvalue())
    assert BASELINE_EVAL_DISCLAIMER in data["disclaimer"]


def test_baseline_confusion_matrix_cli_has_matrix():
    out = StringIO()
    main(["baseline-confusion-matrix-summary"], stdout=out)
    import json
    data = json.loads(out.getvalue())
    assert "confusion_matrix" in data
    assert "per_pathway_precision" in data
    assert "per_pathway_recall" in data
    assert "per_pathway_f1" in data


# ---------------------------------------------------------------------------
# Score determinism
# ---------------------------------------------------------------------------


def test_score_determinism_check_cli_exit_zero():
    out = StringIO()
    ret = main(["score-determinism-check"], stdout=out)
    assert ret == 0


def test_score_determinism_check_cli_all_deterministic():
    out = StringIO()
    main(["score-determinism-check"], stdout=out)
    import json
    data = json.loads(out.getvalue())
    assert data["all_deterministic"] is True


def test_score_determinism_check_cli_results_structure():
    out = StringIO()
    main(["score-determinism-check"], stdout=out)
    import json
    data = json.loads(out.getvalue())
    for result in data["results"]:
        assert "deterministic" in result
        assert "runs_requested" in result
        assert "runs_completed" in result
        assert "differing_fields" in result


def test_score_determinism_check_explicit_path(tmp_path):
    candidate_path = (
        Path(__file__).resolve().parent.parent / "examples" / "candidates"
        / "radio_clean_candidate.json"
    )
    out = StringIO()
    ret = main(["score-determinism-check", str(candidate_path), "--runs", "2"], stdout=out)
    assert ret == 0
    import json
    data = json.loads(out.getvalue())
    assert data["all_deterministic"] is True
    assert data["runs_per_candidate"] == 2
