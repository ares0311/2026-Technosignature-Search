#!/usr/bin/env python3
"""
bl_fetch.py — Resumable parallel BL data fetch + turboSETI pipeline helper.

Subcommands (called from shell scripts):
  download-h5   Download Voyager 1 H5 from known URLs, resumable + parallel.
  synthetic-h5  Build synthetic BL-format H5 for pipeline smoke-testing.
  run-turboseti Run turboSETI FindDoppler on an H5 file.
  run-pipeline  Run techno-search run-pipeline on .dat files (parallel).
  is-hdf5       Check if a file is valid HDF5 (exits 0 = yes, 1 = no).

All network access is resumable:
  - HTTP range requests split file into chunks (DEFAULT_CONNECTIONS per file).
  - Each chunk is saved to .chunks_<filename>/chunk_NNNN before assembly.
  - On restart, chunks with the correct size are reused automatically.
  - No-range servers fall back to simple streaming; .part file guards partial
    writes but range-based resume is not possible for those servers.

All Python calls must use .venv/bin/python (never bare python3).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import glob
import importlib.metadata
import importlib.util
import json
import logging
import os
import re
import ssl
import subprocess
import sys
import types
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

# ---------------------------------------------------------------------------
# SSL context (uses certifi CA bundle when available; falls back to default)
# ---------------------------------------------------------------------------

def _make_ssl_ctx() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()

_SSL_CTX = _make_ssl_ctx()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HDF5_MAGIC = b"\x89HDF"
DEFAULT_CONNECTIONS = 16  # gigabit wifi + M4 Max NIC throughput
CHUNK_SIZE = 4 * 1024 * 1024  # 4 MiB per chunk
DOWNLOAD_TIMEOUT = 120  # seconds per chunk/request

VOYAGER_URLS = [
    "https://github.com/UCBerkeleySETI/turbo_seti/raw/master/tests/test_data"
    "/Voyager1.single_coarse.fine_res.h5",
    "https://media.githubusercontent.com/media/UCBerkeleySETI/turbo_seti/master"
    "/tests/test_data/Voyager1.single_coarse.fine_res.h5",
    "http://blpd0.ssl.berkeley.edu/Voyager_data/Voyager1.single_coarse.fine_res.h5",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HDF5 detection
# ---------------------------------------------------------------------------


def is_hdf5(path: str | Path) -> bool:
    """Return True if the file starts with the HDF5 magic signature."""
    p = Path(path)
    if not p.is_file() or p.stat().st_size < 4:
        return False
    with open(p, "rb") as fh:
        return fh.read(4) == HDF5_MAGIC


def is_hdf5_bytes(data: bytes) -> bool:
    """Return True if the first 4 bytes are the HDF5 magic signature."""
    return len(data) >= 4 and data[:4] == HDF5_MAGIC


# ---------------------------------------------------------------------------
# Git LFS pointer resolution
# ---------------------------------------------------------------------------

_LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def _is_lfs_pointer(data: bytes) -> bool:
    """Return True if data looks like a Git LFS pointer file."""
    return data[:42] == _LFS_POINTER_PREFIX


def _parse_lfs_pointer(data: bytes) -> tuple[str, int] | None:
    """
    Parse a Git LFS pointer and return (oid_hex, size_bytes).
    Returns None if the pointer cannot be parsed.
    """
    text = data.decode("utf-8", errors="replace")
    oid_m = re.search(r"oid sha256:([0-9a-f]{64})", text)
    size_m = re.search(r"size (\d+)", text)
    if not oid_m or not size_m:
        return None
    return oid_m.group(1), int(size_m.group(1))


def _lfs_batch_href(
    lfs_server: str,
    oid: str,
    size: int,
    post_fn: Callable[[str, bytes, dict[str, str]], bytes] | None = None,
) -> str | None:
    """
    POST to the GitHub LFS Batch API and return the CDN download URL.

    lfs_server: e.g. "https://github.com/UCBerkeleySETI/turbo_seti.git"
    Returns None on failure.
    """
    batch_url = f"{lfs_server}/info/lfs/objects/batch"
    payload = json.dumps(
        {"operation": "download", "objects": [{"oid": oid, "size": size}]}
    ).encode()
    req_headers = {
        "Content-Type": "application/vnd.git-lfs+json",
        "Accept": "application/vnd.git-lfs+json",
    }

    try:
        if post_fn is not None:
            body = post_fn(batch_url, payload, req_headers)
        else:
            req = urllib.request.Request(
                batch_url, data=payload, headers=req_headers, method="POST"
            )
            with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp:
                body = resp.read()

        resp_data = json.loads(body)
        href = (
            resp_data.get("objects", [{}])[0]
            .get("actions", {})
            .get("download", {})
            .get("href")
        )
        return href if isinstance(href, str) else None
    except Exception as exc:
        log.debug("LFS batch API failed for %s: %s", batch_url, exc)
        return None


def _lfs_server_from_url(source_url: str) -> str | None:
    """
    Infer the LFS server URL from a GitHub raw content URL.

    "https://github.com/OWNER/REPO/raw/..." → "https://github.com/OWNER/REPO.git"
    "https://raw.githubusercontent.com/OWNER/REPO/..." → "https://github.com/OWNER/REPO.git"
    "https://media.githubusercontent.com/media/OWNER/REPO/..." → "https://github.com/OWNER/REPO.git"
    """
    # media.githubusercontent.com has an extra /media/ prefix
    m_media = re.search(
        r"https://media\.githubusercontent\.com/media/([^/]+/[^/]+)/",
        source_url,
    )
    if m_media:
        return f"https://github.com/{m_media.group(1)}.git"

    m = re.search(
        r"https://(?:github\.com|raw\.githubusercontent\.com)/"
        r"([^/]+/[^/]+?)(?:\.git)?(?:/(?:raw|blob|refs|master|main|[^/]+).*)?$",
        source_url,
    )
    if m:
        return f"https://github.com/{m.group(1)}.git"
    return None


def resolve_lfs_url(
    lfs_data: bytes,
    source_url: str,
    post_fn: Callable[[str, bytes, dict[str, str]], bytes] | None = None,
) -> str | None:
    """
    Given LFS pointer bytes and the URL they came from, return the CDN URL.
    Returns None if resolution fails.
    """
    parsed = _parse_lfs_pointer(lfs_data)
    if parsed is None:
        log.warning("Could not parse LFS pointer.")
        return None
    oid, size = parsed

    lfs_server = _lfs_server_from_url(source_url)
    if lfs_server is None:
        log.warning("Could not infer LFS server from URL: %s", source_url)
        return None

    log.info("  LFS pointer detected; querying Batch API for oid %s...", oid[:16])
    href = _lfs_batch_href(lfs_server, oid, size, post_fn=post_fn)
    if href:
        log.info("  LFS CDN URL obtained.")
    else:
        log.warning("  LFS Batch API returned no download URL.")
    return href


# ---------------------------------------------------------------------------
# SSL-unverified GET (for Berkeley blpd0 self-signed cert)
# ---------------------------------------------------------------------------


def _ssl_unverified_get(url: str, headers: dict[str, str] | None = None) -> bytes:
    """
    Issue GET with SSL certificate verification disabled.
    Used only for blpd0.ssl.berkeley.edu which has a self-signed cert.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, context=ctx, timeout=DOWNLOAD_TIMEOUT) as resp:
        return resp.read()


