"""Admission records for proposed RFI database sources.

These records gate whether an RFI database source is ready to supplement the
synthetic fixture. They do not ingest real monitoring data or authorize live use.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RFI_DATABASE_ADMISSION_SCHEMA_VERSION = "rfi_database_admission_v1"

RFI_DATABASE_ADMISSION_DISCLAIMER = (
    "RFI database admission records are local readiness checks for proposed "
    "RFI source lists. They do not ingest real monitoring data, calibrate "
    "scoring thresholds, authorize live data access, authorize external "
    "submission, or constitute detections, discoveries, or external validation."
)

ALLOWED_RFI_DATABASE_ADMISSION_STATUSES = frozenset(
    {
        "synthetic_only",
        "blocked_pending_provenance",
        "blocked_pending_license",
        "blocked_pending_review",
        "ready_for_local_fixture",
    }
)


def _default_admission_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "rfi_database_admission.json"
    )


@dataclass(frozen=True)
class RfiDatabaseAdmissionRecord:
    source_id: str
    site_id: str
    source_label: str
    admission_status: str
    provenance_reviewed: bool
    license_reviewed: bool
    monitoring_context_reviewed: bool
    external_review_required: bool
    external_review_completed: bool
    real_data_authorized: bool
    synthetic_fixture_only: bool
    blocker_count: int
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "site_id": self.site_id,
            "source_label": self.source_label,
            "admission_status": self.admission_status,
            "provenance_reviewed": self.provenance_reviewed,
            "license_reviewed": self.license_reviewed,
            "monitoring_context_reviewed": self.monitoring_context_reviewed,
            "external_review_required": self.external_review_required,
            "external_review_completed": self.external_review_completed,
            "real_data_authorized": self.real_data_authorized,
            "synthetic_fixture_only": self.synthetic_fixture_only,
            "blocker_count": self.blocker_count,
            "notes": self.notes,
        }


def load_rfi_database_admission_records(
    path: Path | None = None,
) -> list[RfiDatabaseAdmissionRecord]:
    admission_path = path if path is not None else _default_admission_path()
    raw = json.loads(admission_path.read_text(encoding="utf-8"))
    records: list[RfiDatabaseAdmissionRecord] = []
    for item in raw.get("rfi_database_admission_records", []):
        records.append(
            RfiDatabaseAdmissionRecord(
                source_id=str(item["source_id"]),
                site_id=str(item["site_id"]),
                source_label=str(item["source_label"]),
                admission_status=str(item["admission_status"]),
                provenance_reviewed=bool(item.get("provenance_reviewed", False)),
                license_reviewed=bool(item.get("license_reviewed", False)),
                monitoring_context_reviewed=bool(
                    item.get("monitoring_context_reviewed", False)
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


def validate_rfi_database_admission_records(
    records: list[RfiDatabaseAdmissionRecord],
) -> dict[str, Any]:
    issues: list[str] = []
    for record in records:
        prefix = f"{record.source_id}: "
        if record.admission_status not in ALLOWED_RFI_DATABASE_ADMISSION_STATUSES:
            issues.append(prefix + f"unknown admission_status {record.admission_status!r}")
        if not record.site_id.strip():
            issues.append(prefix + "site_id is required")
        if record.real_data_authorized and record.synthetic_fixture_only:
            issues.append(prefix + "real data cannot be authorized for synthetic-only records")
        if record.real_data_authorized and not (
            record.provenance_reviewed
            and record.license_reviewed
            and record.monitoring_context_reviewed
            and record.external_review_completed
            and record.blocker_count == 0
        ):
            issues.append(prefix + "real data authorization requires all reviews and zero blockers")
        if record.admission_status == "ready_for_local_fixture" and record.blocker_count != 0:
            issues.append(prefix + "ready_for_local_fixture requires zero blockers")
    return {"ok": not issues, "issue_count": len(issues), "issues": issues}


def rfi_database_admission_summary(path: Path | None = None) -> dict[str, Any]:
    records = load_rfi_database_admission_records(path)
    validation = validate_rfi_database_admission_records(records)
    by_status: dict[str, int] = {}
    by_site_id: dict[str, int] = {}
    real_data_authorized_count = 0
    synthetic_only_count = 0
    ready_for_local_fixture_count = 0
    blocked_count = 0
    external_review_required_count = 0
    external_review_completed_count = 0
    total_blocker_count = 0

    for record in records:
        by_status[record.admission_status] = by_status.get(record.admission_status, 0) + 1
        by_site_id[record.site_id] = by_site_id.get(record.site_id, 0) + 1
        total_blocker_count += record.blocker_count
        if record.real_data_authorized:
            real_data_authorized_count += 1
        if record.synthetic_fixture_only:
            synthetic_only_count += 1
        if record.admission_status == "ready_for_local_fixture":
            ready_for_local_fixture_count += 1
        if record.admission_status.startswith("blocked_"):
            blocked_count += 1
        if record.external_review_required:
            external_review_required_count += 1
        if record.external_review_completed:
            external_review_completed_count += 1

    return {
        "schema_version": RFI_DATABASE_ADMISSION_SCHEMA_VERSION,
        "disclaimer": RFI_DATABASE_ADMISSION_DISCLAIMER,
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
        "by_site_id": dict(sorted(by_site_id.items())),
        "records": [record.as_dict() for record in records],
    }
