"""Model serving scaffold — versioned inference interface with provenance. No weights loaded."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

MODEL_SERVING_SCHEMA_VERSION = "model_serving_v1"

MODEL_SERVING_DISCLAIMER = (
    "Model serving records are scheduling provenance artifacts only. "
    "No live model weights are loaded, no inference is performed on real observation data, "
    "and no serving record constitutes a detection, discovery, or external validation."
)

ALLOWED_SERVING_STATUSES = frozenset({"active", "standby", "retired", "stub"})
ALLOWED_INFERENCE_BACKENDS = frozenset({"baseline_rule", "onnx_stub", "pytorch_stub", "none"})


def _default_serving_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "model_serving.json"
    )


@dataclass
class ModelServingRecord:
    serving_id: str
    model_id: str
    model_version: str
    inference_backend: str
    serving_status: str
    beats_baseline: bool
    inference_provenance_tag: str
    registered_utc: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "serving_id": self.serving_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "inference_backend": self.inference_backend,
            "serving_status": self.serving_status,
            "beats_baseline": self.beats_baseline,
            "inference_provenance_tag": self.inference_provenance_tag,
            "registered_utc": self.registered_utc,
            "notes": self.notes,
        }


def load_serving_records(
    fixture_path: Path | None = None,
) -> list[ModelServingRecord]:
    import json

    path = fixture_path or _default_serving_path()
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    records = []
    for item in raw.get("serving_records", []):
        records.append(
            ModelServingRecord(
                serving_id=item["serving_id"],
                model_id=item["model_id"],
                model_version=item["model_version"],
                inference_backend=item["inference_backend"],
                serving_status=item["serving_status"],
                beats_baseline=bool(item["beats_baseline"]),
                inference_provenance_tag=item["inference_provenance_tag"],
                registered_utc=item["registered_utc"],
                notes=item["notes"],
            )
        )
    return records


def model_serving_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    records = load_serving_records(fixture_path)

    by_status: dict[str, int] = {}
    by_backend: dict[str, int] = {}
    active_model_ids: list[str] = []
    stub_count = 0

    for r in records:
        by_status[r.serving_status] = by_status.get(r.serving_status, 0) + 1
        by_backend[r.inference_backend] = by_backend.get(r.inference_backend, 0) + 1
        if r.serving_status == "active":
            active_model_ids.append(r.model_id)
        if r.serving_status == "stub":
            stub_count += 1

    return {
        "disclaimer": MODEL_SERVING_DISCLAIMER,
        "schema_version": MODEL_SERVING_SCHEMA_VERSION,
        "record_count": len(records),
        "active_count": by_status.get("active", 0),
        "stub_count": stub_count,
        "by_status": by_status,
        "by_backend": by_backend,
        "active_model_ids": sorted(active_model_ids),
    }
