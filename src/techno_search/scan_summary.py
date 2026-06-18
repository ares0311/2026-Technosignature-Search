"""Anomaly ranking report: rank candidates from multi-target scans by score."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCAN_SUMMARY_SCHEMA_VERSION = "scan_summary_v1"
SCAN_SUMMARY_DISCLAIMER = (
    "Scan summary rankings are local scheduling aids only. "
    "Ranking reflects pipeline score, not astrophysical significance. "
    "No ranked candidate constitutes a detection claim."
)

_FOLLOW_UP_PATHWAYS = {
    "follow_up_target",
    "human_review_queue",
    "candidate_review_packet",
}
_CANDIDATE_REVIEW_PATHWAYS = {"candidate_review_packet"}


def scan_summary(
    candidate_lists: list[dict[str, Any]],
    top_k: int = 10,
) -> dict[str, Any]:
    """Rank candidates by score and return a structured summary.

    Args:
        candidate_lists: Flat list of candidate dicts. Each dict should
            contain ``candidate_id``, ``score``, ``recommended_pathway``,
            ``target_name``, ``frequency_hz``, ``snr``,
            ``drift_rate_hz_per_sec``.
        top_k: Maximum number of top candidates to include.

    Returns:
        Summary dict with ranking information and counts.
    """
    candidates = candidate_lists  # alias for clarity

    # Sort descending by score
    sorted_cands = sorted(
        candidates,
        key=lambda c: float(c.get("score", 0.0)),
        reverse=True,
    )

    follow_up_count = sum(
        1
        for c in candidates
        if c.get("recommended_pathway") in _FOLLOW_UP_PATHWAYS
    )
    candidate_review_count = sum(
        1
        for c in candidates
        if c.get("recommended_pathway") in _CANDIDATE_REVIEW_PATHWAYS
    )

    unique_targets = {str(c.get("target_name", "")) for c in candidates}

    top_candidates = []
    for rank, cand in enumerate(sorted_cands[:top_k], start=1):
        top_candidates.append(
            {
                "rank": rank,
                "candidate_id": cand.get("candidate_id", ""),
                "target_name": cand.get("target_name", ""),
                "score": float(cand.get("score", 0.0)),
                "pathway": cand.get("recommended_pathway", "unknown"),
                "frequency_hz": float(cand.get("frequency_hz", 0.0)),
                "snr": float(cand.get("snr", 0.0)),
            }
        )

    return {
        "schema_version": SCAN_SUMMARY_SCHEMA_VERSION,
        "disclaimer": SCAN_SUMMARY_DISCLAIMER,
        "total_candidates": len(candidates),
        "follow_up_count": follow_up_count,
        "candidate_review_count": candidate_review_count,
        "top_candidates": top_candidates,
        "targets_scanned": len(unique_targets),
    }


def load_candidates_from_batch_dir(batch_dir: Path) -> list[dict[str, Any]]:
    """Load candidates from manifest JSON files in a results directory.

    Same loading logic as ``scan_summary_from_batch_dir`` but returns the
    flat candidate list rather than the ranked summary, so callers can
    group or filter before summarising.
    """
    batch_path = Path(batch_dir)
    manifest_files = sorted(batch_path.glob("**/*manifest.json"))

    candidates: list[dict[str, Any]] = []
    for mf in manifest_files:
        try:
            with mf.open(encoding="utf-8") as fh:
                manifest = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get("artifact_kind") == "production_run_manifest":
            continue

        stem = mf.stem
        if stem.endswith(".manifest"):
            target_name = stem[: -len(".manifest")]
        elif stem.endswith("_manifest"):
            target_name = stem[: -len("_manifest")]
        else:
            target_name = mf.parent.name or stem

        report_data: dict[str, Any] = {}
        json_path_str = manifest.get("json_path", "")
        if json_path_str:
            json_path = Path(json_path_str)
            if not json_path.is_absolute():
                json_path = mf.parent / json_path
            try:
                with json_path.open(encoding="utf-8") as fh:
                    report_data = json.load(fh)
            except (OSError, json.JSONDecodeError):
                pass
        if not report_data:
            companion = mf.parent / (target_name + ".json")
            try:
                with companion.open(encoding="utf-8") as fh:
                    report_data = json.load(fh)
            except (OSError, json.JSONDecodeError):
                pass

        merged = {**report_data, **manifest}
        scores_block = report_data.get("scores", {})
        score = float(
            scores_block.get(
                "followup_value",
                merged.get("score", merged.get("candidate_score", 0.0)),
            )
        )
        features = report_data.get("features", {})
        snr = float(features.get("snr", merged.get("snr", 0.0)))
        freq = float(features.get("frequency_hz", merged.get("frequency_hz", 0.0)))
        drift = float(
            features.get("drift_rate_hz_per_sec", merged.get("drift_rate_hz_per_sec", 0.0))
        )
        candidates.append(
            {
                "candidate_id": merged.get("candidate_id", target_name),
                "score": score,
                "recommended_pathway": merged.get("recommended_pathway", "unknown"),
                "target_name": target_name,
                "frequency_hz": freq,
                "snr": snr,
                "drift_rate_hz_per_sec": drift,
                "track": merged.get("track", "unknown"),
            }
        )

    return candidates


def scan_summary_from_batch_dir(batch_dir: Path) -> dict[str, Any]:
    """Build a scan summary from manifest JSON files in a results directory."""
    return scan_summary(load_candidates_from_batch_dir(batch_dir))
