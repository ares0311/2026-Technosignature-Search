"""Tests for the Gaia DR3 scan workflow (Task 7)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.gaia_scan_workflow import (
    GAIA_SCAN_DISCLAIMER,
    GAIA_SCAN_SCHEMA_VERSION,
    GaiaScanTarget,
    gaia_scan_summary_disabled,
    load_targets_from_json,
    query_gaia_for_targets,
)


class TestGaiaScanTarget:
    def test_default_radius(self) -> None:
        t = GaiaScanTarget("HIP99427", 302.08, 6.96)
        assert t.radius_arcsec == 30.0

    def test_custom_radius(self) -> None:
        t = GaiaScanTarget("test", 0.0, 0.0, radius_arcsec=60.0)
        assert t.radius_arcsec == 60.0


class TestQueryGaiaDisabled:
    def test_returns_disabled_when_env_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", "0")
        result = query_gaia_for_targets([GaiaScanTarget("HIP99427", 302.08, 6.96)])
        assert result["live_data_disabled"] is True

    def test_disabled_result_fields(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", "0")
        result = query_gaia_for_targets([])
        for field in (
            "live_data_disabled",
            "targets_queried",
            "total_sources",
            "target_results",
            "schema_version",
            "disclaimer",
        ):
            assert field in result, f"missing field: {field}"

    def test_disabled_targets_queried_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", "0")
        result = query_gaia_for_targets(
            [GaiaScanTarget("HIP99427", 302.08, 6.96)]
        )
        assert result["targets_queried"] == 0

    def test_disabled_total_sources_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", "0")
        result = query_gaia_for_targets([GaiaScanTarget("HIP99427", 302.08, 6.96)])
        assert result["total_sources"] == 0

    def test_schema_version(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", "0")
        result = query_gaia_for_targets([])
        assert result["schema_version"] == GAIA_SCAN_SCHEMA_VERSION

    def test_disclaimer_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", "0")
        result = query_gaia_for_targets([])
        assert "detection claim" in result["disclaimer"]
        assert result["disclaimer"] == GAIA_SCAN_DISCLAIMER


class TestGaiaScanSummaryDisabled:
    def test_returns_expected_shape(self) -> None:
        result = gaia_scan_summary_disabled()
        assert result["live_data_disabled"] is True
        assert result["targets_queried"] == 0
        assert result["total_sources"] == 0
        assert result["schema_version"] == GAIA_SCAN_SCHEMA_VERSION
        assert "detection claim" in result["disclaimer"]


class TestLoadTargetsFromJson:
    def test_loads_target_list(self, tmp_path: Path) -> None:
        data = [
            {"name": "HIP99427", "ra_deg": 302.08, "dec_deg": 6.96},
            {"name": "HIP100670", "ra_deg": 306.5, "dec_deg": 7.1,
             "radius_arcsec": 45.0},
        ]
        f = tmp_path / "targets.json"
        f.write_text(json.dumps(data))
        targets = load_targets_from_json(f)
        assert len(targets) == 2
        assert targets[0].name == "HIP99427"
        assert targets[0].ra_deg == 302.08
        assert targets[0].radius_arcsec == 30.0
        assert targets[1].radius_arcsec == 45.0

    def test_returns_gaia_scan_target_instances(self, tmp_path: Path) -> None:
        data = [{"name": "test", "ra_deg": 1.0, "dec_deg": 2.0}]
        f = tmp_path / "t.json"
        f.write_text(json.dumps(data))
        targets = load_targets_from_json(f)
        assert all(isinstance(t, GaiaScanTarget) for t in targets)
