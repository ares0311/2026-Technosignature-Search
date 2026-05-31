"""Operational provenance records for system and service health check events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HEALTH_CHECK_LOG_SCHEMA_VERSION = "health_check_log_v1"

ALLOWED_CHECK_KINDS = frozenset(
    {
        "api_health",
        "database_health",
        "network_health",
        "service_health",
        "storage_health",
    }
)

ALLOWED_CHECK_STATUSES = frozenset(
    {
        "degraded",
        "failed",
        "passed",
        "timeout",
    }
)

_DISCLAIMER = (
    "Health check log entries are operational provenance records — "
    "a health check event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "health_check_log.json"
)


@dataclass(frozen=True)
class HealthCheckEntry:
    entry_id: str
    check_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.check_kind not in ALLOWED_CHECK_KINDS:
            raise ValueError(f"Invalid check_kind: {self.check_kind!r}")
        if self.status not in ALLOWED_CHECK_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_health_check_entries(
    path: Path | None = None,
) -> list[HealthCheckEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        HealthCheckEntry(
            entry_id=e["entry_id"],
            check_kind=e["check_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def health_check_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_health_check_entries(path)
    passed = sum(1 for e in entries if e.status == "passed")
    return {
        "schema_version": HEALTH_CHECK_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "passed_count": passed,
        "by_kind": {
            kind: sum(1 for e in entries if e.check_kind == kind)
            for kind in sorted(ALLOWED_CHECK_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_CHECK_STATUSES)
        },
    }
