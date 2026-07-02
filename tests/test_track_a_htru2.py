import json

import numpy as np
import pandas as pd
import pytest

from techno_search.track_a_htru2 import (
    HTRU2_LABEL_COLUMN,
    HTRU2_REQUIRED_FEATURE_COLUMNS,
    acquire_htru2,
    train_htru2_baseline,
)


def test_acquire_htru2_reports_missing_dependency_when_package_absent(
    tmp_path, monkeypatch
) -> None:
    import builtins

    real_import = builtins.__import__

    def _blocked_import(name, *args, **kwargs):
        if name == "ucimlrepo":
            raise ImportError("No module named 'ucimlrepo'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _blocked_import)

    with pytest.raises(RuntimeError, match="ucimlrepo is required"):
        acquire_htru2(project_root=tmp_path)


def _write_fixture_htru2_parquet(tmp_path):
    rng = np.random.default_rng(seed=42)
    n_per_class = 60
    pulsar_features = {
        col: rng.normal(loc=5.0, scale=1.0, size=n_per_class)
        for col in HTRU2_REQUIRED_FEATURE_COLUMNS
    }
    noise_features = {
        col: rng.normal(loc=-5.0, scale=1.0, size=n_per_class)
        for col in HTRU2_REQUIRED_FEATURE_COLUMNS
    }
    features = pd.DataFrame(
        {
            col: np.concatenate([pulsar_features[col], noise_features[col]])
            for col in HTRU2_REQUIRED_FEATURE_COLUMNS
        }
    )
    labels = pd.DataFrame(
        {HTRU2_LABEL_COLUMN: [1] * n_per_class + [0] * n_per_class}
    )

    features_path = tmp_path / "htru2_features.parquet"
    labels_path = tmp_path / "htru2_labels.parquet"
    features.to_parquet(features_path, index=False)
    labels.to_parquet(labels_path, index=False)
    return features_path, labels_path


def test_train_htru2_baseline_fits_and_persists_best_model(tmp_path) -> None:
    pytest.importorskip("pyarrow")
    features_path, labels_path = _write_fixture_htru2_parquet(tmp_path)

    summary = train_htru2_baseline(
        features_path=features_path,
        labels_path=labels_path,
        model_out_dir=tmp_path / "models",
        metrics_out_path=tmp_path / "metrics" / "htru2_baseline_metrics.json",
        schema_out_path=tmp_path / "schemas" / "htru2_schema.json",
    )

    assert summary["best_model_name"] in {
        "logistic_regression",
        "random_forest",
        "hist_gradient_boosting",
    }
    for metrics in summary["by_model"].values():
        assert 0.0 <= metrics["f1"] <= 1.0
        assert metrics["test_row_count"] > 0

    model_path = tmp_path / "models" / f"htru2_{summary['best_model_name']}.joblib"
    assert model_path.exists()

    metrics_path = tmp_path / "metrics" / "htru2_baseline_metrics.json"
    schema_path = tmp_path / "schemas" / "htru2_schema.json"
    assert metrics_path.exists()
    assert schema_path.exists()

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["feature_columns"] == list(HTRU2_REQUIRED_FEATURE_COLUMNS)
    assert schema["label_column"] == HTRU2_LABEL_COLUMN


def test_train_htru2_baseline_rejects_missing_feature_columns(tmp_path) -> None:
    pytest.importorskip("pyarrow")
    features = pd.DataFrame({"Profile_mean": [1.0, 2.0]})
    labels = pd.DataFrame({HTRU2_LABEL_COLUMN: [0, 1]})
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    features.to_parquet(features_path, index=False)
    labels.to_parquet(labels_path, index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        train_htru2_baseline(
            features_path=features_path,
            labels_path=labels_path,
            model_out_dir=tmp_path / "models",
            metrics_out_path=tmp_path / "metrics" / "m.json",
            schema_out_path=tmp_path / "schemas" / "s.json",
        )
