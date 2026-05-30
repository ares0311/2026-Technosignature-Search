"""Operational provenance records for facility user activity events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

USER_ACTIVITY_LOG_SCHEMA_VERSION = "user_activity_log_v1"

ALLOWED_ACTIVITY_KINDS = frozenset(
    {
        "admin_action",
        "api_call",
        "config_change",
        "data_export",
        "login",
    }
)

ALLOWED_ACTIVITY_STATUSES = frozenset(
    {
        "blocked",
        "failed",
        "succeeded",
        "warning",
    }
)

_DISCLAIMER = (
    "User activity log entries are operational provenance records — "
    "a user activity event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "user_activity_log.json"
)


@dataclass(frozen=True)
class UserActivityEntry:
    entry_id: str
    activity_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.activity_kind not in ALLOWED_ACTIVITY_KINDS:
            raise ValueError(f"Invalid activity_kind: {self.activity_kind!r}")
        if self.status not in ALLOWED_ACTIVITY_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_user_activity_entries(
    path: Path | None = None,
) -> list[UserActivityEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        UserActivityEntry(
            entry_id=e["entry_id"],
            activity_kind=e["activity_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def user_activity_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_user_activity_entries(path)
    succeeded = sum(1 for e in entries if e.status == "succeeded")
    return {
        "schema_version": USER_ACTIVITY_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "succeeded_count": succeeded,
        "by_kind": {
            kind: sum(1 for e in entries if e.activity_kind == kind)
            for kind in sorted(ALLOWED_ACTIVITY_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_ACTIVITY_STATUSES)
        },
    }
