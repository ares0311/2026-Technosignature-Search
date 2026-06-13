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


def scan_summary_from_batch_dir(batch_dir: Path) -> dict[str, Any]:
    """Build a scan summary from manifest JSON files in a batch directory.

    Reads all ``*manifest.json`` files directly under ``batch_dir`` (not
    recursively). Each manifest contributes one candidate entry. The
    target_name is derived from the manifest filename stem (stripping a
    trailing ``_manifest`` suffix if present).

    Args:
        batch_dir: Directory containing ``*manifest.json`` files.

    Returns:
        Result of ``scan_summary()`` over the extracted candidate list.
    """
    batch_path = Path(batch_dir)
    manifest_files = sorted(batch_path.glob("*manifest.json"))

    candidates: list[dict[str, Any]] = []
    for mf in manifest_files:
        try:
            with mf.open(encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue

        stem = mf.stem
        target_name = stem[: -len("_manifest")] if stem.endswith("_manifest") else stem

        score = float(
            data.get("candidate_score", data.get("score", 0.0))
        )
        candidates.append(
            {
                "candidate_id": data.get("candidate_id", stem),
                "score": score,
                "recommended_pathway": data.get(
                    "recommended_pathway", "unknown"
                ),
                "target_name": target_name,
                "frequency_hz": float(data.get("frequency_hz", 0.0)),
                "snr": float(data.get("snr", 0.0)),
                "drift_rate_hz_per_sec": float(
                    data.get("drift_rate_hz_per_sec", 0.0)
                ),
                "track": data.get("track", "unknown"),
            }
        )

    return scan_summary(candidates)
