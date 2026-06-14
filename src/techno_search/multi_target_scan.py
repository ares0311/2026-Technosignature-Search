"""Multi-target scan orchestrator for technosignature search.

Coordinates pipeline runs across multiple target directories, aggregates
results, and returns a structured summary. Results are local scheduling
aids only — no result constitutes a detection claim.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MULTI_TARGET_SCAN_SCHEMA_VERSION = "multi_target_scan_v1"
MULTI_TARGET_SCAN_DISCLAIMER = (
    "Multi-target scan results are local scheduling aids only. "
    "No result constitutes a detection claim or authorizes external submission."
)
NEGATIVE_RESULT_SUMMARY_SCHEMA_VERSION = "negative_result_summary_v1"
NEGATIVE_RESULT_SUMMARY_DISCLAIMER = (
    "Negative result summaries are operator scheduling aids only. "
    "A negative result does not constitute evidence of absence of technosignatures "
    "and does not authorize external submission or imply scientific confirmation. "
    "This scan session found no candidates passing the escalation gate."
)


@dataclass
class MultiTargetScanResult:
    """Aggregate result of a multi-target pipeline scan."""

    targets_attempted: int
    targets_succeeded: int
    targets_failed: int
    total_candidates: int
    follow_up_count: int
    candidate_review_count: int
    target_results: list[dict[str, Any]]
    scan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = MULTI_TARGET_SCAN_SCHEMA_VERSION
    disclaimer: str = MULTI_TARGET_SCAN_DISCLAIMER

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "disclaimer": self.disclaimer,
            "scan_id": self.scan_id,
            "targets_attempted": self.targets_attempted,
            "targets_succeeded": self.targets_succeeded,
            "targets_failed": self.targets_failed,
            "total_candidates": self.total_candidates,
            "follow_up_count": self.follow_up_count,
            "candidate_review_count": self.candidate_review_count,
            "target_results": self.target_results,
        }


def run_multi_target_scan(
    target_dirs: list[Path],
    output_dir: Path,
    workers: int | None = None,
) -> MultiTargetScanResult:
    """Run the pipeline across multiple target directories.

    Each target directory is expected to contain a turboSETI ``.dat`` file.
    Runs ``run_pipeline()`` for each target and aggregates results.

    This is a provenance and scheduling aid only — results do not constitute
    detection claims or authorize external submission.
    """
    from techno_search.pipeline_runner import run_pipeline

    output_dir.mkdir(parents=True, exist_ok=True)

    if not target_dirs:
        return MultiTargetScanResult(
            targets_attempted=0,
            targets_succeeded=0,
            targets_failed=0,
            total_candidates=0,
            follow_up_count=0,
            candidate_review_count=0,
            target_results=[],
        )

    target_results: list[dict[str, Any]] = []
    succeeded = 0
    failed = 0
    total_candidates = 0
    follow_up_count = 0
    candidate_review_count = 0

    _follow_up_pathways = {
        "human_review_queue",
        "candidate_review_packet",
        "external_followup_candidate",
    }
    _candidate_review_pathways = {"candidate_review_packet"}

    for target_dir in target_dirs:
        target_name = target_dir.name
        dat_files = list(target_dir.glob("*.dat"))
        if not dat_files:
            # Also try CSV files used as hit tables
            dat_files = list(target_dir.glob("*.csv"))

        if not dat_files:
            target_results.append(
                {
                    "target_name": target_name,
                    "candidate_count": 0,
                    "top_pathway": "unknown",
                    "ok": False,
                    "error_msg": f"No .dat or .csv hit-table file found in {target_dir}",
                }
            )
            failed += 1
            continue

        dat_file = dat_files[0]
        per_target_output = output_dir / target_name
        per_target_output.mkdir(parents=True, exist_ok=True)

        result = run_pipeline(dat_file, track="radio", output_dir=per_target_output)

        if result.ok:
            succeeded += 1
            total_candidates += max(result.row_count, 1)
            pathway = result.pathway
            if pathway in _follow_up_pathways:
                follow_up_count += 1
            if pathway in _candidate_review_pathways:
                candidate_review_count += 1
            target_results.append(
                {
                    "target_name": target_name,
                    "candidate_count": max(result.row_count, 1),
                    "top_pathway": pathway,
                    "ok": True,
                    "error_msg": None,
                }
            )
        else:
            failed += 1
            target_results.append(
                {
                    "target_name": target_name,
                    "candidate_count": 0,
                    "top_pathway": "unknown",
                    "ok": False,
                    "error_msg": result.error or "Pipeline run failed",
                }
            )

    return MultiTargetScanResult(
        targets_attempted=len(target_dirs),
        targets_succeeded=succeeded,
        targets_failed=failed,
        total_candidates=total_candidates,
        follow_up_count=follow_up_count,
        candidate_review_count=candidate_review_count,
        target_results=target_results,
    )


def multi_target_scan_summary(scan_manifest_path: Path) -> dict[str, Any]:
    """Load a JSON scan manifest and return a summary dict.

    The manifest must have a ``target_results`` list field.
    Returns a summary with counts and disclaimer.
    """
    if not scan_manifest_path.exists():
        return {
            "ok": False,
            "error": f"Scan manifest not found: {scan_manifest_path}",
            "schema_version": MULTI_TARGET_SCAN_SCHEMA_VERSION,
            "disclaimer": MULTI_TARGET_SCAN_DISCLAIMER,
        }

    with scan_manifest_path.open(encoding="utf-8") as fh:
        data = json.load(fh)

    target_results: list[dict[str, Any]] = data.get("target_results", [])
    succeeded = sum(1 for t in target_results if t.get("ok"))
    failed = sum(1 for t in target_results if not t.get("ok"))
    total_candidates = sum(int(t.get("candidate_count", 0)) for t in target_results)

    _follow_up_pathways = {
        "human_review_queue",
        "candidate_review_packet",
        "external_followup_candidate",
    }
    _candidate_review_pathways = {"candidate_review_packet"}

    follow_up_count = sum(
        1
        for t in target_results
        if t.get("ok") and t.get("top_pathway") in _follow_up_pathways
    )
    candidate_review_count = sum(
        1
        for t in target_results
        if t.get("ok") and t.get("top_pathway") in _candidate_review_pathways
    )

    return {
        "schema_version": MULTI_TARGET_SCAN_SCHEMA_VERSION,
        "disclaimer": MULTI_TARGET_SCAN_DISCLAIMER,
        "targets_attempted": len(target_results),
        "targets_succeeded": succeeded,
        "targets_failed": failed,
        "total_candidates": total_candidates,
        "follow_up_count": follow_up_count,
        "candidate_review_count": candidate_review_count,
        "ok": True,
    }
