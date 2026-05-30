"""Operational provenance records for facility and system access events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ACCESS_LOG_SCHEMA_VERSION = "access_log_v1"

ALLOWED_ACCESS_KINDS = frozenset(
    {
        "facility_entry",
        "facility_exit",
        "remote_access",
        "system_login",
        "system_logout",
    }
)

ALLOWED_ACCESS_STATUSES = frozenset(
    {
        "denied",
        "expired",
        "granted",
        "revoked",
    }
)

_DISCLAIMER = (
    "Access log entries are operational provenance records — "
    "an access event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent / "tests" / "fixtures" / "access_log.json"
)


@dataclass(frozen=True)
class AccessEntry:
    entry_id: str
    access_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.access_kind not in ALLOWED_ACCESS_KINDS:
            raise ValueError(f"Invalid access_kind: {self.access_kind!r}")
        if self.status not in ALLOWED_ACCESS_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_access_entries(path: Path | None = None) -> list[AccessEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        AccessEntry(
            entry_id=e["entry_id"],
            access_kind=e["access_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def access_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_access_entries(path)
    granted = sum(1 for e in entries if e.status == "granted")
    return {
        "schema_version": ACCESS_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "granted_count": granted,
        "by_kind": {
            kind: sum(1 for e in entries if e.access_kind == kind)
            for kind in sorted(ALLOWED_ACCESS_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_ACCESS_STATUSES)
        },
    }
