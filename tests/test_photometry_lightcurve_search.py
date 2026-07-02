"""Tests for the real MAST light curve search/download wrapper.

Network access is stubbed out (this sandbox cannot reach MAST at all --
verified live, not assumed) so these tests exercise the real download-diff
and zero-result logic without touching the network.
"""

from __future__ import annotations

from pathlib import Path

from techno_search.photometry.lightcurve_search import search_and_download_lightcurves


class _FakeSearchResult:
    def __init__(self, count: int, download_dir: Path, file_names: list[str]) -> None:
        self._count = count
        self._download_dir = download_dir
        self._file_names = file_names

    def __len__(self) -> int:
        return self._count

    def __getitem__(self, key: object) -> _FakeSearchResult:
        return self

    def download_all(self, *, download_dir: str) -> None:
        out_dir = Path(download_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in self._file_names:
            (out_dir / name).write_bytes(b"fake fits bytes")


def test_zero_results_reports_no_download(tmp_path: Path, monkeypatch) -> None:
    import lightkurve as lk

    def _fake_search_lightcurve(target: str, **kwargs: object) -> _FakeSearchResult:
        return _FakeSearchResult(0, tmp_path, [])

    monkeypatch.setattr(lk, "search_lightcurve", _fake_search_lightcurve)

    result = search_and_download_lightcurves(
        "nonexistent-target", download_dir=tmp_path / "dl"
    )

    assert result.result_count == 0
    assert result.downloaded_count == 0
    assert result.downloaded_paths == ()


def test_download_counts_only_new_fits_files(tmp_path: Path, monkeypatch) -> None:
    import lightkurve as lk

    download_dir = tmp_path / "dl"
    download_dir.mkdir()
    (download_dir / "already_here.fits").write_bytes(b"pre-existing")

    def _fake_search_lightcurve(target: str, **kwargs: object) -> _FakeSearchResult:
        return _FakeSearchResult(3, download_dir, ["new_a.fits", "new_b.fits"])

    monkeypatch.setattr(lk, "search_lightcurve", _fake_search_lightcurve)

    result = search_and_download_lightcurves(
        "TIC 12345", download_dir=download_dir, limit=2
    )

    assert result.result_count == 3
    assert result.downloaded_count == 2
    assert all(name.endswith(".fits") for name in result.downloaded_paths)
    assert not any("already_here" in name for name in result.downloaded_paths)


def test_search_criteria_are_forwarded(tmp_path: Path, monkeypatch) -> None:
    import lightkurve as lk

    captured: dict[str, object] = {}

    def _fake_search_lightcurve(target: str, **kwargs: object) -> _FakeSearchResult:
        captured["target"] = target
        captured.update(kwargs)
        return _FakeSearchResult(0, tmp_path, [])

    monkeypatch.setattr(lk, "search_lightcurve", _fake_search_lightcurve)

    search_and_download_lightcurves(
        "KIC 8462852",
        download_dir=tmp_path / "dl",
        mission=("TESS",),
        sector=14,
    )

    assert captured["target"] == "KIC 8462852"
    assert captured["mission"] == ("TESS",)
    assert captured["sector"] == 14
