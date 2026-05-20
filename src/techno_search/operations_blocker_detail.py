"""Detailed local evidence for operations-readiness blocker actions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from techno_search.operations_action_plan import operations_action_plan_summary
from techno_search.operations_readiness import operations_readiness_summary

OPERATIONS_BLOCKER_DETAIL_SCHEMA_VERSION = "operations_blocker_detail_v1"

OPERATIONS_BLOCKER_DETAIL_DISCLAIMER = (
    "Operations blocker-detail summaries are local operator review aids only. "
    "They expand operations action-plan items into fixture-backed source records "
    "so blockers can be traced before any real observation intake, live-provider "
    "workflow, or external submission is considered. They do not clear blockers, "
    "authorize live data access, authorize external submission, or constitute "
    "detections, discoveries, or external validation."
)


def _record_count(records: list[dict[str, Any]]) -> int:
    return len(records)


def _sqlite_context(readiness_summary: dict[str, Any]) -> dict[str, Any]:
    snapshot = readiness_summary.get("sqlite_log_snapshot", {})
    sqlite_snapshot = snapshot if isinstance(snapshot, dict) else {}
    return {
        "category": "sqlite_logs",
        "present": bool(sqlite_snapshot.get("present", False)),
        "integrity_ok": bool(sqlite_snapshot.get("integrity_ok", False)),
        "weekly_digest_ok": bool(sqlite_snapshot.get("weekly_digest_ok", False)),
        "network_access_allowed_count": int(
            sqlite_snapshot.get("network_access_allowed_count", 0)
        ),
        "external_submission_approved_count": int(
            sqlite_snapshot.get("external_submission_approved_count", 0)
        ),
        "log_path": sqlite_snapshot.get("log_path"),
        "note": (
            "SQLite visibility is context for local operations readiness; it does "
            "not clear non-SQLite blockers."
        ),
    }


def _quality_control_detail() -> dict[str, Any]:
    from techno_search.candidate_flags import candidate_flags_summary, load_candidate_flags
    from techno_search.escalation_log import escalation_log_summary, load_escalation_entries
    from techno_search.quality_control_summary import quality_control_summary
    from techno_search.review_deadlines import load_review_deadlines

    flags = [
        flag.as_dict()
        for flag in load_candidate_flags()
        if flag.status == "open" or flag.severity == "critical"
    ]
    escalations = [
        entry.as_dict()
        for entry in load_escalation_entries()
        if entry.status in {"open", "in_review"} or entry.priority == "critical"
    ]
    overdue_deadlines = [
        deadline.as_dict()
        for deadline in load_review_deadlines()
        if deadline.status == "overdue"
    ]
    return {
        "source_summary": {
            "quality_control": quality_control_summary(),
            "candidate_flags": candidate_flags_summary(),
            "escalation_log": escalation_log_summary(),
        },
        "evidence_records": {
            "open_or_critical_flags": flags,
            "open_or_critical_escalations": escalations,
            "overdue_review_deadlines": overdue_deadlines,
        },
        "record_count": _record_count(flags)
        + _record_count(escalations)
        + _record_count(overdue_deadlines),
    }


def _capacity_detail() -> dict[str, Any]:
    from techno_search.candidate_annotation import candidate_annotation_summary
    from techno_search.follow_up_request import follow_up_request_summary
    from techno_search.operator_assignment import operator_assignment_summary
    from techno_search.pipeline_capacity import pipeline_capacity_summary

    return {
        "source_summary": {
            "pipeline_capacity": pipeline_capacity_summary(),
            "operator_assignment": operator_assignment_summary(),
            "follow_up_request": follow_up_request_summary(),
            "candidate_annotation": candidate_annotation_summary(),
        },
        "evidence_records": {},
        "record_count": 0,
    }


def _alerts_detail() -> dict[str, Any]:
    from techno_search.candidate_alert_log import (
        candidate_alert_summary,
        load_alert_entries,
    )

    open_alerts = [entry.as_dict() for entry in load_alert_entries() if not entry.resolved]
    return {
        "source_summary": {"candidate_alert_log": candidate_alert_summary()},
        "evidence_records": {"open_alerts": open_alerts},
        "record_count": _record_count(open_alerts),
    }


def _review_deadlines_detail() -> dict[str, Any]:
    from techno_search.review_deadlines import (
        load_review_deadlines,
        review_deadlines_summary,
    )

    deadlines = [
        deadline.as_dict()
        for deadline in load_review_deadlines()
        if deadline.status in {"overdue", "pending"}
    ]
    return {
        "source_summary": {"review_deadlines": review_deadlines_summary()},
        "evidence_records": {"overdue_or_pending_deadlines": deadlines},
        "record_count": _record_count(deadlines),
    }


def _pipeline_health_detail() -> dict[str, Any]:
    from techno_search.candidate_lifecycle import load_lifecycle_entries
    from techno_search.candidate_triage import load_triage_notes
    from techno_search.epoch_plan import load_epoch_plan
    from techno_search.operator_assignment import load_operator_assignments
    from techno_search.pipeline_health import pipeline_health_summary

    triage = [
        note.as_dict() for note in load_triage_notes() if note.blocking_reasons
    ]
    lifecycle = [
        entry.as_dict()
        for entry in load_lifecycle_entries()
        if entry.blocking_reasons
    ]
    assignments = [
        assignment.as_dict()
        for assignment in load_operator_assignments()
        if assignment.assignment_status in {"pending", "in_progress", "escalated"}
    ]
    epoch_requests = [
        entry.as_dict() for entry in load_epoch_plan() if entry.status == "pending"
    ]
    return {
        "source_summary": {"pipeline_health": pipeline_health_summary()},
        "evidence_records": {
            "triage_with_blockers": triage,
            "lifecycle_with_blockers": lifecycle,
            "active_or_escalated_assignments": assignments,
            "pending_epoch_requests": epoch_requests,
        },
        "record_count": _record_count(triage)
        + _record_count(lifecycle)
        + _record_count(assignments)
        + _record_count(epoch_requests),
    }


def _validation_readiness_detail() -> dict[str, Any]:
    from techno_search.validation_datasets import (
        load_validation_readiness_records,
        validation_readiness_summary,
    )

    records = [
        record
        for record in load_validation_readiness_records()
        if record.readiness_status != "ready"
        or record.blocking_issues
        or record.requires_external_review
    ]
    return {
        "source_summary": {"validation_readiness": validation_readiness_summary()},
        "evidence_records": {
            "records_requiring_review": [
                {
                    "readiness_id": record.readiness_id,
                    "dataset_id": record.dataset_id,
                    "track": record.track.value,
                    "readiness_status": record.readiness_status,
                    "evidence_requirements": list(record.evidence_requirements),
                    "satisfied_evidence": list(record.satisfied_evidence),
                    "blocking_issues": list(record.blocking_issues),
                    "requires_external_review": record.requires_external_review,
                    "promotion_target": record.promotion_target,
                }
                for record in records
            ]
        },
        "record_count": len(records),
    }


def _curated_intake_detail() -> dict[str, Any]:
    from techno_search.curated_dataset_intake import (
        curated_dataset_intake_summary,
        load_intake_records,
    )

    records = [
        record.as_dict()
        for record in load_intake_records()
        if record.intake_status != "approved" or record.blocking_issues
    ]
    return {
        "source_summary": {"curated_dataset_intake": curated_dataset_intake_summary()},
        "evidence_records": {"records_requiring_review": records},
        "record_count": _record_count(records),
    }


def _submission_provenance_detail() -> dict[str, Any]:
    from techno_search.submission_readiness import (
        load_submission_readiness_records,
        submission_readiness_summary,
    )

    records = [
        record.as_dict()
        for record in load_submission_readiness_records()
        if record.missing_provenance_fields or record.blocking_issues
    ]
    return {
        "source_summary": {"submission_readiness": submission_readiness_summary()},
        "evidence_records": {"records_with_missing_or_blocked_provenance": records},
        "record_count": _record_count(records),
    }


def _route_coverage_detail() -> dict[str, Any]:
    from techno_search.baseline_eval import route_coverage_summary

    return {
        "source_summary": {"route_coverage": route_coverage_summary()},
        "evidence_records": {},
        "record_count": 0,
    }


def _default_detail_for_category(
    category: str,
    readiness_summary: dict[str, Any],
) -> dict[str, Any]:
    if category == "quality_control":
        return _quality_control_detail()
    if category == "capacity":
        return _capacity_detail()
    if category == "alerts":
        return _alerts_detail()
    if category == "review_deadlines":
        return _review_deadlines_detail()
    if category == "pipeline_health":
        return _pipeline_health_detail()
    if category == "validation_readiness":
        return _validation_readiness_detail()
    if category == "curated_intake":
        return _curated_intake_detail()
    if category == "submission_provenance":
        return _submission_provenance_detail()
    if category == "route_coverage":
        return _route_coverage_detail()
    if category == "sqlite_logs":
        return {
            "source_summary": {"sqlite_context": _sqlite_context(readiness_summary)},
            "evidence_records": {},
            "record_count": 0,
        }
    return {
        "source_summary": {},
        "evidence_records": {},
        "record_count": 0,
    }


def operations_blocker_detail_summary(
    *,
    sqlite_log_path: Path | None = None,
    readiness_summary: dict[str, Any] | None = None,
    action_plan_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Expand operations actions into local source records for operator review."""

    readiness = readiness_summary or operations_readiness_summary(
        sqlite_log_path=sqlite_log_path
    )
    action_plan = action_plan_summary or operations_action_plan_summary(readiness)
    actions = [
        action for action in action_plan.get("actions", []) if isinstance(action, dict)
    ]
    details = []
    total_record_count = 0
    for action in actions:
        category = str(action.get("category", "unknown"))
        detail = _default_detail_for_category(category, readiness)
        total_record_count += int(detail["record_count"])
        details.append(
            {
                "action_id": str(action.get("action_id", "")),
                "category": category,
                "priority": str(action.get("priority", "unknown")),
                "status": str(action.get("status", "unknown")),
                "title": str(action.get("title", "")),
                "evidence_field": str(action.get("evidence_field", "")),
                "blocker_count": int(action.get("blocker_count", 0)),
                "required_action": str(action.get("required_action", "")),
                **detail,
            }
        )

    sqlite_context = _sqlite_context(readiness)
    network_access_allowed_count = int(
        readiness.get("network_access_allowed_count", 0)
    )
    external_submission_approved_count = int(
        readiness.get("external_submission_approved_count", 0)
    )
    return {
        "schema_version": OPERATIONS_BLOCKER_DETAIL_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_BLOCKER_DETAIL_DISCLAIMER,
        "action_count": len(actions),
        "detail_count": len(details),
        "total_evidence_record_count": total_record_count,
        "categories_with_details": sorted({detail["category"] for detail in details}),
        "local_only": True,
        "network_access_allowed_count": network_access_allowed_count,
        "external_submission_approved_count": external_submission_approved_count,
        "all_external_authorization_disabled": (
            network_access_allowed_count == 0
            and external_submission_approved_count == 0
        ),
        "readiness_recommendation": readiness.get("recommendation", "unknown"),
        "readiness_real_data_blocker_count": int(
            readiness.get("real_data_blocker_count", 0)
        ),
        "sqlite_visibility_context": sqlite_context,
        "sqlite_context_is_resolved": (
            sqlite_context["present"]
            and sqlite_context["integrity_ok"]
            and sqlite_context["weekly_digest_ok"]
            and sqlite_context["network_access_allowed_count"] == 0
            and sqlite_context["external_submission_approved_count"] == 0
        ),
        "details": details,
    }
