from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PIPELINE_CONFIG_SCHEMA_VERSION = "pipeline_config_v1"

PIPELINE_CONFIG_DISCLAIMER = (
    "Pipeline configuration records are local scheduling metadata only. "
    "They describe which scoring config, model serving record, and track configs "
    "are active in a given pipeline run. This record does not authorize external submission "
    "or constitute a detection claim."
)

ALLOWED_PIPELINE_STATUSES = frozenset({"active", "staging", "deprecated", "stub"})


def _default_pipeline_config_fixture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "pipeline_configs.json"
    )


@dataclass
class PipelineConfigRecord:
    config_id: str
    label: str
    scoring_config_version: str
    serving_id: str
    model_id: str
    inference_backend: str
    active_tracks: list[str]
    pipeline_status: str
    created_utc: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "config_id": self.config_id,
            "label": self.label,
            "scoring_config_version": self.scoring_config_version,
            "serving_id": self.serving_id,
            "model_id": self.model_id,
            "inference_backend": self.inference_backend,
            "active_tracks": self.active_tracks,
            "pipeline_status": self.pipeline_status,
            "created_utc": self.created_utc,
            "notes": self.notes,
        }


def load_pipeline_configs(
    fixture_path: Path | None = None,
) -> list[PipelineConfigRecord]:
    path = fixture_path or _default_pipeline_config_fixture_path()
    data = json.loads(Path(path).read_text())
    records = []
    for entry in data.get("pipeline_configs", []):
        records.append(
            PipelineConfigRecord(
                config_id=entry["config_id"],
                label=entry["label"],
                scoring_config_version=entry["scoring_config_version"],
                serving_id=entry["serving_id"],
                model_id=entry["model_id"],
                inference_backend=entry["inference_backend"],
                active_tracks=list(entry.get("active_tracks", [])),
                pipeline_status=entry["pipeline_status"],
                created_utc=entry["created_utc"],
                notes=entry.get("notes", ""),
            )
        )
    return records


def pipeline_config_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    records = load_pipeline_configs(fixture_path)
    by_status: dict[str, int] = {}
    by_backend: dict[str, int] = {}
    for r in records:
        by_status[r.pipeline_status] = by_status.get(r.pipeline_status, 0) + 1
        by_backend[r.inference_backend] = by_backend.get(r.inference_backend, 0) + 1
    active = [r for r in records if r.pipeline_status == "active"]
    return {
        "schema_version": PIPELINE_CONFIG_SCHEMA_VERSION,
        "disclaimer": PIPELINE_CONFIG_DISCLAIMER,
        "config_count": len(records),
        "active_count": len(active),
        "active_config_id": active[0].config_id if active else None,
        "active_model_id": active[0].model_id if active else None,
        "by_status": by_status,
        "by_backend": by_backend,
    }
