"""Minimal learned scoring model using logistic regression on labeled candidates.

This module trains and evaluates a logistic regression classifier on the
labeled candidate dataset.  It is a local scheduling/calibration tool only.

IMPORTANT: A logistic regression trained on 10 synthetic labeled candidates
is NOT a validated or production-ready scoring model.  It must not be used
for external submission decisions or claimed as a scientific result.  It is
a development scaffold only.

Production use requires:
  1. Admitted real labeled datasets with reproducible review evidence
  2. Sufficient labeled examples (> 100 per class minimum)
  3. Independent train/validation/test splits
  4. Independent-method reproduction of the model and its use
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

LEARNED_MODEL_DISCLAIMER = (
    "Learned scoring model outputs are local development scaffolds only. "
    "A model trained on synthetic labeled data does not constitute a validated "
    "scoring model, does not authorize external submission, and does not "
    "constitute a detection claim or scientific result. "
    "Real production use requires admitted real labels and independent-method "
    "citizen-science review."
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
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score
        from sklearn.preprocessing import StandardScaler
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
            "Admitted real labels (>100 examples per class) with reproducible review",
            "Independent train/validation/test splits",
            "Independent-method reproduction of model methodology",
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


# ---------------------------------------------------------------------------
# Setigen synthetic v1 dataset training
# Follows Ma et al. 2023 (Nature Astronomy) methodology.
# ---------------------------------------------------------------------------

import json as _json  # noqa: E402

SYNTHETIC_DATASET_V1_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests" / "fixtures" / "labeled_candidates_synthetic_v1.json"
)

SYNTHETIC_DATASET_METHODOLOGY = (
    "Follows Ma et al. 2023 (Nature Astronomy): synthetic signal injection "
    "into realistic noise with known ground-truth labels via setigen "
    "(Brzycki & Siemion 2022, ascl:2202.003). "
    "600 examples across 4 classes (ETI-like/RFI/noise/known_object). "
    "This is NOT equivalent to expert-labeled real observations."
)

SYNTHETIC_DATASET_DISCLAIMER = (
    "LEARNED MODEL SCORES ARE NOT DETECTION PROBABILITIES. "
    "Scores are local triage aids trained on synthetic data only. "
    "No model output authorizes external submission or constitutes a detection claim. "
    "Independent citizen-science review is required before any action."
)

_LABEL_MAP = {
    "follow_up": 0,
    "false_positive": 1,
    "insufficient_evidence": 2,
    "known_object": 3,
}
_LABEL_NAMES = ["follow_up", "false_positive", "insufficient_evidence", "known_object"]


def _load_synthetic_v1(dataset_path: Path) -> tuple[list[list[float]], list[int]]:
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Synthetic training dataset not found: {dataset_path}. "
            "Run: python scripts/generate_synthetic_training_data.py"
        )
    with dataset_path.open() as fh:
        data = _json.load(fh)
    X: list[list[float]] = []
    y: list[int] = []
    for entry in data["entries"]:
        features = entry["features"]
        row = [float(features[col]) for col in FEATURE_COLUMNS]
        X.append(row)
        y.append(_LABEL_MAP[entry["label"]])
    return X, y


def train_on_synthetic_v1(
    dataset_path: Path | None = None,
    *,
    test_fraction: float = 0.20,
    max_iter: int = 1000,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train logistic regression on the synthetic v1 dataset; report test accuracy."""
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import classification_report
        from sklearn.model_selection import train_test_split
    except ImportError as exc:
        raise ImportError(
            "scikit-learn is required. Install with: pip install 'scikit-learn>=1.4'"
        ) from exc

    path = dataset_path or SYNTHETIC_DATASET_V1_PATH
    X, y = _load_synthetic_v1(path)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_fraction, random_state=random_state, stratify=y,
    )

    clf = LogisticRegression(max_iter=max_iter, random_state=random_state)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    test_accuracy = float(
        sum(a == b for a, b in zip(y_test, y_pred, strict=True)) / len(y_test)
    )

    report = classification_report(
        y_test, y_pred, target_names=_LABEL_NAMES, output_dict=True
    )

    return {
        "disclaimer": SYNTHETIC_DATASET_DISCLAIMER,
        "methodology": SYNTHETIC_DATASET_METHODOLOGY,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "test_accuracy": round(test_accuracy, 4),
        "classification_report": report,
        "feature_columns": FEATURE_COLUMNS,
        "label_names": _LABEL_NAMES,
    }


def synthetic_v1_training_summary(
    dataset_path: Path | None = None,
) -> dict[str, Any]:
    """CLI-facing wrapper for train_on_synthetic_v1."""
    path = dataset_path or SYNTHETIC_DATASET_V1_PATH
    if not path.exists():
        return {
            "ok": False,
            "disclaimer": SYNTHETIC_DATASET_DISCLAIMER,
            "error": f"Dataset not found: {path}",
            "methodology": SYNTHETIC_DATASET_METHODOLOGY,
        }
    try:
        result = train_on_synthetic_v1(dataset_path=path)
        return {"ok": True, "schema_version": "labeled_candidates_synthetic_v1", **result}
    except Exception as exc:
        return {
            "ok": False,
            "disclaimer": SYNTHETIC_DATASET_DISCLAIMER,
            "error": str(exc),
            "methodology": SYNTHETIC_DATASET_METHODOLOGY,
        }
