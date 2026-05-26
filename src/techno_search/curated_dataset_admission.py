"""Admission records for proposed curated validation datasets.

These records gate whether a future non-synthetic labeled dataset is ready to
supplement synthetic fixtures. They do not ingest real observations or authorize
calibration claims.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CURATED_DATASET_ADMISSION_SCHEMA_VERSION = "curated_dataset_admission_v1"

CURATED_DATASET_ADMISSION_DISCLAIMER = (
    "Curated dataset admission records are local readiness checks for proposed "
    "validation datasets. They do not ingest real observation data, calibrate "
    "scoring thresholds, authorize live data access, authorize external "
    "submission, or constitute detections, discoveries, or external validation."
)

ALLOWED_CURATED_DATASET_ADMISSION_STATUSES = frozenset(
    {
        "synthetic_only",
        "blocked_pending_provenance",
        "blocked_pending_license",
        "blocked_pending_labeling",
        "blocked_pending_false_positive_baseline",
        "blocked_pending_review",
        "ready_for_local_fixture",
    }
)


def _default_admission_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "curated_dataset_admission.json"
    )


@dataclass(frozen=True)
class CuratedDatasetAdmissionRecord:
    dataset_id: str
    dataset_label: str
    track: str
    dataset_kind: str
    admission_status: str
    provenance_reviewed: bool
    license_reviewed: bool
    labeling_method_reviewed: bool
    false_positive_baseline_reviewed: bool
    external_review_required: bool
    external_review_completed: bool
    real_data_authorized: bool
    synthetic_fixture_only: bool
    blocker_count: int
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_label": self.dataset_label,
            "track": self.track,
            "dataset_kind": self.dataset_kind,
            "admission_status": self.admission_status,
            "provenance_reviewed": self.provenance_reviewed,
            "license_reviewed": self.license_reviewed,
            "labeling_method_reviewed": self.labeling_method_reviewed,
            "false_positive_baseline_reviewed": (
                self.false_positive_baseline_reviewed
            ),
            "external_review_required": self.external_review_required,
            "external_review_completed": self.external_review_completed,
            "real_data_authorized": self.real_data_authorized,
            "synthetic_fixture_only": self.synthetic_fixture_only,
            "blocker_count": self.blocker_count,
            "notes": self.notes,
        }


def load_curated_dataset_admission_records(
    path: Path | None = None,
) -> list[CuratedDatasetAdmissionRecord]:
    admission_path = path if path is not None else _default_admission_path()
    raw = json.loads(admission_path.read_text(encoding="utf-8"))
    records: list[CuratedDatasetAdmissionRecord] = []
    for item in raw.get("curated_dataset_admission_records", []):
        records.append(
            CuratedDatasetAdmissionRecord(
                dataset_id=str(item["dataset_id"]),
                dataset_label=str(item["dataset_label"]),
                track=str(item["track"]),
                dataset_kind=str(item["dataset_kind"]),
                admission_status=str(item["admission_status"]),
                provenance_reviewed=bool(item.get("provenance_reviewed", False)),
                license_reviewed=bool(item.get("license_reviewed", False)),
                labeling_method_reviewed=bool(
                    item.get("labeling_method_reviewed", False)
                ),
                false_positive_baseline_reviewed=bool(
                    item.get("false_positive_baseline_reviewed", False)
                ),
                external_review_required=bool(item.get("external_review_required", True)),
                external_review_completed=bool(
                    item.get("external_review_completed", False)
                ),
                real_data_authorized=bool(item.get("real_data_authorized", False)),
                synthetic_fixture_only=bool(item.get("synthetic_fixture_only", True)),
                blocker_count=int(item.get("blocker_count", 0)),
                notes=str(item.get("notes", "")),
            )
        )
    return records


def validate_curated_dataset_admission_records(
    records: list[CuratedDatasetAdmissionRecord],
) -> dict[str, Any]:
    issues: list[str] = []
    for record in records:
        prefix = f"{record.dataset_id}: "
        all_reviews_complete = (
            record.provenance_reviewed
            and record.license_reviewed
            and record.labeling_method_reviewed
            and record.false_positive_baseline_reviewed
            and record.external_review_completed
        )
        if record.admission_status not in ALLOWED_CURATED_DATASET_ADMISSION_STATUSES:
            issues.append(prefix + f"unknown admission_status {record.admission_status!r}")
        if not record.track.strip():
            issues.append(prefix + "track is required")
        if record.admission_status == "synthetic_only" and not record.synthetic_fixture_only:
            issues.append(prefix + "synthetic_only status requires synthetic_fixture_only")
        if not record.synthetic_fixture_only and not record.external_review_required:
            issues.append(prefix + "non-synthetic admission requires external review")
        if record.real_data_authorized and record.synthetic_fixture_only:
            issues.append(prefix + "real data cannot be authorized for synthetic-only records")
        if record.real_data_authorized and record.admission_status != "ready_for_local_fixture":
            issues.append(prefix + "real data authorization requires ready_for_local_fixture")
        if record.real_data_authorized and not (
            all_reviews_complete and record.blocker_count == 0
        ):
            issues.append(prefix + "real data authorization requires all reviews and zero blockers")
        if record.admission_status == "ready_for_local_fixture" and not (
            all_reviews_complete and record.blocker_count == 0
        ):
            issues.append(prefix + "ready_for_local_fixture requires all reviews and zero blockers")
    return {"ok": not issues, "issue_count": len(issues), "issues": issues}


def curated_dataset_admission_summary(path: Path | None = None) -> dict[str, Any]:
    records = load_curated_dataset_admission_records(path)
    validation = validate_curated_dataset_admission_records(records)
    by_status: dict[str, int] = {}
    by_track: dict[str, int] = {}
    by_dataset_kind: dict[str, int] = {}
    blocked_count = 0
    ready_for_local_fixture_count = 0
    synthetic_only_count = 0
    real_data_authorized_count = 0
    external_review_required_count = 0
    external_review_completed_count = 0
    total_blocker_count = 0

    for record in records:
        by_status[record.admission_status] = by_status.get(record.admission_status, 0) + 1
        by_track[record.track] = by_track.get(record.track, 0) + 1
        by_dataset_kind[record.dataset_kind] = (
            by_dataset_kind.get(record.dataset_kind, 0) + 1
        )
        total_blocker_count += record.blocker_count
        if record.admission_status.startswith("blocked_"):
            blocked_count += 1
        if record.admission_status == "ready_for_local_fixture":
            ready_for_local_fixture_count += 1
        if record.synthetic_fixture_only:
            synthetic_only_count += 1
        if record.real_data_authorized:
            real_data_authorized_count += 1
        if record.external_review_required:
            external_review_required_count += 1
        if record.external_review_completed:
            external_review_completed_count += 1

    return {
        "schema_version": CURATED_DATASET_ADMISSION_SCHEMA_VERSION,
        "disclaimer": CURATED_DATASET_ADMISSION_DISCLAIMER,
        "record_count": len(records),
        "blocked_count": blocked_count,
        "ready_for_local_fixture_count": ready_for_local_fixture_count,
        "synthetic_only_count": synthetic_only_count,
        "real_data_authorized_count": real_data_authorized_count,
        "external_review_required_count": external_review_required_count,
        "external_review_completed_count": external_review_completed_count,
        "total_blocker_count": total_blocker_count,
        "validation_ok": bool(validation["ok"]),
        "validation_issue_count": int(validation["issue_count"]),
        "validation_issues": validation["issues"],
        "by_status": dict(sorted(by_status.items())),
        "by_track": dict(sorted(by_track.items())),
        "by_dataset_kind": dict(sorted(by_dataset_kind.items())),
        "records": [record.as_dict() for record in records],
    }
