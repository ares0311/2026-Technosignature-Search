"""Operational provenance records for cross-system event correlation runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EVENT_CORRELATION_LOG_SCHEMA_VERSION = "event_correlation_log_v1"

ALLOWED_CORRELATION_KINDS = frozenset(
    {
        "alert_cluster",
        "causal_chain",
        "fault_event",
        "observation_link",
        "temporal_cluster",
    }
)

ALLOWED_CORRELATION_STATUSES = frozenset(
    {
        "correlated",
        "inconclusive",
        "no_match",
        "pending",
    }
)

_DISCLAIMER = (
    "Event correlation log entries are operational provenance records — "
    "an event correlation run does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "event_correlation_log.json"
)


@dataclass(frozen=True)
class EventCorrelationEntry:
    entry_id: str
    correlation_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.correlation_kind not in ALLOWED_CORRELATION_KINDS:
            raise ValueError(f"Invalid correlation_kind: {self.correlation_kind!r}")
        if self.status not in ALLOWED_CORRELATION_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_event_correlation_entries(
    path: Path | None = None,
) -> list[EventCorrelationEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        EventCorrelationEntry(
            entry_id=e["entry_id"],
            correlation_kind=e["correlation_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def event_correlation_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_event_correlation_entries(path)
    correlated = sum(1 for e in entries if e.status == "correlated")
    return {
        "schema_version": EVENT_CORRELATION_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "correlated_count": correlated,
        "by_kind": {
            kind: sum(1 for e in entries if e.correlation_kind == kind)
            for kind in sorted(ALLOWED_CORRELATION_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_CORRELATION_STATUSES)
        },
    }
