"""Tests for the real MAST JWST MIRI LRS x1d spectrum search/download wrapper.

Network access is stubbed out (this sandbox cannot reach MAST at all --
verified live, not assumed) so these tests exercise the real x1d-filename
filtering and zero-result logic without touching the network.
"""

from __future__ import annotations

from pathlib import Path

import pytest

astroquery_mast = pytest.importorskip("astroquery.mast")

from techno_search.spectroscopy.jwst_search import (  # noqa: E402
    MIRI_LRS_INSTRUMENT_NAMES,
    MIRI_LRS_PRISM_FILTER,
    search_and_download_miri_lrs_spectra,
)


class _FakeTable:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self._rows = rows

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, key: object) -> object:
        if isinstance(key, str):
            return [row[key] for row in self._rows]
        if isinstance(key, list):
            return _FakeTable(
                [row for row, keep in zip(self._rows, key, strict=True) if keep]
            )
        if isinstance(key, slice):
            return _FakeTable(self._rows[key])
        msg = f"Unsupported key: {key!r}"
        raise TypeError(msg)


def test_zero_observations_reports_no_download(tmp_path: Path, monkeypatch) -> None:
    def _fake_query_criteria(**kwargs: object) -> _FakeTable:
        return _FakeTable([])

    monkeypatch.setattr(astroquery_mast.Observations, "query_criteria", _fake_query_criteria)

    result = search_and_download_miri_lrs_spectra(
        "nonexistent-target", download_dir=tmp_path / "dl"
    )

    assert result.result_count == 0
    assert result.x1d_product_count == 0
    assert result.downloaded_count == 0
    assert result.downloaded_paths == ()


def test_non_x1d_products_are_filtered_out(tmp_path: Path, monkeypatch) -> None:
    def _fake_query_criteria(**kwargs: object) -> _FakeTable:
        return _FakeTable([{"obsid": "1"}])

    def _fake_get_product_list(observations: object) -> _FakeTable:
        return _FakeTable(
            [
                {"productFilename": "jw01234_uncal.fits"},
                {"productFilename": "jw01234_rate.fits"},
                {"productFilename": "jw01234_cal.fits"},
            ]
        )

    monkeypatch.setattr(astroquery_mast.Observations, "query_criteria", _fake_query_criteria)
    monkeypatch.setattr(astroquery_mast.Observations, "get_product_list", _fake_get_product_list)

    result = search_and_download_miri_lrs_spectra("some-target", download_dir=tmp_path / "dl")

    assert result.result_count == 1
    assert result.x1d_product_count == 0
    assert result.downloaded_count == 0


def test_x1d_products_are_downloaded(tmp_path: Path, monkeypatch) -> None:
    def _fake_query_criteria(**kwargs: object) -> _FakeTable:
        return _FakeTable([{"obsid": "1"}])

    def _fake_get_product_list(observations: object) -> _FakeTable:
        return _FakeTable(
            [
                {"productFilename": "jw01234_uncal.fits"},
                {"productFilename": "jw01234_x1d.fits"},
                {"productFilename": "jw01234_x1dints.fits"},
            ]
        )

    def _fake_download_products(products: object, *, download_dir: str) -> _FakeTable:
        return _FakeTable(
            [
                {"Local Path": f"{download_dir}/jw01234_x1d.fits"},
                {"Local Path": f"{download_dir}/jw01234_x1dints.fits"},
            ]
        )

    monkeypatch.setattr(astroquery_mast.Observations, "query_criteria", _fake_query_criteria)
    monkeypatch.setattr(astroquery_mast.Observations, "get_product_list", _fake_get_product_list)
    monkeypatch.setattr(astroquery_mast.Observations, "download_products", _fake_download_products)

    result = search_and_download_miri_lrs_spectra(
        "KIC 8462852", download_dir=tmp_path / "dl", limit=None
    )

    assert result.result_count == 1
    assert result.x1d_product_count == 2
    assert result.downloaded_count == 2
    assert all(p.endswith((".fits",)) for p in result.downloaded_paths)


def test_default_search_criteria_use_verified_miri_lrs_values(
    tmp_path: Path, monkeypatch
) -> None:
    captured: dict[str, object] = {}

    def _fake_query_criteria(**kwargs: object) -> _FakeTable:
        captured.update(kwargs)
        return _FakeTable([])

    monkeypatch.setattr(astroquery_mast.Observations, "query_criteria", _fake_query_criteria)

    search_and_download_miri_lrs_spectra("KIC 8462852", download_dir=tmp_path / "dl")

    assert captured["objectname"] == "KIC 8462852"
    assert captured["instrument_name"] == list(MIRI_LRS_INSTRUMENT_NAMES)
    assert captured["filters"] == MIRI_LRS_PRISM_FILTER
