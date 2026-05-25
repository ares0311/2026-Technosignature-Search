"""Site-specific RFI database guardrails.

The database is a local false-positive screening aid for radio candidates. It
does not calibrate radio thresholds and does not authorize live-data use.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RFI_DATABASE_SCHEMA_VERSION = "rfi_database_v1"

RFI_DATABASE_DISCLAIMER = (
    "RFI database records are local false-positive screening aids for radio "
    "candidate review. They do not calibrate scoring thresholds, confirm or "
    "rule out technosignature interest, authorize live data access, authorize "
    "external submission, or constitute detections, discoveries, or external "
    "validation."
)

ALLOWED_RFI_SOURCE_CLASSES = frozenset(
    {
        "gps",
        "aircraft",
        "satellite",
        "observatory_local",
        "test_equipment",
        "unknown",
    }
)

ALLOWED_RFI_REVIEW_STATUSES = frozenset(
    {"reviewed", "provisional", "deprecated", "rejected"}
)


def _default_rfi_database_path() -> Path:
    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "rfi_database.json"


@dataclass(frozen=True)
class RfiDatabaseRecord:
    entry_id: str
    site_id: str
    site_name: str
    frequency_low_hz: float
    frequency_high_hz: float
    source_class: str
    confidence: float
    review_status: str
    provenance: str
    notes: str
    active: bool = True
    synthetic: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "site_id": self.site_id,
            "site_name": self.site_name,
            "frequency_low_hz": self.frequency_low_hz,
            "frequency_high_hz": self.frequency_high_hz,
            "source_class": self.source_class,
            "confidence": self.confidence,
            "review_status": self.review_status,
            "provenance": self.provenance,
            "notes": self.notes,
            "active": self.active,
            "synthetic": self.synthetic,
        }

    def contains(self, frequency_hz: float) -> bool:
        return self.active and self.frequency_low_hz <= frequency_hz <= self.frequency_high_hz


def load_rfi_database_records(path: Path | None = None) -> list[RfiDatabaseRecord]:
    db_path = path if path is not None else _default_rfi_database_path()
    raw = json.loads(db_path.read_text(encoding="utf-8"))
    records: list[RfiDatabaseRecord] = []
    for item in raw.get("rfi_database_entries", []):
        records.append(
            RfiDatabaseRecord(
                entry_id=str(item["entry_id"]),
                site_id=str(item["site_id"]),
                site_name=str(item["site_name"]),
                frequency_low_hz=float(item["frequency_low_hz"]),
                frequency_high_hz=float(item["frequency_high_hz"]),
                source_class=str(item["source_class"]),
                confidence=float(item["confidence"]),
                review_status=str(item["review_status"]),
                provenance=str(item.get("provenance", "")),
                notes=str(item.get("notes", "")),
                active=bool(item.get("active", True)),
                synthetic=bool(item.get("synthetic", True)),
            )
        )
    return records


def validate_rfi_database_records(records: list[RfiDatabaseRecord]) -> dict[str, Any]:
    issues: list[str] = []
    for record in records:
        prefix = f"{record.entry_id}: "
        if record.frequency_low_hz <= 0.0:
            issues.append(prefix + "frequency_low_hz must be positive")
        if record.frequency_high_hz <= record.frequency_low_hz:
            issues.append(prefix + "frequency_high_hz must exceed frequency_low_hz")
        if record.source_class not in ALLOWED_RFI_SOURCE_CLASSES:
            issues.append(prefix + f"unknown source_class {record.source_class!r}")
        if not 0.0 <= record.confidence <= 1.0:
            issues.append(prefix + "confidence must be in the range 0..1")
        if record.review_status not in ALLOWED_RFI_REVIEW_STATUSES:
            issues.append(prefix + f"unknown review_status {record.review_status!r}")
        if not record.provenance.strip():
            issues.append(prefix + "provenance is required")
        if not record.site_id.strip():
            issues.append(prefix + "site_id is required")
    return {"ok": not issues, "issue_count": len(issues), "issues": issues}


def rfi_database_matches(
    frequency_hz: float,
    path: Path | None = None,
) -> list[RfiDatabaseRecord]:
    records = load_rfi_database_records(path)
    return [
        record
        for record in records
        if record.review_status != "rejected" and record.contains(frequency_hz)
    ]


def rfi_database_summary(path: Path | None = None) -> dict[str, Any]:
    records = load_rfi_database_records(path)
    validation = validate_rfi_database_records(records)
    by_source_class: dict[str, int] = {}
    by_review_status: dict[str, int] = {}
    by_site_id: dict[str, int] = {}
    active_count = 0
    reviewed_count = 0
    provisional_count = 0
    synthetic_count = 0

    for record in records:
        by_source_class[record.source_class] = by_source_class.get(record.source_class, 0) + 1
        by_review_status[record.review_status] = (
            by_review_status.get(record.review_status, 0) + 1
        )
        by_site_id[record.site_id] = by_site_id.get(record.site_id, 0) + 1
        if record.active:
            active_count += 1
        if record.review_status == "reviewed":
            reviewed_count += 1
        if record.review_status == "provisional":
            provisional_count += 1
        if record.synthetic:
            synthetic_count += 1

    return {
        "schema_version": RFI_DATABASE_SCHEMA_VERSION,
        "disclaimer": RFI_DATABASE_DISCLAIMER,
        "record_count": len(records),
        "active_count": active_count,
        "reviewed_count": reviewed_count,
        "provisional_count": provisional_count,
        "synthetic_count": synthetic_count,
        "real_record_count": len(records) - synthetic_count,
        "validation_ok": bool(validation["ok"]),
        "validation_issue_count": int(validation["issue_count"]),
        "validation_issues": validation["issues"],
        "by_source_class": dict(sorted(by_source_class.items())),
        "by_review_status": dict(sorted(by_review_status.items())),
        "by_site_id": dict(sorted(by_site_id.items())),
    }
