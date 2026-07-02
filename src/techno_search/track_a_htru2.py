"""Track A known-explanation baseline: HTRU2 pulsar vs RFI/noise classifier.

Implements the first milestone from docs/technosignature_datasets_agent_brief.md:
a small, auditable supervised classifier distinguishing real pulsar candidates
from RFI/noise on the HTRU2 dataset (Lyon et al., UCI ML Repository id=372,
CC BY 4.0). This is Track A only — a known-explanation classifier. It is not a
technosignature detector and makes no claim about candidate anomaly status.

Acquisition requires network access to archive-beta.ics.uci.edu via the
`ucimlrepo` package, per the brief's verified access method. This module does
not fabricate an alternate source or URL if that access method fails.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from techno_search.track_a_data_guard import (
    AcquisitionManifestRecord,
    append_acquisition_manifest,
    check_disk_budget_or_raise,
    log_progress,
)

HTRU2_SOURCE_URL = "https://archive-beta.ics.uci.edu/dataset/372/htru2"
HTRU2_EXPECTED_ROW_COUNT = 17898
HTRU2_REQUIRED_FEATURE_COLUMNS = (
    "Profile_mean",
    "Profile_stdev",
    "Profile_skewness",
    "Profile_kurtosis",
    "DM_mean",
    "DM_stdev",
    "DM_skewness",
    "DM_kurtosis",
)
HTRU2_LABEL_COLUMN = "class"

TRACK_A_HTRU2_TRAINING_SCHEMA_VERSION = "track_a_htru2_baseline_v1"

TRACK_A_HTRU2_DISCLAIMER = (
    "This is a Track A known-explanation classifier trained on the real, "
    "publicly labeled HTRU2 pulsar candidate dataset (Lyon et al., CC BY 4.0). "
    "It distinguishes real pulsars from RFI/noise. It is not a technosignature "
    "detector, does not evaluate anomaly/candidate status, and does not "
    "authorize any detection, discovery, or external-submission claim."
)


def default_htru2_cache_dir(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parents[2]
    return root / "data_cache" / "raw" / "htru2"


def acquire_htru2(
    *,
    output_dir: Path | None = None,
    manifest_path: Path | None = None,
    project_root: Path | None = None,
) -> AcquisitionManifestRecord:
    """Download HTRU2 via `ucimlrepo` and write normalized parquet + manifest entry.

    Raises RuntimeError if the `ucimlrepo` package is not installed, if the
    disk budget guard would be exceeded, or if the downloaded row count does
    not match the documented 17,898-row dataset.
    """

    try:
        from ucimlrepo import fetch_ucirepo
    except ImportError as exc:
        msg = (
            "ucimlrepo is required to acquire HTRU2. Install with "
            "`.venv/bin/pip install ucimlrepo pyarrow` before running acquisition."
        )
        raise RuntimeError(msg) from exc

    root = project_root or Path(__file__).resolve().parents[2]
    out_dir = output_dir or default_htru2_cache_dir(root)
    check_disk_budget_or_raise(
        project_root=root,
        additional_expected_bytes=5 * 1024 * 1024,
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    log_progress(f"[START] Downloading HTRU2 via ucimlrepo (id=372) -> {out_dir}")
    htru2 = fetch_ucirepo(id=372)
    features = htru2.data.features
    labels = htru2.data.targets
    log_progress(f"[INFO] Downloaded {len(features)} rows, verifying row count")

    if len(features) != HTRU2_EXPECTED_ROW_COUNT:
        msg = (
            f"HTRU2 row count mismatch: expected {HTRU2_EXPECTED_ROW_COUNT}, "
            f"got {len(features)}. Refusing to write an unverified dataset."
        )
        raise RuntimeError(msg)

    label_col = HTRU2_LABEL_COLUMN if HTRU2_LABEL_COLUMN in labels.columns else labels.columns[0]

    features_path = out_dir / "htru2_features.parquet"
    labels_path = out_dir / "htru2_labels.parquet"
    features.to_parquet(features_path, index=False)
    labels.rename(columns={label_col: HTRU2_LABEL_COLUMN}).to_parquet(labels_path, index=False)
    log_progress(f"[OK] Wrote {len(features)} verified rows -> {features_path}")

    record = AcquisitionManifestRecord(
        source_name="htru2",
        source_url=HTRU2_SOURCE_URL,
        access_method="ucimlrepo.fetch_ucirepo(id=372)",
        downloaded_at_utc=datetime.now(UTC).isoformat(),
        local_path=str(features_path),
        file_size_bytes=features_path.stat().st_size + labels_path.stat().st_size,
        row_count=len(features),
        auth_required=False,
        license_or_terms="CC BY 4.0",
    )
    manifest = manifest_path or (root / "artifacts" / "manifests" / "data_manifest.jsonl")
    append_acquisition_manifest(record, manifest)
    return record


@dataclass(frozen=True)
class TrackAHtru2Metrics:
    """Held-out evaluation metrics for one candidate baseline model."""

    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: list[list[int]]
    train_row_count: int
    test_row_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "confusion_matrix": self.confusion_matrix,
            "train_row_count": self.train_row_count,
            "test_row_count": self.test_row_count,
        }


_CANDIDATE_MODEL_NAMES = ("logistic_regression", "random_forest", "hist_gradient_boosting")


def _build_model(name: str, *, random_state: int) -> Any:
    if name == "logistic_regression":
        from sklearn.linear_model import LogisticRegression

        return LogisticRegression(max_iter=1000, random_state=random_state)
    if name == "random_forest":
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(n_estimators=200, random_state=random_state, n_jobs=-1)
    if name == "hist_gradient_boosting":
        from sklearn.ensemble import HistGradientBoostingClassifier

        return HistGradientBoostingClassifier(random_state=random_state)
    msg = f"Unknown Track A baseline model name: {name!r}"
    raise ValueError(msg)


def train_htru2_baseline(
    *,
    features_path: Path,
    labels_path: Path,
    model_out_dir: Path,
    metrics_out_path: Path,
    schema_out_path: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train and evaluate small auditable baseline models on HTRU2.

    Trains LogisticRegression, RandomForestClassifier, and
    HistGradientBoostingClassifier (per the brief's Phase 1 recommendation),
    evaluates held-out precision/recall/F1, and persists the best-F1 model
    plus a metrics/schema record. Returns the full metrics summary.
    """

    import joblib
    import pandas as pd
    from sklearn.metrics import confusion_matrix as sk_confusion_matrix
    from sklearn.model_selection import train_test_split

    features = pd.read_parquet(features_path)
    labels_df = pd.read_parquet(labels_path)
    missing_cols = [c for c in HTRU2_REQUIRED_FEATURE_COLUMNS if c not in features.columns]
    if missing_cols:
        msg = f"HTRU2 features missing required columns: {missing_cols}"
        raise ValueError(msg)
    if HTRU2_LABEL_COLUMN not in labels_df.columns:
        msg = f"HTRU2 labels missing required column: {HTRU2_LABEL_COLUMN!r}"
        raise ValueError(msg)

    x = features[list(HTRU2_REQUIRED_FEATURE_COLUMNS)]
    y = labels_df[HTRU2_LABEL_COLUMN]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    results: dict[str, TrackAHtru2Metrics] = {}
    fitted_models: dict[str, Any] = {}
    for model_name in _CANDIDATE_MODEL_NAMES:
        log_progress(f"[START] Training {model_name} on {len(x_train)} rows")
        model = _build_model(model_name, random_state=random_state)
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        log_progress(f"[OK] {model_name} evaluated on {len(x_test)} held-out rows")

        from sklearn.metrics import (
            accuracy_score,
            f1_score,
            precision_score,
            recall_score,
        )

        cm = sk_confusion_matrix(y_test, predictions).tolist()
        results[model_name] = TrackAHtru2Metrics(
            model_name=model_name,
            accuracy=float(accuracy_score(y_test, predictions)),
            precision=float(precision_score(y_test, predictions, zero_division=0)),
            recall=float(recall_score(y_test, predictions, zero_division=0)),
            f1=float(f1_score(y_test, predictions, zero_division=0)),
            confusion_matrix=cm,
            train_row_count=len(x_train),
            test_row_count=len(x_test),
        )
        fitted_models[model_name] = model

    best_model_name = max(results, key=lambda name: results[name].f1)
    best_model = fitted_models[best_model_name]

    model_out_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_out_dir / f"htru2_{best_model_name}.joblib"
    joblib.dump(best_model, model_path)

    summary = {
        "schema_version": TRACK_A_HTRU2_TRAINING_SCHEMA_VERSION,
        "disclaimer": TRACK_A_HTRU2_DISCLAIMER,
        "best_model_name": best_model_name,
        "best_model_path": str(model_path),
        "by_model": {name: metrics.as_dict() for name, metrics in results.items()},
        "feature_columns": list(HTRU2_REQUIRED_FEATURE_COLUMNS),
        "label_column": HTRU2_LABEL_COLUMN,
        "test_size": test_size,
        "random_state": random_state,
        "trained_at_utc": datetime.now(UTC).isoformat(),
    }

    metrics_out_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_out_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    schema = {
        "schema_version": TRACK_A_HTRU2_TRAINING_SCHEMA_VERSION,
        "feature_columns": list(HTRU2_REQUIRED_FEATURE_COLUMNS),
        "label_column": HTRU2_LABEL_COLUMN,
        "label_meaning": {"0": "rfi_or_noise", "1": "pulsar"},
    }
    schema_out_path.parent.mkdir(parents=True, exist_ok=True)
    schema_out_path.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")

    return summary
