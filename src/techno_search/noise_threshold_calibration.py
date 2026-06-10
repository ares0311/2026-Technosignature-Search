"""Provenance-aware real-noise analysis for scoring threshold calibration."""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.observation_artifact import (
    assess_observation_artifact,
    provenance_path_for,
    sha256_file,
)

NOISE_CALIBRATION_DISCLAIMER = (
    "Noise distribution analysis outputs are local calibration aids only. "
    "Derived thresholds must pass independent-method citizen-science review "
    "before use in production scoring. They do not constitute calibrated "
    "survey sensitivities, detection thresholds, or validated scoring parameters."
)

MINIMUM_CADENCES = 3
MINIMUM_TARGETS = 3
MINIMUM_EPOCHS = 2
MINIMUM_HITS = 100
MAX_CADENCE_HIT_FRACTION = 0.50
MAX_LEAVE_ONE_RELATIVE_SHIFT = 0.25
MAX_BOOTSTRAP_RELATIVE_SPAN = 0.50


@dataclass(frozen=True)
class CalibrationArtifact:
    """An admitted hit table and its calibration grouping metadata."""

    path: Path
    provenance: dict[str, Any]
    cadence_id: str
    target_id: str
    epoch_id: str


def analyze_hit_directory(
    hit_dir: Path,
    *,
    snr_percentiles: tuple[float, ...] = (50.0, 75.0, 90.0, 95.0, 99.0),
    max_files: int = 500,
    require_approved_real_data: bool = True,
) -> dict[str, Any]:
    """Analyze admitted hit tables without double-counting derived cadences."""
    from techno_search.radio.hit_table_reader import read_hit_table_csv

    hit_dir = Path(hit_dir)
    if not hit_dir.is_dir():
        return _error_result(hit_dir, f"Directory not found: {hit_dir}")

    artifacts, skipped = select_calibration_artifacts(
        hit_dir,
        max_files=max_files,
        require_approved_real_data=require_approved_real_data,
    )
    selection_summary = _selection_summary(hit_dir, artifacts, skipped)
    if not artifacts:
        return _error_result(
            hit_dir,
            "No eligible hit tables passed the calibration admission checks.",
            selection_summary=selection_summary,
        )

    all_snr: list[float] = []
    all_drift: list[float] = []
    grouped_rows: list[tuple[CalibrationArtifact, list[dict[str, Any]]]] = []
    failed_files: list[str] = []
    for artifact in artifacts:
        try:
            rows = read_hit_table_csv(artifact.path)
        except Exception as exc:  # noqa: BLE001
            failed_files.append(f"{artifact.path.name}: {exc}")
            continue
        grouped_rows.append((artifact, rows))
        all_snr.extend(float(row["snr"]) for row in rows if row.get("snr") is not None)
        all_drift.extend(
            float(row["drift_rate_hz_per_sec"])
            for row in rows
            if row.get("drift_rate_hz_per_sec") is not None
        )

    if not all_snr:
        return _error_result(
            hit_dir,
            "No valid SNR values found across admitted files.",
            selection_summary=selection_summary,
            failed_files=failed_files,
        )

    snr_sorted = sorted(all_snr)
    cadence_stats = _group_diagnostics(grouped_rows, "cadence_id")
    target_stats = _group_diagnostics(grouped_rows, "target_id")
    epoch_stats = _group_diagnostics(grouped_rows, "epoch_id")
    bootstrap = _bootstrap_stability(snr_sorted)
    leave_one = _leave_one_cadence_out(grouped_rows, snr_sorted)
    dominance = _dominance_summary(cadence_stats, len(all_snr))
    gates = _acceptance_gates(
        cadence_stats=cadence_stats,
        target_stats=target_stats,
        epoch_stats=epoch_stats,
        total_hits=len(all_snr),
        dominance=dominance,
        bootstrap=bootstrap,
        leave_one=leave_one,
    )

    return {
        "schema_version": "noise_threshold_calibration_v2",
        "disclaimer": NOISE_CALIBRATION_DISCLAIMER,
        "ok": True,
        "calibration_ready": all(gate["passed"] for gate in gates.values()),
        "hit_dir": str(hit_dir),
        "file_count": len(grouped_rows),
        "total_hit_count": len(all_snr),
        "failed_file_count": len(failed_files),
        "failed_files": failed_files[:10],
        "selection_summary": selection_summary,
        "snr_stats": {
            "count": len(all_snr),
            "min": min(all_snr),
            "max": max(all_snr),
            "mean": sum(all_snr) / len(all_snr),
            "median": _percentile(snr_sorted, 50.0),
            "std_dev": _std_dev(all_snr),
            "percentiles": {
                f"p{p:.0f}": _percentile(snr_sorted, p) for p in snr_percentiles
            },
        },
        "drift_stats": _drift_stats(all_drift) if all_drift else {},
        "cadence_stats": cadence_stats,
        "target_stats": target_stats,
        "epoch_stats": epoch_stats,
        "dominance_analysis": dominance,
        "bootstrap_stability": bootstrap,
        "leave_one_cadence_out": leave_one,
        "acceptance_gates": gates,
        "suggested_thresholds": _suggest_thresholds(snr_sorted, all_drift),
    }


