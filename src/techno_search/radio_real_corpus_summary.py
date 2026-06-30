"""Summarize real radio corpus evidence for Phase 1 validation."""

from __future__ import annotations

import json
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
DEFAULT_STATIONARY_DRIFT_EPSILON = 1e-9


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


def discover_hit_ndjson_files(paths: list[Path]) -> list[Path]:
    """Return NDJSON hit-corpus files from explicit files or directories."""
    hit_files: list[Path] = []
    for item in paths:
        path = Path(item)
        if not path.exists():
            raise FileNotFoundError(f"Radio hit-NDJSON path does not exist: {path}")
        if path.is_file():
            if path.suffix == ".ndjson":
                hit_files.append(path)
            continue
        hit_files.extend(
            sorted(candidate for candidate in path.rglob("*.ndjson") if candidate.is_file())
        )
    return sorted(dict.fromkeys(hit_files))


def radio_real_corpus_summary(
    dat_paths: list[Path],
    *,
    hit_ndjson_paths: list[Path] | None = None,
    semisupervised_model_path: Path | None = None,
    max_files: int | None = None,
    max_hit_rows: int | None = None,
    candidate_sample_limit: int = 20,
    freq_tolerance_hz: float = DEFAULT_RFI_TOLERANCE_HZ,
) -> dict[str, Any]:
    """Summarize local real radio hit evidence without writing payloads."""
    dat_files = discover_dat_files(dat_paths)
    if max_files is not None:
        dat_files = dat_files[:max_files]
    hit_ndjson_files = discover_hit_ndjson_files(hit_ndjson_paths or [])

    unreadable_files: list[str] = []
    unreadable_hit_ndjson_files: list[str] = []
    zero_hit_files: list[str] = []
    hit_bearing_files: list[str] = []
    candidate_lists: list[list[dict[str, Any]]] = []
    review_candidates: list[dict[str, Any]] = []
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
            review_candidates.append(enriched)
            hit_rows_for_scorer.append(_scorer_features(row, rows))
        candidate_lists.append(per_file_candidates)

    hit_ndjson_row_count = 0
    for hit_ndjson_file in hit_ndjson_files:
        try:
            rows = _load_hit_ndjson_rows(
                hit_ndjson_file,
                remaining_rows=(
                    None
                    if max_hit_rows is None
                    else max(0, max_hit_rows - hit_ndjson_row_count)
                ),
            )
        except Exception as exc:  # pragma: no cover - defensive local payload report
            unreadable_hit_ndjson_files.append(f"{hit_ndjson_file}: {exc}")
            continue
        if not rows:
            continue
        per_file_candidates = []
        for index, row in enumerate(rows, start=1):
            target_name = str(
                row.get("target_id")
                or row.get("target_name")
                or row.get("source_name")
                or hit_ndjson_file.stem
            )
            unique_targets.add(target_name)
            frequency_hz = _float(row, "frequency_hz")
            drift = _float(row, "drift_rate_hz_per_sec")
            normalized_drift = _float(
                row,
                "normalized_drift_hz_s_per_ghz",
                _normalised_drift(drift, frequency_hz),
            )
            if frequency_hz > 0:
                drift_rows += 1
                max_abs_normalized_drift = max(max_abs_normalized_drift, abs(normalized_drift))
                if abs(normalized_drift) <= 0.44:
                    earth_consistent_rows += 1
            enriched = {
                **row,
                "candidate_id": str(
                    row.get("candidate_id") or f"{hit_ndjson_file.stem}:{index}"
                ),
                "target_name": target_name,
                "normalized_drift_hz_s_per_ghz": normalized_drift,
                "is_earth_drift_consistent": abs(normalized_drift) <= 0.44,
            }
            per_file_candidates.append(enriched)
            review_candidates.append(enriched)
            hit_rows_for_scorer.append(_scorer_features_from_normalized_hit(row))
        candidate_lists.append(per_file_candidates)
        hit_ndjson_row_count += len(rows)
        if max_hit_rows is not None and hit_ndjson_row_count >= max_hit_rows:
            break

    cross_target_flags = flag_cross_target_rfi(candidate_lists, freq_tolerance_hz)
    scorer_summary, anomaly_scores = _score_with_local_model(
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
        "ok": not unreadable_files and not unreadable_hit_ndjson_files,
        "dat_file_count": len(dat_files),
        "hit_ndjson_file_count": len(hit_ndjson_files),
        "hit_ndjson_row_count": hit_ndjson_row_count,
        "hit_ndjson_row_limit": max_hit_rows,
        "hit_bearing_dat_file_count": len(hit_bearing_files),
        "zero_hit_dat_file_count": len(zero_hit_files),
        "unreadable_dat_file_count": len(unreadable_files),
        "unreadable_dat_files": unreadable_files,
        "unreadable_hit_ndjson_file_count": len(unreadable_hit_ndjson_files),
        "unreadable_hit_ndjson_files": unreadable_hit_ndjson_files,
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
        "candidate_review": _candidate_review_summary(
            review_candidates,
            cross_target_flags=cross_target_flags,
            anomaly_scores=anomaly_scores,
            sample_limit=candidate_sample_limit,
        ),
        "sample_dat_files": [str(path) for path in dat_files[:10]],
        "sample_hit_ndjson_files": [str(path) for path in hit_ndjson_files[:10]],
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
) -> tuple[dict[str, Any], list[float | None]]:
    if semisupervised_model_path is None:
        semisupervised_model_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "meerkat_hits"
            / "semisupervised_scorer.joblib"
        )
    model_path = Path(semisupervised_model_path)
    if not model_path.exists():
        return (
            {
                "model_path": str(model_path),
                "model_exists": False,
                "model_used": False,
                "scored_hit_count": 0,
            },
            [None] * len(hit_rows),
        )
    if not hit_rows:
        return (
            {
                "model_path": str(model_path),
                "model_exists": True,
                "model_used": False,
                "scored_hit_count": 0,
                "limitation": "No hit-bearing rows were available to score.",
            },
            [],
        )

    from techno_search.semisupervised_scorer import load_fitted_scorer_joblib

    try:
        scorer = load_fitted_scorer_joblib(model_path)
        scores = scorer.score_hits(hit_rows)
    except Exception as exc:  # noqa: BLE001
        return (
            {
                "model_path": str(model_path),
                "model_exists": True,
                "model_used": False,
                "scored_hit_count": 0,
                "error": str(exc),
            },
            [None] * len(hit_rows),
        )
    return (
        {
            "model_path": str(model_path),
            "model_exists": True,
            "model_used": True,
            "scored_hit_count": len(scores),
            "max_anomaly_score": max(scores),
            "mean_anomaly_score": sum(scores) / len(scores),
        },
        list(scores),
    )


