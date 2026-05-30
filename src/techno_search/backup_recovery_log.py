"""Operational provenance records for facility backup and recovery events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BACKUP_RECOVERY_LOG_SCHEMA_VERSION = "backup_recovery_log_v1"

ALLOWED_BACKUP_KINDS = frozenset(
    {
        "differential_backup",
        "full_backup",
        "incremental_backup",
        "recovery_test",
        "snapshot",
    }
)

ALLOWED_BACKUP_STATUSES = frozenset(
    {
        "completed",
        "failed",
        "in_progress",
        "skipped",
    }
)

_DISCLAIMER = (
    "Backup and recovery log entries are operational provenance records — "
    "a backup or recovery event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "backup_recovery_log.json"
)


@dataclass(frozen=True)
class BackupRecoveryEntry:
    entry_id: str
    backup_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.backup_kind not in ALLOWED_BACKUP_KINDS:
            raise ValueError(f"Invalid backup_kind: {self.backup_kind!r}")
        if self.status not in ALLOWED_BACKUP_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_backup_recovery_entries(
    path: Path | None = None,
) -> list[BackupRecoveryEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        BackupRecoveryEntry(
            entry_id=e["entry_id"],
            backup_kind=e["backup_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def backup_recovery_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_backup_recovery_entries(path)
    completed = sum(1 for e in entries if e.status == "completed")
    return {
        "schema_version": BACKUP_RECOVERY_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": completed,
        "by_kind": {
            kind: sum(1 for e in entries if e.backup_kind == kind)
            for kind in sorted(ALLOWED_BACKUP_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_BACKUP_STATUSES)
        },
    }
