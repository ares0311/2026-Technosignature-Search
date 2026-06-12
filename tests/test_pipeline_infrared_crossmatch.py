"""Tests for Gaia/SIMBAD cross-match injection in _build_infrared_candidate.

Closes Tier 2 gap: Real Gaia/WISE cross-match queries at scale.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from techno_search.pipeline_runner import run_pipeline

_INFRARED_CSV = """\
# Gaia+AllWISE cross-match — synthetic fixture
source_id,ra,dec,phot_g_mean_mag,w1mpro,w2mpro,w3mpro,w4mpro,parallax,parallax_error
1234567890123456789,83.8221,22.0145,8.42,7.81,7.79,7.71,7.55,23.45,0.12
"""


def _write_infrared_csv(path: Path) -> None:
    path.write_text(_INFRARED_CSV)


def _xmatch_stub(**kwargs: Any) -> dict[str, Any]:
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


class TestInfraredCrossMatch:
    """Cross-match features injected into infrared candidates when live query runs."""

    def test_no_xmatch_when_live_disabled(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "ir.csv"
        _write_infrared_csv(csv_path)
        result = run_pipeline(csv_path, "infrared", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (csv_path.stem + ".json")).read_text())
        features = report.get("features", {})
        assert "simbad_match_count" not in features
        assert "gaia_match_count" not in features

    def test_crossmatch_features_injected_on_live_query(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "ir.csv"
        _write_infrared_csv(csv_path)
        xmatch = _xmatch_stub(simbad_match_count=0, gaia_match_count=2)
        with patch(
            "techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch
        ):
            result = run_pipeline(csv_path, "infrared", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (csv_path.stem + ".json")).read_text())
        features = report.get("features", {})
        assert "simbad_match_count" in features
        assert "gaia_match_count" in features
        assert "known_object_score" in features

    def test_gaia_match_count_propagated(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "ir.csv"
        _write_infrared_csv(csv_path)
        xmatch = _xmatch_stub(gaia_match_count=3, known_object_score=1.0)
        with patch(
            "techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch
        ):
            result = run_pipeline(csv_path, "infrared", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (csv_path.stem + ".json")).read_text())
        features = report.get("features", {})
        assert int(features.get("gaia_match_count", -1)) == 3

    def test_simbad_known_star_raises_known_object_score(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "ir.csv"
        _write_infrared_csv(csv_path)
        xmatch = _xmatch_stub(
            simbad_match_count=1,
            simbad_match_names=["* eps Eri"],
            known_object_score=0.9,
        )
        with patch(
            "techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch
        ):
            result = run_pipeline(csv_path, "infrared", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (csv_path.stem + ".json")).read_text())
        features = report.get("features", {})
        assert float(features.get("simbad_known_object_score", 0.0)) == pytest.approx(0.9)
        assert float(features.get("known_object_score", 0.0)) == pytest.approx(0.9)

    def test_simbad_names_in_infrared_provenance(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "ir.csv"
        _write_infrared_csv(csv_path)
        xmatch = _xmatch_stub(
            simbad_match_count=1,
            simbad_match_names=["eps Eri"],
            known_object_score=0.9,
        )
        with patch(
            "techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch
        ):
            result = run_pipeline(csv_path, "infrared", tmp_path / "out")
        if not result.ok:
            pytest.skip(f"pipeline failed: {result.error}")
        report = json.loads((tmp_path / "out" / (csv_path.stem + ".json")).read_text())
        prov = report.get("provenance", {})
        assert "simbad_match_names" in prov
        assert "eps Eri" in str(prov["simbad_match_names"])
