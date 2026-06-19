"""Production scan run IDs and conservative outcome ledgers.

These artifacts are operator ledgers for local citizen-science production use.
They do not make detection, discovery, external-validation, expert-review, or
external-submission claims.
"""

from __future__ import annotations

import json
import re
import secrets
import string
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from techno_search.scan_summary import load_candidates_from_batch_dir, scan_summary

PRODUCTION_RUN_MANIFEST_SCHEMA_VERSION = "production_run_manifest_v1"
PRODUCTION_NON_DETECTIONS_SCHEMA_VERSION = "production_non_detections_v1"
PRODUCTION_FOLLOW_UPS_SCHEMA_VERSION = "production_follow_ups_v1"
PRODUCTION_TARGET_STATUS_SCHEMA_VERSION = "production_target_status_v1"
PRODUCTION_OUTCOME_DISCLAIMER = (
    "Production run outcome files are local citizen-science operations ledgers "
    "only. They do not constitute detection, discovery, expert review, peer "
    "review, external validation, or authorization for external submission."
)
PRODUCTION_PROMOTION_SCOPE = "local_citizen_science_operations_only"

FOLLOW_UP_PATHWAYS = {
    "candidate_review_packet",
    "follow_up_target",
    "human_review_queue",
    "external_followup_candidate",
}


def make_production_run_id(
    *,
    now: datetime | None = None,
    token: str | None = None,
    run_type: str = "prod-scan",
) -> str:
    """Return a human-readable run ID such as ``RUN-2026-06-18_201325Z-A7K4-prod-scan``."""
    moment = now or datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    moment = moment.astimezone(UTC)
    clean_token = (token or _random_token()).upper()
    if not clean_token.isalnum() or len(clean_token) != 4:
        raise ValueError("token must be exactly four alphanumeric characters")
    clean_type = "-".join(part for part in run_type.lower().split() if part)
    if not clean_type.replace("-", "").isalnum():
        raise ValueError("run_type must contain only letters, numbers, spaces, or hyphens")
    return f"RUN-{moment.strftime('%Y-%m-%d_%H%M%SZ')}-{clean_token}-{clean_type}"


