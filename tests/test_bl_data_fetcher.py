"""
Tests for scripts/bl_fetch.py — BL data fetcher + turboSETI pipeline helpers.

All network calls are replaced by in-process fakes so tests run offline.
Tests cover: HDF5 detection, probe_url, range download, parallel assembly,
simple fallback, synthetic H5 creation, pkg_resources shim, and the
parallel pipeline runner.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure scripts/ is importable
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import bl_fetch  # noqa: E402  (after sys.path patch)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HDF5_HEADER = b"\x89HDF\r\n\x1a\n" + b"\x00" * 512  # minimal HDF5-like bytes


def _make_hdf5_bytes() -> bytes:
    """Return bytes that start with the HDF5 magic signature."""
    return HDF5_HEADER


def _make_non_hdf5_bytes() -> bytes:
    return b"<html><body>Not a file</body></html>"


# ---------------------------------------------------------------------------
# is_hdf5
# ---------------------------------------------------------------------------


def test_is_hdf5_true(tmp_path: Path) -> None:
    f = tmp_path / "good.h5"
    f.write_bytes(_make_hdf5_bytes())
    assert bl_fetch.is_hdf5(f) is True


def test_is_hdf5_false_html(tmp_path: Path) -> None:
    f = tmp_path / "bad.h5"
    f.write_bytes(_make_non_hdf5_bytes())
    assert bl_fetch.is_hdf5(f) is False


def test_is_hdf5_missing_file(tmp_path: Path) -> None:
    assert bl_fetch.is_hdf5(tmp_path / "nonexistent.h5") is False


def test_is_hdf5_empty_file(tmp_path: Path) -> None:
    f = tmp_path / "empty.h5"
    f.write_bytes(b"")
    assert bl_fetch.is_hdf5(f) is False


def test_is_hdf5_accepts_string_path(tmp_path: Path) -> None:
    f = tmp_path / "good.h5"
    f.write_bytes(_make_hdf5_bytes())
    assert bl_fetch.is_hdf5(str(f)) is True


# ---------------------------------------------------------------------------
# probe_url
# ---------------------------------------------------------------------------


def _fake_head_with_range(url: str) -> dict[str, str]:
    return {"content-length": "1024", "accept-ranges": "bytes"}


def _fake_head_no_range(url: str) -> dict[str, str]:
    return {"content-length": "1024"}


def _fake_head_error(url: str) -> dict[str, str]:
    raise OSError("network error")


def test_probe_url_with_range() -> None:
    size, supports = bl_fetch.probe_url("http://example.com/file.h5", head_fn=_fake_head_with_range)
    assert size == 1024
    assert supports is True


def test_probe_url_no_range() -> None:
    size, supports = bl_fetch.probe_url("http://example.com/file.h5", head_fn=_fake_head_no_range)
    assert size == 1024
    assert supports is False


def test_probe_url_error_returns_none_false() -> None:
    size, supports = bl_fetch.probe_url("http://example.com/file.h5", head_fn=_fake_head_error)
    assert size is None
    assert supports is False


# ---------------------------------------------------------------------------
# plan_chunks
# ---------------------------------------------------------------------------


def test_plan_chunks_single_chunk() -> None:
    chunks = bl_fetch._plan_chunks(100, 1)
    assert len(chunks) == 1
    assert chunks[0] == (0, 99)


def test_plan_chunks_multiple_connections() -> None:
    # 16 MiB file, 4 connections → 4 chunks of 4 MiB each
    file_size = 16 * 1024 * 1024
    chunks = bl_fetch._plan_chunks(file_size, 4)
    assert len(chunks) == 4
    assert chunks[0][0] == 0
    assert chunks[-1][1] == file_size - 1
    # No gaps
    for i in range(len(chunks) - 1):
        assert chunks[i][1] + 1 == chunks[i + 1][0]


def test_plan_chunks_covers_full_file() -> None:
    file_size = 12_345_678
    chunks = bl_fetch._plan_chunks(file_size, 16)
    assert chunks[0][0] == 0
    assert chunks[-1][1] == file_size - 1


# ---------------------------------------------------------------------------
# download_range
# ---------------------------------------------------------------------------


def test_download_range_success(tmp_path: Path) -> None:
    data = b"A" * 512

    def _fake_get(url: str, headers: dict | None) -> bytes:
        assert headers is not None
        assert "Range" in headers
        return data

    chunk_file = tmp_path / "chunk_0000"
    ok = bl_fetch.download_range("http://x", 0, 511, chunk_file, get_fn=_fake_get)
    assert ok is True
    assert chunk_file.read_bytes() == data


def test_download_range_reuses_existing_chunk(tmp_path: Path) -> None:
    data = b"B" * 100
    chunk_file = tmp_path / "chunk_0000"
    chunk_file.write_bytes(data)  # already the correct size

    call_count = 0

    def _fake_get(url: str, headers: dict | None) -> bytes:
        nonlocal call_count
        call_count += 1
        return data

    ok = bl_fetch.download_range("http://x", 0, 99, chunk_file, get_fn=_fake_get)
    assert ok is True
    assert call_count == 0  # not re-downloaded


def test_download_range_network_error(tmp_path: Path) -> None:
    def _bad_get(url: str, headers: dict | None) -> bytes:
        raise OSError("timeout")

    chunk_file = tmp_path / "chunk_fail"
    ok = bl_fetch.download_range("http://x", 0, 99, chunk_file, get_fn=_bad_get)
    assert ok is False


# ---------------------------------------------------------------------------
# parallel_download + simple_download
# ---------------------------------------------------------------------------


def test_parallel_download_skips_existing_hdf5(tmp_path: Path) -> None:
    dest = tmp_path / "file.h5"
    dest.write_bytes(_make_hdf5_bytes())

    call_count = 0

    def _fake_head(url: str) -> dict:
        nonlocal call_count
        call_count += 1
        return {}

    ok = bl_fetch.parallel_download("http://x", dest, head_fn=_fake_head)
    assert ok is True
    assert call_count == 0  # did not probe because file already exists


def test_parallel_download_falls_back_when_no_range(tmp_path: Path) -> None:
    dest = tmp_path / "file.h5"
    hdf5_data = _make_hdf5_bytes()

    def _fake_head(url: str) -> dict:
        return {"content-length": str(len(hdf5_data))}  # no accept-ranges

    def _fake_get(url: str, headers: dict | None) -> bytes:
        return hdf5_data

    ok = bl_fetch.parallel_download(dest=dest, url="http://x", head_fn=_fake_head, get_fn=_fake_get)
    assert ok is True
    assert bl_fetch.is_hdf5(dest)


def test_simple_download_success(tmp_path: Path) -> None:
    dest = tmp_path / "file.h5"
    data = _make_hdf5_bytes()

    def _fake_get(url: str, headers: dict | None) -> bytes:
        return data

    ok = bl_fetch.simple_download("http://x", dest, get_fn=_fake_get)
    assert ok is True
    assert dest.read_bytes() == data


def test_simple_download_rejects_html(tmp_path: Path) -> None:
    dest = tmp_path / "file.h5"

    def _fake_get(url: str, headers: dict | None) -> bytes:
        return _make_non_hdf5_bytes()

    ok = bl_fetch.simple_download("http://x", dest, get_fn=_fake_get)
    assert ok is False
    assert not dest.exists()


def test_simple_download_network_error(tmp_path: Path) -> None:
    dest = tmp_path / "file.h5"

    def _bad_get(url: str, headers: dict | None) -> bytes:
        raise OSError("connection refused")

    ok = bl_fetch.simple_download("http://x", dest, get_fn=_bad_get)
    assert ok is False


def test_download_first_valid_skips_on_existing(tmp_path: Path) -> None:
    dest = tmp_path / "file.h5"
    dest.write_bytes(_make_hdf5_bytes())

    called_urls: list[str] = []

    def _fake_head(url: str) -> dict:
        called_urls.append(url)
        return {}

    ok = bl_fetch.download_first_valid(["http://a", "http://b"], dest, head_fn=_fake_head)
    assert ok is True
    assert called_urls == []  # no requests because file already exists


def test_download_first_valid_tries_next_on_failure(tmp_path: Path) -> None:
    dest = tmp_path / "file.h5"
    hdf5_data = _make_hdf5_bytes()
    call_count = [0]

    def _fake_head(url: str) -> dict:
        return {"content-length": str(len(hdf5_data))}  # no range support → simple_download

    def _fake_get(url: str, headers: dict | None) -> bytes:
        call_count[0] += 1
        if "bad" in url:
            return _make_non_hdf5_bytes()
        return hdf5_data

    ok = bl_fetch.download_first_valid(
        ["http://bad/file.h5", "http://good/file.h5"],
        dest,
        head_fn=_fake_head,
        get_fn=_fake_get,
    )
    assert ok is True
    assert call_count[0] == 2


# ---------------------------------------------------------------------------
# apply_pkg_resources_shim
# ---------------------------------------------------------------------------


def test_pkg_resources_shim_installs_get_distribution() -> None:
    # Temporarily remove pkg_resources to test fresh install
    saved = sys.modules.pop("pkg_resources", None)
    try:
        bl_fetch.apply_pkg_resources_shim()
        import pkg_resources as pr  # noqa: PLC0415

        # get_distribution should work for an installed package
        dist = pr.get_distribution("pytest")
        assert hasattr(dist, "version")
        assert dist.version  # non-empty
    finally:
        if saved is not None:
            sys.modules["pkg_resources"] = saved
        else:
            sys.modules.pop("pkg_resources", None)


def test_pkg_resources_shim_resource_filename() -> None:
    saved = sys.modules.pop("pkg_resources", None)
    try:
        bl_fetch.apply_pkg_resources_shim()
        import pkg_resources as pr  # noqa: PLC0415

        path = pr.resource_filename("pytest", "")
        assert isinstance(path, str)
        assert len(path) > 0
    finally:
        if saved is not None:
            sys.modules["pkg_resources"] = saved
        else:
            sys.modules.pop("pkg_resources", None)


def test_pkg_resources_shim_is_idempotent() -> None:
    saved = sys.modules.pop("pkg_resources", None)
    try:
        bl_fetch.apply_pkg_resources_shim()
        first_module = sys.modules["pkg_resources"]
        bl_fetch.apply_pkg_resources_shim()
        assert sys.modules["pkg_resources"] is first_module
    finally:
        if saved is not None:
            sys.modules["pkg_resources"] = saved
        else:
            sys.modules.pop("pkg_resources", None)


def test_pkg_resources_shim_distribution_not_found_is_exception() -> None:
    saved = sys.modules.pop("pkg_resources", None)
    try:
        bl_fetch.apply_pkg_resources_shim()
        import pkg_resources as pr  # noqa: PLC0415

        assert issubclass(pr.DistributionNotFound, Exception)
    finally:
        if saved is not None:
            sys.modules["pkg_resources"] = saved
        else:
            sys.modules.pop("pkg_resources", None)


# ---------------------------------------------------------------------------
# build_synthetic_h5
# ---------------------------------------------------------------------------


def test_build_synthetic_h5_creates_valid_hdf5(tmp_path: Path) -> None:
    pytest.importorskip("h5py")
    dest = tmp_path / "synth.h5"
    bl_fetch.build_synthetic_h5(dest)
    assert bl_fetch.is_hdf5(dest)


def test_build_synthetic_h5_has_required_headers(tmp_path: Path) -> None:
    h5py = pytest.importorskip("h5py")
    dest = tmp_path / "synth.h5"
    bl_fetch.build_synthetic_h5(dest)
    with h5py.File(dest, "r") as f:
        ds = f["data"]
        assert "fch1" in ds.attrs
        assert "foff" in ds.attrs
        assert "tsamp" in ds.attrs
        assert "nchans" in ds.attrs
        # Fix 3: headers on dataset, not root group
        assert "fch1" not in f.attrs


def test_build_synthetic_h5_data_shape(tmp_path: Path) -> None:
    h5py = pytest.importorskip("h5py")
    dest = tmp_path / "synth.h5"
    bl_fetch.build_synthetic_h5(dest)
    with h5py.File(dest, "r") as f:
        shape = f["data"].shape
    assert shape[0] == 16  # Fix 5: n_time = 16
    assert shape[1] == 1
    assert shape[2] == 65536


def test_build_synthetic_h5_source_name(tmp_path: Path) -> None:
    h5py = pytest.importorskip("h5py")
    dest = tmp_path / "synth.h5"
    bl_fetch.build_synthetic_h5(dest)
    with h5py.File(dest, "r") as f:
        name = f["data"].attrs["source_name"]
    assert b"SYNTH" in name


def test_build_synthetic_h5_deterministic(tmp_path: Path) -> None:
    h5py = pytest.importorskip("h5py")
    import numpy as np

    a = tmp_path / "a.h5"
    b = tmp_path / "b.h5"
    bl_fetch.build_synthetic_h5(a)
    bl_fetch.build_synthetic_h5(b)
    with h5py.File(a, "r") as fa, h5py.File(b, "r") as fb:
        np.testing.assert_array_equal(fa["data"][:], fb["data"][:])


# ---------------------------------------------------------------------------
# run_pipeline_parallel (mocked techno-search)
# ---------------------------------------------------------------------------


def test_run_pipeline_parallel_skips_existing(tmp_path: Path) -> None:
    dat = tmp_path / "test.dat"
    dat.write_text("# mock\n1 2 3\n")
    out_dir = tmp_path / "results"
    file_out_dir = out_dir / "test"
    file_out_dir.mkdir(parents=True)
    (file_out_dir / "test.manifest.json").write_text("{}")

    call_log: list[str] = []

    def _fake_run(cmd: list, **kwargs):  # type: ignore[override]
        call_log.extend(cmd)
        return MagicMock(returncode=0)

    with patch("subprocess.run", _fake_run):
        results = bl_fetch.run_pipeline_parallel(
            [str(dat)], out_dir, "techno-search", workers=1
        )

    assert results[str(dat)] is True
    assert not call_log  # was skipped


def test_run_pipeline_parallel_calls_techno_search(tmp_path: Path) -> None:
    dat = tmp_path / "signal.dat"
    dat.write_text("# header\n0.1 0.2 3\n")
    out_dir = tmp_path / "results"

    called_cmds: list[list[str]] = []

    def _fake_run(cmd: list, **kwargs):  # type: ignore[override]
        called_cmds.append(cmd)
        return MagicMock(returncode=0)

    with patch("subprocess.run", _fake_run):
        results = bl_fetch.run_pipeline_parallel(
            [str(dat)], out_dir, "/fake/techno-search", workers=1
        )

    assert results[str(dat)] is True
    assert len(called_cmds) == 1
    assert called_cmds[0][0] == "/fake/techno-search"
    assert called_cmds[0][1] == "run-pipeline"
    assert str(dat) in called_cmds[0]


def test_collect_dat_files_finds_nested_target_hit_tables(tmp_path: Path) -> None:
    dat_dir = tmp_path / "data"
    nested = dat_dir / "HIP99427" / "cadence_a"
    nested.mkdir(parents=True)
    top_level = dat_dir / "top.dat"
    child = nested / "hit.dat"
    top_level.write_text("# top\n")
    child.write_text("# child\n")
    (nested / "ignore.h5").write_text("not a hit table\n")

    assert bl_fetch.collect_dat_files(dat_dir) == sorted([top_level, child])


def test_run_pipeline_parallel_preserves_nested_output_paths(tmp_path: Path) -> None:
    dat_root = tmp_path / "data"
    dat = dat_root / "HIP99427" / "cadence_a" / "hit table.dat"
    dat.parent.mkdir(parents=True)
    dat.write_text("# header\n0.1 0.2 3\n")
    out_dir = tmp_path / "results"

    called_cmds: list[list[str]] = []

    def _fake_run(cmd: list, **kwargs):  # type: ignore[override]
        called_cmds.append(cmd)
        return MagicMock(returncode=0)

    with patch("subprocess.run", _fake_run):
        results = bl_fetch.run_pipeline_parallel(
            [str(dat)], out_dir, "/fake/techno-search", workers=1, dat_root=dat_root
        )

    expected_output = out_dir / "HIP99427" / "cadence_a" / "hit_table"
    assert results[str(dat)] is True
    assert expected_output.exists()
    assert called_cmds[0][called_cmds[0].index("--output-dir") + 1] == str(expected_output)
    assert called_cmds[0][called_cmds[0].index("--candidate-id") + 1] == (
        "HIP99427__cadence_a__hit_table"
    )


def test_run_pipeline_parallel_reports_failure(tmp_path: Path) -> None:
    dat = tmp_path / "bad.dat"
    dat.write_text("junk\n")
    out_dir = tmp_path / "results"

    def _fake_run(cmd: list, **kwargs):  # type: ignore[override]
        return MagicMock(returncode=1, stderr="pipeline error")

    with patch("subprocess.run", _fake_run):
        results = bl_fetch.run_pipeline_parallel(
            [str(dat)], out_dir, "techno-search", workers=1
        )

    assert results[str(dat)] is False


def test_run_pipeline_parallel_processes_multiple_files(tmp_path: Path) -> None:
    dats = [tmp_path / f"f{i}.dat" for i in range(3)]
    for d in dats:
        d.write_text("# data\n")
    out_dir = tmp_path / "results"

    def _fake_run(cmd: list, **kwargs):  # type: ignore[override]
        return MagicMock(returncode=0)

    with patch("subprocess.run", _fake_run):
        results = bl_fetch.run_pipeline_parallel(
            [str(d) for d in dats], out_dir, "techno-search", workers=3
        )

    assert len(results) == 3
    assert all(ok for ok in results.values())


# ---------------------------------------------------------------------------
# CLI main()
# ---------------------------------------------------------------------------


def test_main_is_hdf5_exit_0(tmp_path: Path) -> None:
    f = tmp_path / "good.h5"
    f.write_bytes(_make_hdf5_bytes())
    rc = bl_fetch.main(["is-hdf5", str(f)])
    assert rc == 0


def test_main_is_hdf5_exit_1(tmp_path: Path) -> None:
    f = tmp_path / "bad.h5"
    f.write_bytes(b"not hdf5")
    rc = bl_fetch.main(["is-hdf5", str(f)])
    assert rc == 1


def test_main_download_h5_success(tmp_path: Path) -> None:
    dest = tmp_path / "out.h5"
    hdf5_data = _make_hdf5_bytes()

    def _fake_head(url: str) -> dict:
        return {"content-length": str(len(hdf5_data))}

    def _fake_get(url: str, headers: dict | None) -> bytes:
        return hdf5_data

    with (
        patch.object(bl_fetch, "_default_head", _fake_head),
        patch.object(bl_fetch, "_default_get", _fake_get),
    ):
        rc = bl_fetch.main(["download-h5", str(dest), "--connections", "1"])

    assert rc == 0
    assert bl_fetch.is_hdf5(dest)


def test_main_download_h5_failure(tmp_path: Path) -> None:
    dest = tmp_path / "out.h5"

    def _fake_head(url: str) -> dict:
        raise OSError("unreachable")

    with patch.object(bl_fetch, "_default_head", _fake_head):
        rc = bl_fetch.main(
            ["download-h5", str(dest), "--url", "http://bad/file.h5"]
        )

    assert rc == 1
    assert not dest.exists()


def test_main_synthetic_h5(tmp_path: Path) -> None:
    pytest.importorskip("h5py")
    dest = tmp_path / "synth.h5"
    rc = bl_fetch.main(["synthetic-h5", str(dest)])
    assert rc == 0
    assert bl_fetch.is_hdf5(dest)


def test_main_run_pipeline_no_dat_files(tmp_path: Path) -> None:
    dat_dir = tmp_path / "data"
    dat_dir.mkdir()
    results = tmp_path / "results"
    rc = bl_fetch.main(["run-pipeline", str(dat_dir), str(results)])
    assert rc == 1


def test_main_run_pipeline_parallel_success(tmp_path: Path) -> None:
    dat_dir = tmp_path / "data"
    dat_dir.mkdir()
    (dat_dir / "hit.dat").write_text("# data\n1 2 3\n")
    results = tmp_path / "results"

    def _fake_run(cmd: list, **kwargs):  # type: ignore[override]
        return MagicMock(returncode=0)

    with patch("subprocess.run", _fake_run):
        rc = bl_fetch.main([
            "run-pipeline", str(dat_dir), str(results),
            "--workers", "1",
        ])

    assert rc == 0


def test_main_run_pipeline_discovers_nested_dat_files(tmp_path: Path) -> None:
    dat_dir = tmp_path / "data"
    nested = dat_dir / "HIP100670"
    nested.mkdir(parents=True)
    dat = nested / "hit.dat"
    dat.write_text("# data\n1 2 3\n")
    results = tmp_path / "results"

    called_cmds: list[list[str]] = []

    def _fake_run(cmd: list, **kwargs):  # type: ignore[override]
        called_cmds.append(cmd)
        return MagicMock(returncode=0)

    with patch("subprocess.run", _fake_run):
        rc = bl_fetch.main([
            "run-pipeline", str(dat_dir), str(results),
            "--workers", "1",
        ])

    assert rc == 0
    assert str(dat) in called_cmds[0]
    assert called_cmds[0][called_cmds[0].index("--candidate-id") + 1] == (
        "HIP100670__hit"
    )


# ---------------------------------------------------------------------------
# Script is importable and has __main__ block
# ---------------------------------------------------------------------------


def test_bl_fetch_module_constants() -> None:
    assert bl_fetch.HDF5_MAGIC == b"\x89HDF"
    assert bl_fetch.DEFAULT_CONNECTIONS == 16
    assert len(bl_fetch.VOYAGER_URLS) >= 2


def test_bl_fetch_module_has_required_functions() -> None:
    for name in [
        "is_hdf5",
        "probe_url",
        "download_range",
        "parallel_download",
        "simple_download",
        "download_first_valid",
        "apply_pkg_resources_shim",
        "build_synthetic_h5",
        "run_turboseti",
        "run_pipeline_parallel",
        "collect_dat_files",
        "main",
        "is_hdf5_bytes",
        "_is_lfs_pointer",
        "_parse_lfs_pointer",
        "_lfs_batch_href",
        "resolve_lfs_url",
        "_try_download_single",
        "configure_matplotlib_cache",
    ]:
        assert hasattr(bl_fetch, name), f"Missing function: {name}"


# ---------------------------------------------------------------------------
# configure_matplotlib_cache
# ---------------------------------------------------------------------------


def test_configure_matplotlib_cache_sets_ignored_cache_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_dir = tmp_path / "cache" / "matplotlib"
    monkeypatch.delenv("MPLCONFIGDIR", raising=False)

    configured = bl_fetch.configure_matplotlib_cache(cache_dir)

    assert configured == cache_dir
    assert cache_dir.is_dir()
    assert os.environ["MPLCONFIGDIR"] == str(cache_dir)
    assert logging.getLogger("matplotlib").level == logging.ERROR
    assert logging.getLogger("matplotlib.font_manager").level == logging.ERROR


def test_configure_matplotlib_cache_respects_existing_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = tmp_path / "already-configured"
    monkeypatch.setenv("MPLCONFIGDIR", str(existing))

    configured = bl_fetch.configure_matplotlib_cache(tmp_path / "unused")

    assert configured == existing
    assert not (tmp_path / "unused").exists()


# ---------------------------------------------------------------------------
# is_hdf5_bytes
# ---------------------------------------------------------------------------


def test_is_hdf5_bytes_true() -> None:
    assert bl_fetch.is_hdf5_bytes(_make_hdf5_bytes()) is True


def test_is_hdf5_bytes_false_html() -> None:
    assert bl_fetch.is_hdf5_bytes(_make_non_hdf5_bytes()) is False


def test_is_hdf5_bytes_too_short() -> None:
    assert bl_fetch.is_hdf5_bytes(b"\x89HD") is False


def test_is_hdf5_bytes_empty() -> None:
    assert bl_fetch.is_hdf5_bytes(b"") is False


# ---------------------------------------------------------------------------
# _is_lfs_pointer + _parse_lfs_pointer
# ---------------------------------------------------------------------------

_LFS_POINTER = (
    b"version https://git-lfs.github.com/spec/v1\n"
    b"oid sha256:abc123def456" + b"0" * 52 + b"\n"
    b"size 98765432\n"
)


def test_is_lfs_pointer_true() -> None:
    assert bl_fetch._is_lfs_pointer(_LFS_POINTER) is True


def test_is_lfs_pointer_false_hdf5() -> None:
    assert bl_fetch._is_lfs_pointer(_make_hdf5_bytes()) is False


def test_is_lfs_pointer_false_html() -> None:
    assert bl_fetch._is_lfs_pointer(_make_non_hdf5_bytes()) is False


def test_parse_lfs_pointer_valid() -> None:
    result = bl_fetch._parse_lfs_pointer(_LFS_POINTER)
    assert result is not None
    oid, size = result
    assert len(oid) == 64
    assert size == 98765432


def test_parse_lfs_pointer_invalid_returns_none() -> None:
    assert bl_fetch._parse_lfs_pointer(b"not a pointer") is None


def test_parse_lfs_pointer_missing_size_returns_none() -> None:
    data = b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"a" * 64 + b"\n"
    assert bl_fetch._parse_lfs_pointer(data) is None


# ---------------------------------------------------------------------------
# _lfs_server_from_url
# ---------------------------------------------------------------------------


def test_lfs_server_from_github_raw() -> None:
    url = "https://github.com/UCBerkeleySETI/turbo_seti/raw/master/tests/test_data/file.h5"
    server = bl_fetch._lfs_server_from_url(url)
    assert server == "https://github.com/UCBerkeleySETI/turbo_seti.git"


def test_lfs_server_from_media_githubusercontent() -> None:
    url = (
        "https://media.githubusercontent.com/media/UCBerkeleySETI/turbo_seti"
        "/master/tests/test_data/file.h5"
    )
    server = bl_fetch._lfs_server_from_url(url)
    assert server == "https://github.com/UCBerkeleySETI/turbo_seti.git"


def test_lfs_server_unrecognised_returns_none() -> None:
    assert bl_fetch._lfs_server_from_url("http://example.com/file.h5") is None


# ---------------------------------------------------------------------------
# _lfs_batch_href
# ---------------------------------------------------------------------------


def test_lfs_batch_href_returns_cdn_url() -> None:
    cdn_url = "https://objects.githubusercontent.com/github-production-release-asset/cdn/file.h5"

    def _fake_post(url: str, payload: bytes, headers: dict) -> bytes:
        import json
        assert "lfs/objects/batch" in url
        return json.dumps(
            {"objects": [{"actions": {"download": {"href": cdn_url}}}]}
        ).encode()

    href = bl_fetch._lfs_batch_href(
        "https://github.com/UCBerkeleySETI/turbo_seti.git",
        "a" * 64,
        12345678,
        post_fn=_fake_post,
    )
    assert href == cdn_url


def test_lfs_batch_href_returns_none_on_error() -> None:
    def _bad_post(url: str, payload: bytes, headers: dict) -> bytes:
        raise OSError("network unreachable")

    href = bl_fetch._lfs_batch_href(
        "https://github.com/UCBerkeleySETI/turbo_seti.git",
        "a" * 64,
        12345678,
        post_fn=_bad_post,
    )
    assert href is None


def test_lfs_batch_href_returns_none_on_missing_href() -> None:
    import json

    def _empty_post(url: str, payload: bytes, headers: dict) -> bytes:
        return json.dumps({"objects": [{}]}).encode()

    href = bl_fetch._lfs_batch_href(
        "https://github.com/UCBerkeleySETI/turbo_seti.git",
        "a" * 64,
        12345678,
        post_fn=_empty_post,
    )
    assert href is None


# ---------------------------------------------------------------------------
# resolve_lfs_url
# ---------------------------------------------------------------------------


def test_resolve_lfs_url_success() -> None:
    cdn_url = "https://cdn.example.com/file.h5"
    oid_hex = "a" * 64

    pointer = (
        b"version https://git-lfs.github.com/spec/v1\n"
        + f"oid sha256:{oid_hex}\n".encode()
        + b"size 12345678\n"
    )

    def _fake_post(url: str, payload: bytes, headers: dict) -> bytes:
        import json
        return json.dumps(
            {"objects": [{"actions": {"download": {"href": cdn_url}}}]}
        ).encode()

    source_url = "https://github.com/UCBerkeleySETI/turbo_seti/raw/master/tests/file.h5"
    result = bl_fetch.resolve_lfs_url(pointer, source_url, post_fn=_fake_post)
    assert result == cdn_url


def test_resolve_lfs_url_invalid_pointer_returns_none() -> None:
    result = bl_fetch.resolve_lfs_url(b"not a pointer", "https://github.com/o/r/raw/main/f.h5")
    assert result is None


def test_resolve_lfs_url_unknown_server_returns_none() -> None:
    oid_hex = "b" * 64
    pointer = (
        b"version https://git-lfs.github.com/spec/v1\n"
        + f"oid sha256:{oid_hex}\n".encode()
        + b"size 9999\n"
    )
    result = bl_fetch.resolve_lfs_url(pointer, "http://unknown.example.com/file.h5")
    assert result is None


# ---------------------------------------------------------------------------
# _try_download_single — LFS flow
# ---------------------------------------------------------------------------


def test_try_download_single_resolves_lfs_and_downloads(tmp_path: Path) -> None:
    dest = tmp_path / "out.h5"
    hdf5_data = _make_hdf5_bytes()
    oid_hex = "c" * 64
    cdn_url = "https://cdn.example.com/file.h5"

    lfs_pointer = (
        b"version https://git-lfs.github.com/spec/v1\n"
        + f"oid sha256:{oid_hex}\n".encode()
        + f"size {len(hdf5_data)}\n".encode()
    )

    def _fake_head(url: str) -> dict:
        if "cdn" in url:
            return {"content-length": str(len(hdf5_data)), "accept-ranges": "bytes"}
        # GitHub raw — does not report content-length for LFS pointers
        return {}

    def _fake_get(url: str, headers: dict | None) -> bytes:
        if "cdn" in url:
            if headers and "Range" in headers:
                return hdf5_data  # chunk
            return hdf5_data
        # GitHub raw URL returns LFS pointer
        return lfs_pointer

    def _fake_post(url: str, payload: bytes, headers: dict) -> bytes:
        import json
        return json.dumps(
            {"objects": [{"actions": {"download": {"href": cdn_url}}}]}
        ).encode()

    source_url = "https://github.com/UCBerkeleySETI/turbo_seti/raw/master/tests/file.h5"
    ok = bl_fetch._try_download_single(
        source_url, dest, connections=2,
        get_fn=_fake_get, head_fn=_fake_head, post_fn=_fake_post,
    )
    assert ok is True
    assert bl_fetch.is_hdf5(dest)


def test_try_download_single_direct_hdf5(tmp_path: Path) -> None:
    dest = tmp_path / "out.h5"
    hdf5_data = _make_hdf5_bytes()

    def _fake_head(url: str) -> dict:
        return {}  # no range support

    def _fake_get(url: str, headers: dict | None) -> bytes:
        return hdf5_data

    ok = bl_fetch._try_download_single(
        "http://example.com/file.h5", dest, connections=1,
        get_fn=_fake_get, head_fn=_fake_head,
    )
    assert ok is True
    assert bl_fetch.is_hdf5(dest)


def test_try_download_single_returns_false_on_non_hdf5_non_lfs(tmp_path: Path) -> None:
    dest = tmp_path / "out.h5"

    def _fake_head(url: str) -> dict:
        return {}

    def _fake_get(url: str, headers: dict | None) -> bytes:
        return b"<html>Portal</html>"

    ok = bl_fetch._try_download_single(
        "http://example.com/file.h5", dest, connections=1,
        get_fn=_fake_get, head_fn=_fake_head,
    )
    assert ok is False
    assert not dest.exists()


def test_try_download_single_skips_if_already_hdf5(tmp_path: Path) -> None:
    dest = tmp_path / "out.h5"
    dest.write_bytes(_make_hdf5_bytes())

    called = [False]

    def _fake_head(url: str) -> dict:
        called[0] = True
        return {}

    ok = bl_fetch._try_download_single(
        "http://example.com/file.h5", dest, connections=1,
        get_fn=None, head_fn=_fake_head,
    )
    assert ok is True
    assert not called[0]  # no network activity when file already valid


# ---------------------------------------------------------------------------
# download_first_valid — LFS integration
# ---------------------------------------------------------------------------


def test_download_first_valid_handles_lfs_pointer(tmp_path: Path) -> None:
    dest = tmp_path / "voyager.h5"
    hdf5_data = _make_hdf5_bytes()
    oid_hex = "d" * 64
    cdn_url = "https://cdn.example.com/voyager.h5"

    lfs_pointer = (
        b"version https://git-lfs.github.com/spec/v1\n"
        + f"oid sha256:{oid_hex}\n".encode()
        + f"size {len(hdf5_data)}\n".encode()
    )

    def _fake_head(url: str) -> dict:
        if "cdn" in url:
            return {"content-length": str(len(hdf5_data)), "accept-ranges": "bytes"}
        return {}

    def _fake_get(url: str, headers: dict | None) -> bytes:
        if "cdn" in url:
            return hdf5_data
        return lfs_pointer

    def _fake_post(url: str, payload: bytes, headers: dict) -> bytes:
        import json
        return json.dumps(
            {"objects": [{"actions": {"download": {"href": cdn_url}}}]}
        ).encode()

    ok = bl_fetch.download_first_valid(
        ["https://github.com/UCBerkeleySETI/turbo_seti/raw/master/tests/file.h5"],
        dest,
        connections=1,
        get_fn=_fake_get,
        head_fn=_fake_head,
        post_fn=_fake_post,
    )
    assert ok is True
    assert bl_fetch.is_hdf5(dest)
