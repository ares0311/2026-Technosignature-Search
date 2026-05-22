from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

WORKFLOW_STATE_SCHEMA_VERSION = "workflow_state_log_v1"

WORKFLOW_STATE_DISCLAIMER = (
    "Workflow state log entries are local scheduling coordination records only. "
    "A workflow state entry records a formal operator review state transition for "
    "a candidate review assignment — such as initial assignment, state change, "
    "reassignment, closure, or reopening. State transitions are local scheduling "
    "aids only. They do not modify candidate posteriors, scores, or pathway routing, "
    "do not authorize external submission, and do not constitute a detection claim."
)

ALLOWED_WORKFLOW_STATES = frozenset({
    "assigned",
    "in_review",
    "pending_second_opinion",
    "escalated",
    "closed",
    "deferred",
})

ALLOWED_WORKFLOW_TRANSITION_KINDS = frozenset({
    "initial_assign",
    "state_change",
    "reassign",
    "close",
    "reopen",
})


def _default_workflow_state_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "workflow_state_log.json"
    )


@dataclass
class WorkflowStateEntry:
    transition_id: str
    candidate_id: str
    transition_kind: str
    from_state: str | None
    to_state: str
    operator_id: str
    transitioned_utc: str
    assignment_id: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "candidate_id": self.candidate_id,
            "transition_kind": self.transition_kind,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "operator_id": self.operator_id,
            "transitioned_utc": self.transitioned_utc,
            "assignment_id": self.assignment_id,
            "notes": self.notes,
        }


def load_workflow_state_entries(
    fixture_path: Path | None = None,
) -> list[WorkflowStateEntry]:
    path = fixture_path or _default_workflow_state_path()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = []
    for raw in data.get("workflow_state_entries", []):
        entries.append(
            WorkflowStateEntry(
                transition_id=raw["transition_id"],
                candidate_id=raw["candidate_id"],
                transition_kind=raw["transition_kind"],
                from_state=raw.get("from_state"),
                to_state=raw["to_state"],
                operator_id=raw["operator_id"],
                transitioned_utc=raw["transitioned_utc"],
                assignment_id=raw.get("assignment_id"),
                notes=raw.get("notes", ""),
            )
        )
    return entries


def workflow_state_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_workflow_state_entries(fixture_path)
    by_to_state: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    candidates: set[str] = set()
    for e in entries:
        by_to_state[e.to_state] = by_to_state.get(e.to_state, 0) + 1
        by_kind[e.transition_kind] = by_kind.get(e.transition_kind, 0) + 1
        candidates.add(e.candidate_id)
    closed_count = by_to_state.get("closed", 0)
    open_count = sum(
        v for k, v in by_to_state.items() if k != "closed"
    )
    return {
        "schema_version": WORKFLOW_STATE_SCHEMA_VERSION,
        "disclaimer": WORKFLOW_STATE_DISCLAIMER,
        "entry_count": len(entries),
        "unique_candidate_count": len(candidates),
        "closed_count": closed_count,
        "open_transition_count": open_count,
        "by_to_state": by_to_state,
        "by_kind": by_kind,
    }