def select_calibration_artifacts(
    hit_dir: Path,
    *,
    max_files: int = 500,
    require_approved_real_data: bool = True,
) -> tuple[list[CalibrationArtifact], list[dict[str, str]]]:
    """Select eligible inputs and prefer source DAT files over derived CSV copies."""
    paths = sorted((*hit_dir.glob("*.dat"), *hit_dir.glob("*.csv")))
    if not require_approved_real_data:
        selected = [
            CalibrationArtifact(
                path=path,
                provenance={"classification": "development_fixture"},
                cadence_id=path.stem,
                target_id="development_fixture",
                epoch_id="development_fixture",
            )
            for path in paths[:max_files]
        ]
        development_skipped = [
            {"filename": path.name, "reason": "max_files_limit"}
            for path in paths[max_files:]
        ]
        return selected, development_skipped

    selected_dat: list[CalibrationArtifact] = []
    derived_candidates: list[tuple[Path, dict[str, Any]]] = []
    skipped: list[dict[str, str]] = []

    for path in paths:
        if path.suffix.lower() == ".dat":
            assessment = assess_observation_artifact(path)
            if not assessment.approved_for_pipeline:
                reason = "; ".join(assessment.issues) or "not_approved_real_observation"
                skipped.append({"filename": path.name, "reason": reason})
                continue
            provenance = _read_json_object(assessment.provenance_path)
            if provenance is None:
                skipped.append({"filename": path.name, "reason": "unreadable_provenance"})
                continue
            selected_dat.append(_artifact_from_provenance(path, provenance))
            continue

        provenance = _read_json_object(provenance_path_for(path))
        csv_reason = _derived_csv_rejection_reason(path, provenance)
        if csv_reason:
            skipped.append({"filename": path.name, "reason": csv_reason})
        else:
            assert provenance is not None
            derived_candidates.append((path, provenance))

    selected_names = {artifact.path.name for artifact in selected_dat}
    selected = list(selected_dat)
    for path, provenance in derived_candidates:
        source_names = {
            str(item.get("artifact_filename", ""))
            for item in provenance.get("source_artifacts", [])
            if isinstance(item, dict)
        }
        if selected_names.intersection(source_names):
            skipped.append(
                {
                    "filename": path.name,
                    "reason": "derived_cadence_overlaps_selected_source_dat",
                }
            )
            continue
        selected.append(_artifact_from_provenance(path, provenance))

    if len(selected) > max_files:
        for artifact in selected[max_files:]:
            skipped.append(
                {"filename": artifact.path.name, "reason": "max_files_limit"}
            )
        selected = selected[:max_files]
    return selected, skipped


def _derived_csv_rejection_reason(
    path: Path, provenance: dict[str, Any] | None
) -> str | None:
    if provenance is None:
        return "missing_or_unreadable_provenance"
    if provenance.get("classification") != "derived_real_observation_cadence":
        return "not_an_approved_derived_real_cadence"
    if provenance.get("artifact_filename") != path.name:
        return "provenance_filename_mismatch"
    if provenance.get("sha256") != sha256_file(path):
        return "provenance_sha256_mismatch"
    if provenance.get("external_submission_authorized") is not False:
        return "external_submission_safety_flag_missing"
    source_artifacts = provenance.get("source_artifacts")
    if not isinstance(source_artifacts, list) or not source_artifacts:
        return "source_artifact_provenance_missing"
    return None


def _artifact_from_provenance(
    path: Path, provenance: dict[str, Any]
) -> CalibrationArtifact:
    cadence_id = str(provenance.get("cadence_id") or path.stem)
    target_id = str(
        provenance.get("target_id") or provenance.get("source_name") or "unknown"
    )
    utc_start = str(provenance.get("observation_utc_start") or "")
    mjd = provenance.get("observation_mjd")
    epoch_id = utc_start[:10] if len(utc_start) >= 10 else ""
    if not epoch_id and mjd is not None:
        epoch_id = f"mjd-{math.floor(float(mjd))}"
    return CalibrationArtifact(
        path=path,
        provenance=provenance,
        cadence_id=cadence_id,
        target_id=target_id,
        epoch_id=epoch_id or "unknown",
    )


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _selection_summary(
    hit_dir: Path,
    artifacts: list[CalibrationArtifact],
    skipped: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "discovered_file_count": len(
            list(hit_dir.glob("*.dat")) + list(hit_dir.glob("*.csv"))
        ),
        "selected_file_count": len(artifacts),
        "skipped_file_count": len(skipped),
        "selected_files": [
            {
                "filename": artifact.path.name,
                "sha256": sha256_file(artifact.path),
                "classification": artifact.provenance.get("classification"),
                "cadence_id": artifact.cadence_id,
                "target_id": artifact.target_id,
                "epoch_id": artifact.epoch_id,
            }
            for artifact in artifacts
        ],
        "skipped_files": skipped,
    }


