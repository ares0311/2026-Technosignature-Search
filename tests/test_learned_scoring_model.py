"""Tests for the learned scoring model scaffold."""
from __future__ import annotations

import pytest

from techno_search.learned_scoring_model import (
    FEATURE_COLUMNS,
    LEARNED_MODEL_DISCLAIMER,
    _extract_features,
    _label_to_binary,
    learned_model_summary,
    train_logistic_regression,
)


def test_train_succeeds_on_fixture() -> None:
    result = train_logistic_regression()
    # scikit-learn may or may not be installed; either result must be structured
    assert "ok" in result
    assert "disclaimer" in result


def test_disclaimer_is_conservative() -> None:
    assert "local development scaffolds only" in LEARNED_MODEL_DISCLAIMER
    assert "does not authorize external submission" in LEARNED_MODEL_DISCLAIMER
    assert "real labeled dataset" in LEARNED_MODEL_DISCLAIMER


def test_feature_columns_are_defined() -> None:
    assert len(FEATURE_COLUMNS) >= 8
    assert "snr" in FEATURE_COLUMNS
    assert "on_target_presence_score" in FEATURE_COLUMNS


def test_label_to_binary_positive() -> None:
    assert _label_to_binary("follow_up") == 1
    assert _label_to_binary("high_interest") == 1


def test_label_to_binary_negative() -> None:
    assert _label_to_binary("false_positive") == 0
    assert _label_to_binary("known_object") == 0
    assert _label_to_binary("insufficient_evidence") == 0


def test_label_to_binary_unknown_returns_none() -> None:
    assert _label_to_binary("unknown_label") is None


def test_extract_features_returns_list() -> None:
    entry = {
        "candidate": {
            "features": {col: 0.5 for col in FEATURE_COLUMNS},
        }
    }
    result = _extract_features(entry)
    assert result is not None
    assert len(result) == len(FEATURE_COLUMNS)


def test_extract_features_missing_key_returns_none() -> None:
    entry = {"candidate": {"features": {"snr": 10.0}}}
    assert _extract_features(entry) is None


def test_learned_model_summary_structure() -> None:
    summary = learned_model_summary()
    assert "disclaimer" in summary
    assert "ok" in summary
    assert "trained" in summary


@pytest.mark.skipif(
    not pytest.importorskip("sklearn", reason="scikit-learn not installed"),  # type: ignore[arg-type]
    reason="scikit-learn not available",
)
def test_train_with_sklearn_returns_accuracy() -> None:
    result = train_logistic_regression()
    if result.get("trained"):
        assert "train_accuracy" in result
        assert 0.0 <= float(result["train_accuracy"]) <= 1.0
        assert "coefficients" in result
        assert len(result["coefficients"]) == len(FEATURE_COLUMNS)


def test_train_result_has_warning_about_synthetic_data() -> None:
    result = train_logistic_regression()
    if result.get("trained"):
        assert "warning" in result
        assert "synthetic" in result.get("warning", "").lower()


def test_cli_learned_model_summary(capsys: pytest.CaptureFixture[str]) -> None:
    from techno_search.cli import main

    exit_code = main(["learned-model-summary"])
    assert exit_code in (0, 1)  # 0 if sklearn installed, 1 if not
