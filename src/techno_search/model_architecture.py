"""ML model architecture scaffold definitions — stubs only, no weights, not validated."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

MODEL_ARCHITECTURE_SCHEMA_VERSION = "model_architecture_v1"

MODEL_ARCHITECTURE_DISCLAIMER = (
    "Model architecture entries are scaffold definitions only. "
    "No weights are included, no models have been trained, and no architecture "
    "constitutes a detection, discovery, or external validation."
)

ALLOWED_ARCHITECTURE_KINDS = frozenset(
    {
        "cnn_radio",
        "transformer_radio",
        "hybrid_rule_learned",
        "self_supervised",
        "foundation_embedding",
    }
)

ALLOWED_ARCHITECTURE_STATUSES = frozenset({"stub", "prototype", "experimental"})


def _default_architecture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "model_architecture.json"
    )


@dataclass
class ModelArchitectureEntry:
    arch_id: str
    kind: str
    label: str
    track: str
    status: str
    weights_available: bool
    input_feature_schema_version: str
    layer_descriptor: str
    created_utc: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "arch_id": self.arch_id,
            "kind": self.kind,
            "label": self.label,
            "track": self.track,
            "status": self.status,
            "weights_available": self.weights_available,
            "input_feature_schema_version": self.input_feature_schema_version,
            "layer_descriptor": self.layer_descriptor,
            "created_utc": self.created_utc,
            "notes": self.notes,
        }


def load_architecture_entries(
    fixture_path: Path | None = None,
) -> list[ModelArchitectureEntry]:
    import json

    path = fixture_path or _default_architecture_path()
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    entries = []
    for item in raw.get("architectures", []):
        entries.append(
            ModelArchitectureEntry(
                arch_id=item["arch_id"],
                kind=item["kind"],
                label=item["label"],
                track=item["track"],
                status=item["status"],
                weights_available=bool(item["weights_available"]),
                input_feature_schema_version=item["input_feature_schema_version"],
                layer_descriptor=item["layer_descriptor"],
                created_utc=item["created_utc"],
                notes=item["notes"],
            )
        )
    return entries


def model_architecture_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_architecture_entries(fixture_path)

    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_track: dict[str, int] = {}
    weights_available_count = 0

    for e in entries:
        by_kind[e.kind] = by_kind.get(e.kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_track[e.track] = by_track.get(e.track, 0) + 1
        if e.weights_available:
            weights_available_count += 1

    return {
        "disclaimer": MODEL_ARCHITECTURE_DISCLAIMER,
        "schema_version": MODEL_ARCHITECTURE_SCHEMA_VERSION,
        "architecture_count": len(entries),
        "weights_available_count": weights_available_count,
        "by_kind": by_kind,
        "by_status": by_status,
        "by_track": by_track,
        "kinds_defined": sorted(by_kind),
    }
