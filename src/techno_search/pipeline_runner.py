"""End-to-end pipeline runner: real input file to scored candidate report."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from techno_search.data_quality import DataQualityResult, validate_input
from techno_search.reporting import ReportPaths, write_candidate_reports
from techno_search.schemas import Candidate, FeatureValue, Track
from techno_search.scoring import score_candidate

PIPELINE_RUN_DISCLAIMER = (
    "Pipeline run results are local triage and provenance records only. They "
    "do not constitute detections, discoveries, external validation, or "
    "authorization for external submission."
)
KNOWN_SPACECRAFT_TOKENS = ("voyager", "spacecraft", "probe")
MJD_EPOCH = datetime(1858, 11, 17, tzinfo=UTC)


@dataclass
class PipelineRunResult:
    candidate_id: str
    track: Track
    pathway: str
    report_paths: ReportPaths
    ok: bool
    error: str | None = None
    input_path: str = ""
    reader_type: str = ""
    row_count: int = 0
    input_validation: dict[str, Any] = field(default_factory=dict)
    disclaimer: str = PIPELINE_RUN_DISCLAIMER

    def as_dict(self) -> dict[str, Any]:
        return {
            "disclaimer": self.disclaimer,
            "candidate_id": self.candidate_id,
            "track": self.track.value,
            "pathway": self.pathway,
            "input_path": self.input_path,
            "reader_type": self.reader_type,
            "row_count": self.row_count,
            "input_validation": self.input_validation,
            "markdown_path": str(self.report_paths.markdown_path),
            "json_path": str(self.report_paths.json_path),
            "manifest_path": str(self.report_paths.manifest_path),
            "ok": self.ok,
            "error": self.error,
        }


def run_pipeline(
    input_path: Path,
    track: str,
    output_dir: Path,
    *,
    candidate_id: str | None = None,
    epoch_dat_files: list[Path] | None = None,
    semisupervised_model_path: Path | None = None,
) -> PipelineRunResult:
    """Run the full pipeline on a real input file.

    Supports:
      - radio: turboSETI-format CSV hit table
      - infrared: Gaia+WISE cross-match CSV
      - anomaly: archival/catalog anomaly CSV feature table
      - photometry: real Kepler/K2/TESS light curve FITS file (BLS periodic
        transit search + aperiodic-dip detection)

    ``epoch_dat_files`` (radio only): additional .dat files from separate
    observation sessions.  When provided the multi-epoch persistence score is
    injected into the candidate features before scoring.

    Returns a PipelineRunResult with report paths and pathway assignment.
    This is a provenance record only — results do not constitute a detection claim.
    """
    cid = candidate_id or _candidate_id_from_path(input_path)
    validation = validate_input(input_path, track)
    validation_data = validation.as_dict()
    try:
        track_enum = _parse_track(track)
        if not validation.ok:
            msg = "Input validation failed: " + "; ".join(validation.issues)
            raise ValueError(msg)
        candidate = _build_candidate(
            input_path,
            track_enum,
            cid,
            epoch_dat_files=epoch_dat_files,
            semisupervised_model_path=semisupervised_model_path,
        )
        scored = score_candidate(candidate)
        paths = write_candidate_reports(scored, output_dir)
        return PipelineRunResult(
            candidate_id=cid,
            track=track_enum,
            pathway=scored.recommended_pathway.value,
            report_paths=paths,
            ok=True,
            input_path=str(input_path),
            reader_type=_reader_type(track_enum),
            row_count=validation.row_count,
            input_validation=validation_data,
        )
    except Exception as exc:  # noqa: BLE001
        return _error_result(
            candidate_id=cid,
            track=track,
            output_dir=output_dir,
            input_path=input_path,
            validation=validation,
            error=str(exc),
        )


def _candidate_id_from_path(path: Path) -> str:
    return path.stem.replace(" ", "_")


def _parse_track(track: str) -> Track:
    mapping = {
        "radio": Track.RADIO,
        "infrared": Track.INFRARED,
        "anomaly": Track.ANOMALY,
        "photometry": Track.TRANSIT_PHOTOMETRY,
    }
    key = track.lower()
    if key not in mapping:
        msg = f"Unknown track '{track}'. Expected: radio, infrared, anomaly, photometry."
        raise ValueError(msg)
    return mapping[key]


def _reader_type(track: Track) -> str:
    if track == Track.RADIO:
        return "turboSETI_csv"
    if track == Track.INFRARED:
        return "gaia_wise_csv"
    if track == Track.TRANSIT_PHOTOMETRY:
        return "lightkurve_fits"
    return "archival_anomaly_csv"


def _error_result(
    *,
    candidate_id: str,
    track: str,
    output_dir: Path,
    input_path: Path,
    validation: DataQualityResult,
    error: str,
) -> PipelineRunResult:
    try:
        track_enum = _parse_track(track)
    except ValueError:
        track_enum = Track.RADIO
    return PipelineRunResult(
        candidate_id=candidate_id,
        track=track_enum,
        pathway="unknown",
        report_paths=ReportPaths(
            markdown_path=output_dir / f"{candidate_id}.md",
            json_path=output_dir / f"{candidate_id}.json",
            manifest_path=output_dir / f"{candidate_id}.manifest.json",
        ),
        ok=False,
        error=error,
        input_path=str(input_path),
        reader_type=_reader_type(track_enum),
        row_count=validation.row_count,
        input_validation=validation.as_dict(),
    )


def _build_candidate(
    path: Path,
    track: Track,
    candidate_id: str,
    *,
    epoch_dat_files: list[Path] | None = None,
    semisupervised_model_path: Path | None = None,
) -> Candidate:
    if track == Track.RADIO:
        return _build_radio_candidate(
            path,
            candidate_id,
            epoch_dat_files=epoch_dat_files,
            semisupervised_model_path=semisupervised_model_path,
        )
    if track == Track.INFRARED:
        return _build_infrared_candidate(path, candidate_id)
    if track == Track.TRANSIT_PHOTOMETRY:
        return _build_photometry_candidate(path, candidate_id)
    return _build_anomaly_candidate(path, candidate_id)


def _build_radio_candidate(
    path: Path,
    candidate_id: str,
    *,
    epoch_dat_files: list[Path] | None = None,
    semisupervised_model_path: Path | None = None,
) -> Candidate:
    from techno_search.catalog_crossmatch import catalog_crossmatch
    from techno_search.gbt_cadence import cadence_candidate_context
    from techno_search.radio.hit_table_reader import (  # noqa: E501
        hit_table_to_radio_hit_dicts,
        read_hit_table_csv,
    )
    from techno_search.radio.prototype import build_radio_candidate

    rows = hit_table_to_radio_hit_dicts(path)
    source_ids, provenance = cadence_candidate_context(path)
    if not source_ids:
        source_ids = (str(path),)
    if "source_file" not in provenance:
        provenance = {**provenance, "source_file": str(path), "reader_type": "turboSETI_csv"}
    if not rows:
        return _build_radio_non_detection_candidate(path, candidate_id, source_ids, provenance)
    candidate = build_radio_candidate(
        candidate_id,
        rows,
        source_ids=source_ids,
        provenance=provenance,
    )

    # Optional live catalog cross-match (requires TECHNO_SEARCH_ENABLE_LIVE_DATA=1)
    raw_rows = read_hit_table_csv(path)
    ra = next((r["ra_deg"] for r in raw_rows if r.get("ra_deg") is not None), None)
    dec = next((r["dec_deg"] for r in raw_rows if r.get("dec_deg") is not None), None)
    mjd = next((r["mjd"] for r in raw_rows if r.get("mjd") is not None), None)
    xmatch = catalog_crossmatch(ra, dec)
    known_score = float(xmatch.get("known_object_score", 0.0))

    # Inject cross-match score into features when the query actually ran.
    # SIMBAD-specific fields are always injected on a live query so that
    # a zero-match result (no known object) is also recorded as evidence.
    extra_features: dict[str, FeatureValue] = {}
    extra_provenance: dict[str, FeatureValue] = {}
    if ra is not None:
        extra_features["ra_deg"] = float(ra)
        extra_provenance["ra_deg"] = float(ra)
    if dec is not None:
        extra_features["dec_deg"] = float(dec)
        extra_provenance["dec_deg"] = float(dec)
    if mjd is not None:
        extra_features["observation_mjd"] = float(mjd)
        extra_provenance["observation_mjd"] = float(mjd)
        observation_time_utc = _mjd_to_utc_iso(float(mjd))
        if observation_time_utc is not None:
            extra_features["observation_time_utc"] = observation_time_utc
            extra_provenance["observation_time_utc"] = observation_time_utc
    if xmatch.get("query_attempted"):
        extra_features["known_object_score"] = known_score
        extra_features["catalog_crossmatch_provider"] = str(xmatch.get("provider", ""))
        extra_provenance["catalog_crossmatch_provider"] = str(xmatch.get("provider", ""))
        extra_provenance["catalog_crossmatch_known_object_score"] = known_score
        # SIMBAD-specific match details (closes Tier 2: SIMBAD cross-match)
        simbad_count = int(xmatch.get("simbad_match_count", 0))
        extra_features["simbad_match_count"] = simbad_count
        extra_provenance["simbad_match_count"] = simbad_count
        simbad_names: list[str] = list(xmatch.get("simbad_match_names") or [])
        extra_provenance["simbad_match_names"] = ", ".join(simbad_names[:5]) or "none"
        extra_features["simbad_known_object_score"] = (
            0.9 if simbad_count == 1 else (1.0 if simbad_count > 1 else 0.0)
        )
        # Gaia-specific match details
        gaia_count = int(xmatch.get("gaia_match_count", 0))
        extra_features["gaia_match_count"] = gaia_count
        extra_provenance["gaia_match_count"] = gaia_count

    local_known_score = _local_radio_known_object_score(
        path=path,
        candidate_id=candidate_id,
        raw_rows=raw_rows,
        source_ids=source_ids,
    )
    if local_known_score > 0.0:
        existing_known_score = extra_features.get("known_object_score", 0.0)
        known_score = (
            float(existing_known_score)
            if isinstance(existing_known_score, (int, float, str))
            else 0.0
        )
        extra_features["known_object_score"] = max(
            known_score,
            local_known_score,
        )
        extra_features["local_known_object_reason"] = "spacecraft_calibration_target"
        extra_provenance["local_known_object_reason"] = "spacecraft_calibration_target"
        extra_provenance["local_known_object_score"] = local_known_score

    # Multi-epoch persistence injection (radio only, opt-in via epoch_dat_files)
    if epoch_dat_files:
        from techno_search.multi_epoch import compare_epochs

        all_dat = [path, *epoch_dat_files]
        me_result = compare_epochs(all_dat)
        extra_features["multi_epoch_persistence_score"] = me_result.max_persistence_score
        extra_features["multi_epoch_group_count"] = len(me_result.multi_epoch_groups)
        extra_features["multi_epoch_epoch_count"] = me_result.epoch_count
        extra_provenance["multi_epoch_epoch_count"] = me_result.epoch_count
        extra_provenance["multi_epoch_group_count"] = len(me_result.multi_epoch_groups)
        extra_provenance["multi_epoch_max_persistence_score"] = (
            me_result.max_persistence_score
        )

    semisupervised_features, semisupervised_provenance = (
        _semisupervised_model_context(
            rows,
            model_path=semisupervised_model_path,
        )
    )
    extra_features.update(semisupervised_features)
    extra_provenance.update(semisupervised_provenance)

    if extra_features:
        candidate = Candidate(
            candidate_id=candidate.candidate_id,
            track=candidate.track,
            features={**candidate.features, **extra_features},
            source_ids=candidate.source_ids,
            provenance={**candidate.provenance, **extra_provenance},
        )

    return candidate


def _mjd_to_utc_iso(mjd: float) -> str | None:
    try:
        observed_at = MJD_EPOCH + timedelta(days=mjd)
    except OverflowError:
        return None
    return observed_at.isoformat(timespec="seconds").replace("+00:00", "Z")


def _default_semisupervised_model_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "data"
        / "meerkat_hits"
        / "semisupervised_scorer.joblib"
    )


def _semisupervised_model_context(
    rows: list[dict[str, Any]],
    *,
    model_path: Path | None,
) -> tuple[dict[str, FeatureValue], dict[str, FeatureValue]]:
    resolved_model = (
        Path(model_path) if model_path is not None else _default_semisupervised_model_path()
    )
    if not resolved_model.exists():
        return {}, {}

    from techno_search.semisupervised_scorer import load_fitted_scorer_joblib

    try:
        scorer = load_fitted_scorer_joblib(resolved_model)
        enriched_rows = [_semisupervised_hit_features(row, rows) for row in rows]
        scores = scorer.score_hits(enriched_rows)
    except Exception as exc:  # noqa: BLE001
        return {}, {
            "semisupervised_model_path": str(resolved_model),
            "semisupervised_model_error": str(exc),
        }

    if not scores:
        return {}, {}
    max_score = max(scores)
    mean_score = sum(scores) / len(scores)
    features: dict[str, FeatureValue] = {
        "semisupervised_anomaly_score": max_score,
        "semisupervised_mean_anomaly_score": mean_score,
        "semisupervised_scored_hit_count": len(scores),
        "semisupervised_model_used": True,
    }
    provenance: dict[str, FeatureValue] = {
        "semisupervised_model_path": str(resolved_model),
        "semisupervised_scored_hit_count": len(scores),
        "semisupervised_score_policy": "max_hit_score_local_triage_only",
    }
    return features, provenance


def _semisupervised_hit_features(
    row: dict[str, Any],
    all_rows: list[dict[str, Any]],
) -> dict[str, FeatureValue]:
    frequency_hz = _float_feature(row, "frequency_hz")
    drift = _float_feature(row, "drift_rate_hz_per_sec")
    snr = _float_feature(row, "snr")
    same_frequency_rows = [
        other
        for other in all_rows
        if abs(_float_feature(other, "frequency_hz") - frequency_hz)
        <= 5.0
    ]
    scan_roles = [str(other.get("scan_role", "")).lower() for other in same_frequency_rows]
    on_hit_count = sum(1 for role in scan_roles if not role.startswith("off"))
    off_hit_count = sum(1 for role in scan_roles if role.startswith("off"))
    total_role_hits = max(1, on_hit_count + off_hit_count)
    median_snr = _median_positive_snr(all_rows)
    normalized_drift = drift / (frequency_hz / 1e9) if frequency_hz > 0 else 0.0
    return {
        "snr": snr,
        "drift_rate_hz_per_sec": drift,
        "frequency_hz": frequency_hz,
        "bandwidth_hz": _float_feature(row, "bandwidth_hz"),
        "normalized_drift_hz_s_per_ghz": normalized_drift,
        "relative_snr": snr / median_snr,
        "on_off_consistency_score": off_hit_count / total_role_hits,
        "is_earth_drift_consistent": 1.0 if abs(normalized_drift) <= 0.44 else 0.0,
        "rfi_band_overlap_score": 0.0,
        "frequency_persistence_score": _clamp(
            max(0, len(same_frequency_rows) - 1) / max(1, len(all_rows) - 1)
        ),
        "on_hit_count": on_hit_count,
        "off_hit_count": off_hit_count,
    }


def _float_feature(row: dict[str, Any], key: str) -> float:
    try:
        return float(row.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _median_positive_snr(rows: list[dict[str, Any]]) -> float:
    values = sorted(
        _float_feature(row, "snr")
        for row in rows
        if _float_feature(row, "snr") > 0
    )
    if not values:
        return 1.0
    midpoint = len(values) // 2
    if len(values) % 2 == 1:
        return values[midpoint]
    return (values[midpoint - 1] + values[midpoint]) / 2.0


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _local_radio_known_object_score(
    *,
    path: Path,
    candidate_id: str,
    raw_rows: list[dict[str, Any]],
    source_ids: tuple[str, ...],
) -> float:
    identifiers: list[str] = [candidate_id, path.name, path.stem, *source_ids]
    identifiers.extend(
        str(row.get("source_name", "")) for row in raw_rows if row.get("source_name")
    )
    searchable = " ".join(identifiers).lower()
    return 1.0 if any(token in searchable for token in KNOWN_SPACECRAFT_TOKENS) else 0.0


def _build_radio_non_detection_candidate(
    path: Path,
    candidate_id: str,
    source_ids: tuple[str, ...],
    provenance: dict[str, Any],
) -> Candidate:
    """Build a non-detection candidate when turboSETI found 0 hits above threshold.

    Routes to do_not_submit_false_positive via zero SNR, which is the correct
    disposition: the target was searched and no narrowband signal was detected.
    Writes a manifest so prod-scan can record this as a confirmed non-detection.
    """
    return Candidate(
        candidate_id=candidate_id,
        track=Track.RADIO,
        features={
            "snr": 0.0,
            "bandwidth_hz": 0.0,
            "drift_rate_hz_per_sec": 0.0,
            "on_target_presence_score": 0.0,
            "off_target_presence_score": 0.0,
            "rfi_band_overlap_score": 0.0,
            "frequency_persistence_score": 0.0,
            "nearby_target_recurrence_score": 0.0,
            "instrumental_artifact_score": 0.0,
            "injection_recovery_score": 0.0,
            "repeat_observation_score": 0.0,
            "data_quality_score": 1.0,
            "metadata_completeness_score": 0.5,
            "turboseti_hit_count": 0,
            "zero_hit_non_detection": True,
        },
        source_ids=source_ids,
        provenance={
            **provenance,
            "non_detection": True,
            "hit_count": 0,
            "source_file": str(path),
            "reader_type": "turboSETI_csv",
            "classification": "zero_hit_non_detection",
        },
    )


def _build_infrared_candidate(path: Path, candidate_id: str) -> Candidate:
    from techno_search.catalog_crossmatch import catalog_crossmatch
    from techno_search.infrared.catalog_reader import catalog_rows_to_infrared_source_dicts
    from techno_search.infrared.prototype import build_infrared_candidate
    from techno_search.infrared_wise.agn_indicator import wise_agn_indicator
    from techno_search.infrared_wise.photosphere_excess import wise_ir_excess_result

    rows = catalog_rows_to_infrared_source_dicts(path)
    if not rows:
        msg = f"No valid catalog rows found in {path}"
        raise ValueError(msg)
    row = dict(rows[0])

    # Real WISE W1/W2-photosphere vs. W3/W4 excess check (Planck's-law
    # blackbody, not a synthetic heuristic). Overrides the fallback
    # color-based ir_excess_score/sed_fit_residual_score in
    # infrared/prototype.py when W1-W4 photometry is present.
    wise_excess = wise_ir_excess_result(
        row.get("w1"),
        row.get("w2"),
        row.get("w3"),
        row.get("w4"),
        w3_mag_err=row.get("w3_mag_err"),
        w4_mag_err=row.get("w4_mag_err"),
    )
    if wise_excess.computable:
        row["ir_excess_score"] = wise_excess.ir_excess_score()
        row["sed_fit_residual_score"] = wise_excess.ir_excess_score()

    # Real WISE W1-W2 AGN color indicator (Stern et al. 2012 / Assef et al.
    # 2013 literature thresholds, not an invented cutoff). Overrides the
    # caller-supplied default galaxy_agn_indicator_score when W1/W2 are
    # present.
    agn_indicator = wise_agn_indicator(
        row.get("w1"),
        row.get("w2"),
        w2_mag_for_reliability_limit=row.get("w2"),
    )
    if agn_indicator.computable:
        row["galaxy_agn_indicator_score"] = agn_indicator.agn_indicator_score()

    candidate = build_infrared_candidate(candidate_id, row)

    if wise_excess.computable:
        candidate = Candidate(
            candidate_id=candidate.candidate_id,
            track=candidate.track,
            features={
                **candidate.features,
                "wise_photosphere_temperature_k": wise_excess.photosphere_temperature_k,
                "wise_w3_excess_significance": wise_excess.w3_excess_significance,
                "wise_w4_excess_significance": wise_excess.w4_excess_significance,
            },
            source_ids=candidate.source_ids,
            provenance={
                **candidate.provenance,
                "wise_excess_method": "single_temperature_blackbody_w1w2_photosphere",
            },
        )

    if agn_indicator.computable:
        candidate = Candidate(
            candidate_id=candidate.candidate_id,
            track=candidate.track,
            features={
                **candidate.features,
                "wise_w1_minus_w2": agn_indicator.w1_minus_w2,
                "wise_agn_meets_stern_2012_threshold": (
                    agn_indicator.meets_stern_2012_reliable_threshold
                ),
            },
            source_ids=candidate.source_ids,
            provenance={
                **candidate.provenance,
                "wise_agn_indicator_method": "stern_2012_assef_2013_w1w2_color",
            },
        )

    # Optional live catalog cross-match (requires TECHNO_SEARCH_ENABLE_LIVE_DATA=1)
    ra = row.get("ra_deg")
    dec = row.get("dec_deg")
    xmatch = catalog_crossmatch(ra, dec)
    known_score = float(xmatch.get("known_object_score", 0.0))

    extra_features: dict[str, FeatureValue] = {}
    extra_provenance: dict[str, FeatureValue] = {}
    if xmatch.get("query_attempted"):
        extra_features["known_object_score"] = known_score
        extra_features["catalog_crossmatch_provider"] = str(xmatch.get("provider", ""))
        extra_provenance["catalog_crossmatch_provider"] = str(xmatch.get("provider", ""))
        extra_provenance["catalog_crossmatch_known_object_score"] = known_score
        simbad_count = int(xmatch.get("simbad_match_count", 0))
        extra_features["simbad_match_count"] = simbad_count
        extra_provenance["simbad_match_count"] = simbad_count
        simbad_names: list[str] = list(xmatch.get("simbad_match_names") or [])
        extra_provenance["simbad_match_names"] = ", ".join(simbad_names[:5]) or "none"
        extra_features["simbad_known_object_score"] = (
            0.9 if simbad_count == 1 else (1.0 if simbad_count > 1 else 0.0)
        )
        gaia_count = int(xmatch.get("gaia_match_count", 0))
        extra_features["gaia_match_count"] = gaia_count
        extra_provenance["gaia_match_count"] = gaia_count

    if extra_features:
        candidate = Candidate(
            candidate_id=candidate.candidate_id,
            track=candidate.track,
            features={**candidate.features, **extra_features},
            source_ids=candidate.source_ids,
            provenance={**candidate.provenance, **extra_provenance},
        )
    return candidate


def _build_anomaly_candidate(path: Path, candidate_id: str) -> Candidate:
    from techno_search.anomalies.catalog_reader import anomaly_rows_to_candidate_dicts
    from techno_search.anomalies.prototype import build_anomaly_candidate

    rows = anomaly_rows_to_candidate_dicts(path)
    if not rows:
        msg = f"No valid anomaly rows found in {path}"
        raise ValueError(msg)
    row = rows[0]
    source_ids = [
        str(source_id)
        for source_id in (
            row.get("historical_source_id"),
            row.get("modern_source_id"),
        )
        if source_id
    ]
    return build_anomaly_candidate(
        candidate_id,
        row,
        source_ids=source_ids,
        provenance={"source_file": str(path), "reader_type": "archival_anomaly_csv"},
    )


def _build_photometry_candidate(path: Path, candidate_id: str) -> Candidate:
    from techno_search.catalog_crossmatch import catalog_crossmatch
    from techno_search.photometry.aperiodic_dip import detect_aperiodic_dips
    from techno_search.photometry.bls_detection import run_bls_transit_search
    from techno_search.photometry.lightcurve_io import load_lightcurve_file
    from techno_search.photometry.prototype import build_transit_photometry_candidate
    from techno_search.photometry.transit_shape import classify_transit_shape

    raw_lc = load_lightcurve_file(path)
    raw_cadence_count = int(len(raw_lc.time))
    clean_lc = raw_lc.remove_nans().normalize()
    finite_fraction = (
        int(len(clean_lc.time)) / raw_cadence_count if raw_cadence_count > 0 else 0.0
    )

    ra_deg = _lightcurve_coordinate(clean_lc, "ra")
    dec_deg = _lightcurve_coordinate(clean_lc, "dec")
    target_id = str(clean_lc.meta.get("OBJECT") or clean_lc.meta.get("LABEL") or candidate_id)

    # Aperiodic-dip detection runs on the normalized-but-not-flattened light
    # curve: flattening removes long-timescale variability, which would also
    # suppress the kind of long, irregular dimming events this detector looks
    # for (Boyajian's Star-style events last days, longer than a typical
    # flatten() smoothing window).
    dip_events = detect_aperiodic_dips(clean_lc.time.value, clean_lc.flux.value)

    # BLS periodic-transit search runs on the flattened light curve, following
    # standard practice: BLS assumes a fixed-depth periodic signal, and
    # unremoved stellar variability degrades period/depth recovery.
    flattened_lc = clean_lc.flatten()
    bls_result = run_bls_transit_search(flattened_lc)
    shape_result = classify_transit_shape(
        flattened_lc.time.value, flattened_lc.flux.value, bls_result
    )

    # Optional live catalog cross-match (requires TECHNO_SEARCH_ENABLE_LIVE_DATA=1)
    xmatch = catalog_crossmatch(ra_deg, dec_deg)
    known_score = float(xmatch.get("known_object_score", 0.0))

    candidate = build_transit_photometry_candidate(
        candidate_id,
        bls_result=bls_result,
        dip_events=dip_events,
        shape_result=shape_result,
        target_id=target_id,
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        cadence_count=int(len(clean_lc.time)),
        finite_cadence_fraction=finite_fraction,
        known_object_score=known_score,
        source_ids=(target_id,),
        provenance={"source_file": str(path), "reader_type": "lightkurve_fits"},
    )

    if xmatch.get("query_attempted"):
        extra_features: dict[str, FeatureValue] = {
            "catalog_crossmatch_provider": str(xmatch.get("provider", "")),
        }
        extra_provenance: dict[str, FeatureValue] = {
            "catalog_crossmatch_provider": str(xmatch.get("provider", "")),
            "catalog_crossmatch_known_object_score": known_score,
        }
        simbad_count = int(xmatch.get("simbad_match_count", 0))
        extra_features["simbad_match_count"] = simbad_count
        extra_provenance["simbad_match_count"] = simbad_count
        simbad_names: list[str] = list(xmatch.get("simbad_match_names") or [])
        extra_provenance["simbad_match_names"] = ", ".join(simbad_names[:5]) or "none"
        gaia_count = int(xmatch.get("gaia_match_count", 0))
        extra_features["gaia_match_count"] = gaia_count
        extra_provenance["gaia_match_count"] = gaia_count
        candidate = Candidate(
            candidate_id=candidate.candidate_id,
            track=candidate.track,
            features={**candidate.features, **extra_features},
            source_ids=candidate.source_ids,
            provenance={**candidate.provenance, **extra_provenance},
        )

    return candidate


def _lightcurve_coordinate(lc: Any, name: str) -> float | None:
    value = getattr(lc, name, None)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
