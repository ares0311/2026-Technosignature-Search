from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_ALERT_SCHEMA_VERSION = "candidate_alert_log_v1"

CANDIDATE_ALERT_DISCLAIMER = (
    "Candidate alert log entries are operational provenance records only. "
    "An alert indicates a threshold crossing or status change that requires "
    "operator awareness — it does not constitute a detection claim, authorize "
    "external submission, or modify scores or pathway routing."
)

ALLOWED_ALERT_SEVERITIES = frozenset({"info", "warning", "critical"})

ALLOWED_ALERT_KINDS = frozenset(
    {
        "score_threshold_crossed",
        "pathway_changed",
        "flag_raised",
        "rescore_triggered",
        "provenance_inconsistency",
        "deadline_approaching",
        "operator_action_required",
    }
)


def _default_alert_fixture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent / "tests" / "fixtures" / "candidate_alert_log.json"
    )


@dataclass
class CandidateAlertEntry:
    alert_id: str
    candidate_id: str
    alert_kind: str
    severity: str
    message: str
    resolved: bool
    alert_utc: str
    resolved_utc: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "candidate_id": self.candidate_id,
            "alert_kind": self.alert_kind,
            "severity": self.severity,
            "message": self.message,
            "resolved": self.resolved,
            "alert_utc": self.alert_utc,
            "resolved_utc": self.resolved_utc,
            "notes": self.notes,
        }


def load_alert_entries(
    fixture_path: Path | str | None = None,
) -> list[CandidateAlertEntry]:
    path = Path(fixture_path) if fixture_path is not None else _default_alert_fixture_path()
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = []
    for entry in data.get("candidate_alert_entries", []):
        entries.append(
            CandidateAlertEntry(
                alert_id=entry["alert_id"],
                candidate_id=entry["candidate_id"],
                alert_kind=entry["alert_kind"],
                severity=entry["severity"],
                message=entry["message"],
                resolved=bool(entry["resolved"]),
                alert_utc=entry["alert_utc"],
                resolved_utc=entry.get("resolved_utc"),
                notes=entry.get("notes", ""),
            )
        )
    return entries


def candidate_alert_summary(
    fixture_path: Path | str | None = None,
) -> dict[str, Any]:
    entries = load_alert_entries(fixture_path)
    by_severity: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    open_count = 0
    for e in entries:
        by_severity[e.severity] = by_severity.get(e.severity, 0) + 1
        by_kind[e.alert_kind] = by_kind.get(e.alert_kind, 0) + 1
        if not e.resolved:
            open_count += 1
    critical_open = sum(
        1 for e in entries if e.severity == "critical" and not e.resolved
    )
    return {
        "disclaimer": CANDIDATE_ALERT_DISCLAIMER,
        "schema_version": CANDIDATE_ALERT_SCHEMA_VERSION,
        "entry_count": len(entries),
        "open_count": open_count,
        "resolved_count": len(entries) - open_count,
        "critical_open_count": critical_open,
        "by_severity": by_severity,
        "by_kind": by_kind,
    }
