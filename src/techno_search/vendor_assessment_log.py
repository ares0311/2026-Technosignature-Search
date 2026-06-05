from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VENDOR_ASSESSMENT_LOG_SCHEMA_VERSION = "vendor_assessment_log_v1"

ALLOWED_VENDOR_ASSESSMENT_KINDS = frozenset(
    {
        "financial_review",
        "performance_review",
        "risk_review",
        "security_review",
        "technical_review",
    }
)

ALLOWED_VENDOR_ASSESSMENT_STATUSES = frozenset(
    {
        "accepted",
        "completed",
        "in_progress",
        "rejected",
    }
)

_DISCLAIMER = (
    "Vendor assessment entries are operational provenance records — a vendor "
    "assessment event does not modify candidate scores or pathway routing, does not "
    "authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent / "tests" / "fixtures" / "vendor_assessment_log.json"
)


@dataclass(frozen=True)
class VendorAssessmentEntry:
    entry_id: str
    assessment_kind: str
    status: str
    vendor_id: str
    description: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.assessment_kind not in ALLOWED_VENDOR_ASSESSMENT_KINDS:
            raise ValueError(
                f"invalid assessment_kind {self.assessment_kind!r}; "
                f"allowed: {sorted(ALLOWED_VENDOR_ASSESSMENT_KINDS)}"
            )
        if self.status not in ALLOWED_VENDOR_ASSESSMENT_STATUSES:
            raise ValueError(
                f"invalid status {self.status!r}; "
                f"allowed: {sorted(ALLOWED_VENDOR_ASSESSMENT_STATUSES)}"
            )


def load_vendor_assessment_entries(path: Path | None = None) -> list[VendorAssessmentEntry]:
    fixture = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    return [
        VendorAssessmentEntry(
            entry_id=e["entry_id"],
            assessment_kind=e["assessment_kind"],
            status=e["status"],
            vendor_id=e["vendor_id"],
            description=e["description"],
            notes=e.get("notes", ""),
        )
        for e in raw["entries"]
    ]


def vendor_assessment_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_vendor_assessment_entries(path)
    completed_count = sum(1 for e in entries if e.status == "completed")
    kind_counts = {k: 0 for k in ALLOWED_VENDOR_ASSESSMENT_KINDS}
    status_counts = {s: 0 for s in ALLOWED_VENDOR_ASSESSMENT_STATUSES}
    for e in entries:
        kind_counts[e.assessment_kind] += 1
        status_counts[e.status] += 1
    return {
        "schema_version": VENDOR_ASSESSMENT_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "completed_count": completed_count,
        "kind_counts": kind_counts,
        "status_counts": status_counts,
        "disclaimer": _DISCLAIMER,
    }
