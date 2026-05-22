from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OPERATOR_ESCALATION_SCHEMA_VERSION = "operator_escalation_log_v1"

OPERATOR_ESCALATION_DISCLAIMER = (
    "Operator escalation log entries are scheduling coordination provenance records only. "
    "An escalation records that an operator transferred responsibility for a candidate "
    "or alert to another operator — it does not constitute a detection claim, authorize "
    "external submission, or modify scores or pathway routing. Escalation severity "
    "reflects scheduling priority, not candidate scientific significance."
)

ALLOWED_OPERATOR_ESCALATION_SEVERITIES = frozenset({"routine", "urgent", "critical"})

ALLOWED_OPERATOR_ESCALATION_STATUSES = frozenset({"open", "acknowledged", "resolved"})


def _default_operator_escalation_fixture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "operator_escalation_log.json"
    )


@dataclass
class OperatorEscalationEntry:
    escalation_id: str
    candidate_id: str
    from_operator: str
    to_operator: str
    escalation_reason: str
    severity: str
    status: str
    escalated_utc: str
    resolved_utc: str | None = None
    linked_alert_ids: list[str] | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if self.linked_alert_ids is None:
            self.linked_alert_ids = []

    def as_dict(self) -> dict[str, Any]:
        return {
            "escalation_id": self.escalation_id,
            "candidate_id": self.candidate_id,
            "from_operator": self.from_operator,
            "to_operator": self.to_operator,
            "escalation_reason": self.escalation_reason,
            "severity": self.severity,
            "status": self.status,
            "escalated_utc": self.escalated_utc,
            "resolved_utc": self.resolved_utc,
            "linked_alert_ids": self.linked_alert_ids or [],
            "notes": self.notes,
        }


def load_operator_escalation_entries(
    fixture_path: Path | str | None = None,
) -> list[OperatorEscalationEntry]:
    path = (
        Path(fixture_path)
        if fixture_path is not None
        else _default_operator_escalation_fixture_path()
    )
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = []
    for entry in data.get("operator_escalation_entries", []):
        entries.append(
            OperatorEscalationEntry(
                escalation_id=entry["escalation_id"],
                candidate_id=entry["candidate_id"],
                from_operator=entry["from_operator"],
                to_operator=entry["to_operator"],
                escalation_reason=entry["escalation_reason"],
                severity=entry["severity"],
                status=entry["status"],
                escalated_utc=entry["escalated_utc"],
                resolved_utc=entry.get("resolved_utc"),
                linked_alert_ids=list(entry.get("linked_alert_ids", [])),
                notes=entry.get("notes", ""),
            )
        )
    return entries


def operator_escalation_summary(
    fixture_path: Path | str | None = None,
) -> dict[str, Any]:
    entries = load_operator_escalation_entries(fixture_path)
    by_severity: dict[str, int] = {}
    by_status: dict[str, int] = {}
    open_count = 0
    for e in entries:
        by_severity[e.severity] = by_severity.get(e.severity, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "open":
            open_count += 1
    resolved_count = by_status.get("resolved", 0)
    acknowledged_count = by_status.get("acknowledged", 0)
    return {
        "disclaimer": OPERATOR_ESCALATION_DISCLAIMER,
        "schema_version": OPERATOR_ESCALATION_SCHEMA_VERSION,
        "entry_count": len(entries),
        "open_count": open_count,
        "acknowledged_count": acknowledged_count,
        "resolved_count": resolved_count,
        "by_severity": by_severity,
        "by_status": by_status,
    }
