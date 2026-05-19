"""Prioritized local action plan for operations-readiness blockers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

OPERATIONS_ACTION_PLAN_SCHEMA_VERSION = "operations_action_plan_v1"

OPERATIONS_ACTION_PLAN_DISCLAIMER = (
    "Operations action plans are local operator scheduling aids only. "
    "They translate operations-readiness blockers into review tasks before any "
    "real observation intake, live-provider workflow, or external submission is "
    "considered. They do not authorize live data access, external submission, "
    "detections, discoveries, or external validation."
)

ALLOWED_ACTION_PRIORITIES = frozenset({"critical", "high", "medium", "low"})
ALLOWED_ACTION_STATUSES = frozenset(
    {"open", "blocked_for_real_data", "operator_review_required"}
)
ALLOWED_ACTION_CATEGORIES = frozenset(
    {
        "quality_control",
        "capacity",
        "alerts",
        "review_deadlines",
        "pipeline_health",
        "validation_readiness",
        "curated_intake",
        "submission_provenance",
        "route_coverage",
        "sqlite_logs",
        "external_submission",
        "network_access",
    }
)


@dataclass(frozen=True)
class OperationsAction:
    action_id: str
    category: str
    priority: str
    status: str
    title: str
    required_action: str
    evidence_field: str
    blocker_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "title": self.title,
            "required_action": self.required_action,
            "evidence_field": self.evidence_field,
            "blocker_count": self.blocker_count,
        }


def _int_value(mapping: dict[str, Any], key: str) -> int:
    value = mapping.get(key, 0)
    return int(value) if isinstance(value, (int, float)) else 0


def _str_value(mapping: dict[str, Any], key: str, default: str = "unknown") -> str:
    value = mapping.get(key, default)
    return str(value)


def _append_action(
    actions: list[OperationsAction],
    *,
    category: str,
    priority: str,
    status: str,
    title: str,
    required_action: str,
    evidence_field: str,
    blocker_count: int,
) -> None:
    action_number = len(actions) + 1
    actions.append(
        OperationsAction(
            action_id=f"ops-action-{action_number:03d}",
            category=category,
            priority=priority,
            status=status,
            title=title,
            required_action=required_action,
            evidence_field=evidence_field,
            blocker_count=blocker_count,
        )
    )


def build_operations_actions(
    readiness_summary: dict[str, Any] | None = None,
) -> list[OperationsAction]:
    """Build prioritized actions from an operations-readiness summary."""

    if readiness_summary is None:
        from techno_search.operations_readiness import operations_readiness_summary

        readiness_summary = operations_readiness_summary()

    actions: list[OperationsAction] = []
    qc_health = _str_value(readiness_summary, "qc_overall_health")
    if qc_health == "blocked":
        _append_action(
            actions,
            category="quality_control",
            priority="critical",
            status="operator_review_required",
            title="Resolve blocked QC state",
            required_action=(
                "Review critical flags, escalations, and overdue items before "
                "advancing any candidate workflow."
            ),
            evidence_field="qc_overall_health",
            blocker_count=1,
        )
    elif qc_health == "degraded":
        _append_action(
            actions,
            category="quality_control",
            priority="high",
            status="operator_review_required",
            title="Review degraded QC state",
            required_action="Clear or acknowledge open QC issues before real-data planning.",
            evidence_field="qc_overall_health",
            blocker_count=1,
        )

    capacity_status = _str_value(readiness_summary, "pipeline_capacity_status")
    if capacity_status in {"strained", "overloaded"}:
        _append_action(
            actions,
            category="capacity",
            priority="high" if capacity_status == "overloaded" else "medium",
            status="operator_review_required",
            title=f"Reduce {capacity_status} pipeline capacity",
            required_action=(
                "Triage pending assignments, follow-up requests, and queue depth "
                "before adding new operational load."
            ),
            evidence_field="pipeline_capacity_status",
            blocker_count=1,
        )

    open_alert_count = _int_value(readiness_summary, "open_alert_count")
    critical_open_alert_count = _int_value(readiness_summary, "critical_open_alert_count")
    if open_alert_count:
        _append_action(
            actions,
            category="alerts",
            priority="critical" if critical_open_alert_count else "high",
            status="operator_review_required",
            title="Review open candidate alerts",
            required_action=(
                "Resolve, acknowledge, or downgrade open alert records without "
                "changing candidate scores automatically."
            ),
            evidence_field="open_alert_count",
            blocker_count=open_alert_count,
        )

    overdue_review_count = _int_value(
        readiness_summary, "overdue_review_deadline_count"
    )
    if overdue_review_count:
        _append_action(
            actions,
            category="review_deadlines",
            priority="high",
            status="operator_review_required",
            title="Clear overdue review deadlines",
            required_action=(
                "Complete, waive, or reschedule overdue local review obligations "
                "with notes preserved in the review log."
            ),
            evidence_field="overdue_review_deadline_count",
            blocker_count=overdue_review_count,
        )

    pipeline_blocked_count = _int_value(
        readiness_summary, "pipeline_health_blocked_count"
    )
    if pipeline_blocked_count:
        _append_action(
            actions,
            category="pipeline_health",
            priority="high",
            status="operator_review_required",
            title="Review pipeline blocked items",
            required_action=(
                "Inspect per-track pipeline health and document why each blocked "
                "item remains blocked or can be cleared."
            ),
            evidence_field="pipeline_health_blocked_count",
            blocker_count=pipeline_blocked_count,
        )

    validation_blockers = _int_value(
        readiness_summary, "validation_readiness_blocking_issue_count"
    )
    if validation_blockers:
        _append_action(
            actions,
            category="validation_readiness",
            priority="critical",
            status="blocked_for_real_data",
            title="Resolve validation-readiness blockers",
            required_action=(
                "Complete provenance, labeling, false-positive baseline, and "
                "external-review prerequisites before any real observation intake."
            ),
            evidence_field="validation_readiness_blocking_issue_count",
            blocker_count=validation_blockers,
        )

    intake_blockers = _int_value(
        readiness_summary, "curated_intake_blocking_issue_count"
    )
    if intake_blockers:
        _append_action(
            actions,
            category="curated_intake",
            priority="critical",
            status="blocked_for_real_data",
            title="Resolve curated-intake blockers",
            required_action=(
                "Keep non-synthetic intake blocked until licensing, provenance, "
                "labeling, and review requirements are satisfied."
            ),
            evidence_field="curated_intake_blocking_issue_count",
            blocker_count=intake_blockers,
        )

    missing_submission_fields = _int_value(
        readiness_summary, "submission_missing_provenance_field_count"
    )
    submission_blockers = _int_value(readiness_summary, "submission_blocking_issue_count")
    submission_total = missing_submission_fields + submission_blockers
    if submission_total:
        _append_action(
            actions,
            category="submission_provenance",
            priority="critical",
            status="blocked_for_real_data",
            title="Complete submission provenance prerequisites",
            required_action=(
                "Fill missing provenance fields and blocking issue documentation "
                "before any external handoff can be reviewed."
            ),
            evidence_field="submission_missing_provenance_field_count",
            blocker_count=submission_total,
        )

    route_uncovered = _int_value(readiness_summary, "route_uncovered_pathway_count")
    if route_uncovered:
        _append_action(
            actions,
            category="route_coverage",
            priority="high",
            status="open",
            title="Add missing synthetic route coverage",
            required_action=(
                "Add conservative synthetic fixtures for uncovered Pathway enum "
                "values without authorizing external workflow."
            ),
            evidence_field="route_uncovered_pathway_count",
            blocker_count=route_uncovered,
        )

    sqlite_snapshot_raw = readiness_summary.get("sqlite_log_snapshot", {})
    sqlite_snapshot = (
        sqlite_snapshot_raw if isinstance(sqlite_snapshot_raw, dict) else {}
    )
    if not bool(sqlite_snapshot.get("integrity_ok", False)):
        _append_action(
            actions,
            category="sqlite_logs",
            priority="critical",
            status="operator_review_required",
            title="Restore SQLite log integrity visibility",
            required_action=(
                "Initialize or repair the top-level SQLite log before relying on "
                "readiness summaries for operator handoff."
            ),
            evidence_field="sqlite_log_snapshot.integrity_ok",
            blocker_count=1,
        )
    if not bool(sqlite_snapshot.get("weekly_digest_ok", False)):
        _append_action(
            actions,
            category="sqlite_logs",
            priority="medium",
            status="operator_review_required",
            title="Restore SQLite weekly digest visibility",
            required_action=(
                "Generate or repair the review-safe SQLite weekly digest before "
                "weekly operator handoff."
            ),
            evidence_field="sqlite_log_snapshot.weekly_digest_ok",
            blocker_count=1,
        )

    external_approved = _int_value(
        readiness_summary, "external_submission_approved_count"
    )
    if external_approved:
        _append_action(
            actions,
            category="external_submission",
            priority="critical",
            status="blocked_for_real_data",
            title="Audit external submission approval records",
            required_action=(
                "Confirm every external-submission approval was explicitly entered "
                "by the user and has complete provenance."
            ),
            evidence_field="external_submission_approved_count",
            blocker_count=external_approved,
        )

    network_access = _int_value(readiness_summary, "network_access_allowed_count")
    if network_access:
        _append_action(
            actions,
            category="network_access",
            priority="critical",
            status="blocked_for_real_data",
            title="Audit logged network access",
            required_action=(
                "Review any logged network-enabled run before default local "
                "validation can be considered non-networked."
            ),
            evidence_field="network_access_allowed_count",
            blocker_count=network_access,
        )

    return actions


def operations_action_plan_summary(
    readiness_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an aggregate action plan for current local readiness blockers."""

    actions = build_operations_actions(readiness_summary)
    by_category: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for action in actions:
        by_category[action.category] = by_category.get(action.category, 0) + 1
        by_priority[action.priority] = by_priority.get(action.priority, 0) + 1
        by_status[action.status] = by_status.get(action.status, 0) + 1

    critical_count = by_priority.get("critical", 0)
    real_data_blocking_count = by_status.get("blocked_for_real_data", 0)
    operator_review_count = by_status.get("operator_review_required", 0)
    next_action = actions[0].as_dict() if actions else None

    return {
        "schema_version": OPERATIONS_ACTION_PLAN_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_ACTION_PLAN_DISCLAIMER,
        "action_count": len(actions),
        "critical_action_count": critical_count,
        "real_data_blocking_action_count": real_data_blocking_count,
        "operator_review_action_count": operator_review_count,
        "all_actions_clear": len(actions) == 0,
        "by_category": dict(sorted(by_category.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "by_status": dict(sorted(by_status.items())),
        "next_action": next_action,
        "actions": [action.as_dict() for action in actions],
    }
