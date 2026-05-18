"""Curated dataset intake checklist — conservative placeholder, no real data ingested."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

CURATED_DATASET_INTAKE_SCHEMA_VERSION = "curated_dataset_intake_v1"

CURATED_DATASET_INTAKE_DISCLAIMER = (
    "Curated dataset intake records are planning placeholders only. "
    "No real observation data has been ingested, no catalog has been queried, "
    "and no intake record constitutes a detection, discovery, or external validation. "
    "All entries describe future intake requirements under conservative review gates."
)

ALLOWED_INTAKE_STATUSES = frozenset(
    {"planning", "pending_review", "approved", "blocked", "deferred"}
)
ALLOWED_DATA_KINDS = frozenset(
    {"radio_survey", "infrared_survey", "archival_catalog", "multi_wavelength", "synthetic"}
)


def _default_intake_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "curated_dataset_intake.json"
    )


@dataclass
class CuratedDatasetIntakeRecord:
    intake_id: str
    dataset_label: str
    data_kind: str
    track: str
    intake_status: str
    has_provenance_documentation: bool
    has_false_positive_baseline: bool
    requires_external_approval: bool
    blocking_issues: list[str]
    created_utc: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "intake_id": self.intake_id,
            "dataset_label": self.dataset_label,
            "data_kind": self.data_kind,
            "track": self.track,
            "intake_status": self.intake_status,
            "has_provenance_documentation": self.has_provenance_documentation,
            "has_false_positive_baseline": self.has_false_positive_baseline,
            "requires_external_approval": self.requires_external_approval,
            "blocking_issues": self.blocking_issues,
            "created_utc": self.created_utc,
            "notes": self.notes,
        }


def load_intake_records(
    fixture_path: Path | None = None,
) -> list[CuratedDatasetIntakeRecord]:
    import json

    path = fixture_path or _default_intake_path()
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    records = []
    for item in raw.get("intake_records", []):
        records.append(
            CuratedDatasetIntakeRecord(
                intake_id=item["intake_id"],
                dataset_label=item["dataset_label"],
                data_kind=item["data_kind"],
                track=item["track"],
                intake_status=item["intake_status"],
                has_provenance_documentation=bool(item["has_provenance_documentation"]),
                has_false_positive_baseline=bool(item["has_false_positive_baseline"]),
                requires_external_approval=bool(item["requires_external_approval"]),
                blocking_issues=list(item.get("blocking_issues", [])),
                created_utc=item["created_utc"],
                notes=item["notes"],
            )
        )
    return records


def curated_dataset_intake_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    records = load_intake_records(fixture_path)

    by_status: dict[str, int] = {}
    by_track: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    total_blocking_issues = 0
    approved_count = 0
    blocked_count = 0

    for r in records:
        by_status[r.intake_status] = by_status.get(r.intake_status, 0) + 1
        by_track[r.track] = by_track.get(r.track, 0) + 1
        by_kind[r.data_kind] = by_kind.get(r.data_kind, 0) + 1
        total_blocking_issues += len(r.blocking_issues)
        if r.intake_status == "approved":
            approved_count += 1
        if r.intake_status == "blocked":
            blocked_count += 1

    return {
        "disclaimer": CURATED_DATASET_INTAKE_DISCLAIMER,
        "schema_version": CURATED_DATASET_INTAKE_SCHEMA_VERSION,
        "record_count": len(records),
        "approved_count": approved_count,
        "blocked_count": blocked_count,
        "total_blocking_issue_count": total_blocking_issues,
        "by_status": by_status,
        "by_track": by_track,
        "by_kind": by_kind,
    }
