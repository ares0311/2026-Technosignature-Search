"""Operational provenance records for access control events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ACCESS_CONTROL_LOG_SCHEMA_VERSION = "access_control_log_v1"
ACCESS_CONTROL_LOG_DISCLAIMER = (
    "Access control log entries are operational provenance records — "
    "an access control event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)
ALLOWED_ACCESS_CONTROL_KINDS = frozenset(
    {
        "access_grant",
        "access_revocation",
        "authentication_attempt",
        "authorization_check",
        "permission_change",
    }
)
ALLOWED_ACCESS_CONTROL_STATUSES = frozenset(
    {
        "allowed",
        "blocked",
        "expired",
        "pending",
    }
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent / "tests" / "fixtures" / "access_control_log.json"
)


@dataclass(frozen=True)
class AccessControlEntry:
    entry_id: str
    access_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.access_kind not in ALLOWED_ACCESS_CONTROL_KINDS:
            raise ValueError(f"Invalid access_kind: {self.access_kind!r}")
        if self.status not in ALLOWED_ACCESS_CONTROL_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_access_control_entries(path: Path | None = None) -> list[AccessControlEntry]:
    fixture_path = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(Path(fixture_path).read_text())
    return [
        AccessControlEntry(
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


def access_control_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_access_control_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    allowed_count = 0
    for e in entries:
        by_kind[e.access_kind] = by_kind.get(e.access_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "allowed":
            allowed_count += 1
    return {
        "schema_version": ACCESS_CONTROL_LOG_SCHEMA_VERSION,
        "disclaimer": ACCESS_CONTROL_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "allowed_count": allowed_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