# ---------------------------------------------------------------------------
# HTTP helpers (injectable for tests)
# ---------------------------------------------------------------------------

HeadFn = Callable[[str], dict[str, str]]
GetFn = Callable[[str, dict[str, str] | None], bytes]


def _default_head(url: str) -> dict[str, str]:
    """Issue HEAD request and return response headers (lower-cased keys)."""
    req = urllib.request.Request(url, method="HEAD")
    ctx = None if url.startswith("http://") else _SSL_CTX
    with urllib.request.urlopen(req, context=ctx, timeout=DOWNLOAD_TIMEOUT) as resp:
        return {k.lower(): v for k, v in resp.headers.items()}


def _default_get(url: str, headers: dict[str, str] | None = None) -> bytes:
    """Issue GET request (with optional headers) and return body bytes."""
    req = urllib.request.Request(url, headers=headers or {})
    ctx = None if url.startswith("http://") else _SSL_CTX
    with urllib.request.urlopen(req, context=ctx, timeout=DOWNLOAD_TIMEOUT) as resp:
        return resp.read()


def probe_url(
    url: str,
    head_fn: HeadFn | None = None,
) -> tuple[int | None, bool]:
    """
    Return (content_length, supports_range).
    content_length is None if the server does not report it.
    supports_range is True only if Accept-Ranges: bytes is present.
    """
    fn = head_fn or _default_head
    try:
        hdrs = fn(url)
        size_str = hdrs.get("content-length", "0")
        size = int(size_str) if size_str.isdigit() else None
        supports_range = hdrs.get("accept-ranges", "").lower() == "bytes"
        return size, supports_range
    except Exception as exc:
        log.debug("probe_url %s failed: %s", url, exc)
        return None, False


