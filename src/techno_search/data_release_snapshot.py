"""Data release snapshot and cross-release comparison.

A data release snapshot captures the pathway assignments and score statistics
for a named pipeline run. Comparing two snapshots reveals which candidates
changed pathway between pipeline versions or calibration updates.

These records are reproducibility provenance artifacts only. Pathway changes
reported here are local scheduling observations — they do not constitute
detection claims, calibration approvals, or authorization for external
submission.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DATA_RELEASE_SNAPSHOT_SCHEMA_VERSION = "data_release_snapshot_v1"

DATA_RELEASE_SNAPSHOT_DISCLAIMER = (
    "Data release snapshots are local reproducibility provenance records. "
    "Pathway changes detected across releases are scheduling observations "
    "only. They do not constitute detection claims, calibration approvals, "
    "scientific verdicts, or authorization for external submission."
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_snapshot_path() -> Path:
    return _project_root() / "tests" / "fixtures" / "data_release_snapshots.json"


def load_data_release_snapshots(
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Load the list of data release snapshots from the fixture file."""
    snapshot_path = path if path is not None else _default_snapshot_path()
    raw = json.loads(snapshot_path.read_text(encoding="utf-8"))
    return list(raw.get("snapshots", []))


def snapshot_from_batch_manifest(
    manifest_path: Path | str,
    *,
    snapshot_id: str,
    data_release_label: str,
) -> dict[str, Any]:
    """Build a data release snapshot dict from a batch_manifest.json file.

    The snapshot captures pathway assignments and a deterministic hash of
    those assignments. It does not read per-candidate score details.
    """
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    reports = manifest.get("reports", [])
    per_candidate: list[dict[str, str]] = []
    pathway_counts: dict[str, int] = {}
    track_counts: dict[str, int] = {}

    for report in reports:
        cid = str(report.get("candidate_id", ""))
        track = str(report.get("track", ""))
        pathway = str(report.get("recommended_pathway", ""))
        per_candidate.append(
            {"candidate_id": cid, "track": track, "recommended_pathway": pathway}
        )
        pathway_counts[pathway] = pathway_counts.get(pathway, 0) + 1
        track_counts[track] = track_counts.get(track, 0) + 1

    assignment_hash = _pathway_assignment_hash(per_candidate)

    return {
        "schema_version": DATA_RELEASE_SNAPSHOT_SCHEMA_VERSION,
        "disclaimer": DATA_RELEASE_SNAPSHOT_DISCLAIMER,
        "snapshot_id": snapshot_id,
        "data_release_label": data_release_label,
        "pipeline_version": str(manifest.get("config_version", "")),
        "created_at_utc": str(manifest.get("generated_at_utc", "")),
        "candidate_count": len(per_candidate),
        "pathway_distribution": pathway_counts,
        "track_distribution": track_counts,
        "pathway_assignment_hash": assignment_hash,
        "per_candidate": per_candidate,
    }


