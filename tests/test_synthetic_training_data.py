"""
Tests for the synthetic labeled training dataset and learned scoring model.

Validates:
- Fixture structure and completeness (600 entries, all 4 labels)
- Feature ranges and discriminativeness
- train_on_synthetic_v1 uses a proper test split and reports test accuracy
- Conservative disclaimer language
- CLI synthetic-training-summary command exits 0
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "labeled_candidates_synthetic_v1.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "labeled_candidates_synthetic_v1.schema.json"

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


@pytest.fixture(scope="module")
def dataset():
    assert FIXTURE_PATH.exists(), f"Dataset not found: {FIXTURE_PATH}"
    with FIXTURE_PATH.open() as fh:
        return json.load(fh)


def test_fixture_exists():
    assert FIXTURE_PATH.exists(), "labeled_candidates_synthetic_v1.json must exist"


def test_schema_exists():
    assert SCHEMA_PATH.exists(), "labeled_candidates_synthetic_v1.schema.json must exist"


def test_schema_version(dataset):
    assert dataset["schema_version"] == "labeled_candidates_synthetic_v1"


def test_total_entries_600(dataset):
    assert dataset["total_entries"] == 600
    assert len(dataset["entries"]) == 600


def test_all_four_labels_present(dataset):
    labels = {e["label"] for e in dataset["entries"]}
    assert labels == {"follow_up", "false_positive", "insufficient_evidence", "known_object"}


def test_at_least_50_per_class(dataset):
    from collections import Counter
    counts = Counter(e["label"] for e in dataset["entries"])
    for label, count in counts.items():
        assert count >= 50, f"Label {label!r} has only {count} examples"


def test_all_feature_columns_numeric(dataset):
    for entry in dataset["entries"]:
        features = entry["features"]
        for col in FEATURE_COLUMNS:
            assert col in features, f"Missing feature {col!r} in {entry['candidate_id']}"
            assert isinstance(features[col], (int, float))


def test_score_features_in_0_1(dataset):
    score_cols = [c for c in FEATURE_COLUMNS if c.endswith("_score")]
    for entry in dataset["entries"]:
        features = entry["features"]
        for col in score_cols:
            v = features[col]
            assert 0.0 <= v <= 1.0, (
                f"{col}={v} out of [0,1] for {entry['candidate_id']}"
            )


def test_eti_mean_on_target_high(dataset):
    eti = [e for e in dataset["entries"] if e["label"] == "follow_up"]
    mean_on = sum(e["features"]["on_target_presence_score"] for e in eti) / len(eti)
    assert mean_on >= 0.80, f"ETI mean on_target_presence_score too low: {mean_on:.3f}"


def test_rfi_mean_off_target_high(dataset):
    rfi = [e for e in dataset["entries"] if e["label"] == "false_positive"]
    mean_off = sum(e["features"]["off_target_presence_score"] for e in rfi) / len(rfi)
    assert mean_off >= 0.65, (
        f"RFI mean off_target_presence_score too low: {mean_off:.3f}"
    )


def test_setigen_in_labeled_by(dataset):
    for entry in dataset["entries"]:
        assert "setigen" in entry["labeled_by"].lower(), (
            f"Expected 'setigen' in labeled_by for {entry['candidate_id']}"
        )


def test_conservative_disclaimer(dataset):
    desc = dataset.get("description", "")
    assert "SYNTHETIC" in desc.upper()
    assert "NOT REAL" in desc.upper() or "not real" in desc.lower()


def test_methodology_references_ma_et_al(dataset):
    methodology = dataset.get("methodology", "")
    assert "Ma et al" in methodology or "Ma et al." in methodology
    assert "setigen" in methodology.lower() or "setigen" in methodology


def test_train_on_synthetic_v1_returns_test_accuracy():
    pytest.importorskip("sklearn")
    from techno_search.learned_scoring_model import train_on_synthetic_v1
    result = train_on_synthetic_v1(FIXTURE_PATH)
    assert "test_accuracy" in result
    assert isinstance(result["test_accuracy"], float)
    assert 0.0 < result["test_accuracy"] <= 1.0


def test_train_on_synthetic_v1_uses_proper_split():
    pytest.importorskip("sklearn")
    from techno_search.learned_scoring_model import train_on_synthetic_v1
    result = train_on_synthetic_v1(FIXTURE_PATH, test_fraction=0.20)
    total = result["train_size"] + result["test_size"]
    assert total == 600
    assert result["test_size"] == 120  # 20% of 600


def test_accuracy_at_least_60_percent():
    pytest.importorskip("sklearn")
    from techno_search.learned_scoring_model import train_on_synthetic_v1
    result = train_on_synthetic_v1(FIXTURE_PATH)
    assert result["test_accuracy"] >= 0.60, (
        f"Test accuracy {result['test_accuracy']:.3f} below 60% threshold"
    )


def test_disclaimer_in_training_result():
    pytest.importorskip("sklearn")
    from techno_search.learned_scoring_model import train_on_synthetic_v1
    result = train_on_synthetic_v1(FIXTURE_PATH)
    assert "disclaimer" in result
    assert "NOT" in result["disclaimer"].upper() or "not" in result["disclaimer"]


def test_missing_file_raises_error():
    pytest.importorskip("sklearn")
    from techno_search.learned_scoring_model import train_on_synthetic_v1
    with pytest.raises(FileNotFoundError):
        train_on_synthetic_v1(Path("/nonexistent/file.json"))


def test_cli_synthetic_training_summary_exits_0():
    pytest.importorskip("sklearn")
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "synthetic-training-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    data = json.loads(result.stdout)
    assert data.get("ok") is True
    assert data.get("test_accuracy", 0.0) >= 0.60