# ---------------------------------------------------------------------------
# Parallel chunk download
# ---------------------------------------------------------------------------


def download_range(
    url: str,
    start: int,
    end: int,
    chunk_file: Path,
    get_fn: GetFn | None = None,
) -> bool:
    """
    Download bytes [start, end] from url into chunk_file.
    Idempotent: if chunk_file already has the correct size, skip the request.
    Returns True on success.
    """
    expected = end - start + 1
    if chunk_file.is_file() and chunk_file.stat().st_size == expected:
        return True  # already downloaded this chunk

    fn = get_fn or _default_get
    try:
        data = fn(url, {"Range": f"bytes={start}-{end}"})
        chunk_file.write_bytes(data)
        return chunk_file.stat().st_size == expected
    except Exception as exc:
        log.warning("  chunk %s failed: %s", chunk_file.name, exc)
        return False


def _plan_chunks(
    file_size: int,
    connections: int,
) -> list[tuple[int, int]]:
    """Return list of (start, end) byte ranges for the given file size."""
    chunk_size = max(CHUNK_SIZE, (file_size + connections - 1) // connections)
    ranges: list[tuple[int, int]] = []
    pos = 0
    while pos < file_size:
        end = min(pos + chunk_size - 1, file_size - 1)
        ranges.append((pos, end))
        pos = end + 1
    return ranges


def parallel_download(
    url: str,
    dest: Path,
    connections: int = DEFAULT_CONNECTIONS,
    get_fn: GetFn | None = None,
    head_fn: HeadFn | None = None,
) -> bool:
    """
    Download url → dest using parallel range requests.

    Resume behaviour:
    - Chunk files under .chunks_<dest.name>/ are reused if they have the
      expected byte count.  Stop the script and restart at any time.
    - If the server does not support range requests, falls back to
      simple_download (no chunk-level resume, but .part protects dest).

    Returns True if dest is a valid HDF5 after download.
    """
    if is_hdf5(dest):
        log.info("  Already have complete HDF5: %s", dest)
        return True

    file_size, supports_range = probe_url(url, head_fn=head_fn)

    if not supports_range or not file_size:
        log.info("  Server does not support range requests; using simple download.")
        return simple_download(url, dest, get_fn=get_fn)

    chunk_dir = dest.parent / f".chunks_{dest.name}"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    ranges = _plan_chunks(file_size, connections)
    log.info(
        "  Parallel download: %s bytes in %d chunks (%d connections)",
        f"{file_size:,}",
        len(ranges),
        min(connections, len(ranges)),
    )

    chunk_files = [chunk_dir / f"chunk_{i:04d}" for i in range(len(ranges))]

    fn = get_fn or _default_get

    ok_flags: list[bool] = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(connections, len(ranges))
    ) as pool:
        futures = {
            pool.submit(download_range, url, s, e, cf, fn): (s, e, cf)
            for (s, e), cf in zip(ranges, chunk_files, strict=True)
        }
        for future in concurrent.futures.as_completed(futures):
            ok_flags.append(future.result())

    failed = ok_flags.count(False)
    if failed:
        log.error("  %d chunk(s) failed. Partial chunks saved; re-run to resume.", failed)
        return False

    # Assemble
    part = dest.parent / f"{dest.name}.part"
    with open(part, "wb") as out:
        for cf in chunk_files:
            out.write(cf.read_bytes())

    if not is_hdf5(part):
        log.error("  Assembled file is not HDF5 (server may have returned HTML).")
        part.unlink(missing_ok=True)
        return False

    part.rename(dest)
    import shutil

    shutil.rmtree(chunk_dir, ignore_errors=True)
    log.info("  Download complete: %s (%s bytes)", dest.name, f"{dest.stat().st_size:,}")
    return True