def compare_snapshots(
    snapshot_a: dict[str, Any],
    snapshot_b: dict[str, Any],
) -> dict[str, Any]:
    """Compare two data release snapshots and report pathway changes.

    Returns a comparison record. ``ok=True`` means no pathway changes were
    detected. Pathway changes are reproducibility observations only — not
    scientific verdicts.
    """
    cand_a = {e["candidate_id"]: e for e in snapshot_a.get("per_candidate", [])}
    cand_b = {e["candidate_id"]: e for e in snapshot_b.get("per_candidate", [])}

    all_ids = sorted(set(cand_a) | set(cand_b))
    pathway_changes: list[dict[str, str]] = []
    new_candidates: list[str] = []
    removed_candidates: list[str] = []

    for cid in all_ids:
        if cid not in cand_a:
            new_candidates.append(cid)
        elif cid not in cand_b:
            removed_candidates.append(cid)
        else:
            pa = cand_a[cid]["recommended_pathway"]
            pb = cand_b[cid]["recommended_pathway"]
            if pa != pb:
                pathway_changes.append(
                    {
                        "candidate_id": cid,
                        "from_pathway": pa,
                        "to_pathway": pb,
                        "track": cand_b[cid].get("track", cand_a[cid].get("track", "")),
                    }
                )

    dist_a = snapshot_a.get("pathway_distribution", {})
    dist_b = snapshot_b.get("pathway_distribution", {})
    all_pathways = sorted(set(dist_a) | set(dist_b))
    pathway_delta = {
        p: {
            "snapshot_a_count": int(dist_a.get(p, 0)),
            "snapshot_b_count": int(dist_b.get(p, 0)),
            "delta": int(dist_b.get(p, 0)) - int(dist_a.get(p, 0)),
        }
        for p in all_pathways
    }

    same_hash = (
        snapshot_a.get("pathway_assignment_hash")
        == snapshot_b.get("pathway_assignment_hash")
    )

    return {
        "schema_version": DATA_RELEASE_SNAPSHOT_SCHEMA_VERSION,
        "disclaimer": DATA_RELEASE_SNAPSHOT_DISCLAIMER,
        "snapshot_a_id": str(snapshot_a.get("snapshot_id", "")),
        "snapshot_b_id": str(snapshot_b.get("snapshot_id", "")),
        "snapshot_a_pipeline_version": str(snapshot_a.get("pipeline_version", "")),
        "snapshot_b_pipeline_version": str(snapshot_b.get("pipeline_version", "")),
        "ok": not pathway_changes and not new_candidates and not removed_candidates,
        "pathway_change_count": len(pathway_changes),
        "new_candidate_count": len(new_candidates),
        "removed_candidate_count": len(removed_candidates),
        "same_pathway_assignment_hash": same_hash,
        "pathway_changes": pathway_changes,
        "new_candidates": new_candidates,
        "removed_candidates": removed_candidates,
        "pathway_distribution_delta": pathway_delta,
    }


def data_release_snapshot_summary(
    path: Path | None = None,
) -> dict[str, Any]:
    """Summarize the data release snapshot fixture file."""
    snapshots = load_data_release_snapshots(path)

    snapshot_ids = [s.get("snapshot_id", "") for s in snapshots]
    pipeline_versions = sorted({s.get("pipeline_version", "") for s in snapshots})
    total_candidates = sum(int(s.get("candidate_count", 0)) for s in snapshots)

    comparisons: list[dict[str, Any]] = []
    for i in range(1, len(snapshots)):
        comparisons.append(compare_snapshots(snapshots[i - 1], snapshots[i]))

    total_pathway_changes = sum(
        int(c.get("pathway_change_count", 0)) for c in comparisons
    )
    all_reproduced = all(c.get("ok", False) for c in comparisons) if comparisons else True

    return {
        "schema_version": DATA_RELEASE_SNAPSHOT_SCHEMA_VERSION,
        "disclaimer": DATA_RELEASE_SNAPSHOT_DISCLAIMER,
        "snapshot_count": len(snapshots),
        "snapshot_ids": snapshot_ids,
        "pipeline_versions_seen": pipeline_versions,
        "total_candidates_across_snapshots": total_candidates,
        "cross_release_comparison_count": len(comparisons),
        "total_pathway_changes_detected": total_pathway_changes,
        "all_releases_reproduced": all_reproduced,
        "comparisons": comparisons,
    }


def _pathway_assignment_hash(per_candidate: list[dict[str, str]]) -> str:
    """Compute a deterministic SHA-256 hash of sorted pathway assignments."""
    sorted_entries = sorted(
        per_candidate, key=lambda e: e.get("candidate_id", "")
    )
    payload = json.dumps(
        [
            {"candidate_id": e["candidate_id"], "recommended_pathway": e["recommended_pathway"]}
            for e in sorted_entries
        ],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()
