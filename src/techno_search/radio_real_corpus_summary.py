"""Summarize real radio corpus evidence for Phase 1 validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from techno_search.cross_target_rfi import flag_cross_target_rfi
from techno_search.radio.hit_table_reader import hit_table_to_radio_hit_dicts

RADIO_REAL_CORPUS_SCHEMA_VERSION = "radio_real_corpus_summary_v1"
RADIO_REAL_CORPUS_DISCLAIMER = (
    "Real radio corpus summaries are local validation evidence for drift, RFI, "
    "and scorer integration only. They do not constitute detections, discoveries, "
    "expert review, external validation, or authorization for external submission."
)
DEFAULT_RFI_TOLERANCE_HZ = 500.0


def discover_dat_files(paths: list[Path]) -> list[Path]:
    """Return `.dat` files below paths in stable order."""
    dat_files: list[Path] = []
    for item in paths:
        path = Path(item)
        if not path.exists():
            raise FileNotFoundError(f"Radio corpus path does not exist: {path}")
        if path.is_file():
            if path.suffix == ".dat":
                dat_files.append(path)
            continue
        dat_files.extend(
            sorted(candidate for candidate in path.rglob("*.dat") if candidate.is_file())
        )
    return sorted(dict.fromkeys(dat_files))


def radio_real_corpus_summary(
    dat_paths: list[Path],
    *,
    semisupervised_model_path: Path | None = None,
    max_files: int | None = None,
    freq_tolerance_hz: float = DEFAULT_RFI_TOLERANCE_HZ,
) -> dict[str, Any]:
    """Summarize local real radio `.dat` evidence without writing payloads."""
    dat_files = discover_dat_files(dat_paths)
    if max_files is not None:
        dat_files = dat_files[:max_files]

    unreadable_files: list[str] = []
    zero_hit_files: list[str] = []
    hit_bearing_files: list[str] = []
    candidate_lists: list[list[dict[str, Any]]] = []
    hit_rows_for_scorer: list[dict[str, Any]] = []
    drift_rows = 0
    earth_consistent_rows = 0
    max_abs_normalized_drift = 0.0
    unique_targets: set[str] = set()

    for dat_file in dat_files:
        try:
            rows = hit_table_to_radio_hit_dicts(dat_file)
        except Exception as exc:  # pragma: no cover - defensive local payload report
            unreadable_files.append(f"{dat_file}: {exc}")
            continue

        if not rows:
            zero_hit_files.append(str(dat_file))
            continue

        hit_bearing_files.append(str(dat_file))
        per_file_candidates: list[dict[str, Any]] = []
        for index, row in enumerate(rows, start=1):
            target_name = str(
                row.get("target_id") or row.get("source_name") or dat_file.parent.name
            )
            unique_targets.add(target_name)
            frequency_hz = _float(row, "frequency_hz")
            drift = _float(row, "drift_rate_hz_per_sec")
            normalized_drift = _normalised_drift(drift, frequency_hz)
            if frequency_hz > 0:
                drift_rows += 1
                max_abs_normalized_drift = max(max_abs_normalized_drift, abs(normalized_drift))
                if abs(normalized_drift) <= 0.44:
                    earth_consistent_rows += 1
            enriched = {
                **row,
                "candidate_id": f"{dat_file.stem}:{index}",
                "target_name": target_name,
                "normalized_drift_hz_s_per_ghz": normalized_drift,
                "is_earth_drift_consistent": abs(normalized_drift) <= 0.44,
            }
            per_file_candidates.append(enriched)
            hit_rows_for_scorer.append(_scorer_features(row, rows))
        candidate_lists.append(per_file_candidates)

    cross_target_flags = flag_cross_target_rfi(candidate_lists, freq_tolerance_hz)
    scorer_summary = _score_with_local_model(
        hit_rows_for_scorer,
        semisupervised_model_path=semisupervised_model_path,
    )
    hit_count = len(hit_rows_for_scorer)
    validation_readiness = _validation_readiness(
        hit_bearing_target_count=len(unique_targets),
        drift_row_count=drift_rows,
        semisupervised_scorer=scorer_summary,
    )

    return {
        "schema_version": RADIO_REAL_CORPUS_SCHEMA_VERSION,
        "disclaimer": RADIO_REAL_CORPUS_DISCLAIMER,
        "ok": not unreadable_files,
        "dat_file_count": len(dat_files),
        "hit_bearing_dat_file_count": len(hit_bearing_files),
        "zero_hit_dat_file_count": len(zero_hit_files),
        "unreadable_dat_file_count": len(unreadable_files),
        "unreadable_dat_files": unreadable_files,
        "hit_count": hit_count,
        "unique_target_count": len(unique_targets),
        "hit_bearing_target_count": len(unique_targets),
        "validation_readiness": validation_readiness,
        "limitations": validation_readiness["limitations"],
        "drift_evidence": {
            "drift_row_count": drift_rows,
            "earth_consistent_row_count": earth_consistent_rows,
            "earth_inconsistent_row_count": max(0, drift_rows - earth_consistent_rows),
            "validation_ready": validation_readiness["drift_validation_ready"],
            "max_abs_normalized_drift_hz_s_per_ghz": max_abs_normalized_drift,
        },
        "cross_target_rfi": {
            "frequency_tolerance_hz": float(freq_tolerance_hz),
            "flagged_candidate_count": len(cross_target_flags),
            "flagged_candidate_ids": sorted(cross_target_flags)[:20],
            "flagged_candidate_id_count_returned": min(20, len(cross_target_flags)),
            "hit_bearing_target_count": len(unique_targets),
            "validation_ready": validation_readiness["cross_target_rfi_validation_ready"],
        },
        "semisupervised_scorer": scorer_summary,
        "sample_dat_files": [str(path) for path in dat_files[:10]],
        "sample_hit_bearing_dat_files": hit_bearing_files[:10],
        "sample_zero_hit_dat_files": zero_hit_files[:10],
    }


def _validation_readiness(
    *,
    hit_bearing_target_count: int,
    drift_row_count: int,
    semisupervised_scorer: dict[str, Any],
) -> dict[str, Any]:
    limitations: list[str] = []
    cross_target_ready = hit_bearing_target_count >= 2
    drift_ready = drift_row_count > 0
    scorer_ready = bool(semisupervised_scorer.get("model_used", False))

    if not cross_target_ready:
        limitations.append(
            "Cross-target RFI suppression needs at least 2 independent "
            "hit-bearing targets; current corpus cannot validate recurrence "
            "suppression."
        )
    if not drift_ready:
        limitations.append(
            "Drift validation needs at least 1 hit row with a positive frequency."
        )
    if not scorer_ready:
        limitations.append(
            "Semi-supervised scorer integration was not exercised by this corpus "
            "summary."
        )

    return {
        "cross_target_rfi_validation_ready": cross_target_ready,
        "drift_validation_ready": drift_ready,
        "semisupervised_scorer_validation_ready": scorer_ready,
        "phase1_radio_validation_ready": (
            cross_target_ready and drift_ready and scorer_ready
        ),
        "limitations": limitations,
    }


def _score_with_local_model(
    hit_rows: list[dict[str, Any]],
    *,
    semisupervised_model_path: Path | None,
) -> dict[str, Any]:
    if semisupervised_model_path is None:
        semisupervised_model_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "meerkat_hits"
            / "semisupervised_scorer.joblib"
        )
    model_path = Path(semisupervised_model_path)
    if not model_path.exists():
        return {
            "model_path": str(model_path),
            "model_exists": False,
            "model_used": False,
            "scored_hit_count": 0,
        }
    if not hit_rows:
        return {
            "model_path": str(model_path),
            "model_exists": True,
            "model_used": False,
            "scored_hit_count": 0,
            "limitation": "No hit-bearing rows were available to score.",
        }

    from techno_search.semisupervised_scorer import load_fitted_scorer_joblib

    try:
        scorer = load_fitted_scorer_joblib(model_path)
        scores = scorer.score_hits(hit_rows)
    except Exception as exc:  # noqa: BLE001
        return {
            "model_path": str(model_path),
            "model_exists": True,
            "model_used": False,
            "scored_hit_count": 0,
            "error": str(exc),
        }
    return {
        "model_path": str(model_path),
        "model_exists": True,
        "model_used": True,
        "scored_hit_count": len(scores),
        "max_anomaly_score": max(scores),
        "mean_anomaly_score": sum(scores) / len(scores),
    }


def _scorer_features(row: dict[str, Any], all_rows: list[dict[str, Any]]) -> dict[str, Any]:
    frequency_hz = _float(row, "frequency_hz")
    drift = _float(row, "drift_rate_hz_per_sec")
    snr = _float(row, "snr")
    same_frequency_rows = [
        other for other in all_rows if abs(_float(other, "frequency_hz") - frequency_hz) <= 5.0
    ]
    scan_roles = [str(other.get("scan_role", "")).lower() for other in same_frequency_rows]
    on_hit_count = sum(1 for role in scan_roles if not role.startswith("off"))
    off_hit_count = sum(1 for role in scan_roles if role.startswith("off"))
    total_role_hits = max(1, on_hit_count + off_hit_count)
    normalized_drift = _normalised_drift(drift, frequency_hz)
    return {
        "snr": snr,
        "drift_rate_hz_per_sec": drift,
        "frequency_hz": frequency_hz,
        "bandwidth_hz": _float(row, "bandwidth_hz"),
        "normalized_drift_hz_s_per_ghz": normalized_drift,
        "relative_snr": snr / _median_positive_snr(all_rows),
        "on_off_consistency_score": off_hit_count / total_role_hits,
        "is_earth_drift_consistent": 1.0 if abs(normalized_drift) <= 0.44 else 0.0,
        "rfi_band_overlap_score": 0.0,
        "frequency_persistence_score": min(
            1.0,
            max(0, len(same_frequency_rows) - 1) / max(1, len(all_rows) - 1),
        ),
        "on_hit_count": on_hit_count,
        "off_hit_count": off_hit_count,
    }


def _normalised_drift(drift_rate_hz_per_sec: float, frequency_hz: float) -> float:
    frequency_ghz = frequency_hz / 1e9
    if frequency_ghz <= 0:
        return 0.0
    return drift_rate_hz_per_sec / frequency_ghz


def _median_positive_snr(rows: list[dict[str, Any]]) -> float:
    values = sorted(_float(row, "snr") for row in rows if _float(row, "snr") > 0)
    if not values:
        return 1.0
    midpoint = len(values) // 2
    if len(values) % 2 == 1:
        return values[midpoint]
    return (values[midpoint - 1] + values[midpoint]) / 2.0


def _float(row: dict[str, Any], key: str) -> float:
    try:
        return float(row.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0
