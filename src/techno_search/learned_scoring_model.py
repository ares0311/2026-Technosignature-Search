"""Minimal learned scoring model using logistic regression on labeled candidates.

This module trains and evaluates a logistic regression classifier on the
labeled candidate dataset.  It is a local scheduling/calibration tool only.

IMPORTANT: A logistic regression trained on 10 synthetic labeled candidates
is NOT a validated or production-ready scoring model.  It must not be used
for external submission decisions or claimed as a scientific result.  It is
a development scaffold only.

Production use requires:
  1. Real labeled dataset (not synthetic) approved by domain expert
  2. Sufficient labeled examples (> 100 per class minimum)
  3. Independent train/validation/test splits
  4. External peer review of the model and its use
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

LEARNED_MODEL_DISCLAIMER = (
    "Learned scoring model outputs are local development scaffolds only. "
    "A model trained on synthetic labeled data does not constitute a validated "
    "scoring model, does not authorize external submission, and does not "
    "constitute a detection claim or scientific result. "
    "Real production use requires a real labeled dataset approved by a domain expert."
)

# Labels that map to 'positive' (technosignature interest) class
_POSITIVE_LABELS = {"follow_up", "high_interest"}
# Labels that map to 'negative' (false positive / no interest) class
_NEGATIVE_LABELS = {"false_positive", "known_object", "insufficient_evidence"}

FEATURE_COLUMNS = [
    "snr",
    "drift_rate_hz_per_sec",
    "on_target_presence_score",
    "off_target_presence_score",
    "rfi_band_overlap_score",
    "frequency_persistence_score",
    "nearby_target_recurrence_score",
    "instrumental_artifact_score",
    "metadata_completeness_score",
    "data_quality_score",
    "provenance_completeness_score",
]


def _load_labeled_dataset(path: Path | None = None) -> list[dict[str, Any]]:
    """Load the labeled candidate dataset from the fixture or a custom path."""
    import json

    if path is None:
        path = (
            Path(__file__).resolve().parents[2]
            / "tests"
            / "fixtures"
            / "labeled_candidates.json"
        )
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return list(data.get("entries", []))


def _extract_features(entry: dict[str, Any]) -> list[float] | None:
    """Extract normalized feature vector from a labeled candidate entry."""
    candidate = entry.get("candidate", {})
    features = candidate.get("features", {})
    row: list[float] = []
    for col in FEATURE_COLUMNS:
        val = features.get(col)
        if val is None:
            return None
        try:
            row.append(float(val))
        except (TypeError, ValueError):
            return None
    return row


def _label_to_binary(label: str) -> int | None:
    if label in _POSITIVE_LABELS:
        return 1
    if label in _NEGATIVE_LABELS:
        return 0
    return None


def train_logistic_regression(
    labeled_dataset_path: Path | None = None,
    *,
    max_iter: int = 1000,
) -> dict[str, Any]:
    """Train a logistic regression on the labeled candidate dataset.

    Returns a summary dict including the model coefficients, training accuracy,
    and a strong disclaimer that this is a development scaffold only.

    Requires scikit-learn (pip install scikit-learn).  If not available,
    returns a stub result with an explanation.
    """
    try:
        from sklearn.linear_model import LogisticRegression  # type: ignore[import-not-found]
        from sklearn.metrics import accuracy_score  # type: ignore[import-not-found]
        from sklearn.preprocessing import StandardScaler  # type: ignore[import-not-found]
    except ImportError:
        return {
            "disclaimer": LEARNED_MODEL_DISCLAIMER,
            "ok": False,
            "error": (
                "scikit-learn is not installed. "
                "Run: pip install scikit-learn"
            ),
            "trained": False,
        }

    entries = _load_labeled_dataset(labeled_dataset_path)

    X: list[list[float]] = []
    y: list[int] = []
    skipped: list[str] = []

    for entry in entries:
        features = _extract_features(entry)
        label = _label_to_binary(str(entry.get("label", "")))
        if features is None or label is None:
            skipped.append(str(entry.get("entry_id", "?")))
            continue
        X.append(features)
        y.append(label)

    if len(X) < 4:
        return {
            "disclaimer": LEARNED_MODEL_DISCLAIMER,
            "ok": False,
            "error": (
                f"Only {len(X)} labeled examples available. "
                "Need at least 4 for a minimal train/test split. "
                "A real dataset with 100+ labeled examples per class is required."
            ),
            "trained": False,
            "skipped_entries": skipped,
        }

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=max_iter, random_state=42)
    model.fit(X_scaled, y)

    y_pred = model.predict(X_scaled)
    train_accuracy = float(accuracy_score(y, y_pred))

    positive_count = sum(y)
    negative_count = len(y) - positive_count

    return {
        "disclaimer": LEARNED_MODEL_DISCLAIMER,
        "ok": True,
        "trained": True,
        "training_sample_count": len(X),
        "positive_class_count": positive_count,
        "negative_class_count": negative_count,
        "skipped_entries": skipped,
        "feature_columns": FEATURE_COLUMNS,
        "train_accuracy": round(train_accuracy, 4),
        "coefficients": {
            col: round(float(coef), 6)
            for col, coef in zip(FEATURE_COLUMNS, model.coef_[0], strict=False)
        },
        "intercept": round(float(model.intercept_[0]), 6),
        "scaler_mean": [round(float(m), 6) for m in scaler.mean_],
        "scaler_scale": [round(float(s), 6) for s in scaler.scale_],
        "warning": (
            "This model is trained on synthetic data only. "
            "Train accuracy on the same data used for training is not a valid "
            "performance estimate. Real performance requires a held-out test set."
        ),
        "production_requirements": [
            "Real labeled dataset (>100 examples per class) approved by domain expert",
            "Independent train/validation/test splits",
            "External peer review of model methodology",
            "Operator approval before any use in candidate triage",
        ],
    }


def learned_model_summary(
    labeled_dataset_path: Path | None = None,
) -> dict[str, Any]:
    """Return a training summary for the CLI validate-all gate."""
    result = train_logistic_regression(labeled_dataset_path)
    return {
        "disclaimer": LEARNED_MODEL_DISCLAIMER,
        "ok": result.get("ok", False),
        "trained": result.get("trained", False),
        "training_sample_count": result.get("training_sample_count", 0),
        "train_accuracy": result.get("train_accuracy"),
        "positive_class_count": result.get("positive_class_count", 0),
        "negative_class_count": result.get("negative_class_count", 0),
        "error": result.get("error"),
        "warning": result.get("warning"),
    }