def simple_download(
    url: str,
    dest: Path,
    get_fn: GetFn | None = None,
) -> bool:
    """
    Stream-download url → dest via a single connection.
    Uses dest.parent/<name>.part as a partial-file guard.
    Returns True if dest is valid HDF5.
    """
    part = dest.parent / f"{dest.name}.part"
    fn = get_fn or _default_get
    try:
        log.info("  Streaming download (no range support): %s", url)
        data = fn(url, None)
        part.write_bytes(data)
    except Exception as exc:
        log.error("  Download failed: %s", exc)
        return False

    if not is_hdf5(part):
        log.error("  Response is not HDF5 (server returned HTML or redirect).")
        part.unlink(missing_ok=True)
        return False

    part.rename(dest)
    log.info("  Downloaded: %s (%s bytes)", dest.name, f"{dest.stat().st_size:,}")
    return True


def _try_download_single(
    url: str,
    dest: Path,
    connections: int,
    get_fn: GetFn | None,
    head_fn: HeadFn | None,
    post_fn: Callable[[str, bytes, dict[str, str]], bytes] | None = None,
) -> bool:
    """
    Attempt to download url → dest as HDF5, handling:
    - Git LFS pointer files: resolve via Batch API then parallel-download CDN URL
    - Berkeley blpd0 self-signed cert: use SSL-unverified GET
    - Normal parallel range download

    Returns True if dest is valid HDF5.
    """
    if is_hdf5(dest):
        return True

    # Choose appropriate GET function
    effective_get = get_fn
    if effective_get is None and "blpd0.ssl.berkeley.edu" in url:
        effective_get = _ssl_unverified_get

    # Try parallel download first (probes for range support)
    file_size, supports_range = probe_url(url, head_fn=head_fn)

    if supports_range and file_size:
        # Server supports range — parallel download directly
        ok = parallel_download(
            url, dest, connections=connections, get_fn=effective_get, head_fn=head_fn
        )
        if ok:
            return True
        # parallel_download may have assembled a non-HDF5 (LFS pointer assembled)
        # Fall through to check the assembled content below

    # Single-stream probe to check for LFS pointer or get the file
    try:
        fn = effective_get or _default_get
        probe_data = fn(url, None)
    except Exception as exc:
        log.warning("  Probe GET failed: %s", exc)
        return False

    if is_hdf5_bytes(probe_data):
        # Small file or server returned everything at once
        part = dest.parent / f"{dest.name}.part"
        part.write_bytes(probe_data)
        part.rename(dest)
        log.info("  Downloaded (single stream): %s (%s bytes)", dest.name, f"{len(probe_data):,}")
        return True

    if _is_lfs_pointer(probe_data):
        real_url = resolve_lfs_url(probe_data, url, post_fn=post_fn)
        if real_url:
            log.info("  Downloading from LFS CDN: %s", real_url[:80])
            return parallel_download(
                real_url, dest, connections=connections, get_fn=get_fn, head_fn=head_fn
            )
        log.warning("  LFS resolution failed for: %s", url)
        return False

    log.warning("  Response is not HDF5 and not an LFS pointer (%d bytes).", len(probe_data))
    return False


