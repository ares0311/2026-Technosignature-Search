#!/usr/bin/env python3
"""
setigen_injection_grid.py

Injection-recovery grid using setigen to augment the follow_up class
with synthetic narrowband signals injected into real GBT HDF5 files.

This addresses the class imbalance problem: real GBT cadences contain
~200 hits of which <5 are genuine follow_up candidates.  By injecting
synthetic signals across a grid of (SNR, drift_rate, frequency) values
into real noise backgrounds, we generate a balanced training set.

Scientific guardrail:
  Injected signals are synthetic.  Recovered hits are not real
  technosignature candidates and do not constitute detection claims.
  This script generates augmentation data only.

Usage:
  .venv/bin/python scripts/setigen_injection_grid.py \
      --h5-file data/bl_hits/Voyager1.single_coarse.fine_res.h5 \
      --output-dir data/injection_grid \
      [--n-snr 5] [--n-drift 5] [--n-freq 3] [--dry-run]

Dependencies:
  .venv/bin/pip install setigen
  .venv/bin/pip install turbo_seti
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

INJECTION_DISCLAIMER = (
    "Injection-recovery grid outputs are synthetic augmentation data only. "
    "Recovered hits are not real technosignature candidates and do not "
    "constitute detection claims or authorize external submission."
)

# Default injection parameter grid
DEFAULT_SNR_VALUES = [20.0, 50.0, 100.0, 200.0, 500.0]
DEFAULT_DRIFT_RATES = [-2.0, -0.5, 0.0, 0.5, 2.0]   # Hz/s
DEFAULT_N_FREQ_OFFSETS = 3   # inject at N evenly-spaced frequencies per coarse channel


def _check_dependencies() -> bool:
    """Return True if setigen and turbo_seti are available."""
    missing = []
    try:
        import setigen  # noqa: F401
    except ImportError:
        missing.append("setigen")
    try:
        import turbo_seti  # noqa: F401
    except ImportError:
        missing.append("turbo_seti")
    if missing:
        print(f"[WARN]  Missing dependencies: {', '.join(missing)}")
        print(f"        Install with: .venv/bin/pip install {' '.join(missing)}")
        return False
    return True


def inject_signal(
    h5_path: Path,
    snr: float,
    drift_rate_hz_s: float,
    freq_offset_mhz: float,
    output_h5_path: Path,
) -> bool:
    """Inject a synthetic narrowband signal into an HDF5 file.

    Returns True on success, False if setigen is unavailable or injection fails.
    """
    try:
        import setigen as stg
    except ImportError:
        return False

    try:
        frame = stg.Frame(waterfall=str(h5_path))
        # Inject at centre frequency + offset
        center_freq_mhz = frame.get_frequency(0) / 1e6
        inject_freq_mhz = center_freq_mhz + freq_offset_mhz
        frame.add_signal(
            path=stg.paths.constant_path(
                f_start=inject_freq_mhz * 1e6,
                drift_rate=drift_rate_hz_s,
            ),
            t_profile=stg.t_profiles.constant_t_profile(level=frame.get_intensity(snr=snr)),
            f_profile=stg.f_profiles.gaussian_f_profile(width=frame.df),
            bp_profile=stg.bp_profiles.constant_bp_profile(level=1.0),
        )
        frame.save_h5(str(output_h5_path))
        return True
    except Exception as exc:
        print(f"[WARN]  Injection failed: {exc}")
        return False


def run_turboseti_on_h5(h5_path: Path, output_dir: Path) -> Path | None:
    """Run turboSETI on an injected HDF5 file and return the .dat path."""
    try:
        from turbo_seti.find_doppler.find_doppler import FindDoppler
    except ImportError:
        return None

    try:
        finder = FindDoppler(
            datafile=str(h5_path),
            max_drift=5.0,
            snr=10.0,
            out_dir=str(output_dir),
            gpu_backend=False,
        )
        finder.search()
        # turboSETI writes <stem>.dat in output_dir
        dat_path = output_dir / (h5_path.stem + ".dat")
        if dat_path.exists():
            return dat_path
        # Search for any .dat in output dir
        dats = list(output_dir.glob("*.dat"))
        return dats[0] if dats else None
    except Exception as exc:
        print(f"[WARN]  turboSETI search failed: {exc}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--h5-file",
        type=Path,
        default=REPO_ROOT / "data" / "bl_hits" / "Voyager1.single_coarse.fine_res.h5",
        help="Input GBT HDF5 file to inject into",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "injection_grid",
        help="Output directory for injected H5 files and .dat hit tables",
    )
    parser.add_argument(
        "--snr-values",
        nargs="+",
        type=float,
        default=DEFAULT_SNR_VALUES,
        help="SNR values to inject (default: 20 50 100 200 500)",
    )
    parser.add_argument(
        "--drift-rates",
        nargs="+",
        type=float,
        default=DEFAULT_DRIFT_RATES,
        help="Drift rates in Hz/s (default: -2.0 -0.5 0.0 0.5 2.0)",
    )
    parser.add_argument(
        "--n-freq-offsets",
        type=int,
        default=DEFAULT_N_FREQ_OFFSETS,
        help="Number of frequency offsets per coarse channel (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the injection grid without running injections",
    )
    args = parser.parse_args()

    print("[START] Injection-recovery grid")
    print(f"[INFO]  Input H5: {args.h5_file}")
    print(f"[INFO]  Output dir: {args.output_dir}")
    print(f"[INFO]  SNR values: {args.snr_values}")
    print(f"[INFO]  Drift rates: {args.drift_rates}")
    print(f"[INFO]  Freq offsets per channel: {args.n_freq_offsets}")

    if not args.h5_file.exists():
        print(f"[WARN]  H5 file not found: {args.h5_file}")
        print("        Run download scripts first to obtain GBT H5 data.")
        if not args.dry_run:
            sys.exit(1)

    # Build injection grid
    freq_offsets = [
        (i - args.n_freq_offsets // 2) * 0.5
        for i in range(args.n_freq_offsets)
    ]  # ±0.5 MHz offsets

    grid: list[dict] = []
    for snr in args.snr_values:
        for drift in args.drift_rates:
            for freq_off in freq_offsets:
                grid.append({
                    "snr": snr,
                    "drift_rate_hz_s": drift,
                    "freq_offset_mhz": freq_off,
                })

    total = len(grid)
    print(f"[INFO]  Total injections to run: {total}")

    if args.dry_run:
        print("[DRY-RUN] Grid entries:")
        for i, entry in enumerate(grid[:5]):
            print(f"  [{i+1}/{total}] {entry}")
        if total > 5:
            print(f"  ... ({total - 5} more)")
        print(f"[INFO]  Disclaimer: {INJECTION_DISCLAIMER}")
        return

    if not _check_dependencies():
        print("[ERROR] Cannot proceed without setigen and turbo_seti installed.")
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    results: list[dict] = []

    for i, entry in enumerate(grid):
        snr = entry["snr"]
        drift = entry["drift_rate_hz_s"]
        freq_off = entry["freq_offset_mhz"]

        label = f"snr{snr:.0f}_drift{drift:.1f}_foff{freq_off:.1f}".replace("-", "m")
        inj_h5 = args.output_dir / f"injected_{label}.h5"
        dat_dir = args.output_dir / f"dat_{label}"
        dat_dir.mkdir(exist_ok=True)

        print(f"[{i+1}/{total}] SNR={snr} drift={drift} Hz/s freq_off={freq_off} MHz")

        if inj_h5.exists():
            print(f"         [SKIP] Already injected: {inj_h5.name}")
        else:
            success = inject_signal(args.h5_file, snr, drift, freq_off, inj_h5)
            if not success:
                print("         [FAIL] Injection failed — skipping")
                continue

        dat_path = run_turboseti_on_h5(inj_h5, dat_dir)
        result: dict = {
            "snr_injected": snr,
            "drift_rate_hz_s": drift,
            "freq_offset_mhz": freq_off,
            "h5_path": str(inj_h5),
            "dat_path": str(dat_path) if dat_path else None,
            "recovered": dat_path is not None and dat_path.exists(),
        }
        results.append(result)

    # Write results manifest
    elapsed = time.time() - t0
    manifest = {
        "schema_version": "injection_grid_manifest_v1",
        "disclaimer": INJECTION_DISCLAIMER,
        "total_injections": len(results),
        "recovered_count": sum(1 for r in results if r["recovered"]),
        "elapsed_seconds": elapsed,
        "grid": results,
    }
    manifest_path = args.output_dir / "injection_grid_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    recovered = sum(1 for r in results if r["recovered"])
    print(f"[DONE]  {recovered}/{len(results)} injections recovered in {elapsed:.1f}s")
    print(f"[INFO]  Manifest: {manifest_path}")
    print("")
    print(f"Scientific guardrail: {INJECTION_DISCLAIMER}")


if __name__ == "__main__":
    main()
