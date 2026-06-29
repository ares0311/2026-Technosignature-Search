#!/usr/bin/env python3
"""Download, verify, process, and combine an approved GBT cadence."""

from __future__ import annotations

import argparse
import glob
import importlib.metadata
import importlib.util
import json
import logging
import os
import shutil
import ssl
import sys
import types
import urllib.request
import warnings
from pathlib import Path
from typing import Any

import certifi

from techno_search.gbt_cadence import (
    apply_turboseti_numpy_compatibility,
    build_cadence_csv,
    download_archive_file,
    load_cadence_manifest,
    write_hit_provenance,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MPLCONFIGDIR = REPO_ROOT / "cache" / "matplotlib"


def _configure_matplotlib_cache(cache_dir: Path | None = None) -> Path:
    """Set a writable ignored Matplotlib cache before turboSETI imports it."""
    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    configured = os.environ.get("MPLCONFIGDIR")
    if configured:
        return Path(configured)
    target = cache_dir or DEFAULT_MPLCONFIGDIR
    target.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(target)
    return target


def _install_pkg_resources_compatibility() -> None:
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="pkg_resources is deprecated as an API.*",
            )
            import pkg_resources  # noqa: F401
    except ImportError:
        module = types.ModuleType("pkg_resources")

        class DistributionNotFound(Exception):
            pass

        def get_distribution(name: str) -> object:
            try:
                distribution = importlib.metadata.distribution(name)
            except importlib.metadata.PackageNotFoundError as exc:
                raise DistributionNotFound(name) from exc
            return types.SimpleNamespace(version=distribution.version)

        def resource_filename(package: str, resource: str) -> str:
            spec = importlib.util.find_spec(package)
            if spec is None:
                raise DistributionNotFound(package)
            if spec.submodule_search_locations:
                root = Path(next(iter(spec.submodule_search_locations)))
            elif spec.origin:
                root = Path(spec.origin).parent
            else:
                raise DistributionNotFound(package)
            return str(root / resource)

        module.DistributionNotFound = DistributionNotFound
        module.get_distribution = get_distribution
        module.require = lambda *_args, **_kwargs: None
        module.resource_filename = resource_filename
        sys.modules["pkg_resources"] = module


def _ensure_drift_indexes(package_dir: Path) -> None:
    drift_dir = package_dir / "drift_indexes"
    drift_dir.mkdir(parents=True, exist_ok=True)
    if list(drift_dir.glob("drift_indexes_array_*.txt")):
        return
    base = (
        "https://raw.githubusercontent.com/UCBerkeleySETI/"
        "turbo_seti/master/turbo_seti/drift_indexes"
    )
    context = ssl.create_default_context(cafile=certifi.where())
    for power in range(2, 12):
        filename = f"drift_indexes_array_{power}.txt"
        try:
            with (
                urllib.request.urlopen(f"{base}/{filename}", context=context) as response,
                (drift_dir / filename).open("wb") as handle,
            ):
                shutil.copyfileobj(response, handle)
        except Exception:
            continue
    if not list(drift_dir.glob("drift_indexes_array_*.txt")):
        raise RuntimeError("Unable to obtain turboSETI drift-index files.")


def _run_turboseti(
    hdf5_path: Path,
    output_dir: Path,
    analysis: dict[str, Any],
) -> tuple[Path, str]:
    _configure_matplotlib_cache()
    _install_pkg_resources_compatibility()
    package_spec = importlib.util.find_spec("turbo_seti")
    if package_spec is None or not package_spec.submodule_search_locations:
        raise RuntimeError("turboSETI package is not installed.")
    package_dir = Path(next(iter(package_spec.submodule_search_locations)))
    apply_turboseti_numpy_compatibility(package_dir)

    import turbo_seti
    from turbo_seti.find_doppler.find_doppler import FindDoppler

    _ensure_drift_indexes(package_dir)
    expected = output_dir / hdf5_path.with_suffix(".dat").name
    completion_marker = expected.with_name(expected.name + ".processing.json")
    version = str(getattr(turbo_seti, "__version__", "2.3.2"))
    requested_analysis = {
        "max_drift_hz_per_sec": float(analysis["max_drift_hz_per_sec"]),
        "min_drift_hz_per_sec": float(analysis["min_drift_hz_per_sec"]),
        "snr_threshold": float(analysis["snr_threshold"]),
    }
    if expected.exists() and completion_marker.exists():
        try:
            completed = json.loads(completion_marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            completed = {}
        if completed.get("analysis") == requested_analysis:
            return expected, version

    expected.unlink(missing_ok=True)
    expected.with_suffix(".log").unlink(missing_ok=True)
    completion_marker.unlink(missing_ok=True)
    before = set(glob.glob(str(output_dir / "*.dat")))
    finder = FindDoppler(
        str(hdf5_path),
        max_drift=float(analysis["max_drift_hz_per_sec"]),
        min_drift=float(analysis["min_drift_hz_per_sec"]),
        snr=float(analysis["snr_threshold"]),
        out_dir=str(output_dir),
        log_level_int=30,
    )
    finder.search()
    candidates = sorted(
        set(glob.glob(str(output_dir / "*.dat"))) - before,
        key=lambda item: Path(item).stat().st_mtime,
        reverse=True,
    )
    if not expected.exists():
        if not candidates:
            raise RuntimeError(f"turboSETI did not create a hit table for {hdf5_path.name}.")
        expected = Path(candidates[0])
        completion_marker = expected.with_name(expected.name + ".processing.json")
    completion_marker.write_text(
        json.dumps(
            {
                "input_hdf5": hdf5_path.name,
                "output_dat": expected.name,
                "turbo_seti_version": version,
                "numpy_hit_counter_compatibility_patch": True,
                "analysis": requested_analysis,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return expected, version


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("configs/gbt_hip99427_cadence_v1.json"),
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path.home() / "technosignature-data",
    )
    args = parser.parse_args()

    manifest = load_cadence_manifest(args.manifest)
    cadence_id = str(manifest["cadence_id"])
    raw_dir = args.data_root / "bl_observations" / cadence_id
    hit_dir = args.data_root / "bl_hits"
    hit_dir.mkdir(parents=True, exist_ok=True)
    dat_paths: list[Path] = []

    for scan in manifest["scans"]:
        hdf5_path = download_archive_file(scan, raw_dir / scan["filename"])
        dat_path, version = _run_turboseti(hdf5_path, hit_dir, manifest["analysis"])
        write_hit_provenance(
            dat_path,
            hdf5_path,
            manifest,
            scan,
            turbo_seti_version=version,
        )
        dat_paths.append(dat_path)

    cadence_csv = hit_dir / f"{cadence_id}.csv"
    result = build_cadence_csv(
        dat_paths,
        cadence_csv,
        cadence_id=cadence_id,
        target_name=str(manifest["target_name"]),
    )
    result["source_dat_files"] = [str(path) for path in dat_paths]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
