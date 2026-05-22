from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_EXPORT_SCHEMA_VERSION = "candidate_export_log_v1"

CANDIDATE_EXPORT_DISCLAIMER = (
    "Candidate export log entries are operational provenance records only. "
    "An export log entry records that candidate data was prepared or delivered "
    "for internal review or reproducibility purposes. Export records do not "
    "modify candidate scores, do not affect pathway routing, do not authorize "
    "external submission or publication, and do not constitute a detection claim."
)

ALLOWED_EXPORT_FORMATS = frozenset({
    "json",
    "csv",
    "markdown",
    "fits_stub",
    "parquet_stub",
})

ALLOWED_EXPORT_STATUSES = frozenset({
    "prepared",
    "exported",
    "delivered",
    "failed",
    "cancelled",
})


def _default_candidate_export_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests" / "fixtures" / "candidate_export_log.json"
    )


@dataclass
class CandidateExportEntry:
    export_id: str
    candidate_id: str
    export_format: str
    status: str
    exported_by: str
    exported_utc: str
    destination: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "export_id": self.export_id,
            "candidate_id": self.candidate_id,
            "export_format": self.export_format,
            "status": self.status,
            "exported_by": self.exported_by,
            "exported_utc": self.exported_utc,
            "destination": self.destination,
            "notes": self.notes,
        }


def load_export_entries(
    fixture_path: Path | None = None,
) -> list[CandidateExportEntry]:
    path = fixture_path or _default_candidate_export_path()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = []
    for raw in data.get("candidate_export_entries", []):
        entries.append(CandidateExportEntry(
            export_id=raw["export_id"],
            candidate_id=raw["candidate_id"],
            export_format=raw["export_format"],
            status=raw["status"],
            exported_by=raw["exported_by"],
            exported_utc=raw["exported_utc"],
            destination=raw.get("destination"),
            notes=raw.get("notes", ""),
        ))
    return entries


def candidate_export_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_export_entries(fixture_path)
    by_status: dict[str, int] = {}
    by_format: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_format[e.export_format] = by_format.get(e.export_format, 0) + 1
    return {
        "schema_version": CANDIDATE_EXPORT_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_EXPORT_DISCLAIMER,
        "entry_count": len(entries),
        "delivered_count": by_status.get("delivered", 0),
        "exported_count": by_status.get("exported", 0),
        "failed_count": by_status.get("failed", 0),
        "by_status": by_status,
        "by_format": by_format,
    }