def download_first_valid(
    urls: list[str],
    dest: Path,
    connections: int = DEFAULT_CONNECTIONS,
    get_fn: GetFn | None = None,
    head_fn: HeadFn | None = None,
    post_fn: Callable[[str, bytes, dict[str, str]], bytes] | None = None,
) -> bool:
    """
    Try each url in order until dest is a valid HDF5.
    Resumable: existing chunks/part files from a previous attempt are reused.
    Handles Git LFS pointer resolution and SSL-unverified connections.
    """
    if is_hdf5(dest):
        log.info("Already have valid HDF5: %s", dest)
        return True

    for url in urls:
        log.info("Trying: %s", url)
        ok = _try_download_single(
            url, dest, connections=connections,
            get_fn=get_fn, head_fn=head_fn, post_fn=post_fn,
        )
        if ok:
            return True
        log.warning("  URL did not yield valid HDF5; trying next.")

    return False


# ---------------------------------------------------------------------------
# pkg_resources shim (all 6 turboSETI Python 3.13+ fixes)
# ---------------------------------------------------------------------------


def apply_pkg_resources_shim() -> None:
    """
    Install a minimal pkg_resources shim for Python 3.13+ where the package
    was removed.  Covers all import sites used by turboSETI:
      Fix 1: get_distribution
      Fix 6: resource_filename (Python 3.14 regression)
    """
    if "pkg_resources" in sys.modules:
        return

    pkg = types.ModuleType("pkg_resources")

    def _get_dist(name: str) -> object:
        class _D:
            version = importlib.metadata.version(name)

        return _D()

    pkg.get_distribution = _get_dist  # type: ignore[attr-defined]
    pkg.DistributionNotFound = Exception  # type: ignore[attr-defined]

    def _resource_filename(package_name: object, resource_name: str) -> str:
        if not isinstance(package_name, str):
            package_name = getattr(package_name, "__name__", str(package_name))
        top = str(package_name).split(".")[0]
        spec = importlib.util.find_spec(top)
        if spec and spec.submodule_search_locations:
            base = list(spec.submodule_search_locations)[0]
            return os.path.join(base, resource_name.replace("/", os.sep).lstrip(os.sep))
        return resource_name

    pkg.resource_filename = _resource_filename  # type: ignore[attr-defined]
    pkg.resource_stream = None  # type: ignore[attr-defined]
    sys.modules["pkg_resources"] = pkg


# ---------------------------------------------------------------------------
# drift_indexes bootstrap
# ---------------------------------------------------------------------------


def ensure_drift_indexes() -> None:
    """
    Download turboSETI drift_indexes text files from GitHub if absent.
    Fix 2: required at the turbo_seti package root.
    """
    import turbo_seti as _ts

    pkg_dir = os.path.dirname(os.path.abspath(_ts.__file__))
    drift_dir = os.path.join(pkg_dir, "drift_indexes")
    os.makedirs(drift_dir, exist_ok=True)

    avail = sorted(glob.glob(os.path.join(drift_dir, "drift_indexes_array_*.txt")))
    if avail:
        return

    base = (
        "https://raw.githubusercontent.com/UCBerkeleySETI/turbo_seti"
        "/master/turbo_seti/drift_indexes"
    )
    for pow_ in range(2, 12):
        fname = f"drift_indexes_array_{pow_}.txt"
        log.info("  Downloading drift index: %s", fname)
        urllib.request.urlretrieve(f"{base}/{fname}", os.path.join(drift_dir, fname))


# ---------------------------------------------------------------------------
# turboSETI runner
# ---------------------------------------------------------------------------


