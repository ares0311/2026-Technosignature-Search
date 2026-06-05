from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_MILESTONE_LOG_SCHEMA_VERSION = "project_milestone_log_v1"

ALLOWED_PROJECT_MILESTONE_KINDS = frozenset(
    {
        "checkpoint",
        "deliverable",
        "go_live",
        "phase_completion",
        "review_gate",
    }
)

ALLOWED_PROJECT_MILESTONE_STATUSES = frozenset(
    {
        "achieved",
        "at_risk",
        "deferred",
        "missed",
    }
)

_DISCLAIMER = (
    "Project milestone entries are operational provenance records — a project "
    "milestone event does not modify candidate scores or pathway routing, does not "
    "authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent / "tests" / "fixtures" / "project_milestone_log.json"
)


@dataclass(frozen=True)
class ProjectMilestoneEntry:
    entry_id: str
    milestone_kind: str
    status: str
    project_id: str
    description: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.milestone_kind not in ALLOWED_PROJECT_MILESTONE_KINDS:
            raise ValueError(
                f"invalid milestone_kind {self.milestone_kind!r}; "
                f"allowed: {sorted(ALLOWED_PROJECT_MILESTONE_KINDS)}"
            )
        if self.status not in ALLOWED_PROJECT_MILESTONE_STATUSES:
            raise ValueError(
                f"invalid status {self.status!r}; "
                f"allowed: {sorted(ALLOWED_PROJECT_MILESTONE_STATUSES)}"
            )


def load_project_milestone_entries(path: Path | None = None) -> list[ProjectMilestoneEntry]:
    fixture = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    return [
        ProjectMilestoneEntry(
            entry_id=e["entry_id"],
            milestone_kind=e["milestone_kind"],
            status=e["status"],
            project_id=e["project_id"],
            description=e["description"],
            notes=e.get("notes", ""),
        )
        for e in raw["entries"]
    ]


def project_milestone_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_project_milestone_entries(path)
    achieved_count = sum(1 for e in entries if e.status == "achieved")
    kind_counts = {k: 0 for k in ALLOWED_PROJECT_MILESTONE_KINDS}
    status_counts = {s: 0 for s in ALLOWED_PROJECT_MILESTONE_STATUSES}
    for e in entries:
        kind_counts[e.milestone_kind] += 1
        status_counts[e.status] += 1
    return {
        "schema_version": PROJECT_MILESTONE_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "achieved_count": achieved_count,
        "kind_counts": kind_counts,
        "status_counts": status_counts,
        "disclaimer": _DISCLAIMER,
    }
