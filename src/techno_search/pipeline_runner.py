"""End-to-end pipeline runner: real input file to scored candidate report."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from techno_search.data_quality import DataQualityResult, validate_input
from techno_search.reporting import ReportPaths, write_candidate_reports
from techno_search.schemas import Candidate, Track
from techno_search.scoring import score_candidate

PIPELINE_RUN_DISCLAIMER = (
    "Pipeline run results are local triage and provenance records only. They "
    "do not constitute detections, discoveries, external validation, or "
    "authorization for external submission."
)


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
) -> PipelineRunResult:
    """Run the full pipeline on a real input file.

    Supports:
      - radio: turboSETI-format CSV hit table
      - infrared: Gaia+WISE cross-match CSV
      - anomaly: archival/catalog anomaly CSV feature table

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
        candidate = _build_candidate(input_path, track_enum, cid)
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
    mapping = {"radio": Track.RADIO, "infrared": Track.INFRARED, "anomaly": Track.ANOMALY}
    key = track.lower()
    if key not in mapping:
        msg = f"Unknown track '{track}'. Expected: radio, infrared, anomaly."
        raise ValueError(msg)
    return mapping[key]


def _reader_type(track: Track) -> str:
    if track == Track.RADIO:
        return "turboSETI_csv"
    if track == Track.INFRARED:
        return "gaia_wise_csv"
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


def _build_candidate(path: Path, track: Track, candidate_id: str) -> Candidate:
    if track == Track.RADIO:
        return _build_radio_candidate(path, candidate_id)
    if track == Track.INFRARED:
        return _build_infrared_candidate(path, candidate_id)
    return _build_anomaly_candidate(path, candidate_id)


def _build_radio_candidate(path: Path, candidate_id: str) -> Candidate:
    from techno_search.catalog_crossmatch import catalog_crossmatch
    from techno_search.gbt_cadence import cadence_candidate_context
    from techno_search.radio.hit_table_reader import (  # noqa: E501
        hit_table_to_radio_hit_dicts,
        read_hit_table_csv,
    )
    from techno_search.radio.prototype import build_radio_candidate

    rows = hit_table_to_radio_hit_dicts(path)
    if not rows:
        msg = f"No valid hits found in {path}"
        raise ValueError(msg)
    source_ids, provenance = cadence_candidate_context(path)
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
    xmatch = catalog_crossmatch(ra, dec)
    known_score = float(xmatch.get("known_object_score", 0.0))

    # Inject cross-match score into features (only if the query actually ran)
    if xmatch.get("query_attempted") and known_score > 0.0:
        updated_features = dict(candidate.features)
        updated_features["known_object_score"] = known_score
        updated_features["catalog_crossmatch_provider"] = str(xmatch.get("provider", ""))
        candidate = Candidate(
            candidate_id=candidate.candidate_id,
            track=candidate.track,
            features=updated_features,
            source_ids=candidate.source_ids,
            provenance={
                **candidate.provenance,
                "catalog_crossmatch_provider": str(xmatch.get("provider", "")),
                "catalog_crossmatch_match_count": int(xmatch.get("match_count", 0)),
                "catalog_crossmatch_known_object_score": known_score,
            },
        )

    return candidate


def _build_infrared_candidate(path: Path, candidate_id: str) -> Candidate:
    from techno_search.infrared.catalog_reader import catalog_rows_to_infrared_source_dicts
    from techno_search.infrared.prototype import build_infrared_candidate

    rows = catalog_rows_to_infrared_source_dicts(path)
    if not rows:
        msg = f"No valid catalog rows found in {path}"
        raise ValueError(msg)
    return build_infrared_candidate(candidate_id, rows[0])


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
