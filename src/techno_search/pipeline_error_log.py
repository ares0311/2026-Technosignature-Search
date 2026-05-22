from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PIPELINE_ERROR_SCHEMA_VERSION = "pipeline_error_log_v1"

PIPELINE_ERROR_DISCLAIMER = (
    "Pipeline error log entries are operational provenance records only. "
    "A pipeline error entry records that a scoring, data, configuration, or "
    "validation error occurred during pipeline execution. Error records are "
    "operational scheduling aids and do not modify candidate scores, do not "
    "affect pathway routing, do not authorize external submission, and do not "
    "constitute a detection claim."
)

ALLOWED_ERROR_KINDS = frozenset({
    "scoring_failure", "data_missing", "config_mismatch",
    "timeout", "validation_error",
})

ALLOWED_ERROR_SEVERITIES = frozenset({
    "warning", "error", "critical",
})


def _default_pipeline_error_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests" / "fixtures" / "pipeline_error_log.json"
    )


@dataclass
class PipelineErrorEntry:
    error_id: str
    error_kind: str
    severity: str
    resolved: bool
    reported_by: str
    reported_utc: str
    pipeline_stage: str
    resolved_utc: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "error_id": self.error_id,
            "error_kind": self.error_kind,
            "severity": self.severity,
            "resolved": self.resolved,
            "reported_by": self.reported_by,
            "reported_utc": self.reported_utc,
            "pipeline_stage": self.pipeline_stage,
            "resolved_utc": self.resolved_utc,
            "notes": self.notes,
        }


def load_error_entries(fixture_path: Path | None = None) -> list[PipelineErrorEntry]:
    path = fixture_path or _default_pipeline_error_path()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = []
    for raw in data.get("pipeline_error_entries", []):
        entries.append(PipelineErrorEntry(
            error_id=raw["error_id"],
            error_kind=raw["error_kind"],
            severity=raw["severity"],
            resolved=raw["resolved"],
            reported_by=raw["reported_by"],
            reported_utc=raw["reported_utc"],
            pipeline_stage=raw["pipeline_stage"],
            resolved_utc=raw.get("resolved_utc"),
            notes=raw.get("notes", ""),
        ))
    return entries


def pipeline_error_summary(fixture_path: Path | None = None) -> dict[str, Any]:
    entries = load_error_entries(fixture_path)
    by_severity: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for e in entries:
        by_severity[e.severity] = by_severity.get(e.severity, 0) + 1
        by_kind[e.error_kind] = by_kind.get(e.error_kind, 0) + 1
    unresolved_count = sum(1 for e in entries if not e.resolved)
    return {
        "schema_version": PIPELINE_ERROR_SCHEMA_VERSION,
        "disclaimer": PIPELINE_ERROR_DISCLAIMER,
        "entry_count": len(entries),
        "unresolved_count": unresolved_count,
        "resolved_count": sum(1 for e in entries if e.resolved),
        "critical_count": by_severity.get("critical", 0),
        "by_severity": by_severity,
        "by_kind": by_kind,
    }
