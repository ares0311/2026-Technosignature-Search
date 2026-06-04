"""Operational provenance records for compliance audit events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COMPLIANCE_AUDIT_LOG_SCHEMA_VERSION = "compliance_audit_log_v1"
COMPLIANCE_AUDIT_LOG_DISCLAIMER = (
    "Compliance audit log entries are operational provenance records — "
    "a compliance audit event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)
ALLOWED_COMPLIANCE_AUDIT_KINDS = frozenset(
    {
        "access_policy",
        "data_handling",
        "operational_policy",
        "retention_policy",
        "security_policy",
    }
)
ALLOWED_COMPLIANCE_AUDIT_STATUSES = frozenset(
    {
        "failed",
        "passed",
        "under_review",
        "waived",
    }
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "compliance_audit_log.json"
)


@dataclass(frozen=True)
class ComplianceAuditEntry:
    entry_id: str
    audit_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.audit_kind not in ALLOWED_COMPLIANCE_AUDIT_KINDS:
            raise ValueError(f"Invalid audit_kind: {self.audit_kind!r}")
        if self.status not in ALLOWED_COMPLIANCE_AUDIT_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_compliance_audit_entries(path: Path | None = None) -> list[ComplianceAuditEntry]:
    fixture_path = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(Path(fixture_path).read_text())
    return [
        ComplianceAuditEntry(
            entry_id=e["entry_id"],
            audit_kind=e["audit_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def compliance_audit_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_compliance_audit_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    passed_count = 0
    for e in entries:
        by_kind[e.audit_kind] = by_kind.get(e.audit_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "passed":
            passed_count += 1
    return {
        "schema_version": COMPLIANCE_AUDIT_LOG_SCHEMA_VERSION,
        "disclaimer": COMPLIANCE_AUDIT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "passed_count": passed_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