def _group_diagnostics(
    grouped_rows: list[tuple[CalibrationArtifact, list[dict[str, Any]]]],
    attribute: str,
) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for artifact, rows in grouped_rows:
        group_id = str(getattr(artifact, attribute))
        group = groups.setdefault(
            group_id, {"file_count": 0, "hit_count": 0, "snr": [], "drift": []}
        )
        group["file_count"] += 1
        group["hit_count"] += len(rows)
        group["snr"].extend(float(row["snr"]) for row in rows if row.get("snr") is not None)
        group["drift"].extend(
            abs(float(row["drift_rate_hz_per_sec"]))
            for row in rows
            if row.get("drift_rate_hz_per_sec") is not None
        )
    return {
        group_id: {
            "file_count": values["file_count"],
            "hit_count": values["hit_count"],
            "snr_p95": _percentile(sorted(values["snr"]), 95.0),
            "abs_drift_p95_hz_s": _percentile(sorted(values["drift"]), 95.0),
        }
        for group_id, values in sorted(groups.items())
    }


def _dominance_summary(
    cadence_stats: dict[str, dict[str, Any]], total_hits: int
) -> dict[str, Any]:
    fractions = {
        cadence_id: values["hit_count"] / total_hits
        for cadence_id, values in cadence_stats.items()
    }
    dominant_id = max(fractions, key=lambda cadence_id: fractions[cadence_id])
    return {
        "cadence_hit_fractions": fractions,
        "dominant_cadence_id": dominant_id,
        "maximum_cadence_hit_fraction": fractions[dominant_id],
        "limit": MAX_CADENCE_HIT_FRACTION,
    }


def _bootstrap_stability(
    snr_sorted: list[float], *, iterations: int = 100, seed: int = 20260610
) -> dict[str, Any]:
    rng = random.Random(seed)
    samples: dict[str, list[float]] = {"p90": [], "p95": [], "p99": []}
    for _ in range(iterations):
        sample = sorted(rng.choice(snr_sorted) for _ in snr_sorted)
        for percentile in (90, 95, 99):
            samples[f"p{percentile}"].append(_percentile(sample, float(percentile)))
    intervals: dict[str, dict[str, float]] = {}
    for key, values in samples.items():
        ordered = sorted(values)
        point = _percentile(snr_sorted, float(key[1:]))
        low = _percentile(ordered, 5.0)
        high = _percentile(ordered, 95.0)
        intervals[key] = {
            "point_estimate": point,
            "p05": low,
            "p95": high,
            "relative_span": (high - low) / max(abs(point), 1.0),
        }
    return {
        "method": "fixed-seed nonparametric bootstrap",
        "seed": seed,
        "iterations": iterations,
        "intervals": intervals,
        "maximum_relative_span": max(
            interval["relative_span"] for interval in intervals.values()
        ),
    }


def _leave_one_cadence_out(
    grouped_rows: list[tuple[CalibrationArtifact, list[dict[str, Any]]]],
    snr_sorted: list[float],
) -> dict[str, Any]:
    cadence_ids = sorted({artifact.cadence_id for artifact, _ in grouped_rows})
    if len(cadence_ids) < 2:
        return {
            "status": "blocked_insufficient_cadences",
            "cadence_count": len(cadence_ids),
            "maximum_relative_shift": None,
            "results": [],
        }
    baseline = {
        percentile: _percentile(snr_sorted, float(percentile))
        for percentile in (90, 95, 99)
    }
    results: list[dict[str, Any]] = []
    maximum_shift = 0.0
    for omitted in cadence_ids:
        remaining = sorted(
            float(row["snr"])
            for artifact, rows in grouped_rows
            if artifact.cadence_id != omitted
            for row in rows
            if row.get("snr") is not None
        )
        shifts = {
            f"p{percentile}": abs(
                _percentile(remaining, float(percentile)) - baseline[percentile]
            )
            / max(abs(baseline[percentile]), 1.0)
            for percentile in (90, 95, 99)
        }
        maximum_shift = max(maximum_shift, *shifts.values())
        results.append({"omitted_cadence_id": omitted, "relative_shifts": shifts})
    return {
        "status": "complete",
        "cadence_count": len(cadence_ids),
        "maximum_relative_shift": maximum_shift,
        "results": results,
    }


