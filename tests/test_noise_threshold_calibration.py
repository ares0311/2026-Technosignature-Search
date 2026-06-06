"""Tests for noise threshold calibration tool."""
from __future__ import annotations

from pathlib import Path

import pytest

from techno_search.noise_threshold_calibration import (
    NOISE_CALIBRATION_DISCLAIMER,
    _percentile,
    _std_dev,
    analyze_hit_directory,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "radio"


def test_analyze_fixture_dir_succeeds() -> None:
    result = analyze_hit_directory(FIXTURE_DIR)
    assert result["ok"] is True


def test_analyze_returns_snr_stats() -> None:
    result = analyze_hit_directory(FIXTURE_DIR)
    stats = result["snr_stats"]
    assert stats["count"] > 0
    assert stats["max"] > stats["min"]


def test_analyze_returns_percentiles() -> None:
    result = analyze_hit_directory(FIXTURE_DIR)
    percentiles = result["snr_stats"]["percentiles"]
    assert "p50" in percentiles
    assert "p95" in percentiles
    assert "p99" in percentiles


def test_analyze_returns_suggested_thresholds() -> None:
    result = analyze_hit_directory(FIXTURE_DIR)
    thresholds = result["suggested_thresholds"]
    assert "snr_high_interest_candidate" in thresholds
    assert "snr_follow_up_candidate" in thresholds
    assert thresholds["review_required"] is True


def test_analyze_nonexistent_dir_returns_error() -> None:
    result = analyze_hit_directory(Path("/nonexistent/path/12345"))
    assert result["ok"] is False
    assert "error" in result


def test_analyze_empty_dir_returns_error(tmp_path: Path) -> None:
    result = analyze_hit_directory(tmp_path)
    assert result["ok"] is False


def test_analyze_dat_format_fixture() -> None:
    """Verify .dat format files are analyzed correctly."""
    result = analyze_hit_directory(FIXTURE_DIR)
    assert result["file_count"] >= 2  # at least sample_hits.csv + sample_hits_real_format.dat


def test_disclaimer_is_conservative() -> None:
    assert "must be reviewed" in NOISE_CALIBRATION_DISCLAIMER
    assert "domain expert" in NOISE_CALIBRATION_DISCLAIMER
    assert "do not constitute" in NOISE_CALIBRATION_DISCLAIMER


def test_percentile_single_value() -> None:
    assert _percentile([5.0], 50.0) == pytest.approx(5.0)


def test_percentile_empty_returns_zero() -> None:
    assert _percentile([], 50.0) == pytest.approx(0.0)


def test_percentile_median() -> None:
    vals = sorted([1.0, 2.0, 3.0, 4.0, 5.0])
    assert _percentile(vals, 50.0) == pytest.approx(3.0)


def test_std_dev_constant_values() -> None:
    assert _std_dev([5.0, 5.0, 5.0]) == pytest.approx(0.0)


def test_std_dev_known_value() -> None:
    # sample std dev of [1, 3] = sqrt(2) ≈ 1.4142
    vals = [1.0, 3.0]
    assert _std_dev(vals) == pytest.approx(2.0 ** 0.5, rel=1e-4)


def test_cli_noise_threshold_calibration(tmp_path: Path) -> None:
    from techno_search.cli import main

    exit_code = main(["noise-threshold-calibration", str(FIXTURE_DIR)])
    assert exit_code == 0
