"""Operational provenance records for audit trail events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

AUDIT_TRAIL_LOG_SCHEMA_VERSION = "audit_trail_log_v1"

ALLOWED_AUDIT_KINDS = frozenset(
    {
        "compliance_check",
        "config_change",
        "data_access",
        "system_event",
        "user_action",
    }
)

ALLOWED_AUDIT_STATUSES = frozenset(
    {
        "archived",
        "flagged",
        "recorded",
        "reviewed",
    }
)

_DISCLAIMER = (
    "Audit trail log entries are operational provenance records — "
    "an audit event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "audit_trail_log.json"
)


@dataclass(frozen=True)
class AuditTrailEntry:
    entry_id: str
    audit_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.audit_kind not in ALLOWED_AUDIT_KINDS:
            raise ValueError(f"Invalid audit_kind: {self.audit_kind!r}")
        if self.status not in ALLOWED_AUDIT_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_audit_trail_entries(path: Path | None = None) -> list[AuditTrailEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        AuditTrailEntry(
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


def audit_trail_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_audit_trail_entries(path)
    recorded = sum(1 for e in entries if e.status == "recorded")
    return {
        "schema_version": AUDIT_TRAIL_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "recorded_count": recorded,
        "by_kind": {
            kind: sum(1 for e in entries if e.audit_kind == kind)
            for kind in sorted(ALLOWED_AUDIT_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_AUDIT_STATUSES)
        },
    }
