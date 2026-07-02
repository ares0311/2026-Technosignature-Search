"""Tests for Gaia/SIMBAD cross-match injection in _build_photometry_candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

lightkurve = pytest.importorskip("lightkurve")

from techno_search.pipeline_runner import run_pipeline  # noqa: E402

PHOTOMETRY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "photometry" / "sample_lightcurve.fits"
)


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


def test_no_xmatch_when_live_disabled(tmp_path: Path) -> None:
    result = run_pipeline(PHOTOMETRY_FIXTURE, "photometry", tmp_path)
    assert result.ok, f"pipeline failed: {result.error}"
    report = json.loads(result.report_paths.json_path.read_text(encoding="utf-8"))
    features = report.get("features", {})
    assert "simbad_match_count" not in features
    assert "gaia_match_count" not in features
    assert features["known_object_score"] == 0.0


def test_crossmatch_features_injected_on_live_query(tmp_path: Path) -> None:
    xmatch = _xmatch_stub(simbad_match_count=0, gaia_match_count=2)
    with patch("techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch):
        result = run_pipeline(PHOTOMETRY_FIXTURE, "photometry", tmp_path)
    assert result.ok, f"pipeline failed: {result.error}"
    report = json.loads(result.report_paths.json_path.read_text(encoding="utf-8"))
    features = report.get("features", {})
    assert "simbad_match_count" in features
    assert "gaia_match_count" in features
    assert int(features["gaia_match_count"]) == 2


def test_simbad_known_star_raises_known_object_score(tmp_path: Path) -> None:
    xmatch = _xmatch_stub(
        simbad_match_count=1,
        simbad_match_names=["* KIC 8462852"],
        known_object_score=0.9,
    )
    with patch("techno_search.catalog_crossmatch.catalog_crossmatch", return_value=xmatch):
        result = run_pipeline(PHOTOMETRY_FIXTURE, "photometry", tmp_path)
    assert result.ok, f"pipeline failed: {result.error}"
    report = json.loads(result.report_paths.json_path.read_text(encoding="utf-8"))
    features = report.get("features", {})
    prov = report.get("provenance", {})
    assert float(features["known_object_score"]) == pytest.approx(0.9)
    assert "* KIC 8462852" in str(prov["simbad_match_names"])
