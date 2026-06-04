from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROBLEM_MANAGEMENT_LOG_SCHEMA_VERSION = "problem_management_log_v1"

ALLOWED_PROBLEM_MANAGEMENT_KINDS = frozenset({
    "hardware",
    "infrastructure",
    "process",
    "security",
    "software",
})

ALLOWED_PROBLEM_MANAGEMENT_STATUSES = frozenset({
    "closed",
    "identified",
    "resolved",
    "under_investigation",
})

_DISCLAIMER = (
    "Problem management entries are operational provenance records — a problem"
    " management event does not modify candidate scores or pathway routing, does not"
    " authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "problem_management_log.json"
)


@dataclass(frozen=True)
class ProblemManagementEntry:
    entry_id: str
    problem_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str

    def __post_init__(self) -> None:
        if self.problem_kind not in ALLOWED_PROBLEM_MANAGEMENT_KINDS:
            raise ValueError(
                f"problem_kind {self.problem_kind!r} not in"
                f" {sorted(ALLOWED_PROBLEM_MANAGEMENT_KINDS)}"
            )
        if self.status not in ALLOWED_PROBLEM_MANAGEMENT_STATUSES:
            raise ValueError(
                f"status {self.status!r} not in"
                f" {sorted(ALLOWED_PROBLEM_MANAGEMENT_STATUSES)}"
            )


def load_problem_management_entries(
    fixture_path: Path | None = None,
) -> list[ProblemManagementEntry]:
    path = fixture_path or _DEFAULT_FIXTURE
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        ProblemManagementEntry(
            entry_id=e["entry_id"],
            problem_kind=e["problem_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes", ""),
        )
        for e in data["entries"]
    ]


def problem_management_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_problem_management_entries(fixture_path)
    resolved_count = sum(1 for e in entries if e.status == "resolved")
    return {
        "schema_version": PROBLEM_MANAGEMENT_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "resolved_count": resolved_count,
        "disclaimer": _DISCLAIMER,
    }
