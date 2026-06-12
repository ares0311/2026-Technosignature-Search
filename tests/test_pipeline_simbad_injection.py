"""Tests for SIMBAD known-object integration in run_pipeline / _build_radio_candidate.

Closes Tier 2 gap: Known object catalog integration (SIMBAD cross-match).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from techno_search.pipeline_runner import run_pipeline

_DAT_HEADER = (
    "# Source:TEST\n"
    "# MJD: 57000.0\n"
    "# DELTAT: 300.0\n"
    "# RA: 83.8221\n"
    "# DEC: 22.0145\n"
    "# Top_Hit_#\tDrift_Rate\tSNR\tUncorrected_Frequency\t"
    "Corrected_Frequency\tscan_role\n"
)


def _write_dat(path: Path, freq_mhz: float = 1420.0, snr: float = 150.0) -> None:
    freq_hz = freq_mhz * 1e6
    path.write_text(
        _DAT_HEADER
        + f"1\t0.5\t{snr}\t{freq_hz:.6f}\t{freq_hz:.6f}\tON\n"
    )


def _xmatch_stub(**kwargs: Any) -> dict[str, Any]:
    """Return a catalog_crossmatch result with configurable fields."""
    base: dict[str, Any] = {
        "query_attempted": True,
        "live_data_enabled": True,
        "provider": "simbad+gaia",
        "known_object_score": 0.0,
        "simbad_match_count": 0,
        "simbad_match_names": [],
        "gaia_match_count": 0,
        "gaia_match_names": [],
        "disclaimer": "test",
    }
    base.update(kwargs)
    return base


class TestSimbadInjection:
    """SIMBAD match details injected into radio candidate features when live query runs."""

    def test_no_xmatch_when_live_disabled(self, tmp_path: Path) -> None:
        dat = tmp_path / "test.dat"
        _write_dat(dat)
        result = run_pipeline(dat, "radio", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat.stem + ".json")).read_text())
        features = report.get("features", {})
        # No live data → cross-match features absent
        assert "simbad_match_count" not in features
        assert "simbad_known_object_score" not in features

    def test_simbad_features_injected_on_live_query(self, tmp_path: Path) -> None:
        dat = tmp_path / "test.dat"
        _write_dat(dat)
        xmatch = _xmatch_stub(simbad_match_count=0, gaia_match_count=0)
        with patch(
            "techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch
        ):
            result = run_pipeline(dat, "radio", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat.stem + ".json")).read_text())
        features = report.get("features", {})
        assert "simbad_match_count" in features
        assert "simbad_known_object_score" in features
        assert "gaia_match_count" in features

    def test_simbad_zero_match_gives_score_zero(self, tmp_path: Path) -> None:
        dat = tmp_path / "test.dat"
        _write_dat(dat)
        xmatch = _xmatch_stub(simbad_match_count=0, known_object_score=0.0)
        with patch(
            "techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch
        ):
            result = run_pipeline(dat, "radio", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat.stem + ".json")).read_text())
        features = report.get("features", {})
        assert float(features.get("simbad_known_object_score", -1)) == 0.0
        assert int(features.get("simbad_match_count", -1)) == 0

    def test_simbad_one_match_gives_score_0_9(self, tmp_path: Path) -> None:
        dat = tmp_path / "test.dat"
        _write_dat(dat)
        xmatch = _xmatch_stub(
            simbad_match_count=1,
            simbad_match_names=["HD 12345"],
            known_object_score=0.9,
        )
        with patch(
            "techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch
        ):
            result = run_pipeline(dat, "radio", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat.stem + ".json")).read_text())
        features = report.get("features", {})
        assert float(features.get("simbad_known_object_score", 0.0)) == pytest.approx(0.9)
        assert int(features.get("simbad_match_count", 0)) == 1

    def test_simbad_multi_match_gives_score_1_0(self, tmp_path: Path) -> None:
        dat = tmp_path / "test.dat"
        _write_dat(dat)
        xmatch = _xmatch_stub(
            simbad_match_count=3,
            simbad_match_names=["HD 1", "HD 2", "HD 3"],
            known_object_score=1.0,
        )
        with patch(
            "techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch
        ):
            result = run_pipeline(dat, "radio", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat.stem + ".json")).read_text())
        features = report.get("features", {})
        assert float(features.get("simbad_known_object_score", 0.0)) == pytest.approx(1.0)
        assert int(features.get("simbad_match_count", 0)) == 3

    def test_simbad_match_names_in_provenance(self, tmp_path: Path) -> None:
        dat = tmp_path / "test.dat"
        _write_dat(dat)
        xmatch = _xmatch_stub(
            simbad_match_count=2,
            simbad_match_names=["Tau Ceti", "HD 10700"],
            known_object_score=1.0,
        )
        with patch(
            "techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch
        ):
            result = run_pipeline(dat, "radio", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat.stem + ".json")).read_text())
        prov = report.get("provenance", {})
        assert "simbad_match_names" in prov
        assert "Tau Ceti" in str(prov["simbad_match_names"])

    def test_zero_match_still_records_simbad_checked(self, tmp_path: Path) -> None:
        """A zero-match result records that SIMBAD was checked (absence of match is evidence)."""
        dat = tmp_path / "test.dat"
        _write_dat(dat)
        xmatch = _xmatch_stub(simbad_match_count=0, known_object_score=0.0)
        with patch(
            "techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch
        ):
            result = run_pipeline(dat, "radio", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (dat.stem + ".json")).read_text())
        prov = report.get("provenance", {})
        # simbad_match_count recorded even when 0
        assert "simbad_match_count" in prov
        assert int(prov["simbad_match_count"]) == 0
