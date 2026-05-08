"""Validation dataset manifest helpers."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.schemas import Pathway, Track

VALIDATION_DATASET_SCHEMA_VERSION = "validation_dataset_manifest_v1"
VALIDATION_DATASET_DISCLAIMER = (
    "Validation dataset manifests describe dataset coverage and readiness only; "
    "they are not calibrated survey performance claims."
)


@dataclass(frozen=True)
class ValidationDatasetEntry:
    """One validation dataset manifest entry."""

    dataset_id: str
    track: Track
    dataset_kind: str
    readiness: str
    source_fixture_path: str
    case_count: int
    false_positive_classes: tuple[str, ...]
    expected_pathways: tuple[Pathway, ...]


def default_validation_dataset_manifest_path() -> Path:
    """Return the repository-local validation dataset manifest fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "validation_dataset_manifest.json"
    )


def load_validation_dataset_entries(
    path: Path | None = None,
) -> tuple[ValidationDatasetEntry, ...]:
    """Load validation dataset manifest entries."""

    manifest_path = path or default_validation_dataset_manifest_path()
    with manifest_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != VALIDATION_DATASET_SCHEMA_VERSION:
        msg = (
            f"Unsupported validation dataset schema version {schema_version!r}; "
            f"expected {VALIDATION_DATASET_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(_entry_from_mapping(entry) for entry in data["datasets"])


def validation_dataset_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize validation dataset manifest coverage."""

    manifest_path = path or default_validation_dataset_manifest_path()
    entries = load_validation_dataset_entries(manifest_path)
    class_values = {
        false_positive_class
        for entry in entries
        for false_positive_class in entry.false_positive_classes
    }
    pathway_values = {
        pathway.value for entry in entries for pathway in entry.expected_pathways
    }

    return {
        "manifest_path": str(manifest_path),
        "schema_version": VALIDATION_DATASET_SCHEMA_VERSION,
        "disclaimer": VALIDATION_DATASET_DISCLAIMER,
        "dataset_count": len(entries),
        "total_case_count": sum(entry.case_count for entry in entries),
        "false_positive_class_count": len(class_values),
        "expected_pathway_count": len(pathway_values),
        "by_track": _counter_to_dict(Counter(entry.track.value for entry in entries)),
        "by_dataset_kind": _counter_to_dict(Counter(entry.dataset_kind for entry in entries)),
        "by_readiness": _counter_to_dict(Counter(entry.readiness for entry in entries)),
        "dataset_ids": sorted(entry.dataset_id for entry in entries),
        "source_fixture_paths": sorted(entry.source_fixture_path for entry in entries),
    }


def _entry_from_mapping(data: dict[str, Any]) -> ValidationDatasetEntry:
    return ValidationDatasetEntry(
        dataset_id=str(data["dataset_id"]),
        track=Track(str(data["track"])),
        dataset_kind=str(data["dataset_kind"]),
        readiness=str(data["readiness"]),
        source_fixture_path=str(data["source_fixture_path"]),
        case_count=int(data["case_count"]),
        false_positive_classes=tuple(
            str(false_positive_class)
            for false_positive_class in data.get("false_positive_classes", ())
        ),
        expected_pathways=tuple(
            Pathway(str(pathway)) for pathway in data.get("expected_pathways", ())
        ),
    )


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