def run_turboseti(h5_path: str | Path, out_dir: str | Path) -> None:
    """
    Run turboSETI FindDoppler on h5_path, writing .dat hit table to out_dir.
    Applies all 6 Python 3.13+ fixes before importing turboSETI.
    """
    apply_pkg_resources_shim()
    ensure_drift_indexes()

    from turbo_seti.find_doppler.find_doppler import FindDoppler  # type: ignore[import]

    fd = FindDoppler(
        str(h5_path),
        max_drift=4,
        min_drift=1e-4,
        snr=10,
        out_dir=str(out_dir),
        log_level_int=30,
    )
    fd.search()


# ---------------------------------------------------------------------------
# Synthetic H5 builder
# ---------------------------------------------------------------------------


def build_synthetic_h5(dest: Path) -> None:
    """
    Build a synthetic BL-format HDF5 with a narrowband drifting signal
    that mimics the Voyager 1 X-band carrier.

    All headers are stored on the DATA DATASET (ds.attrs), not on the root
    group — Fix 3: blimpy reads from ds.attrs, not f.attrs.
    Fix 5: n_time = 16 (2^4, minimum drift_index power).
    """
    import h5py  # type: ignore[import]
    import numpy as np  # type: ignore[import]

    fch1, foff, tsamp = 8421.386719, -2.7939677e-6, 18.25361
    n_chans, n_time = 65536, 16

    rng = np.random.default_rng(42)
    data = rng.normal(500.0, 20.0, (n_time, 1, n_chans)).astype(np.float32)

    sig_chan = int((8421.295 - fch1) / foff)
    drift_cp = 0.38 * tsamp / (abs(foff) * 1e6)
    for t in range(n_time):
        c = int(sig_chan + t * drift_cp)
        if 0 <= c < n_chans:
            data[t, 0, c] += 1500.0

    with h5py.File(dest, "w") as f:
        f.attrs["CLASS"] = "FILTERBANK"
        f.attrs["VERSION"] = "1.0"
        ds = f.create_dataset("data", data=data, compression="lzf")
        ds.dims[0].label = b"time"
        ds.dims[1].label = b"feed_id"
        ds.dims[2].label = b"frequency"
        for k, v in [
            ("fch1", np.float64(fch1)),
            ("foff", np.float64(foff)),
            ("tsamp", np.float64(tsamp)),
            ("tstart", np.float64(59046.9263)),
            ("nchans", np.int64(n_chans)),
            ("nifs", np.int64(1)),
            ("nbits", np.int64(32)),
            ("data_type", np.int64(1)),
            ("machine_id", np.int64(20)),
            ("telescope_id", np.int64(6)),
            ("source_name", np.bytes_("SYNTH_BL_TIER1")),
            ("rawdatafile", np.bytes_("")),
            ("az_start", np.float64(0.0)),
            ("za_start", np.float64(0.0)),
            ("src_raj", np.float64(17.2112)),
            ("src_dej", np.float64(12.4038)),
        ]:
            ds.attrs[k] = v
    log.info("Synthetic H5: %s  shape=%s", dest, data.shape)


# ---------------------------------------------------------------------------
# Parallel pipeline runner
# ---------------------------------------------------------------------------


