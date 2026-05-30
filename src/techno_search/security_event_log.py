"""Operational provenance records for security events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SECURITY_EVENT_LOG_SCHEMA_VERSION = "security_event_log_v1"

ALLOWED_SECURITY_EVENT_KINDS = frozenset(
    {
        "credential_change",
        "intrusion_attempt",
        "physical_breach",
        "policy_violation",
        "unauthorized_access",
    }
)

ALLOWED_SECURITY_EVENT_STATUSES = frozenset(
    {
        "detected",
        "escalated",
        "investigated",
        "resolved",
    }
)

_DISCLAIMER = (
    "Security event log entries are operational provenance records — "
    "a security event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "security_event_log.json"
)


@dataclass(frozen=True)
class SecurityEventEntry:
    entry_id: str
    event_kind: str
    status: str
    severity: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.event_kind not in ALLOWED_SECURITY_EVENT_KINDS:
            raise ValueError(f"Invalid event_kind: {self.event_kind!r}")
        if self.status not in ALLOWED_SECURITY_EVENT_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_security_event_entries(path: Path | None = None) -> list[SecurityEventEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        SecurityEventEntry(
            entry_id=e["entry_id"],
            event_kind=e["event_kind"],
            status=e["status"],
            severity=e["severity"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def security_event_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_security_event_entries(path)
    detected = sum(1 for e in entries if e.status == "detected")
    return {
        "schema_version": SECURITY_EVENT_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "detected_count": detected,
        "by_kind": {
            kind: sum(1 for e in entries if e.event_kind == kind)
            for kind in sorted(ALLOWED_SECURITY_EVENT_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_SECURITY_EVENT_STATUSES)
        },
    }
