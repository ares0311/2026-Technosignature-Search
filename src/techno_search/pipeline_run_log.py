"""Operational reproducibility records for top-level pipeline execution runs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PIPELINE_RUN_LOG_SCHEMA_VERSION = "pipeline_run_log_v1"

PIPELINE_RUN_LOG_DISCLAIMER = (
    "Pipeline run entries are operational reproducibility records. "
    "A pipeline run record does not modify candidate scores or pathway routing "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_RUN_KINDS = frozenset({
    "full_pipeline", "partial_rerun", "calibration_only", "test_run", "recovery_run",
})

ALLOWED_RUN_STATUSES = frozenset({
    "started", "completed", "failed", "aborted", "paused",
})


def _default_pipeline_run_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "pipeline_run_log.json"
    )


@dataclass
class PipelineRunEntry:
    entry_id: str
    run_id: str
    run_kind: str
    status: str
    started_by: str
    started_at: str
    completed_at: str | None = None
    candidate_count: int | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "run_id": self.run_id,
            "run_kind": self.run_kind,
            "status": self.status,
            "started_by": self.started_by,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "candidate_count": self.candidate_count,
            "notes": self.notes,
        }


def load_pipeline_run_entries(
    path: Path | None = None,
) -> list[PipelineRunEntry]:
    fpath = path or _default_pipeline_run_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("pipeline_run_entries", []):
        entries.append(PipelineRunEntry(
            entry_id=item["entry_id"],
            run_id=item["run_id"],
            run_kind=item["run_kind"],
            status=item["status"],
            started_by=item["started_by"],
            started_at=item["started_at"],
            completed_at=item.get("completed_at"),
            candidate_count=item.get("candidate_count"),
            notes=item.get("notes"),
        ))
    return entries


def pipeline_run_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_pipeline_run_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.run_kind] = by_kind.get(e.run_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": PIPELINE_RUN_LOG_SCHEMA_VERSION,
        "disclaimer": PIPELINE_RUN_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": by_status.get("completed", 0),
        "failed_count": by_status.get("failed", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
    }
