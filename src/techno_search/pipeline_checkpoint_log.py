"""Operational reproducibility records for pipeline execution checkpoints."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PIPELINE_CHECKPOINT_LOG_SCHEMA_VERSION = "pipeline_checkpoint_log_v1"

PIPELINE_CHECKPOINT_LOG_DISCLAIMER = (
    "Pipeline checkpoint entries are operational reproducibility records. "
    "A restored checkpoint does not modify candidate scores or pathway routing "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_CHECKPOINT_KINDS = frozenset({
    "stage_start", "stage_complete", "recovery_point", "validation_gate", "end_of_run",
})

ALLOWED_CHECKPOINT_STATUSES = frozenset({
    "saved", "restored", "expired", "invalidated",
})


def _default_pipeline_checkpoint_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "pipeline_checkpoint_log.json"
    )


@dataclass
class PipelineCheckpointEntry:
    entry_id: str
    run_id: str
    checkpoint_kind: str
    status: str
    stage_name: str
    checkpointed_by: str
    checkpointed_at: str
    candidate_count: int | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "run_id": self.run_id,
            "checkpoint_kind": self.checkpoint_kind,
            "status": self.status,
            "stage_name": self.stage_name,
            "checkpointed_by": self.checkpointed_by,
            "checkpointed_at": self.checkpointed_at,
            "candidate_count": self.candidate_count,
            "notes": self.notes,
        }


def load_pipeline_checkpoint_entries(
    path: Path | None = None,
) -> list[PipelineCheckpointEntry]:
    fpath = path or _default_pipeline_checkpoint_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("pipeline_checkpoint_entries", []):
        entries.append(PipelineCheckpointEntry(
            entry_id=item["entry_id"],
            run_id=item["run_id"],
            checkpoint_kind=item["checkpoint_kind"],
            status=item["status"],
            stage_name=item["stage_name"],
            checkpointed_by=item["checkpointed_by"],
            checkpointed_at=item["checkpointed_at"],
            candidate_count=item.get("candidate_count"),
            notes=item.get("notes"),
        ))
    return entries


def pipeline_checkpoint_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_pipeline_checkpoint_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.checkpoint_kind] = by_kind.get(e.checkpoint_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": PIPELINE_CHECKPOINT_LOG_SCHEMA_VERSION,
        "disclaimer": PIPELINE_CHECKPOINT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "saved_count": by_status.get("saved", 0),
        "restored_count": by_status.get("restored", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
    }
