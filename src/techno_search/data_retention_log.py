"""Operational provenance records for data retention policy enforcement events."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_RETENTION_LOG_SCHEMA_VERSION = "data_retention_log_v1"

ALLOWED_DATA_RETENTION_KINDS = frozenset(
    {
        "archive_transfer",
        "deletion_scheduled",
        "policy_review",
        "retention_expired",
        "retention_extended",
    }
)

ALLOWED_DATA_RETENTION_STATUSES = frozenset(
    {
        "completed",
        "deferred",
        "failed",
        "pending",
    }
)

_FIXTURE_PATH = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "data_retention_log.json"
)


@dataclass(frozen=True)
class DataRetentionEntry:
    entry_id: str
    retention_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str

    def __post_init__(self) -> None:
        if self.retention_kind not in ALLOWED_DATA_RETENTION_KINDS:
            raise ValueError(f"Invalid retention_kind: {self.retention_kind!r}")
        if self.status not in ALLOWED_DATA_RETENTION_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_data_retention_entries(
    fixture_path: Path | None = None,
) -> list[DataRetentionEntry]:
    import json

    path = fixture_path or _FIXTURE_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        DataRetentionEntry(
            entry_id=str(entry["entry_id"]),
            retention_kind=str(entry["retention_kind"]),
            status=str(entry["status"]),
            actor_id=str(entry["actor_id"]),
            resource_id=str(entry["resource_id"]),
            timestamp_utc=str(entry["timestamp_utc"]),
            notes=str(entry["notes"]),
        )
        for entry in data["entries"]
    ]


def data_retention_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_data_retention_entries(fixture_path)
    completed_count = sum(1 for e in entries if e.status == "completed")
    return {
        "schema_version": DATA_RETENTION_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "completed_count": completed_count,
        "disclaimer": (
            "Data retention entries are operational provenance records — "
            "a data retention event does not modify candidate scores or "
            "pathway routing, does not authorize external submission, and does "
            "not constitute a detection claim."
        ),
    }