def _candidate_review_summary(
    candidates: list[dict[str, Any]],
    *,
    cross_target_flags: dict[str, dict[str, Any]],
    anomaly_scores: list[float | None],
    sample_limit: int,
) -> dict[str, Any]:
    reviewed: list[dict[str, Any]] = []
    drift_inconsistent_count = 0
    follow_up_candidate_count = 0
    known_control_candidate_count = 0
    stationary_drift_candidate_count = 0
    score_values = list(anomaly_scores)
    if len(score_values) < len(candidates):
        score_values.extend([None] * (len(candidates) - len(score_values)))

    for candidate, anomaly_score in zip(candidates, score_values, strict=False):
        candidate_id = str(candidate.get("candidate_id", ""))
        rfi_flag = cross_target_flags.get(candidate_id)
        known_control = _is_known_control_candidate(candidate)
        normalized_drift = _float(candidate, "normalized_drift_hz_s_per_ghz")
        stationary_drift = abs(normalized_drift) <= DEFAULT_STATIONARY_DRIFT_EPSILON
        drift_consistent = bool(candidate.get("is_earth_drift_consistent", False))
        if not drift_consistent:
            drift_inconsistent_count += 1
        if known_control:
            known_control_candidate_count += 1
        if stationary_drift:
            stationary_drift_candidate_count += 1
        survives_current_filters = (
            rfi_flag is None and drift_consistent and not stationary_drift and not known_control
        )
        if survives_current_filters:
            follow_up_candidate_count += 1
        reviewed.append(
            {
                "candidate_id": candidate_id,
                "target_name": str(candidate.get("target_name", "")),
                "source_artifact": str(candidate.get("source_artifact", "")),
                "backend_host": str(candidate.get("backend_host", "")),
                "beam": _int(candidate, "beam", default=-1),
                "coarse_channel": _int(candidate, "coarse_channel", default=-1),
                "tstart_mjd": _float(candidate, "tstart_mjd"),
                "ra_deg": _float(candidate, "ra_deg"),
                "dec_deg": _float(candidate, "dec_deg"),
                "corpus_source": str(candidate.get("corpus_source", "")),
                "frequency_hz": _float(candidate, "frequency_hz"),
                "snr": _float(candidate, "snr"),
                "drift_rate_hz_per_sec": _float(candidate, "drift_rate_hz_per_sec"),
                "normalized_drift_hz_s_per_ghz": normalized_drift,
                "is_earth_drift_consistent": drift_consistent,
                "stationary_drift": stationary_drift,
                "known_control_target": known_control,
                "cross_target_rfi_flagged": rfi_flag is not None,
                "cross_target_match_count": int(rfi_flag.get("match_count", 0))
                if rfi_flag is not None
                else 0,
                "semisupervised_anomaly_score": anomaly_score,
                "survives_current_automated_filters": survives_current_filters,
                "review_label": (
                    "needs_follow_up_review"
                    if survives_current_filters
                    else (
                        "known_spacecraft_or_calibration_control"
                        if known_control
                        else (
                            "stationary_frequency_review"
                            if stationary_drift
                            else (
                                "likely_cross_target_rfi"
                                if rfi_flag is not None
                                else "drift_inconsistent_review"
                            )
                        )
                    )
                ),
            }
        )

    ranked = sorted(
        reviewed,
        key=lambda row: (
            1 if row["survives_current_automated_filters"] else 0,
            float(row["semisupervised_anomaly_score"] or 0.0),
            float(row["snr"]),
        ),
        reverse=True,
    )
    ranked_survivors = [
        row for row in ranked if bool(row["survives_current_automated_filters"])
    ]
    ranked_rejected_or_controls = [
        row for row in ranked if not bool(row["survives_current_automated_filters"])
    ]
    limited_sample = max(0, sample_limit)
    review_targets = _review_target_groups(ranked_survivors, sample_limit=None)
    return {
        "reviewed_candidate_count": len(reviewed),
        "follow_up_candidate_count": follow_up_candidate_count,
        "follow_up_target_count": len(review_targets),
        "rfi_rejected_candidate_count": len(cross_target_flags),
        "drift_inconsistent_candidate_count": drift_inconsistent_count,
        "stationary_drift_candidate_count": stationary_drift_candidate_count,
        "known_control_candidate_count": known_control_candidate_count,
        "sample_limit": limited_sample,
        "top_review_candidates": ranked_survivors[:limited_sample],
        "top_review_targets": review_targets[:limited_sample],
        "target_concentration": _target_concentration_summary(
            review_targets,
            follow_up_candidate_count=follow_up_candidate_count,
        ),
        "top_rejected_or_control_candidates": ranked_rejected_or_controls[:limited_sample],
        "claim_guardrail": (
            "Rows labeled needs_follow_up_review are automated triage survivors "
            "only, not detections, discoveries, expert review, external validation, "
            "or external-submission approval."
        ),
    }


