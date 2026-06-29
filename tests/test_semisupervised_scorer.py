"""Tests for the PCA + IsolationForest semi-supervised scorer."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from techno_search.semisupervised_scorer import (
    DEFAULT_CONTAMINATION,
    DEFAULT_N_COMPONENTS,
    DEFAULT_N_ESTIMATORS,
    DEFAULT_WORKERS,
    SEMISUPERVISED_CORPUS_DISCLAIMER,
    SEMISUPERVISED_CORPUS_VERSION,
    SEMISUPERVISED_FEATURE_NAMES,
    SEMISUPERVISED_SCORER_DISCLAIMER,
    SEMISUPERVISED_SCORER_VERSION,
    SemisupervisedScorer,
    build_training_corpus_from_dat_files,
    load_training_hits_ndjson,
    semisupervised_scorer_summary,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hit(
    freq: float = 1.42e9,
    snr: float = 10.0,
    drift: float = 0.1,
    on_off: float = 0.5,
) -> dict:
    return {
        "frequency_hz": freq,
        "snr": snr,
        "drift_rate_hz_per_sec": drift,
        "bandwidth_hz": 2.0,
        "normalized_drift_hz_s_per_ghz": drift / (freq / 1e9),
        "relative_snr": 1.0,
        "on_off_consistency_score": on_off,
        "is_earth_drift_consistent": 1.0,
        "rfi_band_overlap_score": 0.0,
        "frequency_persistence_score": 0.5,
        "on_hit_count": 1,
        "off_hit_count": 0,
    }


def _training_corpus(n: int = 50) -> list[dict]:
    """Generate a diverse synthetic RFI corpus for training."""
    hits = []
    for i in range(n):
        hits.append(_make_hit(
            freq=1e9 + i * 1e6,
            snr=5.0 + (i % 10),
            drift=0.0,
            on_off=0.8,
        ))
    return hits


def _write_turboseti_dat(path: Path, source: str, rows: list[tuple[float, float, float]]) -> None:
    lines = [
        "# -------------------------- o --------------------------",
        f"# Source:{source}",
        "# MJD: 57650.782094907408\tRA: 17h10m03.984s\tDEC: 12d10m58.8s",
        "# DELTAT:  18.253611\tDELTAF(Hz):  -2.793968",
        "# --------------------------",
        (
            "# Top_Hit_# \tDrift_Rate \tSNR \tUncorrected_Frequency "
            "\tCorrected_Frequency \tIndex \tSEFD"
        ),
        "# --------------------------",
    ]
    for idx, (drift, snr, frequency_mhz) in enumerate(rows, start=1):
        lines.append(
            f"{idx:06d}\t {drift:.6f}\t {snr:.6f}\t   {frequency_mhz:.6f}"
            f"\t   {frequency_mhz:.6f}\t{700000 + idx}\t0.0"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------

def test_scorer_default_features() -> None:
    s = SemisupervisedScorer()
    assert s.feature_names == SEMISUPERVISED_FEATURE_NAMES


def test_scorer_default_workers_match_local_profile() -> None:
    s = SemisupervisedScorer()
    assert s.n_jobs == DEFAULT_WORKERS


def test_scorer_custom_features() -> None:
    custom = ["snr", "frequency_hz"]
    s = SemisupervisedScorer(feature_names=custom)
    assert s.feature_names == custom


def test_scorer_not_fitted_on_init() -> None:
    s = SemisupervisedScorer()
    assert s._is_fitted is False


# ---------------------------------------------------------------------------
# fit
# ---------------------------------------------------------------------------

def test_fit_marks_fitted() -> None:
    s = SemisupervisedScorer()
    s.fit(_training_corpus(50))
    assert s._is_fitted is True


def test_fit_records_train_hit_count() -> None:
    s = SemisupervisedScorer()
    corpus = _training_corpus(30)
    s.fit(corpus)
    assert s._train_hit_count == 30


def test_fit_too_few_hits_raises() -> None:
    s = SemisupervisedScorer()
    with pytest.raises(ValueError, match="at least 10"):
        s.fit([_make_hit() for _ in range(5)])


def test_fit_returns_self() -> None:
    s = SemisupervisedScorer()
    result = s.fit(_training_corpus(20))
    assert result is s


def test_fit_requires_sklearn() -> None:
    # Just verify the import path is correct — sklearn IS installed
    try:
        import sklearn  # noqa: F401
    except ImportError:
        pytest.skip("sklearn not installed")
    s = SemisupervisedScorer()
    s.fit(_training_corpus(20))
    assert s._is_fitted


# ---------------------------------------------------------------------------
# score_hit
# ---------------------------------------------------------------------------

def test_score_hit_raises_if_not_fitted() -> None:
    s = SemisupervisedScorer()
    with pytest.raises(RuntimeError, match="fitted"):
        s.score_hit(_make_hit())


def test_score_hit_returns_float() -> None:
    s = SemisupervisedScorer()
    s.fit(_training_corpus(50))
    score = s.score_hit(_make_hit())
    assert isinstance(score, float)


def test_score_hit_range() -> None:
    # IsolationForest decision_function can be outside [-1,1] but negated
    # score should be finite
    s = SemisupervisedScorer()
    s.fit(_training_corpus(50))
    score = s.score_hit(_make_hit())
    assert -10.0 < score < 10.0


def test_anomalous_hit_scores_higher() -> None:
    """A hit with unusual features should score higher than a typical RFI hit."""
    corpus = _training_corpus(50)
    s = SemisupervisedScorer()
    s.fit(corpus)

    typical_rfi = _make_hit(freq=1.01e9, snr=6.0, drift=0.0, on_off=0.85)
    anomalous = _make_hit(
        freq=8e9,           # X-band — far from L-band training corpus
        snr=500.0,          # extreme SNR
        drift=2.0,          # high drift
        on_off=0.0,         # not in OFF scans
    )
    rfi_score = s.score_hit(typical_rfi)
    ano_score = s.score_hit(anomalous)
    assert ano_score > rfi_score, (
        f"Anomalous hit ({ano_score:.3f}) should score higher than typical RFI "
        f"({rfi_score:.3f})"
    )


# ---------------------------------------------------------------------------
# score_hits
# ---------------------------------------------------------------------------

def test_score_hits_batch_length() -> None:
    s = SemisupervisedScorer()
    s.fit(_training_corpus(30))
    hits = [_make_hit(freq=1e9 + i * 1e6) for i in range(5)]
    scores = s.score_hits(hits)
    assert len(scores) == 5


def test_score_hits_consistent_with_score_hit() -> None:
    s = SemisupervisedScorer()
    s.fit(_training_corpus(30))
    hit = _make_hit()
    assert s.score_hits([hit])[0] == pytest.approx(s.score_hit(hit))


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

def test_save_creates_json_file() -> None:
    s = SemisupervisedScorer()
    s.fit(_training_corpus(20))
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "scorer.json"
        s.save(p)
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["schema_version"] == SEMISUPERVISED_SCORER_VERSION
        assert data["accelerator"]["used"] == "sklearn_cpu"
        assert data["accelerator"]["default_workers"] == DEFAULT_WORKERS


def test_save_requires_fitted() -> None:
    s = SemisupervisedScorer()
    with tempfile.TemporaryDirectory() as tmp, pytest.raises(RuntimeError, match="fitted"):
        s.save(Path(tmp) / "scorer.json")


def test_load_restores_hyperparameters() -> None:
    s = SemisupervisedScorer(n_components=4, n_estimators=50, n_jobs=3)
    s.fit(_training_corpus(20))
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "scorer.json"
        s.save(p)
        s2 = SemisupervisedScorer.load(p)
        assert s2.n_components == 4
        assert s2.n_estimators == 50
        assert s2.n_jobs == 3


def test_load_restores_train_hit_count() -> None:
    s = SemisupervisedScorer()
    s.fit(_training_corpus(25))
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "scorer.json"
        s.save(p)
        s2 = SemisupervisedScorer.load(p)
        assert s2._train_hit_count == 25


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_unfitted() -> None:
    s = SemisupervisedScorer()
    d = s.summary()
    assert d["is_fitted"] is False
    assert d["train_hit_count"] == 0


def test_summary_fitted() -> None:
    s = SemisupervisedScorer()
    s.fit(_training_corpus(20))
    d = s.summary()
    assert d["is_fitted"] is True
    assert d["train_hit_count"] == 20


def test_semisupervised_scorer_summary_module_level() -> None:
    s = semisupervised_scorer_summary()
    assert s["schema_version"] == SEMISUPERVISED_SCORER_VERSION
    assert "disclaimer" in s
    assert s["feature_count"] == len(SEMISUPERVISED_FEATURE_NAMES)
    assert s["default_workers"] == DEFAULT_WORKERS
    assert s["accelerator"]["used"] == "sklearn_cpu"
    assert s["accelerator"]["default_workers"] == DEFAULT_WORKERS


def test_semisupervised_scorer_summary_with_fitted_scorer() -> None:
    scorer = SemisupervisedScorer()
    scorer.fit(_training_corpus(15))
    s = semisupervised_scorer_summary(scorer)
    assert s["is_fitted"] is True


def test_semisupervised_scorer_disclaimer_conservative() -> None:
    assert "detection" in SEMISUPERVISED_SCORER_DISCLAIMER
    assert "external submission" in SEMISUPERVISED_SCORER_DISCLAIMER


def test_semisupervised_feature_names_count() -> None:
    assert len(SEMISUPERVISED_FEATURE_NAMES) == 12


def test_default_contamination_conservative() -> None:
    assert DEFAULT_CONTAMINATION <= 0.05


def test_default_n_components() -> None:
    assert DEFAULT_N_COMPONENTS >= 4


def test_default_n_estimators() -> None:
    assert DEFAULT_N_ESTIMATORS >= 100


def test_load_training_hits_ndjson_streams_records(tmp_path) -> None:
    path = tmp_path / "hits.ndjson"
    rows = [_make_hit(freq=1.0e9 + i) for i in range(12)]
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    loaded = load_training_hits_ndjson(path, max_hits=5)

    assert len(loaded) == 5
    assert loaded[0]["frequency_hz"] == rows[0]["frequency_hz"]


def test_load_training_hits_ndjson_rejects_non_object(tmp_path) -> None:
    path = tmp_path / "hits.ndjson"
    path.write_text("[1, 2, 3]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected object"):
        load_training_hits_ndjson(path)


def test_build_training_corpus_from_realistic_dat_files(tmp_path) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_turboseti_dat(
        dat_dir / "on.dat",
        "HIP_REAL_ON",
        [(-0.397966, 30.612337, 8419.319368), (-0.377557, 245.709641, 8419.297028)],
    )
    _write_turboseti_dat(
        dat_dir / "off.dat",
        "HIP_REAL_OFF",
        [(-0.397966, 28.612337, 8419.319368)],
    )
    output = tmp_path / "training.ndjson"

    summary = build_training_corpus_from_dat_files(dat_dir, output)
    loaded = load_training_hits_ndjson(output)

    assert summary["schema_version"] == SEMISUPERVISED_CORPUS_VERSION
    assert summary["ok"] is True
    assert summary["hit_count"] == 3
    assert summary["dat_file_count"] == 2
    assert summary["corpus_source"] == "real_turboseti_dat"
    assert "detection" in SEMISUPERVISED_CORPUS_DISCLAIMER
    assert output.exists()
    assert Path(summary["provenance_path"]).exists()
    assert loaded[0]["corpus_source"] == "real_turboseti_dat"
    assert loaded[0]["frequency_hz"] == pytest.approx(8419.319368e6)
    assert loaded[0]["normalized_drift_hz_s_per_ghz"] == pytest.approx(
        -0.397966 / 8.419319368
    )
    assert loaded[0]["frequency_persistence_score"] == pytest.approx(1.0)
    assert "input_dat_path" in loaded[0]


def test_build_training_corpus_rejects_zero_hit_dat_files(tmp_path) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_turboseti_dat(dat_dir / "zero.dat", "HIP_ZERO", [])

    with pytest.raises(ValueError, match="No parseable turboSETI hits"):
        build_training_corpus_from_dat_files(dat_dir, tmp_path / "training.ndjson")
