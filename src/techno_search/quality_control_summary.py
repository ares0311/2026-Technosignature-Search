"""Quality control summary — aggregate QC dashboard across pipeline modules."""

from __future__ import annotations

from typing import Any

QUALITY_CONTROL_DISCLAIMER = (
    "Quality control summaries are local operational dashboards only. "
    "QC health status reflects internal scheduling and workflow state. "
    "'ok' does not mean candidates are confirmed or scientifically validated; "
    "'blocked' does not mean candidates are ruled out. All outputs are "
    "scheduling provenance records, not evidence of a technosignature."
)


def quality_control_summary() -> dict[str, Any]:
    from techno_search.candidate_flags import candidate_flags_summary
    from techno_search.candidate_resolution import candidate_resolution_summary
    from techno_search.candidate_retention import candidate_retention_summary
    from techno_search.candidate_triage import triage_summary
    escalation_log_summary: Any = lambda: {}  # noqa: E731
    from techno_search.review_deadlines import review_deadlines_summary

    flags = candidate_flags_summary()
    triage = triage_summary()
    deadlines = review_deadlines_summary()
    retention = candidate_retention_summary()
    resolution = candidate_resolution_summary()
    escalations = escalation_log_summary()

    total_open_flags = int(flags.get("open_count", 0))
    critical_flag_count = int(flags.get("critical_count", 0))

    triage_count = int(triage.get("note_count", 0))
    triage_cleared = int(triage.get("cleared_count", 0))
    triage_clearance_rate = (
        round(triage_cleared / triage_count, 3) if triage_count > 0 else 0.0
    )

    overdue_deadline_count = int(deadlines.get("overdue_count", 0))
    deadline_count = int(deadlines.get("deadline_count", 0))
    deadline_compliance_rate = (
        round(
            (deadline_count - overdue_deadline_count) / deadline_count, 3
        )
        if deadline_count > 0
        else 1.0
    )

    active_candidate_count = int(retention.get("active_count", 0))
    blocked_candidate_count = int(retention.get("blocked_count", 0))

    resolved_count = int(resolution.get("record_count", 0)) - int(
        resolution.get("unresolved_count", 0)
    )

    open_escalations = int(escalations.get("open_count", 0))
    critical_escalations = int(escalations.get("critical_count", 0))

    if critical_flag_count > 0 or critical_escalations > 0 or overdue_deadline_count > 2:
        overall_qc_health = "blocked"
    elif total_open_flags > 3 or open_escalations > 2 or overdue_deadline_count > 0:
        overall_qc_health = "degraded"
    else:
        overall_qc_health = "ok"

    return {
        "disclaimer": QUALITY_CONTROL_DISCLAIMER,
        "total_open_flags": total_open_flags,
        "critical_flag_count": critical_flag_count,
        "triage_clearance_rate": triage_clearance_rate,
        "overdue_deadline_count": overdue_deadline_count,
        "deadline_compliance_rate": deadline_compliance_rate,
        "active_candidate_count": active_candidate_count,
        "blocked_candidate_count": blocked_candidate_count,
        "resolved_count": resolved_count,
        "open_escalation_count": open_escalations,
        "critical_escalation_count": critical_escalations,
        "overall_qc_health": overall_qc_health,
    }
