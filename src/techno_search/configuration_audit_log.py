"""Operational provenance records for configuration change audit events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIGURATION_AUDIT_LOG_SCHEMA_VERSION = "configuration_audit_log_v1"

ALLOWED_AUDIT_KINDS = frozenset(
    {
        "baseline_check",
        "compliance_scan",
        "drift_detection",
        "manual_audit",
        "scheduled_audit",
    }
)

ALLOWED_AUDIT_STATUSES = frozenset(
    {
        "compliant",
        "drifted",
        "failed",
        "inconclusive",
    }
)

_DISCLAIMER = (
    "Configuration audit log entries are operational provenance records — "
    "a configuration audit event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "configuration_audit_log.json"
)


@dataclass(frozen=True)
class ConfigurationAuditEntry:
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


def load_configuration_audit_entries(
    path: Path | None = None,
) -> list[ConfigurationAuditEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        ConfigurationAuditEntry(
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


def configuration_audit_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_configuration_audit_entries(path)
    compliant = sum(1 for e in entries if e.status == "compliant")
    return {
        "schema_version": CONFIGURATION_AUDIT_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "compliant_count": compliant,
        "by_kind": {
            kind: sum(1 for e in entries if e.audit_kind == kind)
            for kind in sorted(ALLOWED_AUDIT_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_AUDIT_STATUSES)
        },
    }
