"""Operational provenance records for compliance reporting events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COMPLIANCE_REPORT_LOG_SCHEMA_VERSION = "compliance_report_log_v1"

ALLOWED_REPORT_KINDS = frozenset(
    {
        "certification_check",
        "external_audit",
        "internal_audit",
        "policy_review",
        "regulatory_report",
    }
)

ALLOWED_REPORT_STATUSES = frozenset(
    {
        "failed",
        "passed",
        "pending",
        "waived",
    }
)

_DISCLAIMER = (
    "Compliance report log entries are operational provenance records — "
    "a compliance reporting event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "compliance_report_log.json"
)


@dataclass(frozen=True)
class ComplianceReportEntry:
    entry_id: str
    report_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.report_kind not in ALLOWED_REPORT_KINDS:
            raise ValueError(f"Invalid report_kind: {self.report_kind!r}")
        if self.status not in ALLOWED_REPORT_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_compliance_report_entries(
    path: Path | None = None,
) -> list[ComplianceReportEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        ComplianceReportEntry(
            entry_id=e["entry_id"],
            report_kind=e["report_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def compliance_report_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_compliance_report_entries(path)
    passed = sum(1 for e in entries if e.status == "passed")
    return {
        "schema_version": COMPLIANCE_REPORT_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "passed_count": passed,
        "by_kind": {
            kind: sum(1 for e in entries if e.report_kind == kind)
            for kind in sorted(ALLOWED_REPORT_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_REPORT_STATUSES)
        },
    }
