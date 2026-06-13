"""Tests for learned scoring model v1 trained on real HIP99427 labels.

Closes Tier 2 gap: Learned scoring model (replace rule-based baseline).
Model: logistic regression, 3-fold CV, 124 real GBT/HIP99427 citizen-science
labels (hip99427_citizen_science_labels_v1.json).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.learned_scoring_model import (
    REAL_LABEL_FEATURE_COLUMNS,
    REAL_LABELS_MODEL_DISCLAIMER,
    real_labels_model_summary,
    train_on_real_labels,
)

_REAL_LABEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "real_labeled"
    / "hip99427_citizen_science_labels_v1.json"
)


class TestTrainOnRealLabels:
    def test_real_labels_file_exists(self) -> None:
        assert _REAL_LABEL_PATH.exists(), f"Real labels file missing: {_REAL_LABEL_PATH}"

    def test_train_returns_ok(self) -> None:
        result = train_on_real_labels()
        assert result["ok"] is True
        assert result["trained"] is True

    def test_train_uses_all_124_entries(self) -> None:
        result = train_on_real_labels()
        assert int(result["total_entries"]) == 124
        assert int(result["usable_entries"]) == 124
        assert int(result["skipped_entries"]) == 0

    def test_cv_accuracy_above_gate(self) -> None:
        result = train_on_real_labels()
        cv_acc = float(result["cv_accuracy"])
        assert cv_acc >= 0.70, (
            f"Learned model v1 CV accuracy {cv_acc:.4f} below gate 0.70"
        )

    def test_cv_accuracy_above_rule_based_baseline(self) -> None:
        result = train_on_real_labels()
        cv_acc = float(result["cv_accuracy"])
        assert cv_acc >= 0.77, (
            f"Learned model v1 CV accuracy {cv_acc:.4f} below rule-based baseline 0.77"
        )

    def test_train_accuracy_is_float(self) -> None:
        result = train_on_real_labels()
        assert isinstance(result["train_accuracy"], float)

    def test_label_distribution_has_three_classes(self) -> None:
        result = train_on_real_labels()
        dist = result["label_distribution"]
        assert isinstance(dist, dict)
        assert len(dist) == 3

    def test_classes_match_pathways(self) -> None:
        result = train_on_real_labels()
        classes = set(result["classes"])
        assert "candidate_review_packet" in classes
        assert "do_not_submit_false_positive" in classes
        assert "human_review_queue" in classes

    def test_schema_version(self) -> None:
        result = train_on_real_labels()
        assert result["schema_version"] == "learned_scoring_model_v1"

    def test_dataset_field(self) -> None:
        result = train_on_real_labels()
        assert result["dataset"] == "hip99427_citizen_science_labels_v1"

    def test_feature_columns_present(self) -> None:
        result = train_on_real_labels()
        assert result["feature_columns"] == REAL_LABEL_FEATURE_COLUMNS

    def test_cv_folds_default(self) -> None:
        result = train_on_real_labels()
        assert result["cv_folds"] == 3

    def test_cv_accuracy_std_is_finite(self) -> None:
        result = train_on_real_labels()
        std = float(result["cv_accuracy_std"])
        assert 0.0 <= std <= 0.5

    def test_disclaimer_is_conservative(self) -> None:
        assert "does not constitute a detection claim" in REAL_LABELS_MODEL_DISCLAIMER
        assert "local scheduling aids only" in REAL_LABELS_MODEL_DISCLAIMER
        assert "does not authorize external submission" in REAL_LABELS_MODEL_DISCLAIMER

    def test_production_requirements_present(self) -> None:
        result = train_on_real_labels()
        reqs = result["production_requirements"]
        assert isinstance(reqs, list)
        assert len(reqs) >= 1


class TestRealLabelsModelSummary:
    def test_summary_ok(self) -> None:
        result = real_labels_model_summary()
        assert result["ok"] is True

    def test_summary_has_cv_accuracy(self) -> None:
        result = real_labels_model_summary()
        assert "cv_accuracy" in result
        assert isinstance(result["cv_accuracy"], float)

    def test_summary_has_disclaimer(self) -> None:
        result = real_labels_model_summary()
        assert "disclaimer" in result
        assert "detection claim" in str(result["disclaimer"])


class TestRealLabelsModelCLI:
    def test_cli_returns_json(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "techno_search.cli", "real-labels-model-summary"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert data["ok"] is True
        assert data["trained"] is True

    def test_cli_cv_accuracy_field(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "techno_search.cli", "real-labels-model-summary"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        data = json.loads(proc.stdout)
        assert "cv_accuracy" in data
        assert float(data["cv_accuracy"]) >= 0.70

    def test_validate_all_includes_learned_model_fields(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "techno_search.cli", "validate-all"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        data = json.loads(proc.stdout)
        assert "learned_scoring_model_v1_trained" in data
        assert "learned_scoring_model_v1_cv_accuracy" in data
        assert data["learned_scoring_model_v1_trained"] is True

    def test_validate_all_gate_passes(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "techno_search.cli", "validate-all"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        data = json.loads(proc.stdout)
        assert data.get("ok") is True

    def test_validation_summary_includes_learned_model(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "techno_search.cli", "validation-summary"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        data = json.loads(proc.stdout)
        assert "learned_scoring_model_v1_trained" in data
        assert "learned_scoring_model_v1_cv_accuracy" in data
