from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PIPELINE_TELEMETRY_SCHEMA_VERSION = "pipeline_telemetry_v1"

PIPELINE_TELEMETRY_DISCLAIMER = (
    "Pipeline telemetry entries are operational provenance records only. "
    "Latency and throughput data are local scheduling diagnostics and do not "
    "constitute survey performance metrics, detection sensitivity estimates, "
    "or evidence of a technosignature candidate. "
    "This record does not authorize external submission."
)

ALLOWED_TELEMETRY_STAGES = frozenset(
    {"scoring", "model_serving", "audit_log", "rescore", "handoff", "submission_check"}
)


def _default_telemetry_fixture_path() -> Path:
    return Path(__file__).parent.parent.parent / "tests" / "fixtures" / "pipeline_telemetry.json"


@dataclass
class PipelineTelemetryEntry:
    entry_id: str
    candidate_id: str
    stage: str
    latency_ms: float
    success: bool
    error_message: str | None
    recorded_utc: str
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "stage": self.stage,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error_message": self.error_message,
            "recorded_utc": self.recorded_utc,
            "notes": self.notes,
        }


def load_telemetry_entries(
    fixture_path: Path | str | None = None,
) -> list[PipelineTelemetryEntry]:
    path = Path(fixture_path) if fixture_path is not None else _default_telemetry_fixture_path()
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = []
    for entry in data.get("pipeline_telemetry_entries", []):
        entries.append(
            PipelineTelemetryEntry(
                entry_id=entry["entry_id"],
                candidate_id=entry["candidate_id"],
                stage=entry["stage"],
                latency_ms=float(entry["latency_ms"]),
                success=bool(entry["success"]),
                error_message=entry.get("error_message"),
                recorded_utc=entry["recorded_utc"],
                notes=entry.get("notes", ""),
            )
        )
    return entries


def pipeline_telemetry_summary(
    fixture_path: Path | str | None = None,
) -> dict[str, Any]:
    entries = load_telemetry_entries(fixture_path)
    by_stage: dict[str, int] = {}
    latencies: list[float] = []
    failure_count = 0
    for e in entries:
        by_stage[e.stage] = by_stage.get(e.stage, 0) + 1
        latencies.append(e.latency_ms)
        if not e.success:
            failure_count += 1
    mean_latency = sum(latencies) / len(latencies) if latencies else 0.0
    max_latency = max(latencies) if latencies else 0.0
    stages_covered = sorted(by_stage.keys())
    return {
        "disclaimer": PIPELINE_TELEMETRY_DISCLAIMER,
        "schema_version": PIPELINE_TELEMETRY_SCHEMA_VERSION,
        "entry_count": len(entries),
        "success_count": len(entries) - failure_count,
        "failure_count": failure_count,
        "by_stage": by_stage,
        "stages_covered": stages_covered,
        "mean_latency_ms": round(mean_latency, 3),
        "max_latency_ms": round(max_latency, 3),
    }
