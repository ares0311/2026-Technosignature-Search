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
VALIDATION_PROMOTION_SCHEMA_VERSION = "validation_dataset_promotion_rules_v1"
VALIDATION_PROMOTION_DISCLAIMER = (
    "Validation dataset promotion rules describe readiness requirements only; they "
    "do not certify discoveries or calibrated survey performance."
)
VALIDATION_READINESS_SCHEMA_VERSION = "validation_readiness_v1"
VALIDATION_READINESS_DISCLAIMER = (
    "Validation readiness records describe whether datasets are ready for curated "
    "review only; they do not certify discoveries, detections, or calibrated "
    "survey performance."
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


@dataclass(frozen=True)
class ValidationPromotionRule:
    """One rule for promoting a validation dataset to a stronger readiness tier."""

    rule_id: str
    from_readiness: str
    to_readiness: str
    required_evidence: tuple[str, ...]
    blocking_conditions: tuple[str, ...]
    minimum_case_count: int
    requires_external_review: bool


@dataclass(frozen=True)
class ValidationReadinessRecord:
    """One readiness review record for a future curated validation dataset."""

    readiness_id: str
    dataset_id: str
    track: Track
    dataset_kind: str
    readiness_status: str
    current_case_count: int
    minimum_case_count: int
    evidence_requirements: tuple[str, ...]
    satisfied_evidence: tuple[str, ...]
    blocking_issues: tuple[str, ...]
    requires_external_review: bool
    promotion_target: str


def default_validation_dataset_manifest_path() -> Path:
    """Return the repository-local validation dataset manifest fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "validation_dataset_manifest.json"
    )


def default_validation_promotion_rules_path() -> Path:
    """Return the repository-local validation promotion rules fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "validation_promotion_rules.json"
    )


def default_validation_readiness_path() -> Path:
    """Return the repository-local validation readiness fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "validation_readiness.json"
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


def load_validation_promotion_rules(
    path: Path | None = None,
) -> tuple[ValidationPromotionRule, ...]:
    """Load validation dataset promotion rules."""

    rules_path = path or default_validation_promotion_rules_path()
    with rules_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != VALIDATION_PROMOTION_SCHEMA_VERSION:
        msg = (
            f"Unsupported validation promotion schema version {schema_version!r}; "
            f"expected {VALIDATION_PROMOTION_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(_promotion_rule_from_mapping(rule) for rule in data["rules"])


def load_validation_readiness_records(
    path: Path | None = None,
) -> tuple[ValidationReadinessRecord, ...]:
    """Load validation dataset readiness review records."""

    readiness_path = path or default_validation_readiness_path()
    with readiness_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != VALIDATION_READINESS_SCHEMA_VERSION:
        msg = (
            f"Unsupported validation readiness schema version {schema_version!r}; "
            f"expected {VALIDATION_READINESS_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(_readiness_record_from_mapping(record) for record in data["records"])


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


def validation_readiness_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize validation dataset readiness review coverage."""

    readiness_path = path or default_validation_readiness_path()
    records = load_validation_readiness_records(readiness_path)
    all_evidence_requirements = {
        evidence
        for record in records
        for evidence in record.evidence_requirements
    }
    all_blocking_issues = {
        issue for record in records for issue in record.blocking_issues
    }
    ready_dataset_ids = [
        record.dataset_id
        for record in records
        if record.readiness_status == "ready"
    ]

    return {
        "readiness_path": str(readiness_path),
        "schema_version": VALIDATION_READINESS_SCHEMA_VERSION,
        "disclaimer": VALIDATION_READINESS_DISCLAIMER,
        "record_count": len(records),
        "ready_count": sum(
            1 for record in records if record.readiness_status == "ready"
        ),
        "blocked_count": sum(
            1 for record in records if record.readiness_status == "blocked"
        ),
        "not_yet_admissible_count": sum(
            1
            for record in records
            if record.readiness_status == "not_yet_admissible"
        ),
        "evidence_requirement_count": len(all_evidence_requirements),
        "satisfied_evidence_count": sum(
            len(record.satisfied_evidence) for record in records
        ),
        "blocking_issue_count": len(all_blocking_issues),
        "records_requiring_external_review": sum(
            1 for record in records if record.requires_external_review
        ),
        "minimum_case_count_floor": min(
            (record.minimum_case_count for record in records), default=0
        ),
        "total_current_case_count": sum(record.current_case_count for record in records),
        "by_track": _counter_to_dict(Counter(record.track.value for record in records)),
        "by_status": _counter_to_dict(Counter(record.readiness_status for record in records)),
        "by_dataset_kind": _counter_to_dict(Counter(record.dataset_kind for record in records)),
        "ready_dataset_ids": sorted(ready_dataset_ids),
        "record_ids": sorted(record.readiness_id for record in records),
    }


def validation_promotion_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize validation dataset promotion rule coverage."""

    rules_path = path or default_validation_promotion_rules_path()
    rules = load_validation_promotion_rules(rules_path)
    required_evidence_count = sum(len(rule.required_evidence) for rule in rules)
    blocking_values = {
        condition for rule in rules for condition in rule.blocking_conditions
    }

    return {
        "rules_path": str(rules_path),
        "schema_version": VALIDATION_PROMOTION_SCHEMA_VERSION,
        "disclaimer": VALIDATION_PROMOTION_DISCLAIMER,
        "rule_count": len(rules),
        "required_evidence_count": required_evidence_count,
        "blocking_condition_count": len(blocking_values),
        "minimum_case_count_floor": min(
            (rule.minimum_case_count for rule in rules), default=0
        ),
        "rules_requiring_external_review": sum(
            1 for rule in rules if rule.requires_external_review
        ),
        "by_from_readiness": _counter_to_dict(Counter(rule.from_readiness for rule in rules)),
        "by_to_readiness": _counter_to_dict(Counter(rule.to_readiness for rule in rules)),
        "rule_ids": sorted(rule.rule_id for rule in rules),
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


def _promotion_rule_from_mapping(data: dict[str, Any]) -> ValidationPromotionRule:
    return ValidationPromotionRule(
        rule_id=str(data["rule_id"]),
        from_readiness=str(data["from_readiness"]),
        to_readiness=str(data["to_readiness"]),
        required_evidence=tuple(str(item) for item in data.get("required_evidence", ())),
        blocking_conditions=tuple(
            str(item) for item in data.get("blocking_conditions", ())
        ),
        minimum_case_count=int(data["minimum_case_count"]),
        requires_external_review=bool(data["requires_external_review"]),
    )


def _readiness_record_from_mapping(data: dict[str, Any]) -> ValidationReadinessRecord:
    return ValidationReadinessRecord(
        readiness_id=str(data["readiness_id"]),
        dataset_id=str(data["dataset_id"]),
        track=Track(str(data["track"])),
        dataset_kind=str(data["dataset_kind"]),
        readiness_status=str(data["readiness_status"]),
        current_case_count=int(data["current_case_count"]),
        minimum_case_count=int(data["minimum_case_count"]),
        evidence_requirements=tuple(
            str(item) for item in data.get("evidence_requirements", ())
        ),
        satisfied_evidence=tuple(
            str(item) for item in data.get("satisfied_evidence", ())
        ),
        blocking_issues=tuple(
            str(item) for item in data.get("blocking_issues", ())
        ),
        requires_external_review=bool(data["requires_external_review"]),
        promotion_target=str(data["promotion_target"]),
    )


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
