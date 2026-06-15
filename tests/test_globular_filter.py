"""Tests for the GLOBULAR pre-filter."""

from __future__ import annotations

import pytest

from techno_search.globular_filter import (
    GLOBULAR_FEATURE_NAMES,
    GLOBULAR_FILTER_DISCLAIMER,
    GLOBULAR_FILTER_VERSION,
    GlobularResult,
    _build_feature_matrix,
    apply_globular_filter,
    globular_filter_summary,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hit(
    freq: float = 1.42e9,
    drift: float = 0.5,
    snr: float = 20.0,
    role: str = "on",
    extra: dict | None = None,
) -> dict:
    h = {
        "frequency_hz": freq,
        "drift_rate_hz_per_sec": drift,
        "snr": snr,
        "bandwidth_hz": 2.0,
        "scan_role": role,
        "target_id": "A",
        "normalized_drift_hz_s_per_ghz": drift / (freq / 1e9),
        "relative_snr": 1.0,
        "on_off_consistency_score": 0.0,
        "is_earth_drift_consistent": 1.0,
        "rfi_band_overlap_score": 0.0,
        "frequency_persistence_score": 0.5,
        "hit_count": 1,
        "on_hit_count": 1,
        "off_hit_count": 0,
    }
    if extra:
        h.update(extra)
    return h


def _rfi_hit(i: int) -> dict:
    """Hits clustered tightly — look like RFI."""
    return _make_hit(
        freq=1_000_000_000.0 + float(i) * 0.1,  # very close in frequency
        drift=0.0,
        snr=5.0 + float(i % 3),
        extra={"on_off_consistency_score": 0.9, "rfi_band_overlap_score": 1.0},
    )


# ---------------------------------------------------------------------------
# _build_feature_matrix
# ---------------------------------------------------------------------------

def test_build_feature_matrix_shape() -> None:
    hits = [_make_hit(freq=1e9 + i * 1e6) for i in range(5)]
    matrix = _build_feature_matrix(hits, GLOBULAR_FEATURE_NAMES)
    assert len(matrix) == 5
    assert all(len(row) == len(GLOBULAR_FEATURE_NAMES) for row in matrix)


def test_build_feature_matrix_normalised_to_01() -> None:
    hits = [_make_hit(snr=float(snr)) for snr in [10.0, 20.0, 30.0]]
    matrix = _build_feature_matrix(hits, ["snr"])
    # After min-max norm: [0.0, 0.5, 1.0]
    assert matrix[0][0] == pytest.approx(0.0)
    assert matrix[1][0] == pytest.approx(0.5)
    assert matrix[2][0] == pytest.approx(1.0)


def test_build_feature_matrix_identical_column_set_to_zero() -> None:
    hits = [_make_hit(snr=5.0), _make_hit(snr=5.0)]
    matrix = _build_feature_matrix(hits, ["snr"])
    assert all(row[0] == 0.0 for row in matrix)


def test_build_feature_matrix_empty() -> None:
    assert _build_feature_matrix([], GLOBULAR_FEATURE_NAMES) == []


def test_build_feature_matrix_missing_field_defaults_zero() -> None:
    hits = [{"frequency_hz": 1e9}]  # missing all other features
    matrix = _build_feature_matrix(hits, ["snr", "bandwidth_hz"])
    assert matrix[0] == [0.0, 0.0]


# ---------------------------------------------------------------------------
# apply_globular_filter
# ---------------------------------------------------------------------------

def test_apply_globular_filter_returns_one_result_per_hit() -> None:
    hits = [_make_hit(freq=1e9 + i * 1e6) for i in range(10)]
    results = apply_globular_filter(hits, min_cluster_size=3)
    assert len(results) == len(hits)


def test_apply_globular_filter_empty_returns_empty() -> None:
    assert apply_globular_filter([]) == []


def test_apply_globular_filter_too_few_hits_all_noise() -> None:
    hits = [_make_hit() for _ in range(3)]
    results = apply_globular_filter(hits, min_cluster_size=5)
    assert all(r.cluster_label == -1 for r in results)
    assert all(not r.is_rfi_cluster for r in results)


def test_apply_globular_filter_result_type() -> None:
    hits = [_make_hit(freq=1e9 + i * 1e6) for i in range(5)]
    results = apply_globular_filter(hits, min_cluster_size=2)
    for r in results:
        assert isinstance(r, GlobularResult)
        assert r.hit_index >= 0


def test_apply_globular_filter_dense_cluster_flagged() -> None:
    # 20 very similar RFI-like hits should cluster together
    hits = [_rfi_hit(i) for i in range(20)]
    results = apply_globular_filter(hits, min_cluster_size=5, min_samples=3)
    rfi_count = sum(1 for r in results if r.is_rfi_cluster)
    # Most of the dense cluster should be flagged
    assert rfi_count >= 10, (
        f"Expected ≥10 hits flagged as RFI cluster, got {rfi_count}"
    )


def test_apply_globular_filter_outlier_survives() -> None:
    # One isolated hit amid dense cluster should survive as noise
    hits = [_rfi_hit(i) for i in range(20)]
    # Add one very different outlier
    outlier = _make_hit(
        freq=8_000_000_000.0,  # far away in frequency space
        snr=500.0,
        extra={
            "on_off_consistency_score": 0.0,
            "rfi_band_overlap_score": 0.0,
            "normalized_drift_hz_s_per_ghz": 2.0,
        },
    )
    hits.append(outlier)
    results = apply_globular_filter(hits, min_cluster_size=5, min_samples=3)
    last_result = results[-1]
    # The outlier should be in the noise set (label == -1)
    assert not last_result.is_rfi_cluster


def test_apply_globular_filter_features_used_recorded() -> None:
    hits = [_make_hit(freq=1e9 + i * 1e6) for i in range(5)]
    results = apply_globular_filter(hits, min_cluster_size=2)
    for r in results:
        assert r.features_used == GLOBULAR_FEATURE_NAMES


def test_apply_globular_filter_custom_features() -> None:
    hits = [_make_hit(freq=1e9 + i * 1e6) for i in range(5)]
    custom = ["frequency_hz", "snr"]
    results = apply_globular_filter(hits, feature_names=custom, min_cluster_size=2)
    for r in results:
        assert r.features_used == custom


# ---------------------------------------------------------------------------
# globular_filter_summary
# ---------------------------------------------------------------------------

def test_globular_filter_summary_keys() -> None:
    hits = [_make_hit(freq=1e9 + i * 1e6) for i in range(5)]
    results = apply_globular_filter(hits, min_cluster_size=2)
    s = globular_filter_summary(results)
    assert s["schema_version"] == GLOBULAR_FILTER_VERSION
    assert "disclaimer" in s
    assert s["total_hits"] == 5
    assert s["rfi_cluster_hits"] + s["noise_hits"] == 5


def test_globular_filter_summary_disclaimer_conservative() -> None:
    hits = [_make_hit(freq=1e9 + i * 1e6) for i in range(5)]
    results = apply_globular_filter(hits, min_cluster_size=2)
    s = globular_filter_summary(results)
    assert "detection claim" in s["disclaimer"]
    assert "external submission" in s["disclaimer"]


def test_globular_filter_summary_reduction_fraction_range() -> None:
    hits = [_rfi_hit(i) for i in range(20)]
    results = apply_globular_filter(hits, min_cluster_size=5)
    s = globular_filter_summary(results)
    assert 0.0 <= s["rfi_reduction_fraction"] <= 1.0


def test_globular_filter_result_as_dict() -> None:
    r = GlobularResult(
        hit_index=0,
        cluster_label=-1,
        is_rfi_cluster=False,
        cluster_size=0,
        features_used=GLOBULAR_FEATURE_NAMES[:3],
    )
    d = r.as_dict()
    assert d["hit_index"] == 0
    assert d["is_rfi_cluster"] is False
    assert "disclaimer" in d


def test_globular_feature_names_count() -> None:
    assert len(GLOBULAR_FEATURE_NAMES) == 13


def test_globular_filter_version_constant() -> None:
    assert GLOBULAR_FILTER_VERSION == "globular_filter_v1"


def test_globular_filter_disclaimer_not_empty() -> None:
    assert len(GLOBULAR_FILTER_DISCLAIMER) > 20
