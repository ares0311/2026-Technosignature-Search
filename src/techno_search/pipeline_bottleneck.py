"""Pipeline bottleneck analysis — identifies where candidates are stalling."""

from __future__ import annotations

from typing import Any

PIPELINE_BOTTLENECK_DISCLAIMER = (
    "Pipeline bottleneck summaries are local operational dashboards only. "
    "Stalled candidate counts identify scheduling or workflow delays — they do "
    "not reflect candidate scientific priority and do not constitute evidence of "
    "a technosignature. Bottleneck stage identification is a provenance aid for "
    "operator workflow management, not a scientific ranking or routing decision."
)


def pipeline_bottleneck_summary() -> dict[str, Any]:
    from techno_search.candidate_flags import load_candidate_flags
    from techno_search.candidate_lifecycle import load_lifecycle_entries
    from techno_search.escalation_log import load_escalation_entries
    from techno_search.operator_assignment import load_operator_assignments
    from techno_search.review_deadlines import load_review_deadlines

    lifecycle_entries = load_lifecycle_entries()
    flags = load_candidate_flags()
    deadlines = load_review_deadlines()
    assignments = load_operator_assignments()
    escalations = load_escalation_entries()

    _stalled_stages = {"under_review", "awaiting_confirmation", "follow_up_scheduled"}
    stalled = [e for e in lifecycle_entries if e.stage in _stalled_stages]

    stage_counts: dict[str, int] = {}
    for e in stalled:
        stage_counts[e.stage] = stage_counts.get(e.stage, 0) + 1

    per_track_stall: dict[str, int] = {}
    for e in stalled:
        per_track_stall[e.track] = per_track_stall.get(e.track, 0) + 1

    top_stage = max(stage_counts, key=lambda s: stage_counts[s]) if stage_counts else "none"

    overdue_count = sum(1 for d in deadlines if d.status == "overdue")

    _not_done = ("completed", "deferred")
    assigned_candidate_ids = {
        a.candidate_id for a in assignments if a.assignment_status not in _not_done
    }
    all_active_candidates = {
        e.candidate_id for e in lifecycle_entries if e.stage in _stalled_stages
    }
    unassigned_count = len(all_active_candidates - assigned_candidate_ids)

    critical_flag_count = sum(
        1 for f in flags if f.severity == "critical" and f.status == "open"
    )

    open_escalation_count = sum(
        1 for es in escalations if es.status in ("open", "in_review")
    )

    total_stalled = len(stalled)

    return {
        "disclaimer": PIPELINE_BOTTLENECK_DISCLAIMER,
        "total_stalled_candidates": total_stalled,
        "bottleneck_stages": dict(sorted(stage_counts.items())),
        "top_bottleneck_stage": top_stage,
        "overdue_review_count": overdue_count,
        "unassigned_candidate_count": unassigned_count,
        "critical_blocker_count": critical_flag_count,
        "open_escalation_count": open_escalation_count,
        "per_track_stall_counts": dict(sorted(per_track_stall.items())),
    }
