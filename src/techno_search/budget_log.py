"""Operational provenance records for budget allocation and expenditure events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BUDGET_LOG_SCHEMA_VERSION = "budget_log_v1"

ALLOWED_BUDGET_KINDS = frozenset(
    {
        "capital_expenditure",
        "contingency",
        "operational_expenditure",
        "project_budget",
        "travel_budget",
    }
)

ALLOWED_BUDGET_STATUSES = frozenset(
    {
        "allocated",
        "approved",
        "closed",
        "overspent",
    }
)

_DISCLAIMER = (
    "Budget log entries are operational provenance records only. "
    "A budget event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a "
    "detection claim."
)


def _default_fixture_path() -> Path:
    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "budget_log.json"


@dataclass(frozen=True)
class BudgetEntry:
    entry_id: str
    budget_kind: str
    status: str
    cost_center: str
    description: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.budget_kind not in ALLOWED_BUDGET_KINDS:
            raise ValueError(f"invalid budget_kind: {self.budget_kind!r}")
        if self.status not in ALLOWED_BUDGET_STATUSES:
            raise ValueError(f"invalid status: {self.status!r}")


def load_budget_entries(path: Path | None = None) -> list[BudgetEntry]:
    fixture_path = path if path is not None else _default_fixture_path()
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    return [
        BudgetEntry(
            entry_id=str(entry["entry_id"]),
            budget_kind=str(entry["budget_kind"]),
            status=str(entry["status"]),
            cost_center=str(entry["cost_center"]),
            description=str(entry["description"]),
            notes=str(entry.get("notes", "")),
        )
        for entry in raw["entries"]
    ]


def budget_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_budget_entries(path)
    approved_count = sum(1 for e in entries if e.status == "approved")
    return {
        "schema_version": BUDGET_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "approved_count": approved_count,
        "kind_counts": {
            kind: sum(1 for e in entries if e.budget_kind == kind)
            for kind in sorted(ALLOWED_BUDGET_KINDS)
        },
        "status_counts": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_BUDGET_STATUSES)
        },
    }
