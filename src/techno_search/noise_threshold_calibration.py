"""Noise distribution analysis for scoring threshold calibration.

Analyzes SNR and drift-rate distributions from a set of real or synthetic
turboSETI hit tables to derive empirical scoring thresholds.

IMPORTANT: outputs are provenance-only calibration aids. Derived thresholds
must pass the project's citizen-science reproducibility review before being
committed to scoring_v1.json. They do not constitute calibrated survey
sensitivities or detection thresholds.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

NOISE_CALIBRATION_DISCLAIMER = (
    "Noise distribution analysis outputs are local calibration aids only. "
    "Derived thresholds must pass independent-method citizen-science review "
    "before use in production scoring. They do not constitute calibrated "
    "survey sensitivities, detection thresholds, or validated scoring parameters."
)


def analyze_hit_directory(
    hit_dir: Path,
    *,
    snr_percentiles: tuple[float, ...] = (50.0, 75.0, 90.0, 95.0, 99.0),
    max_files: int = 500,
) -> dict[str, Any]:
    """Analyze all .dat and .csv hit tables in hit_dir.

    Returns per-percentile SNR thresholds, drift-rate statistics, and
    hit-count distribution suitable for informing scoring_v1.json thresholds.
    """
    from techno_search.radio.hit_table_reader import read_hit_table_csv

    hit_dir = Path(hit_dir)
    if not hit_dir.is_dir():
        return {
            "disclaimer": NOISE_CALIBRATION_DISCLAIMER,
            "ok": False,
            "error": f"Directory not found: {hit_dir}",
            "hit_dir": str(hit_dir),
        }

    files = sorted(
        list(hit_dir.glob("*.dat")) + list(hit_dir.glob("*.csv"))
    )[:max_files]

    if not files:
        return {
            "disclaimer": NOISE_CALIBRATION_DISCLAIMER,
            "ok": False,
            "error": "No .dat or .csv files found.",
            "hit_dir": str(hit_dir),
            "file_count": 0,
        }

    all_snr: list[float] = []
    all_drift: list[float] = []
    total_hits = 0
    failed_files: list[str] = []

    for f in files:
        try:
            rows = read_hit_table_csv(f)
            for row in rows:
                snr = row.get("snr")
                drift = row.get("drift_rate_hz_per_sec")
                if snr is not None:
                    all_snr.append(float(snr))
                if drift is not None:
                    all_drift.append(float(drift))
            total_hits += len(rows)
        except Exception as exc:  # noqa: BLE001
            failed_files.append(f"{f.name}: {exc}")

    if not all_snr:
        return {
            "disclaimer": NOISE_CALIBRATION_DISCLAIMER,
            "ok": False,
            "error": "No valid SNR values found across all files.",
            "hit_dir": str(hit_dir),
            "file_count": len(files),
            "failed_files": failed_files,
        }

    snr_sorted = sorted(all_snr)

    snr_percentile_values = {
        f"p{p:.0f}": _percentile(snr_sorted, p)
        for p in snr_percentiles
    }

    return {
        "disclaimer": NOISE_CALIBRATION_DISCLAIMER,
        "ok": True,
        "hit_dir": str(hit_dir),
        "file_count": len(files),
        "total_hit_count": total_hits,
        "failed_file_count": len(failed_files),
        "failed_files": failed_files[:10],
        "snr_stats": {
            "count": len(all_snr),
            "min": min(all_snr),
            "max": max(all_snr),
            "mean": sum(all_snr) / len(all_snr),
            "median": _percentile(snr_sorted, 50.0),
            "std_dev": _std_dev(all_snr),
            "percentiles": snr_percentile_values,
        },
        "drift_stats": _drift_stats(all_drift) if all_drift else {},
        "suggested_thresholds": _suggest_thresholds(snr_sorted, all_drift),
    }


def _suggest_thresholds(
    snr_sorted: list[float],
    drift_rates: list[float],
) -> dict[str, Any]:
    """Suggest scoring threshold candidates from empirical distributions.

    These are suggestions for reproducibility review, not validated thresholds.
    All outputs require independent-method review before use.
    """
    p90 = _percentile(snr_sorted, 90.0)
    p95 = _percentile(snr_sorted, 95.0)
    p99 = _percentile(snr_sorted, 99.0)

    drift_abs = [abs(d) for d in drift_rates]
    drift_p95 = _percentile(sorted(drift_abs), 95.0) if drift_abs else None

    return {
        "note": (
            "Suggested thresholds are empirical starting points only. "
            "They must pass independent-method citizen-science review."
        ),
        "snr_high_interest_candidate": p99,
        "snr_follow_up_candidate": p95,
        "snr_noise_floor_estimate": p90,
        "drift_rate_abs_p95_hz_s": drift_p95,
        "review_required": True,
    }


def _drift_stats(drift_rates: list[float]) -> dict[str, Any]:
    drift_abs = sorted(abs(d) for d in drift_rates)
    return {
        "count": len(drift_rates),
        "min": min(drift_rates),
        "max": max(drift_rates),
        "mean": sum(drift_rates) / len(drift_rates),
        "abs_median": _percentile(drift_abs, 50.0),
        "abs_p95": _percentile(drift_abs, 95.0),
        "zero_drift_fraction": sum(1 for d in drift_rates if abs(d) < 0.01) / len(drift_rates),
    }


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    idx = (p / 100.0) * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


def _std_dev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)
