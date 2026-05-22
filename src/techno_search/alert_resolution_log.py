from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALERT_RESOLUTION_SCHEMA_VERSION = "alert_resolution_log_v1"

ALERT_RESOLUTION_DISCLAIMER = (
    "Alert resolution log entries are operational provenance records only. "
    "An alert resolution records how an open candidate alert was formally closed — "
    "through operator review, automated check, deadline expiry, or pathway confirmation. "
    "A resolved_follow_up status means follow-up was scheduled as a local scheduling "
    "action only. Alert resolution does not constitute a detection claim, authorize "
    "external submission, or modify scores or pathway routing."
)

ALLOWED_ALERT_RESOLUTION_STATUSES = frozenset(
    {
        "resolved_false_positive",
        "resolved_follow_up",
        "resolved_archived",
        "resolved_operator_closed",
        "open",
    }
)

ALLOWED_ALERT_RESOLUTION_KINDS = frozenset(
    {
        "operator_review",
        "automated_consistency_check",
        "deadline_expiry",
        "pathway_confirmed",
        "watchlist_action",
    }
)


def _default_alert_resolution_fixture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "alert_resolution_log.json"
    )


@dataclass
class AlertResolutionEntry:
    resolution_id: str
    candidate_id: str
    linked_alert_ids: list[str]
    status: str
    resolution_kind: str
    resolving_operator: str
    resolution_utc: str
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "resolution_id": self.resolution_id,
            "candidate_id": self.candidate_id,
            "linked_alert_ids": self.linked_alert_ids,
            "status": self.status,
            "resolution_kind": self.resolution_kind,
            "resolving_operator": self.resolving_operator,
            "resolution_utc": self.resolution_utc,
            "notes": self.notes,
        }


def load_alert_resolution_entries(
    fixture_path: Path | str | None = None,
) -> list[AlertResolutionEntry]:
    path = (
        Path(fixture_path)
        if fixture_path is not None
        else _default_alert_resolution_fixture_path()
    )
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = []
    for entry in data.get("alert_resolution_entries", []):
        entries.append(
            AlertResolutionEntry(
                resolution_id=entry["resolution_id"],
                candidate_id=entry["candidate_id"],
                linked_alert_ids=list(entry.get("linked_alert_ids", [])),
                status=entry["status"],
                resolution_kind=entry["resolution_kind"],
                resolving_operator=entry["resolving_operator"],
                resolution_utc=entry["resolution_utc"],
                notes=entry.get("notes", ""),
            )
        )
    return entries


def alert_resolution_summary(
    fixture_path: Path | str | None = None,
) -> dict[str, Any]:
    entries = load_alert_resolution_entries(fixture_path)
    by_status: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    open_count = 0
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_kind[e.resolution_kind] = by_kind.get(e.resolution_kind, 0) + 1
        if e.status == "open":
            open_count += 1
    return {
        "disclaimer": ALERT_RESOLUTION_DISCLAIMER,
        "schema_version": ALERT_RESOLUTION_SCHEMA_VERSION,
        "entry_count": len(entries),
        "open_count": open_count,
        "resolved_count": len(entries) - open_count,
        "by_status": by_status,
        "by_kind": by_kind,
    }
