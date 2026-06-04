"""Operational provenance records for service level events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SERVICE_LEVEL_LOG_SCHEMA_VERSION = "service_level_log_v1"
SERVICE_LEVEL_LOG_DISCLAIMER = (
    "Service level log entries are operational provenance records — "
    "a service level event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)
ALLOWED_SERVICE_LEVEL_KINDS = frozenset(
    {
        "availability_check",
        "compliance_check",
        "error_rate_check",
        "latency_check",
        "throughput_check",
    }
)
ALLOWED_SERVICE_LEVEL_STATUSES = frozenset(
    {
        "at_risk",
        "met",
        "missed",
        "not_applicable",
    }
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent / "tests" / "fixtures" / "service_level_log.json"
)


@dataclass(frozen=True)
class ServiceLevelEntry:
    entry_id: str
    level_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.level_kind not in ALLOWED_SERVICE_LEVEL_KINDS:
            raise ValueError(f"Invalid level_kind: {self.level_kind!r}")
        if self.status not in ALLOWED_SERVICE_LEVEL_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_service_level_entries(path: Path | None = None) -> list[ServiceLevelEntry]:
    fixture_path = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(Path(fixture_path).read_text())
    return [
        ServiceLevelEntry(
            entry_id=e["entry_id"],
            level_kind=e["level_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def service_level_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_service_level_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    met_count = 0
    for e in entries:
        by_kind[e.level_kind] = by_kind.get(e.level_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "met":
            met_count += 1
    return {
        "schema_version": SERVICE_LEVEL_LOG_SCHEMA_VERSION,
        "disclaimer": SERVICE_LEVEL_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "met_count": met_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
