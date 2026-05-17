"""ML model registry for version tracking and evaluation provenance."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ML_MODEL_REGISTRY_SCHEMA_VERSION = "ml_model_registry_v1"
ML_MODEL_REGISTRY_DISCLAIMER = (
    "Model registry entries are development provenance records only. "
    "No registered model constitutes a detection, discovery, or external validation. "
    "A model must exceed baseline pathway accuracy before operational use."
)
ALLOWED_MODEL_KINDS = frozenset({
    "cnn_radio",
    "transformer_radio",
    "hybrid_rule_learned",
    "self_supervised",
    "foundation_embedding",
    "baseline_rule_based",
})
ALLOWED_MODEL_STATUSES = frozenset({
    "experimental",
    "validated",
    "deprecated",
    "pending_review",
})


def _default_registry_path() -> Path:
    return Path(__file__).parent.parent.parent / "tests" / "fixtures" / "ml_model_registry.json"


@dataclass
class MLModelRegistryEntry:
    model_id: str
    model_kind: str
    version: str
    status: str
    training_data_version: str
    feature_schema_version: str
    baseline_accuracy: float
    model_accuracy: float
    is_above_baseline: bool
    registered_utc: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_kind": self.model_kind,
            "version": self.version,
            "status": self.status,
            "training_data_version": self.training_data_version,
            "feature_schema_version": self.feature_schema_version,
            "baseline_accuracy": self.baseline_accuracy,
            "model_accuracy": self.model_accuracy,
            "is_above_baseline": self.is_above_baseline,
            "registered_utc": self.registered_utc,
            "notes": self.notes,
        }


def load_model_registry_entries(
    fixture_path: Path | None = None,
) -> list[MLModelRegistryEntry]:
    path = fixture_path or _default_registry_path()
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = data.get("ml_model_registry", [])
    return [
        MLModelRegistryEntry(
            model_id=e["model_id"],
            model_kind=e["model_kind"],
            version=e["version"],
            status=e["status"],
            training_data_version=e["training_data_version"],
            feature_schema_version=e["feature_schema_version"],
            baseline_accuracy=float(e["baseline_accuracy"]),
            model_accuracy=float(e["model_accuracy"]),
            is_above_baseline=bool(e["is_above_baseline"]),
            registered_utc=e["registered_utc"],
            notes=e["notes"],
        )
        for e in entries
    ]


def model_registry_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_model_registry_entries(fixture_path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    above_baseline = 0
    below_baseline = 0
    validated_count = 0
    experimental_count = 0

    for e in entries:
        by_kind[e.model_kind] = by_kind.get(e.model_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.is_above_baseline:
            above_baseline += 1
        else:
            below_baseline += 1
        if e.status == "validated":
            validated_count += 1
        if e.status == "experimental":
            experimental_count += 1

    return {
        "schema_version": ML_MODEL_REGISTRY_SCHEMA_VERSION,
        "disclaimer": ML_MODEL_REGISTRY_DISCLAIMER,
        "registry_count": len(entries),
        "above_baseline_count": above_baseline,
        "below_baseline_count": below_baseline,
        "validated_count": validated_count,
        "experimental_count": experimental_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