def _review_target_groups(
    survivors: list[dict[str, Any]],
    sample_limit: int | None,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in survivors:
        grouped.setdefault(str(row["target_name"]), []).append(row)

    summaries: list[dict[str, Any]] = []
    for target_name, rows in grouped.items():
        ranked_rows = sorted(
            rows,
            key=lambda row: (
                float(row["semisupervised_anomaly_score"] or 0.0),
                float(row["snr"]),
            ),
            reverse=True,
        )
        top_row = ranked_rows[0]
        frequencies = [float(row["frequency_hz"]) for row in rows]
        source_artifacts = sorted(
            {str(row["source_artifact"]) for row in rows if str(row["source_artifact"])}
        )
        backend_hosts = _sorted_nonempty_strings(rows, "backend_host")
        beams = _sorted_nonnegative_ints(rows, "beam")
        coarse_channels = _sorted_nonnegative_ints(rows, "coarse_channel")
        tstarts = _positive_floats(rows, "tstart_mjd")
        ra_values = _positive_floats(rows, "ra_deg")
        dec_values = _finite_floats(rows, "dec_deg")
        summaries.append(
            {
                "target_name": target_name,
                "candidate_count": len(rows),
                "top_candidate_id": str(top_row["candidate_id"]),
                "max_semisupervised_anomaly_score": top_row[
                    "semisupervised_anomaly_score"
                ],
                "max_snr": max(float(row["snr"]) for row in rows),
                "min_frequency_hz": min(frequencies),
                "max_frequency_hz": max(frequencies),
                "source_artifact_count": len(source_artifacts),
                "sample_source_artifacts": source_artifacts[:3],
                "source_context": {
                    "beam_count": len(beams),
                    "beams": beams[:10],
                    "backend_host_count": len(backend_hosts),
                    "backend_hosts": backend_hosts[:10],
                    "coarse_channel_count": len(coarse_channels),
                    "coarse_channels": coarse_channels[:10],
                    "min_tstart_mjd": min(tstarts) if tstarts else None,
                    "max_tstart_mjd": max(tstarts) if tstarts else None,
                    "min_ra_deg": min(ra_values) if ra_values else None,
                    "max_ra_deg": max(ra_values) if ra_values else None,
                    "min_dec_deg": min(dec_values) if dec_values else None,
                    "max_dec_deg": max(dec_values) if dec_values else None,
                },
            }
        )

    ranked_summaries = sorted(
        summaries,
        key=lambda row: (
            int(row["candidate_count"]),
            float(row["max_semisupervised_anomaly_score"] or 0.0),
            float(row["max_snr"]),
        ),
        reverse=True,
    )
    if sample_limit is None:
        return ranked_summaries
    return ranked_summaries[:sample_limit]


def _target_concentration_summary(
    review_targets: list[dict[str, Any]],
    *,
    follow_up_candidate_count: int,
) -> dict[str, Any]:
    if follow_up_candidate_count <= 0 or not review_targets:
        return {
            "dominant_target_name": None,
            "dominant_target_candidate_count": 0,
            "dominant_target_fraction": 0.0,
            "source_context_review_needed": False,
        }
    dominant = review_targets[0]
    dominant_count = int(dominant["candidate_count"])
    dominant_fraction = dominant_count / follow_up_candidate_count
    return {
        "dominant_target_name": dominant["target_name"],
        "dominant_target_candidate_count": dominant_count,
        "dominant_target_fraction": dominant_fraction,
        "source_context_review_needed": dominant_fraction > 0.5,
        "reason": (
            "More than half of automated survivor rows come from one target; "
            "review source context and instrumental explanations before treating "
            "the rows as independent follow-up evidence."
        )
        if dominant_fraction > 0.5
        else "",
    }


def _is_known_control_candidate(candidate: dict[str, Any]) -> bool:
    joined = " ".join(
        str(candidate.get(key, "")).lower()
        for key in ("candidate_id", "target_name", "source_artifact", "source_name")
    )
    return "voyager" in joined


def _load_hit_ndjson_rows(
    path: Path,
    *,
    remaining_rows: int | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if remaining_rows is not None and len(rows) >= remaining_rows:
                break
            stripped = line.strip()
            if not stripped:
                continue
            raw = json.loads(stripped)
            if not isinstance(raw, dict):
                raise ValueError(f"{path}:{line_number}: NDJSON row must be an object")
            if _float(raw, "frequency_hz") <= 0:
                raise ValueError(f"{path}:{line_number}: missing positive frequency_hz")
            rows.append(raw)
    return rows


def _scorer_features_from_normalized_hit(row: dict[str, Any]) -> dict[str, Any]:
    frequency_hz = _float(row, "frequency_hz")
    drift = _float(row, "drift_rate_hz_per_sec")
    normalized_drift = _float(
        row,
        "normalized_drift_hz_s_per_ghz",
        _normalised_drift(drift, frequency_hz),
    )
    return {
        "snr": _float(row, "snr"),
        "drift_rate_hz_per_sec": drift,
        "frequency_hz": frequency_hz,
        "bandwidth_hz": _float(row, "bandwidth_hz"),
        "normalized_drift_hz_s_per_ghz": normalized_drift,
        "relative_snr": _float(row, "relative_snr", 1.0),
        "on_off_consistency_score": _float(row, "on_off_consistency_score"),
        "is_earth_drift_consistent": _float(
            row,
            "is_earth_drift_consistent",
            1.0 if abs(normalized_drift) <= 0.44 else 0.0,
        ),
        "rfi_band_overlap_score": _float(row, "rfi_band_overlap_score"),
        "frequency_persistence_score": _float(row, "frequency_persistence_score"),
        "on_hit_count": _float(row, "on_hit_count", 1.0),
        "off_hit_count": _float(row, "off_hit_count"),
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


def _float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _int(row: dict[str, Any], key: str, *, default: int = 0) -> int:
    try:
        return int(row.get(key, default))
    except (TypeError, ValueError):
        return default


def _sorted_nonempty_strings(rows: list[dict[str, Any]], key: str) -> list[str]:
    return sorted({str(row.get(key, "")) for row in rows if str(row.get(key, ""))})


def _sorted_nonnegative_ints(rows: list[dict[str, Any]], key: str) -> list[int]:
    values: set[int] = set()
    for row in rows:
        value = _int(row, key, default=-1)
        if value >= 0:
            values.add(value)
    return sorted(values)


def _positive_floats(rows: list[dict[str, Any]], key: str) -> list[float]:
    return [value for value in _finite_floats(rows, key) if value > 0]


def _finite_floats(rows: list[dict[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        if key not in row or row.get(key) in {None, ""}:
            continue
        value = _float(row, key)
        if value == value and value not in {float("inf"), float("-inf")}:
            values.append(value)
    return values