def run_pipeline_parallel(
    dat_files: list[str],
    results_dir: Path,
    techno_search_bin: str,
    workers: int = 12,
) -> dict[str, bool]:
    """
    Run `techno-search run-pipeline` on each .dat file in parallel.

    Idempotent: files whose output directory already contains a manifest.json
    are skipped.  Workers = 12 matches M4 Max performance core count.

    Returns {dat_path: success_bool} for all inputs.
    """

    def _process(dat: str) -> tuple[str, bool]:
        out_dir = results_dir / Path(dat).stem
        out_dir.mkdir(parents=True, exist_ok=True)

        # Idempotent skip
        if list(out_dir.glob("*.manifest.json")):
            log.info("  Skipping (manifest exists): %s", Path(dat).name)
            return dat, True

        log.info("  Processing: %s", Path(dat).name)
        cmd = [techno_search_bin, "run-pipeline", dat,
               "--track", "radio", "--output-dir", str(out_dir)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            log.error("  FAILED %s:\n%s", Path(dat).name, result.stderr[-500:])
        else:
            log.info("  OK: %s", Path(dat).name)
        return dat, result.returncode == 0

    results: dict[str, bool] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, len(dat_files))) as pool:
        for dat, ok in pool.map(_process, dat_files):
            results[dat] = ok
    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bl_fetch.py",
        description="BL data fetch + turboSETI helpers (resumable, parallel).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # download-h5
    p_dl = sub.add_parser("download-h5", help="Download Voyager 1 H5 (resumable + parallel).")
    p_dl.add_argument("dest", type=Path, help="Output HDF5 file path.")
    p_dl.add_argument(
        "--connections",
        type=int,
        default=DEFAULT_CONNECTIONS,
        help=f"Parallel connections (default {DEFAULT_CONNECTIONS}).",
    )
    p_dl.add_argument("--url", action="append", dest="urls", help="Override URL list (repeatable).")

    # synthetic-h5
    p_syn = sub.add_parser("synthetic-h5", help="Build synthetic BL-format HDF5.")
    p_syn.add_argument("dest", type=Path, help="Output HDF5 file path.")

    # run-turboseti
    p_ts = sub.add_parser("run-turboseti", help="Run turboSETI FindDoppler on an H5.")
    p_ts.add_argument("h5", type=Path, help="Input HDF5 file.")
    p_ts.add_argument("out_dir", type=Path, help="Directory to write .dat hit table.")

    # run-pipeline
    p_rp = sub.add_parser(
        "run-pipeline",
        help="Run techno-search run-pipeline on .dat files (parallel).",
    )
    p_rp.add_argument("dat_dir", type=Path, help="Directory containing .dat files.")
    p_rp.add_argument("results_dir", type=Path, help="Directory for output reports.")
    p_rp.add_argument(
        "--techno-search",
        default=str(Path(sys.executable).parent / "techno-search"),
        help="Path to techno-search binary.",
    )
    p_rp.add_argument(
        "--workers",
        type=int,
        default=12,
        help="Parallel workers (default 12, matches M4 Max perf cores).",
    )

    # is-hdf5
    p_hdf = sub.add_parser("is-hdf5", help="Check if file is valid HDF5 (exit 0=yes).")
    p_hdf.add_argument("path", type=Path)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.cmd == "download-h5":
        args.dest.parent.mkdir(parents=True, exist_ok=True)
        urls = args.urls or VOYAGER_URLS
        ok = download_first_valid(urls, args.dest, connections=args.connections)
        if ok:
            log.info("SUCCESS: %s", args.dest)
            return 0
        log.error("All URLs failed. Re-run to resume partial chunks.")
        return 1

    if args.cmd == "synthetic-h5":
        args.dest.parent.mkdir(parents=True, exist_ok=True)
        build_synthetic_h5(args.dest)
        return 0

    if args.cmd == "run-turboseti":
        args.out_dir.mkdir(parents=True, exist_ok=True)
        run_turboseti(args.h5, args.out_dir)
        return 0

    if args.cmd == "run-pipeline":
        dat_files = sorted(str(p) for p in args.dat_dir.glob("*.dat"))
        if not dat_files:
            log.error("No .dat files found in %s", args.dat_dir)
            return 1
        log.info("Running pipeline on %d file(s) with %d workers ...", len(dat_files), args.workers)
        args.results_dir.mkdir(parents=True, exist_ok=True)
        results = run_pipeline_parallel(
            dat_files, args.results_dir, args.techno_search, workers=args.workers
        )
        failed = [d for d, ok in results.items() if not ok]
        log.info("Done: %d OK, %d failed", len(results) - len(failed), len(failed))
        if failed:
            for f in failed:
                log.error("  FAILED: %s", f)
            return 1
        return 0

    if args.cmd == "is-hdf5":
        if is_hdf5(args.path):
            log.info("%s is valid HDF5", args.path)
            return 0
        log.info("%s is NOT valid HDF5", args.path)
        return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
