"""Operational reproducibility records for pipeline component version tracking."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PIPELINE_VERSION_LOG_SCHEMA_VERSION = "pipeline_version_log_v1"

PIPELINE_VERSION_LOG_DISCLAIMER = (
    "Pipeline version entries are operational reproducibility records — "
    "version tracking does not modify candidate scores or pathway routing, "
    "does not authorize external submission, "
    "and does not constitute a detection claim."
)

ALLOWED_PIPELINE_VERSION_KINDS = frozenset({
    "scoring_engine",
    "rfi_filter",
    "catalog_client",
    "feature_extractor",
    "baseline_model",
})

ALLOWED_PIPELINE_VERSION_STATUSES = frozenset({
    "active",
    "deprecated",
    "superseded",
    "testing",
})


def _default_pipeline_version_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "pipeline_version_log.json"
    )


@dataclass
class PipelineVersionEntry:
    entry_id: str
    run_id: str
    version_kind: str
    status: str
    version_string: str
    recorded_by: str
    recorded_at: str
    component_name: str | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "run_id": self.run_id,
            "version_kind": self.version_kind,
            "status": self.status,
            "version_string": self.version_string,
            "recorded_by": self.recorded_by,
            "recorded_at": self.recorded_at,
            "component_name": self.component_name,
            "notes": self.notes,
        }


def load_pipeline_version_entries(
    path: Path | None = None,
) -> list[PipelineVersionEntry]:
    fpath = path or _default_pipeline_version_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("entries", []):
        entries.append(PipelineVersionEntry(
            entry_id=item["entry_id"],
            run_id=item["run_id"],
            version_kind=item["version_kind"],
            status=item["status"],
            version_string=item["version_string"],
            recorded_by=item["recorded_by"],
            recorded_at=item["recorded_at"],
            component_name=item.get("component_name"),
            notes=item.get("notes"),
        ))
    return entries


def pipeline_version_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_pipeline_version_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.version_kind] = by_kind.get(e.version_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": PIPELINE_VERSION_LOG_SCHEMA_VERSION,
        "disclaimer": PIPELINE_VERSION_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "active_count": by_status.get("active", 0),
        "deprecated_count": by_status.get("deprecated", 0),
        "superseded_count": by_status.get("superseded", 0),
        "testing_count": by_status.get("testing", 0),
        "counts_by_kind": by_kind,
    }
