"""Operational provenance records for disaster recovery events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DISASTER_RECOVERY_LOG_SCHEMA_VERSION = "disaster_recovery_log_v1"
DISASTER_RECOVERY_LOG_DISCLAIMER = (
    "Disaster recovery log entries are operational provenance records — "
    "a disaster recovery event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)
ALLOWED_DISASTER_RECOVERY_KINDS = frozenset(
    {
        "backup_restore",
        "business_continuity_drill",
        "failover",
        "recovery_test",
        "redundancy_check",
    }
)
ALLOWED_DISASTER_RECOVERY_STATUSES = frozenset(
    {
        "completed",
        "failed",
        "in_progress",
        "scheduled",
    }
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "disaster_recovery_log.json"
)


@dataclass(frozen=True)
class DisasterRecoveryEntry:
    entry_id: str
    recovery_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.recovery_kind not in ALLOWED_DISASTER_RECOVERY_KINDS:
            raise ValueError(f"Invalid recovery_kind: {self.recovery_kind!r}")
        if self.status not in ALLOWED_DISASTER_RECOVERY_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_disaster_recovery_entries(
    path: Path | None = None,
) -> list[DisasterRecoveryEntry]:
    fixture_path = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(Path(fixture_path).read_text())
    return [
        DisasterRecoveryEntry(
            entry_id=e["entry_id"],
            recovery_kind=e["recovery_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def disaster_recovery_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_disaster_recovery_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    completed_count = 0
    for e in entries:
        by_kind[e.recovery_kind] = by_kind.get(e.recovery_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "completed":
            completed_count += 1
    return {
        "schema_version": DISASTER_RECOVERY_LOG_SCHEMA_VERSION,
        "disclaimer": DISASTER_RECOVERY_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": completed_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
