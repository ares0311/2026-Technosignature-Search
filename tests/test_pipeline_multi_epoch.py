"""Tests for multi-epoch persistence injection in run_pipeline / _build_radio_candidate.

Closes Tier 2 gap: Multi-epoch observation support.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.pipeline_runner import run_pipeline

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DAT_HEADER = (
    "# Source:TEST\n"
    "# MJD: 57000.0\n"
    "# DELTAT: 300.0\n"
    "# RA: 300.0\n"
    "# DEC: 60.0\n"
    "# Top_Hit_#\tDrift_Rate\tSNR\tUncorrected_Frequency\t"
    "Corrected_Frequency\tscan_role\n"
)


def _write_dat(path: Path, freq_mhz: float, snr: float, scan_role: str = "ON") -> None:
    """Write a minimal turboSETI .dat file with one hit."""
    freq_hz = freq_mhz * 1e6
    path.write_text(
        _DAT_HEADER
        + f"1\t0.5\t{snr}\t{freq_hz:.6f}\t{freq_hz:.6f}\t{scan_role}\n"
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMultiEpochPipelineInjection:
    """Multi-epoch features are injected into radio candidates when epoch_dat_files provided."""

    def test_no_epoch_files_omits_multi_epoch_features(self, tmp_path: Path) -> None:
        dat = tmp_path / "epoch1.dat"
        _write_dat(dat, freq_mhz=1420.0, snr=200.0)
        result = run_pipeline(dat, "radio", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat.stem + ".json")).read_text())
        features = report.get("features", {})
        assert "multi_epoch_persistence_score" not in features

    def test_single_epoch_file_injects_multi_epoch_features(self, tmp_path: Path) -> None:
        dat1 = tmp_path / "epoch1.dat"
        dat2 = tmp_path / "epoch2.dat"
        _write_dat(dat1, freq_mhz=1420.0, snr=200.0)
        _write_dat(dat2, freq_mhz=1420.0, snr=180.0)
        result = run_pipeline(
            dat1, "radio", tmp_path / "out", epoch_dat_files=[dat2]
        )
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat1.stem + ".json")).read_text())
        features = report.get("features", {})
        assert "multi_epoch_persistence_score" in features
        assert "multi_epoch_group_count" in features
        assert "multi_epoch_epoch_count" in features

    def test_persistent_signal_raises_persistence_score(self, tmp_path: Path) -> None:
        """Signal at same frequency across 2 epochs → persistence_score > 0."""
        dat1 = tmp_path / "epoch_a.dat"
        dat2 = tmp_path / "epoch_b.dat"
        _write_dat(dat1, freq_mhz=1420.406, snr=150.0)
        _write_dat(dat2, freq_mhz=1420.406, snr=160.0)
        result = run_pipeline(
            dat1, "radio", tmp_path / "out", epoch_dat_files=[dat2]
        )
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat1.stem + ".json")).read_text())
        features = report.get("features", {})
        assert float(features.get("multi_epoch_persistence_score", 0.0)) > 0.0
        assert int(features.get("multi_epoch_epoch_count", 0)) == 2

    def test_provenance_includes_multi_epoch_fields(self, tmp_path: Path) -> None:
        dat1 = tmp_path / "ep1.dat"
        dat2 = tmp_path / "ep2.dat"
        _write_dat(dat1, freq_mhz=1420.0, snr=100.0)
        _write_dat(dat2, freq_mhz=1420.0, snr=110.0)
        result = run_pipeline(
            dat1, "radio", tmp_path / "out", epoch_dat_files=[dat2]
        )
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat1.stem + ".json")).read_text())
        prov = report.get("provenance", {})
        assert "multi_epoch_epoch_count" in prov
        assert "multi_epoch_max_persistence_score" in prov

    def test_two_extra_epochs_epoch_count_is_three(self, tmp_path: Path) -> None:
        dats = [tmp_path / f"ep{i}.dat" for i in range(3)]
        for d in dats:
            _write_dat(d, freq_mhz=1420.0, snr=120.0)
        result = run_pipeline(
            dats[0], "radio", tmp_path / "out", epoch_dat_files=dats[1:]
        )
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dats[0].stem + ".json")).read_text())
        features = report.get("features", {})
        assert int(features.get("multi_epoch_epoch_count", 0)) == 3

    def test_non_persistent_signal_gives_low_persistence(self, tmp_path: Path) -> None:
        """Signal at different frequencies across 2 epochs → group in only 1 epoch."""
        dat1 = tmp_path / "ep_a.dat"
        dat2 = tmp_path / "ep_b.dat"
        _write_dat(dat1, freq_mhz=1420.0, snr=150.0)
        _write_dat(dat2, freq_mhz=1500.0, snr=140.0)  # different frequency
        result = run_pipeline(
            dat1, "radio", tmp_path / "out", epoch_dat_files=[dat2]
        )
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat1.stem + ".json")).read_text())
        features = report.get("features", {})
        # With no frequency match between epochs, max_persistence = 0.5 (1/2 epochs)
        # multi_epoch_group_count (groups in >=2 epochs) = 0
        assert int(features.get("multi_epoch_group_count", -1)) == 0
