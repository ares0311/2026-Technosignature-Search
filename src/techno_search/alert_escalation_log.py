"""Operational provenance records for alert escalation routing events."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALERT_ESCALATION_LOG_SCHEMA_VERSION = "alert_escalation_log_v1"

ALLOWED_ALERT_ESCALATION_KINDS = frozenset(
    {
        "automatic_escalation",
        "manual_escalation",
        "page_oncall",
        "reassignment",
        "resolution_escalation",
    }
)

ALLOWED_ALERT_ESCALATION_STATUSES = frozenset(
    {
        "acknowledged",
        "escalated",
        "resolved",
        "unacknowledged",
    }
)

_FIXTURE_PATH = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "alert_escalation_log.json"
)


@dataclass(frozen=True)
class AlertEscalationEntry:
    entry_id: str
    escalation_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str

    def __post_init__(self) -> None:
        if self.escalation_kind not in ALLOWED_ALERT_ESCALATION_KINDS:
            raise ValueError(f"Invalid escalation_kind: {self.escalation_kind!r}")
        if self.status not in ALLOWED_ALERT_ESCALATION_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_alert_escalation_entries(
    fixture_path: Path | None = None,
) -> list[AlertEscalationEntry]:
    import json

    path = fixture_path or _FIXTURE_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        AlertEscalationEntry(
            entry_id=str(entry["entry_id"]),
            escalation_kind=str(entry["escalation_kind"]),
            status=str(entry["status"]),
            actor_id=str(entry["actor_id"]),
            resource_id=str(entry["resource_id"]),
            timestamp_utc=str(entry["timestamp_utc"]),
            notes=str(entry["notes"]),
        )
        for entry in data["entries"]
    ]


def alert_escalation_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_alert_escalation_entries(fixture_path)
    resolved_count = sum(1 for e in entries if e.status == "resolved")
    return {
        "schema_version": ALERT_ESCALATION_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "resolved_count": resolved_count,
        "disclaimer": (
            "Alert escalation entries are operational provenance records — "
            "an alert escalation event does not modify candidate scores or "
            "pathway routing, does not authorize external submission, and does "
            "not constitute a detection claim."
        ),
    }
