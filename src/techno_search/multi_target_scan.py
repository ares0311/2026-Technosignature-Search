"""Multi-target scan orchestrator for technosignature search.

Coordinates pipeline runs across multiple target directories, aggregates
results, and returns a structured summary. Results are local scheduling
aids only — no result constitutes a detection claim.
"""

from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Conservative I/O-bound default per LOCAL_SYSTEM_PROFILE.md (M4 Max, 16 cores).
# Pipeline scoring is I/O + light CPU, so 6 workers leave headroom for the OS.
# Pass workers=12 for CPU-heavy runs or workers=1 to force sequential execution.
_DEFAULT_WORKERS = 6

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


def _run_one_target(
    target_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Pipeline run for a single target directory; returns a target_result dict."""
    from techno_search.pipeline_runner import run_pipeline

    target_name = target_dir.name
    dat_files = list(target_dir.glob("*.dat"))
    if not dat_files:
        dat_files = list(target_dir.glob("*.csv"))

    if not dat_files:
        return {
            "target_name": target_name,
            "candidate_count": 0,
            "top_pathway": "unknown",
            "ok": False,
            "error_msg": f"No .dat or .csv hit-table file found in {target_dir}",
        }

    dat_file = dat_files[0]
    per_target_output = output_dir / target_name
    per_target_output.mkdir(parents=True, exist_ok=True)

    result = run_pipeline(dat_file, track="radio", output_dir=per_target_output)

    if result.ok:
        return {
            "target_name": target_name,
            "candidate_count": max(result.row_count, 1),
            "top_pathway": result.pathway,
            "ok": True,
            "error_msg": None,
        }
    return {
        "target_name": target_name,
        "candidate_count": 0,
        "top_pathway": "unknown",
        "ok": False,
        "error_msg": result.error or "Pipeline run failed",
    }


def run_multi_target_scan(
    target_dirs: list[Path],
    output_dir: Path,
    workers: int | None = None,
) -> MultiTargetScanResult:
    """Run the pipeline across multiple target directories.

    Each target directory is expected to contain a turboSETI ``.dat`` file.
    Runs ``run_pipeline()`` for each target in parallel using a thread pool
    (I/O-bound work; threads are safe here — no subprocess or heavy CPU per worker).

    ``workers`` controls the thread-pool size.  Defaults to 6 (conservative I/O
    default for M4 Max per LOCAL_SYSTEM_PROFILE.md).  Pass workers=1 to force
    sequential execution.

    This is a provenance and scheduling aid only — results do not constitute
    detection claims or authorize external submission.
    """
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

    n_workers = workers if workers is not None else _DEFAULT_WORKERS
    n_workers = max(1, min(n_workers, len(target_dirs)))

    _follow_up_pathways = {
        "human_review_queue",
        "candidate_review_packet",
        "external_followup_candidate",
    }
    _candidate_review_pathways = {"candidate_review_packet"}

    # Preserve submission order by keying futures back to their index.
    ordered: dict[int, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        futures = {
            pool.submit(_run_one_target, td, output_dir): i
            for i, td in enumerate(target_dirs)
        }
        for fut in as_completed(futures):
            idx = futures[fut]
            ordered[idx] = fut.result()

    target_results = [ordered[i] for i in range(len(target_dirs))]

    succeeded = sum(1 for t in target_results if t["ok"])
    failed = sum(1 for t in target_results if not t["ok"])
    total_candidates = sum(int(t["candidate_count"]) for t in target_results)
    follow_up_count = sum(
        1 for t in target_results
        if t["ok"] and t["top_pathway"] in _follow_up_pathways
    )
    candidate_review_count = sum(
        1 for t in target_results
        if t["ok"] and t["top_pathway"] in _candidate_review_pathways
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
