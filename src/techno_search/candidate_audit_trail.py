"""Candidate audit trail — append-only local provenance log of actions on candidates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_AUDIT_TRAIL_SCHEMA_VERSION = "candidate_audit_trail_v1"

CANDIDATE_AUDIT_TRAIL_DISCLAIMER = (
    "Audit trail entries are append-only local provenance records. "
    "They document operator actions taken on candidates for scheduling and "
    "reproducibility purposes only. They do not constitute external validation, "
    "detection claims, or discovery announcements."
)

ALLOWED_AUDIT_ACTION_TYPES = frozenset(
    {
        "triage_note_added",
        "stage_transition",
        "observation_scheduled",
        "observation_completed",
        "observation_cancelled",
        "archived",
        "human_reviewed",
    }
)


def _default_audit_trail_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "candidate_audit_trail.json"
    )


@dataclass
class CandidateAuditAction:
    action_id: str
    candidate_id: str
    action_type: str
    operator_id: str
    timestamp_utc: str
    detail: str
    is_reversible: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "candidate_id": self.candidate_id,
            "action_type": self.action_type,
            "operator_id": self.operator_id,
            "timestamp_utc": self.timestamp_utc,
            "detail": self.detail,
            "is_reversible": self.is_reversible,
        }


def load_audit_trail(
    fixture_path: Path | None = None,
) -> list[CandidateAuditAction]:
    path = fixture_path or _default_audit_trail_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    actions = []
    for raw in data.get("actions", []):
        actions.append(
            CandidateAuditAction(
                action_id=str(raw["action_id"]),
                candidate_id=str(raw["candidate_id"]),
                action_type=str(raw["action_type"]),
                operator_id=str(raw["operator_id"]),
                timestamp_utc=str(raw["timestamp_utc"]),
                detail=str(raw.get("detail", "")),
                is_reversible=bool(raw.get("is_reversible", True)),
            )
        )
    return actions


def audit_trail_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return a summary of the candidate audit trail."""

    actions = load_audit_trail(fixture_path)

    by_action_type: dict[str, int] = {}
    by_candidate: dict[str, int] = {}
    irreversible_count = 0

    for action in actions:
        by_action_type[action.action_type] = (
            by_action_type.get(action.action_type, 0) + 1
        )
        by_candidate[action.candidate_id] = (
            by_candidate.get(action.candidate_id, 0) + 1
        )
        if not action.is_reversible:
            irreversible_count += 1

    unique_operators = len({a.operator_id for a in actions})

    return {
        "schema_version": CANDIDATE_AUDIT_TRAIL_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_AUDIT_TRAIL_DISCLAIMER,
        "action_count": len(actions),
        "unique_candidate_count": len(by_candidate),
        "unique_operator_count": unique_operators,
        "irreversible_action_count": irreversible_count,
        "by_action_type": dict(sorted(by_action_type.items())),
        "by_candidate": dict(sorted(by_candidate.items())),
    }