def build_production_outcomes(
    candidates: list[dict[str, Any]],
    *,
    run_id: str,
    started_at_utc: str,
    completed_at_utc: str,
    scan_summary_data: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Split one production scan into manifest, non-detection, and follow-up ledgers."""
    summary = scan_summary_data or scan_summary(candidates)
    follow_up_entries: list[dict[str, Any]] = []
    non_detection_entries: list[dict[str, Any]] = []

    for candidate in candidates:
        pathway = str(candidate.get("recommended_pathway") or candidate.get("pathway") or "unknown")
        if pathway in FOLLOW_UP_PATHWAYS:
            follow_up_entries.append(
                _follow_up_entry(candidate, run_id, len(follow_up_entries) + 1)
            )
        else:
            non_detection_entries.append(
                _non_detection_entry(candidate, run_id, len(non_detection_entries) + 1)
            )

    scan_level_negative_result = {
        "applies": not follow_up_entries,
        "reason": (
            "no_follow_up_pathway_candidates"
            if candidates
            else "no_candidates_loaded_from_results"
        ),
        "candidate_count": len(candidates),
        "follow_up_count": len(follow_up_entries),
    }

    files = {
        "manifest": f"{run_id}_manifest.json",
        "scan_summary": f"{run_id}_scan_summary.json",
        "non_detections": f"{run_id}_non_detections.json",
        "follow_ups": f"{run_id}_follow_ups.json",
        "target_status": f"{run_id}_target_status.json",
        "review_dashboard": f"{run_id}_review_dashboard.json",
    }
    target_status = build_target_status_summary(
        candidates,
        run_id=run_id,
        follow_up_entries=follow_up_entries,
        non_detection_entries=non_detection_entries,
    )

    manifest = {
        "schema_version": PRODUCTION_RUN_MANIFEST_SCHEMA_VERSION,
        "artifact_kind": "production_run_manifest",
        "run_id": run_id,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at_utc,
        "production_promotion_scope": PRODUCTION_PROMOTION_SCOPE,
        "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
        "detection_claimed": False,
        "discovery_claimed": False,
        "expert_review_claimed": False,
        "external_validation_claimed": False,
        "external_submission_allowed": False,
        "candidate_count": len(candidates),
        "non_detection_count": len(non_detection_entries),
        "follow_up_count": len(follow_up_entries),
        "target_status_count": int(target_status["target_count"]),
        "scan_level_negative_result": scan_level_negative_result,
        "files": files,
        "scan_summary": {
            "total_candidates": int(summary.get("total_candidates", len(candidates))),
            "follow_up_count": int(summary.get("follow_up_count", len(follow_up_entries))),
            "candidate_review_count": int(summary.get("candidate_review_count", 0)),
            "targets_scanned": int(summary.get("targets_scanned", 0)),
        },
    }
    non_detections = {
        "schema_version": PRODUCTION_NON_DETECTIONS_SCHEMA_VERSION,
        "artifact_kind": "production_non_detections",
        "run_id": run_id,
        "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
        "detection_claimed": False,
        "external_submission_allowed": False,
        "entry_count": len(non_detection_entries),
        "scan_level_negative_result": scan_level_negative_result,
        "entries": non_detection_entries,
    }
    follow_ups = {
        "schema_version": PRODUCTION_FOLLOW_UPS_SCHEMA_VERSION,
        "artifact_kind": "production_follow_ups",
        "run_id": run_id,
        "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
        "detection_claimed": False,
        "external_submission_allowed": False,
        "entry_count": len(follow_up_entries),
        "entries": follow_up_entries,
    }
    return {
        "manifest": manifest,
        "non_detections": non_detections,
        "follow_ups": follow_ups,
        "target_status": target_status,
    }


def write_production_outcomes(
    *,
    results_dir: Path,
    run_dir: Path,
    run_id: str,
    started_at_utc: str,
    completed_at_utc: str,
    scan_summary_path: Path | None = None,
) -> dict[str, Any]:
    """Load candidates from ``results_dir`` and write run outcome files into ``run_dir``."""
    candidates = load_candidates_from_batch_dir(results_dir)
    summary_data = _load_json(scan_summary_path) if scan_summary_path else scan_summary(candidates)
    outcomes = build_production_outcomes(
        candidates,
        run_id=run_id,
        started_at_utc=started_at_utc,
        completed_at_utc=completed_at_utc,
        scan_summary_data=summary_data,
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "manifest_path": run_dir / f"{run_id}_manifest.json",
        "non_detections_path": run_dir / f"{run_id}_non_detections.json",
        "follow_ups_path": run_dir / f"{run_id}_follow_ups.json",
        "target_status_path": run_dir / f"{run_id}_target_status.json",
    }
    _write_json(paths["manifest_path"], outcomes["manifest"])
    _write_json(paths["non_detections_path"], outcomes["non_detections"])
    _write_json(paths["follow_ups_path"], outcomes["follow_ups"])
    _write_json(paths["target_status_path"], outcomes["target_status"])
    return {
        **outcomes["manifest"],
        **{key: str(path) for key, path in paths.items()},
    }


def production_run_summary(run_dir: Path) -> dict[str, Any]:
    """Return a compact summary for one production run directory."""
    run_path = Path(run_dir)
    manifests = sorted(run_path.glob("RUN-*_manifest.json"))
    if not manifests:
        return {
            "ok": False,
            "error": f"No production run manifest found in {run_path}",
            "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
        }
    manifest = _load_json(manifests[-1])
    run_id = str(manifest.get("run_id", manifests[-1].stem.removesuffix("_manifest")))
    return {
        "ok": True,
        "schema_version": PRODUCTION_RUN_MANIFEST_SCHEMA_VERSION,
        "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
        "run_id": run_id,
        "run_dir": str(run_path),
        "candidate_count": int(manifest.get("candidate_count", 0)),
        "non_detection_count": int(manifest.get("non_detection_count", 0)),
        "follow_up_count": int(manifest.get("follow_up_count", 0)),
        "external_submission_allowed": False,
        "detection_claimed": False,
        "files": manifest.get("files", {}),
    }


def production_run_list(scans_dir: Path) -> dict[str, Any]:
    """List production runs under a scan directory."""
    scan_path = Path(scans_dir)
    summaries = [
        summary
        for child in sorted(scan_path.iterdir()) if child.is_dir()
        for summary in [production_run_summary(child)]
        if summary.get("ok")
    ] if scan_path.exists() else []
    return {
        "ok": scan_path.exists(),
        "schema_version": PRODUCTION_RUN_MANIFEST_SCHEMA_VERSION,
        "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
        "scans_dir": str(scan_path),
        "run_count": len(summaries),
        "runs": summaries,
    }


def latest_production_run_dir(scans_dir: Path) -> Path | None:
    """Return the newest valid production run directory, if one exists."""
    runs = production_run_list(scans_dir).get("runs", [])
    valid_runs = [run for run in runs if run.get("ok") and run.get("run_dir")]
    if not valid_runs:
        return None
    latest = sorted(valid_runs, key=lambda run: str(run.get("run_id", "")))[-1]
    return Path(str(latest["run_dir"]))


def production_run_file(run_dir: Path, kind: str) -> dict[str, Any]:
    """Load the follow-up or non-detection file from one production run."""
    suffix_by_kind = {
        "follow_ups": "_follow_ups.json",
        "non_detections": "_non_detections.json",
        "target_status": "_target_status.json",
    }
    suffix = suffix_by_kind[kind]
    files = sorted(Path(run_dir).glob(f"RUN-*{suffix}"))
    if not files:
        return {
            "ok": False,
            "error": f"No {kind} file found in {run_dir}",
            "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
        }
    return {"ok": True, **_load_json(files[-1])}


def build_target_status_summary(
    candidates: list[dict[str, Any]],
    *,
    run_id: str,
    follow_up_entries: list[dict[str, Any]] | None = None,
    non_detection_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build compact per-target status rows for terminal UX and resume artifacts."""
    index_by_candidate = _index_ids_by_candidate(
        follow_up_entries=follow_up_entries or [],
        non_detection_entries=non_detection_entries or [],
    )
    by_target: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        target_name = str(
            candidate.get("target_name") or candidate.get("candidate_id") or "unknown"
        )
        by_target.setdefault(target_name, []).append(candidate)

    entries: list[dict[str, Any]] = []
    for sequence, target_name in enumerate(sorted(by_target), start=1):
        target_candidates = by_target[target_name]
        best_candidate = max(
            target_candidates,
            key=lambda item: float(item.get("score", 0.0)),
        )
        follow_up_required = any(
            str(item.get("recommended_pathway") or item.get("pathway") or "unknown")
            in FOLLOW_UP_PATHWAYS
            for item in target_candidates
        )
        candidate_id = str(best_candidate.get("candidate_id", ""))
        kind = classify_target_kind(best_candidate)
        index_id = index_by_candidate.get(candidate_id)
        if not index_id:
            prefix = "FU" if follow_up_required else "NEG"
            index_id = _child_id(prefix, run_id, sequence)
        entries.append(
            {
                "index_id": index_id,
                "target_name": target_name,
                "descriptive_name": kind["descriptive_name"],
                "target_kind": kind["target_kind"],
                "target_kind_confidence": kind["target_kind_confidence"],
                "target_kind_limitation": kind["target_kind_limitation"],
                "follow_up_required": follow_up_required,
                "composite_score": float(best_candidate.get("score", 0.0)),
                "score_basis": "pipeline_score",
                "candidate_count": len(target_candidates),
                "top_candidate_id": candidate_id,
                "top_pathway": str(
                    best_candidate.get("recommended_pathway")
                    or best_candidate.get("pathway")
                    or "unknown"
                ),
                "track": str(best_candidate.get("track", "unknown")),
                "detection_claimed": False,
                "external_submission_allowed": False,
            }
        )
    return {
        "schema_version": PRODUCTION_TARGET_STATUS_SCHEMA_VERSION,
        "artifact_kind": "production_target_status",
        "run_id": run_id,
        "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
        "detection_claimed": False,
        "external_submission_allowed": False,
        "target_count": len(entries),
        "follow_up_required_count": sum(
            1 for entry in entries if bool(entry["follow_up_required"])
        ),
        "classification_reliability": "best_effort_from_local_metadata",
        "classification_limitation": (
            "Single-star, binary, and massive-body labels are inferred only when "
            "local target names or candidate metadata make that conservative. "
            "Unknowns should be resolved by a future committed target taxonomy."
        ),
        "entries": entries,
    }


def classify_target_kind(candidate: dict[str, Any]) -> dict[str, str]:
    """Best-effort target kind label from local names and candidate metadata."""
    target_name = str(candidate.get("target_name") or candidate.get("candidate_id") or "unknown")
    track = str(candidate.get("track", "unknown")).lower()
    searchable = " ".join(
        str(value)
        for value in (
            target_name,
            candidate.get("candidate_id", ""),
            candidate.get("pathway", ""),
            candidate.get("recommended_pathway", ""),
            candidate.get("source_ids", ""),
            candidate.get("provenance", ""),
        )
    ).lower()
    if any(token in searchable for token in ("voyager", "spacecraft", "probe")):
        return _target_kind(
            target_name,
            "spacecraft calibration target",
            "high",
            "",
        )
    if any(token in searchable for token in ("_off", "-off", " off", "off-target")):
        return _target_kind(target_name, "off-target control", "medium", "")
    if any(token in searchable for token in ("binary", "double star", "eclipsing")):
        return _target_kind(target_name, "binary stellar system", "medium", "")
    if any(
        token in searchable
        for token in ("planet", "jupiter", "saturn", "mars", "venus", "moon", "asteroid", "comet")
    ):
        return _target_kind(target_name, "solar-system or massive body", "medium", "")
    if target_name.upper().startswith(("HIP", "HD", "TYC", "GJ", "GL ")):
        return _target_kind(
            target_name,
            "stellar target",
            "medium",
            "Local metadata does not reliably distinguish single stars from binaries.",
        )
    if track == "infrared":
        return _target_kind(target_name, "infrared catalog source", "low", "")
    if track == "anomaly":
        return _target_kind(target_name, "archival/catalog anomaly source", "low", "")
    if track == "radio":
        return _target_kind(
            target_name,
            "radio sky target",
            "low",
            "Local metadata does not identify the astrophysical object class.",
        )
    return _target_kind(
        target_name,
        "unknown target type",
        "low",
        "A committed target taxonomy is needed for reliable descriptive labels.",
    )


def _follow_up_entry(candidate: dict[str, Any], run_id: str, sequence: int) -> dict[str, Any]:
    pathway = str(candidate.get("recommended_pathway") or candidate.get("pathway") or "unknown")
    return {
        "follow_up_id": _child_id("FU", run_id, sequence),
        "candidate_id": str(candidate.get("candidate_id", "")),
        "target_name": str(candidate.get("target_name", "")),
        "track": str(candidate.get("track", "unknown")),
        "pathway": pathway,
        "score": float(candidate.get("score", 0.0)),
        "frequency_hz": float(candidate.get("frequency_hz", 0.0)),
        "snr": float(candidate.get("snr", 0.0)),
        "status": "needs_local_citizen_science_review",
        "reason": "candidate_entered_follow_up_pathway",
        "detection_claimed": False,
        "external_submission_allowed": False,
    }


def _non_detection_entry(candidate: dict[str, Any], run_id: str, sequence: int) -> dict[str, Any]:
    pathway = str(candidate.get("recommended_pathway") or candidate.get("pathway") or "unknown")
    return {
        "non_detection_id": _child_id("NEG", run_id, sequence),
        "candidate_id": str(candidate.get("candidate_id", "")),
        "target_name": str(candidate.get("target_name", "")),
        "track": str(candidate.get("track", "unknown")),
        "pathway": pathway,
        "score": float(candidate.get("score", 0.0)),
        "frequency_hz": float(candidate.get("frequency_hz", 0.0)),
        "snr": float(candidate.get("snr", 0.0)),
        "status": "reviewed_no_follow_up_required",
        "reason": "candidate_did_not_enter_follow_up_pathway",
        "negative_evidence": [
            "No production follow-up pathway assigned by local pipeline routing."
        ],
        "detection_claimed": False,
        "external_submission_allowed": False,
    }


def _index_ids_by_candidate(
    *,
    follow_up_entries: list[dict[str, Any]],
    non_detection_entries: list[dict[str, Any]],
) -> dict[str, str]:
    indexes: dict[str, str] = {}
    for entry in follow_up_entries:
        indexes[str(entry.get("candidate_id", ""))] = str(entry.get("follow_up_id", ""))
    for entry in non_detection_entries:
        indexes[str(entry.get("candidate_id", ""))] = str(
            entry.get("non_detection_id", "")
        )
    return indexes


def _target_kind(
    target_name: str,
    target_kind: str,
    confidence: str,
    limitation: str,
) -> dict[str, str]:
    return {
        "descriptive_name": f"{target_name} ({target_kind})",
        "target_kind": target_kind,
        "target_kind_confidence": confidence,
        "target_kind_limitation": limitation,
    }


def _child_id(prefix: str, run_id: str, sequence: int) -> str:
    match = re.match(
        r"^RUN-(?P<stamp>\d{4}-\d{2}-\d{2}_\d{6}Z)-(?P<token>[A-Z0-9]{4})-",
        run_id,
    )
    if match:
        return f"{prefix}-{match.group('stamp')}-{match.group('token')}-{sequence:03d}"
    return f"{prefix}-{run_id}-{sequence:03d}"


def _random_token() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(4))


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
