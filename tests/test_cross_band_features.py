"""Tests for cross-band feature normalization."""

from __future__ import annotations

import pytest

from techno_search.radio.cross_band_features import (
    CROSS_BAND_FEATURE_NAMES,
    CROSS_BAND_FEATURES_DISCLAIMER,
    CROSS_BAND_FEATURES_VERSION,
    EARTH_ACCELERATION_DRIFT_HZ_S_PER_GHZ,
    CrossBandFeatures,
    compute_relative_snr_from_hits,
    cross_band_features_summary,
    extract_cross_band_features,
    is_earth_drift_consistent,
    normalize_drift_rate,
    on_off_consistency_score,
    relative_snr,
)

# ---------------------------------------------------------------------------
# normalize_drift_rate
# ---------------------------------------------------------------------------

def test_normalize_drift_rate_l_band() -> None:
    # GBT L-band ~1.5 GHz; 0.5 Hz/s drift → 0.333 Hz/s/GHz
    result = normalize_drift_rate(0.5, 1_500_000_000.0)
    assert abs(result - 0.5 / 1.5) < 1e-9


def test_normalize_drift_rate_x_band() -> None:
    # GBT X-band ~8 GHz; same physical drift should give larger raw Hz/s
    # but same normalized value
    result = normalize_drift_rate(1.6, 8_000_000_000.0)
    assert abs(result - 1.6 / 8.0) < 1e-9


def test_normalize_drift_rate_zero_freq_returns_zero() -> None:
    assert normalize_drift_rate(1.0, 0.0) == 0.0


def test_normalize_drift_rate_negative_freq_returns_zero() -> None:
    assert normalize_drift_rate(1.0, -100.0) == 0.0


def test_normalize_drift_rate_negative_drift() -> None:
    result = normalize_drift_rate(-1.5, 1_000_000_000.0)
    assert abs(result - (-1.5)) < 1e-9


# ---------------------------------------------------------------------------
# is_earth_drift_consistent
# ---------------------------------------------------------------------------

def test_earth_drift_consistent_within_threshold() -> None:
    assert is_earth_drift_consistent(0.3) is True


def test_earth_drift_consistent_at_threshold() -> None:
    assert is_earth_drift_consistent(EARTH_ACCELERATION_DRIFT_HZ_S_PER_GHZ) is True


def test_earth_drift_inconsistent_above_threshold() -> None:
    assert is_earth_drift_consistent(1.0) is False


def test_earth_drift_consistent_negative() -> None:
    assert is_earth_drift_consistent(-0.3) is True


def test_earth_drift_consistent_custom_threshold() -> None:
    assert is_earth_drift_consistent(0.5, threshold=0.4) is False
    assert is_earth_drift_consistent(0.3, threshold=0.4) is True


# ---------------------------------------------------------------------------
# relative_snr
# ---------------------------------------------------------------------------

def test_relative_snr_above_median() -> None:
    # median is 10, hit is 50 → ratio 5.0
    result = relative_snr(50.0, [5.0, 10.0, 10.0, 15.0])
    assert result == pytest.approx(50.0 / 10.0, rel=1e-6)


def test_relative_snr_empty_window() -> None:
    assert relative_snr(25.0, []) == 25.0


def test_relative_snr_zero_median() -> None:
    assert relative_snr(25.0, [0.0, 0.0]) == 25.0


def test_relative_snr_single_element() -> None:
    result = relative_snr(20.0, [10.0])
    assert result == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# compute_relative_snr_from_hits
# ---------------------------------------------------------------------------

def _make_hits(
    freqs_snrs: list[tuple[float, float]],
    role: str = "on",
) -> list[dict]:
    return [
        {"frequency_hz": f, "snr": s, "scan_role": role}
        for f, s in freqs_snrs
    ]


def test_compute_relative_snr_ignores_distant_hits() -> None:
    all_hits = _make_hits([
        (1_420_000_000.0, 100.0),  # target
        (1_430_000_001.0, 5.0),    # >10 MHz away — excluded
    ])
    # Only the target hit is in window → median = 100 → ratio = 1.0
    result = compute_relative_snr_from_hits(
        1_420_000_000.0, 100.0, all_hits, window_hz=10_000_000.0
    )
    assert result == pytest.approx(1.0)


def test_compute_relative_snr_uses_nearby_hits() -> None:
    all_hits = _make_hits([
        (1_420_000_000.0, 100.0),
        (1_421_000_000.0, 10.0),
        (1_419_000_000.0, 10.0),
    ])
    # Window includes all three; sorted=[10,10,100] → median=10 → ratio=10
    result = compute_relative_snr_from_hits(
        1_420_000_000.0, 100.0, all_hits, window_hz=10_000_000.0
    )
    assert result == pytest.approx(100.0 / 10.0)


# ---------------------------------------------------------------------------
# on_off_consistency_score
# ---------------------------------------------------------------------------

