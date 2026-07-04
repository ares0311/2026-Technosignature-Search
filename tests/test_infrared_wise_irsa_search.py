"""Tests for the real IRSA AllWISE photometry search/download wrapper.

Network access is stubbed out (this sandbox cannot reach IRSA at all --
same restriction already documented for MAST-based tracks) so these tests
exercise the real CSV-write and zero-result logic without touching the
network.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

astropy_coordinates = pytest.importorskip("astropy.coordinates")
irsa_module = pytest.importorskip("astroquery.ipac.irsa")

from techno_search.infrared_wise.irsa_search import (  # noqa: E402
    ALLWISE_SOURCE_CATALOG,
    search_and_download_wise_photometry,
)


class _FakeSkyCoord:
    pass


def test_unresolvable_target_raises_runtime_error(tmp_path: Path, monkeypatch) -> None:
    def _fake_from_name(name: str, **kwargs: object) -> _FakeSkyCoord:
        msg = "Unable to find coordinates for name"
        raise Exception(msg)  # noqa: TRY002

    monkeypatch.setattr(astropy_coordinates.SkyCoord, "from_name", _fake_from_name)

    with pytest.raises(RuntimeError, match="Could not resolve"):
        search_and_download_wise_photometry("not-a-real-target", download_dir=tmp_path / "dl")


def test_zero_results_reports_no_csv(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        astropy_coordinates.SkyCoord, "from_name", lambda name, **kw: _FakeSkyCoord()
    )

    def _fake_query_region(coord: object, **kwargs: object):
        from astropy.table import Table

        return Table({"ra": [], "dec": []})

    monkeypatch.setattr(irsa_module.Irsa, "query_region", _fake_query_region)

    result = search_and_download_wise_photometry("KIC 8462852", download_dir=tmp_path / "dl")

    assert result.result_count == 0
    assert result.csv_path is None


def test_results_are_written_to_a_real_csv_with_irsa_column_names(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        astropy_coordinates.SkyCoord, "from_name", lambda name, **kw: _FakeSkyCoord()
    )

    def _fake_query_region(coord: object, **kwargs: object):
        from astropy.table import Table

        return Table(
            {
                "ra": [301.5643],
                "dec": [44.4568],
                "w1mpro": [7.87],
                "w2mpro": [7.86],
                "w3mpro": [7.87],
                "w4mpro": [7.55],
                "w3sigmpro": [0.02],
                "w4sigmpro": [0.09],
            }
        )

    monkeypatch.setattr(irsa_module.Irsa, "query_region", _fake_query_region)

    download_dir = tmp_path / "dl"
    result = search_and_download_wise_photometry("KIC 8462852", download_dir=download_dir)

    assert result.result_count == 1
    assert result.csv_path is not None
    csv_path = Path(result.csv_path)
    assert csv_path.exists()
    assert csv_path.parent == download_dir

    with csv_path.open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["ra"] == "301.5643"
    assert rows[0]["w1mpro"] == "7.87"


def test_search_criteria_uses_real_allwise_catalog_by_default(
    tmp_path: Path, monkeypatch
) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        astropy_coordinates.SkyCoord, "from_name", lambda name, **kw: _FakeSkyCoord()
    )

    def _fake_query_region(coord: object, **kwargs: object):
        from astropy.table import Table

        captured.update(kwargs)
        return Table({"ra": [], "dec": []})

    monkeypatch.setattr(irsa_module.Irsa, "query_region", _fake_query_region)

    search_and_download_wise_photometry("KIC 8462852", download_dir=tmp_path / "dl")

    assert captured["catalog"] == ALLWISE_SOURCE_CATALOG
    assert captured["spatial"] == "Cone"
