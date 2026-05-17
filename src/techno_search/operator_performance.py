"""Operator performance — per-operator review statistics aggregated from assignments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

OPERATOR_PERFORMANCE_DISCLAIMER = (
    "Operator performance summaries are local scheduling and workflow metrics only. "
    "Completion rates, escalation rates, and review counts reflect operational "
    "workflow state in synthetic fixtures. They do not constitute personnel "
    "evaluations, scientific quality assessments, or external reporting metrics."
)


def operator_performance_summary(
    assignment_fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return per-operator review statistics from assignment records."""

    from techno_search.operator_assignment import (
        OperatorAssignment,
        load_operator_assignments,
    )

    raw_assignments: list[OperatorAssignment] = load_operator_assignments(
        assignment_fixture_path
    )

    by_operator: dict[str, dict[str, Any]] = {}
    for a in raw_assignments:
        op = a.operator_id
        if op not in by_operator:
            by_operator[op] = {
                "total": 0,
                "completed": 0,
                "escalated": 0,
                "deferred": 0,
                "pending": 0,
                "in_progress": 0,
                "tracks": set(),
            }
        by_operator[op]["total"] += 1
        status = a.assignment_status
        if status in by_operator[op]:
            by_operator[op][status] += 1
        by_operator[op]["tracks"].add(a.track)

    per_operator: list[dict[str, Any]] = []
    for op_id, stats in sorted(by_operator.items()):
        total = stats["total"]
        completed = stats["completed"]
        escalated = stats["escalated"]
        completion_rate = round(completed / total, 3) if total > 0 else 0.0
        escalation_rate = round(escalated / total, 3) if total > 0 else 0.0
        per_operator.append(
            {
                "operator_id": op_id,
                "total_assigned": total,
                "completed": completed,
                "escalated": escalated,
                "deferred": stats["deferred"],
                "pending": stats["pending"],
                "in_progress": stats["in_progress"],
                "completion_rate": completion_rate,
                "escalation_rate": escalation_rate,
                "tracks_covered": sorted(stats["tracks"]),
            }
        )

    total_assignments = len(raw_assignments)
    total_completed = sum(s["completed"] for s in by_operator.values())
    total_escalated = sum(s["escalated"] for s in by_operator.values())
    overall_completion_rate = (
        round(total_completed / total_assignments, 3) if total_assignments > 0 else 0.0
    )

    return {
        "disclaimer": OPERATOR_PERFORMANCE_DISCLAIMER,
        "operator_count": len(by_operator),
        "total_assignments": total_assignments,
        "total_completed": total_completed,
        "total_escalated": total_escalated,
        "overall_completion_rate": overall_completion_rate,
        "per_operator": per_operator,
    }