def test_on_off_consistency_no_off_scans() -> None:
    hits = [{"frequency_hz": 1e9, "scan_role": "on", "target_id": "A"}]
    assert on_off_consistency_score(1e9, hits) == 0.0


def test_on_off_consistency_signal_in_all_off() -> None:
    hits = [
        {"frequency_hz": 1e9, "scan_role": "off", "target_id": "B"},
        {"frequency_hz": 1e9, "scan_role": "off", "target_id": "C"},
    ]
    assert on_off_consistency_score(1e9, hits) == pytest.approx(1.0)


def test_on_off_consistency_signal_in_half_off() -> None:
    hits = [
        {"frequency_hz": 1e9, "scan_role": "off", "target_id": "B"},
        {"frequency_hz": 2e9, "scan_role": "off", "target_id": "C"},  # different freq
    ]
    score = on_off_consistency_score(1e9, hits, freq_tol_hz=5.0)
    assert score == pytest.approx(0.5)


def test_on_off_consistency_no_match_returns_zero() -> None:
    hits = [
        {"frequency_hz": 2e9, "scan_role": "off", "target_id": "B"},
    ]
    score = on_off_consistency_score(1e9, hits, freq_tol_hz=5.0)
    assert score == pytest.approx(0.0)


def test_on_off_consistency_uses_target_id_dedup() -> None:
    # Same scan_id appearing twice should count as one OFF scan
    hits = [
        {"frequency_hz": 1e9, "scan_role": "off", "target_id": "B"},
        {"frequency_hz": 1e9, "scan_role": "off", "target_id": "B"},
    ]
    score = on_off_consistency_score(1e9, hits)
    assert score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# extract_cross_band_features
# ---------------------------------------------------------------------------

def test_extract_cross_band_features_returns_dataclass() -> None:
    hit = {
        "frequency_hz": 1_420_000_000.0,
        "drift_rate_hz_per_sec": 0.2,
        "snr": 50.0,
        "scan_role": "on",
        "target_id": "A",
    }
    result = extract_cross_band_features(hit, [hit])
    assert isinstance(result, CrossBandFeatures)


def test_extract_cross_band_features_earth_consistent_flag() -> None:
    hit = {
        "frequency_hz": 1_420_000_000.0,
        "drift_rate_hz_per_sec": 0.3,  # 0.3 Hz/s / 1.42 GHz ≈ 0.211 < 0.44
        "snr": 50.0,
        "scan_role": "on",
        "target_id": "A",
    }
    result = extract_cross_band_features(hit, [hit])
    assert result.is_earth_drift_consistent is True


def test_extract_cross_band_features_high_drift_inconsistent() -> None:
    hit = {
        "frequency_hz": 1_000_000_000.0,
        "drift_rate_hz_per_sec": 2.0,  # 2.0 Hz/s / 1.0 GHz = 2.0 > 0.44
        "snr": 50.0,
        "scan_role": "on",
        "target_id": "A",
    }
    result = extract_cross_band_features(hit, [hit])
    assert result.is_earth_drift_consistent is False


def test_extract_cross_band_features_as_dict_keys() -> None:
    hit = {"frequency_hz": 1e9, "drift_rate_hz_per_sec": 0.1, "snr": 10.0}
    result = extract_cross_band_features(hit, [hit])
    d = result.as_dict()
    for name in CROSS_BAND_FEATURE_NAMES:
        assert name in d


def test_extract_cross_band_features_off_scan_raises_consistency() -> None:
    on_hit = {
        "frequency_hz": 1e9,
        "drift_rate_hz_per_sec": 0.1,
        "snr": 50.0,
        "scan_role": "on",
        "target_id": "A",
    }
    off_hit = {
        "frequency_hz": 1e9,
        "drift_rate_hz_per_sec": 0.1,
        "snr": 48.0,
        "scan_role": "off",
        "target_id": "B",
    }
    all_hits = [on_hit, off_hit]
    result = extract_cross_band_features(on_hit, all_hits)
    # Signal in 1/1 OFF scans → consistency = 1.0 (looks like RFI)
    assert result.on_off_consistency_score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# cross_band_features_summary
# ---------------------------------------------------------------------------

def test_cross_band_features_summary_keys() -> None:
    s = cross_band_features_summary()
    assert s["schema_version"] == CROSS_BAND_FEATURES_VERSION
    assert "disclaimer" in s
    assert s["feature_count"] == len(CROSS_BAND_FEATURE_NAMES)


def test_cross_band_features_summary_disclaimer_conservative() -> None:
    s = cross_band_features_summary()
    assert "detection claim" in s["disclaimer"]
    assert "external submission" in s["disclaimer"]


def test_cross_band_features_version_constant() -> None:
    assert CROSS_BAND_FEATURES_VERSION == "cross_band_features_v1"


def test_cross_band_features_disclaimer_not_empty() -> None:
    assert len(CROSS_BAND_FEATURES_DISCLAIMER) > 20
