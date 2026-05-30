"""Operational provenance records for facility risk assessment events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RISK_ASSESSMENT_LOG_SCHEMA_VERSION = "risk_assessment_log_v1"

ALLOWED_RISK_KINDS = frozenset(
    {
        "compliance_risk",
        "cyber_risk",
        "environmental_risk",
        "operational_risk",
        "physical_risk",
    }
)

ALLOWED_RISK_STATUSES = frozenset(
    {
        "accepted",
        "assessed",
        "identified",
        "mitigated",
    }
)

_DISCLAIMER = (
    "Risk assessment log entries are operational provenance records — "
    "a risk assessment event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "risk_assessment_log.json"
)


@dataclass(frozen=True)
class RiskAssessmentEntry:
    entry_id: str
    risk_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.risk_kind not in ALLOWED_RISK_KINDS:
            raise ValueError(f"Invalid risk_kind: {self.risk_kind!r}")
        if self.status not in ALLOWED_RISK_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_risk_assessment_entries(
    path: Path | None = None,
) -> list[RiskAssessmentEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        RiskAssessmentEntry(
            entry_id=e["entry_id"],
            risk_kind=e["risk_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def risk_assessment_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_risk_assessment_entries(path)
    mitigated = sum(1 for e in entries if e.status == "mitigated")
    return {
        "schema_version": RISK_ASSESSMENT_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "mitigated_count": mitigated,
        "by_kind": {
            kind: sum(1 for e in entries if e.risk_kind == kind)
            for kind in sorted(ALLOWED_RISK_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_RISK_STATUSES)
        },
    }
