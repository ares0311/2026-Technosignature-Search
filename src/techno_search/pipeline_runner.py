"""End-to-end pipeline runner: real input file → scored candidate → report."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.reporting import ReportPaths, write_candidate_reports
from techno_search.schemas import Candidate, Track
from techno_search.scoring import score_candidate


@dataclass
class PipelineRunResult:
    candidate_id: str
    track: Track
    pathway: str
    report_paths: ReportPaths
    ok: bool
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "track": self.track.value,
            "pathway": self.pathway,
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
      - anomaly: not yet supported with real files (uses synthetic pathway)

    Returns a PipelineRunResult with report paths and pathway assignment.
    This is a provenance record only — results do not constitute a detection claim.
    """
    cid = candidate_id or _candidate_id_from_path(input_path)
    try:
        track_enum = _parse_track(track)
        candidate = _build_candidate(input_path, track_enum, cid)
        scored = score_candidate(candidate)
        paths = write_candidate_reports(scored, output_dir)
        return PipelineRunResult(
            candidate_id=cid,
            track=track_enum,
            pathway=scored.recommended_pathway.value,
            report_paths=paths,
            ok=True,
        )
    except Exception as exc:  # noqa: BLE001
        try:
            track_enum = _parse_track(track)
        except ValueError:
            track_enum = Track.RADIO  # fallback for error reporting
        return PipelineRunResult(
            candidate_id=cid,
            track=track_enum,
            pathway="unknown",
            report_paths=ReportPaths(
                markdown_path=output_dir / f"{cid}.md",
                json_path=output_dir / f"{cid}.json",
                manifest_path=output_dir / f"{cid}.manifest.json",
            ),
            ok=False,
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


def _build_candidate(path: Path, track: Track, candidate_id: str) -> Candidate:
    if track == Track.RADIO:
        return _build_radio_candidate(path, candidate_id)
    if track == Track.INFRARED:
        return _build_infrared_candidate(path, candidate_id)
    return _build_anomaly_candidate(path, candidate_id)


def _build_radio_candidate(path: Path, candidate_id: str) -> Candidate:
    from techno_search.radio.hit_table_reader import hit_table_to_radio_hit_dicts
    from techno_search.radio.prototype import build_radio_candidate

    rows = hit_table_to_radio_hit_dicts(path)
    if not rows:
        msg = f"No valid hits found in {path}"
        raise ValueError(msg)
    return build_radio_candidate(candidate_id, rows)


def _build_infrared_candidate(path: Path, candidate_id: str) -> Candidate:
    from techno_search.infrared.catalog_reader import catalog_rows_to_infrared_source_dicts
    from techno_search.infrared.prototype import build_infrared_candidate

    rows = catalog_rows_to_infrared_source_dicts(path)
    if not rows:
        msg = f"No valid catalog rows found in {path}"
        raise ValueError(msg)
    return build_infrared_candidate(candidate_id, rows[0])


def _build_anomaly_candidate(path: Path, candidate_id: str) -> Candidate:
    # Anomaly track: treat the CSV as a generic feature table for now
    # Full archival-crossmatch reader is a future milestone
    from techno_search.anomalies.prototype import build_anomaly_candidate

    return build_anomaly_candidate(candidate_id, {})
