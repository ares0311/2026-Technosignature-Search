"""Tests for catalog_crossmatch — cross-match wiring into the scoring pipeline."""
from __future__ import annotations

import pytest

from techno_search.catalog_crossmatch import (
    CATALOG_CROSSMATCH_DISCLAIMER,
    _known_object_score_from_match_count,
    catalog_crossmatch,
    gaia_cone_search,
    simbad_cone_search,
)


def test_stub_returned_when_live_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", raising=False)
    result = catalog_crossmatch(83.8221, 22.0145)
    assert result["query_attempted"] is False
    assert result["live_data_enabled"] is False
    assert result["known_object_score"] == 0.0


def test_stub_returned_when_no_coordinates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", raising=False)
    result = catalog_crossmatch(None, None)
    assert result["query_attempted"] is False
    assert result["known_object_score"] == 0.0


def test_stub_has_disclaimer() -> None:
    result = catalog_crossmatch(None, None)
    assert result["disclaimer"] == CATALOG_CROSSMATCH_DISCLAIMER


def test_disclaimer_language_is_conservative() -> None:
    assert "provenance records only" in CATALOG_CROSSMATCH_DISCLAIMER
    assert "does not authorize external submission" in CATALOG_CROSSMATCH_DISCLAIMER


def test_gaia_stub_when_live_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", raising=False)
    result = gaia_cone_search(83.8221, 22.0145)
    assert result["query_attempted"] is False
    assert result["known_object_score"] == 0.0
    assert result["provider"] == "gaia"


def test_simbad_stub_when_live_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", raising=False)
    result = simbad_cone_search(83.8221, 22.0145)
    assert result["query_attempted"] is False
    assert result["known_object_score"] == 0.0
    assert result["provider"] == "simbad"


def test_known_object_score_zero_matches() -> None:
    assert _known_object_score_from_match_count(0) == 0.0


def test_known_object_score_one_match() -> None:
    assert _known_object_score_from_match_count(1) == pytest.approx(0.9)


def test_known_object_score_multiple_matches() -> None:
    assert _known_object_score_from_match_count(5) == pytest.approx(1.0)


def test_catalog_crossmatch_no_ra_dec_returns_stub(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", "1")
    result = catalog_crossmatch(None, None)
    assert result["known_object_score"] == 0.0
    assert result["query_attempted"] is False


def test_combined_result_has_required_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", raising=False)
    result = catalog_crossmatch(83.8221, 22.0145)
    assert "disclaimer" in result
    assert "known_object_score" in result
    assert "provider" in result
    assert "query_attempted" in result
    assert "live_data_enabled" in result