def _acceptance_gates(
    *,
    cadence_stats: dict[str, dict[str, Any]],
    target_stats: dict[str, dict[str, Any]],
    epoch_stats: dict[str, dict[str, Any]],
    total_hits: int,
    dominance: dict[str, Any],
    bootstrap: dict[str, Any],
    leave_one: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    leave_one_shift = leave_one["maximum_relative_shift"]
    return {
        "minimum_cadences": _gate(
            len(cadence_stats) >= MINIMUM_CADENCES,
            len(cadence_stats),
            MINIMUM_CADENCES,
        ),
        "minimum_targets": _gate(
            len(target_stats) >= MINIMUM_TARGETS,
            len(target_stats),
            MINIMUM_TARGETS,
        ),
        "minimum_epochs": _gate(
            len(epoch_stats) >= MINIMUM_EPOCHS,
            len(epoch_stats),
            MINIMUM_EPOCHS,
        ),
        "minimum_hits": _gate(total_hits >= MINIMUM_HITS, total_hits, MINIMUM_HITS),
        "cadence_dominance": _gate(
            dominance["maximum_cadence_hit_fraction"] <= MAX_CADENCE_HIT_FRACTION,
            dominance["maximum_cadence_hit_fraction"],
            MAX_CADENCE_HIT_FRACTION,
            comparison="<=",
        ),
        "bootstrap_stability": _gate(
            bootstrap["maximum_relative_span"] <= MAX_BOOTSTRAP_RELATIVE_SPAN,
            bootstrap["maximum_relative_span"],
            MAX_BOOTSTRAP_RELATIVE_SPAN,
            comparison="<=",
        ),
        "leave_one_cadence_out": _gate(
            leave_one_shift is not None
            and leave_one_shift <= MAX_LEAVE_ONE_RELATIVE_SHIFT,
            leave_one_shift,
            MAX_LEAVE_ONE_RELATIVE_SHIFT,
            comparison="<=",
        ),
    }


def _gate(
    passed: bool,
    observed: int | float | None,
    required: int | float,
    *,
    comparison: str = ">=",
) -> dict[str, Any]:
    return {
        "passed": passed,
        "observed": observed,
        "required": required,
        "comparison": comparison,
    }


def _suggest_thresholds(
    snr_sorted: list[float],
    drift_rates: list[float],
) -> dict[str, Any]:
    """Return physical-unit candidates, never pathway probabilities."""
    drift_abs = sorted(abs(drift) for drift in drift_rates)
    return {
        "note": (
            "Physical-unit candidates are empirical starting points only. "
            "Pathway probabilities require separate labeled-data evaluation."
        ),
        "snr_thresholds": {
            "noise_floor_snr": _percentile(snr_sorted, 90.0),
            "follow_up_snr": _percentile(snr_sorted, 95.0),
            "high_interest_snr": _percentile(snr_sorted, 99.0),
        },
        "drift_rate_thresholds": {
            "max_rfi_like_drift_hz_s": (
                _percentile(drift_abs, 95.0) if drift_abs else None
            )
        },
        "pathway_probability_thresholds": {
            "status": "not_derived_by_noise_distribution",
            "required_method": "real labeled pathway evaluation",
        },
        "review_required": True,
    }


def _drift_stats(drift_rates: list[float]) -> dict[str, Any]:
    drift_abs = sorted(abs(drift) for drift in drift_rates)
    return {
        "count": len(drift_rates),
        "min": min(drift_rates),
        "max": max(drift_rates),
        "mean": sum(drift_rates) / len(drift_rates),
        "abs_median": _percentile(drift_abs, 50.0),
        "abs_p95": _percentile(drift_abs, 95.0),
        "zero_drift_fraction": sum(
            1 for drift in drift_rates if abs(drift) < 0.01
        )
        / len(drift_rates),
    }


def _error_result(
    hit_dir: Path,
    error: str,
    **details: Any,
) -> dict[str, Any]:
    return {
        "schema_version": "noise_threshold_calibration_v2",
        "disclaimer": NOISE_CALIBRATION_DISCLAIMER,
        "ok": False,
        "calibration_ready": False,
        "error": error,
        "hit_dir": str(hit_dir),
        **details,
    }


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    idx = (p / 100.0) * (len(sorted_values) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_values) - 1)
    fraction = idx - lo
    return sorted_values[lo] * (1.0 - fraction) + sorted_values[hi] * fraction


def _std_dev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)
