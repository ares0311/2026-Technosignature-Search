"""Operations readiness dashboard for local-only project state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

OPERATIONS_READINESS_SCHEMA_VERSION = "operations_readiness_v1"

OPERATIONS_READINESS_DISCLAIMER = (
    "Operations readiness summaries are local operational dashboards only. "
    "They aggregate validation, review, SQLite-log, and scheduling state to surface "
    "blockers before any real observation intake or external workflow is considered. "
    "They do not authorize live-provider access, external submission, detections, "
    "discoveries, or external validation."
)

ALLOWED_OPERATIONS_READINESS_RECOMMENDATIONS = frozenset(
    {"local_only_ready", "operator_review_required", "blocked_for_real_data"}
)


def _int_value(mapping: dict[str, Any] | None, key: str, default: int = 0) -> int:
    if not isinstance(mapping, dict):
        return default
    value = mapping.get(key, default)
    return int(value) if isinstance(value, (int, float)) else default


def _bool_value(mapping: dict[str, Any] | None, key: str, default: bool = False) -> bool:
    if not isinstance(mapping, dict):
        return default
    value = mapping.get(key, default)
    return bool(value)


def _str_value(mapping: dict[str, Any] | None, key: str, default: str = "unknown") -> str:
    if not isinstance(mapping, dict):
        return default
    value = mapping.get(key, default)
    return str(value)


def _default_sqlite_snapshot(sqlite_log_path: Path | None) -> dict[str, Any]:
    from techno_search.log_store import (
        default_sqlite_log_path,
        sqlite_log_integrity_summary,
        sqlite_log_summary,
        sqlite_log_weekly_digest,
    )

    db_path = sqlite_log_path or default_sqlite_log_path(Path.cwd())
    if not db_path.exists():
        return {
            "log_path": str(db_path),
            "present": False,
            "run_count": 0,
            "network_access_allowed_count": 0,
            "external_submission_approved_count": 0,
            "integrity_ok": False,
            "weekly_digest_ok": False,
        }

    summary = sqlite_log_summary(db_path)
    integrity = sqlite_log_integrity_summary(db_path)
    weekly_digest = sqlite_log_weekly_digest(db_path)
    return {
        "log_path": str(db_path),
        "present": True,
        "run_count": _int_value(summary, "run_count"),
        "network_access_allowed_count": _int_value(
            summary, "network_access_allowed_count"
        ),
        "external_submission_approved_count": _int_value(
            summary, "external_submission_approved_count"
        ),
        "integrity_ok": _bool_value(integrity, "ok"),
        "weekly_digest_ok": _bool_value(weekly_digest, "ok"),
    }


def operations_readiness_summary(
    *,
    quality_control: dict[str, Any] | None = None,
    pipeline_capacity: dict[str, Any] | None = None,
    candidate_alerts: dict[str, Any] | None = None,
    review_deadlines: dict[str, Any] | None = None,
    pipeline_health: dict[str, Any] | None = None,
    route_coverage: dict[str, Any] | None = None,
    validation_readiness: dict[str, Any] | None = None,
    curated_intake: dict[str, Any] | None = None,
    submission_readiness: dict[str, Any] | None = None,
    user_decisions: dict[str, Any] | None = None,
    sqlite_logs: dict[str, Any] | None = None,
    sqlite_integrity: dict[str, Any] | None = None,
    sqlite_weekly_digest: dict[str, Any] | None = None,
    sqlite_log_path: Path | None = None,
) -> dict[str, Any]:
    """Aggregate local operational blockers without contacting live providers."""

    if quality_control is None:
        from techno_search.quality_control_summary import quality_control_summary

        quality_control = quality_control_summary()
    if pipeline_capacity is None:
        from techno_search.pipeline_capacity import pipeline_capacity_summary

        pipeline_capacity = pipeline_capacity_summary()
    if candidate_alerts is None:
        from techno_search.candidate_alert_log import candidate_alert_summary

        candidate_alerts = candidate_alert_summary()
    if review_deadlines is None:
        from techno_search.review_deadlines import review_deadlines_summary

        review_deadlines = review_deadlines_summary()
    if pipeline_health is None:
        from techno_search.pipeline_health import pipeline_health_summary

        pipeline_health = pipeline_health_summary()
    if route_coverage is None:
        from techno_search.baseline_eval import route_coverage_summary

        route_coverage = route_coverage_summary()
    if validation_readiness is None:
        from techno_search.validation_datasets import validation_readiness_summary

        validation_readiness = validation_readiness_summary()
    if curated_intake is None:
        from techno_search.curated_dataset_intake import curated_dataset_intake_summary

        curated_intake = curated_dataset_intake_summary()
    if submission_readiness is None:
        from techno_search.submission_readiness import submission_readiness_summary

        submission_readiness = submission_readiness_summary()
    if user_decisions is None:
        from techno_search.background_search import background_user_decision_summary

        user_decisions = background_user_decision_summary()

    if sqlite_logs is None or sqlite_integrity is None or sqlite_weekly_digest is None:
        sqlite_snapshot = _default_sqlite_snapshot(sqlite_log_path)
    else:
        sqlite_snapshot = {
            "log_path": str(sqlite_log_path) if sqlite_log_path is not None else None,
            "present": True,
            "run_count": _int_value(sqlite_logs, "run_count"),
            "network_access_allowed_count": _int_value(
                sqlite_logs, "network_access_allowed_count"
            ),
            "external_submission_approved_count": _int_value(
                sqlite_logs, "external_submission_approved_count"
            ),
            "integrity_ok": _bool_value(sqlite_integrity, "ok"),
            "weekly_digest_ok": _bool_value(sqlite_weekly_digest, "ok"),
        }

    qc_health = _str_value(quality_control, "overall_qc_health", "unknown")
    capacity_status = _str_value(pipeline_capacity, "capacity_status", "unknown")
    open_alert_count = _int_value(candidate_alerts, "open_count")
    critical_open_alert_count = _int_value(candidate_alerts, "critical_open_count")
    overdue_review_deadline_count = _int_value(review_deadlines, "overdue_count")
    pipeline_blocked_count = _int_value(pipeline_health, "total_blocked_count")
    route_uncovered_count = _int_value(route_coverage, "uncovered_pathway_count")
    validation_blocking_issue_count = _int_value(
        validation_readiness, "blocking_issue_count"
    )
    curated_intake_blocking_issue_count = _int_value(
        curated_intake, "total_blocking_issue_count"
    )
    submission_missing_field_count = _int_value(
        submission_readiness, "total_missing_provenance_field_count"
    )
    submission_blocking_issue_count = _int_value(
        submission_readiness, "total_blocking_issue_count"
    )
    user_external_approved = _int_value(
        user_decisions, "external_submission_approved_count"
    )
    sqlite_external_approved = _int_value(
        sqlite_snapshot, "external_submission_approved_count"
    )
    external_submission_approved_count = max(
        user_external_approved, sqlite_external_approved
    )
    network_access_allowed_count = _int_value(
        sqlite_snapshot, "network_access_allowed_count"
    )
    sqlite_integrity_ok = _bool_value(sqlite_snapshot, "integrity_ok")
    sqlite_weekly_digest_ok = _bool_value(sqlite_snapshot, "weekly_digest_ok")

    real_data_blocker_count = (
        route_uncovered_count
        + validation_blocking_issue_count
        + curated_intake_blocking_issue_count
        + submission_missing_field_count
        + submission_blocking_issue_count
        + external_submission_approved_count
        + network_access_allowed_count
    )
    operator_attention_count = (
        open_alert_count
        + overdue_review_deadline_count
        + pipeline_blocked_count
        + (1 if qc_health in {"degraded", "blocked"} else 0)
        + (1 if capacity_status in {"strained", "overloaded"} else 0)
    )

    outstanding_blockers: list[str] = []
    if qc_health == "blocked":
        outstanding_blockers.append("QC health is blocked")
    elif qc_health == "degraded":
        outstanding_blockers.append("QC health is degraded")
    if capacity_status in {"strained", "overloaded"}:
        outstanding_blockers.append(f"Pipeline capacity is {capacity_status}")
    if open_alert_count:
        outstanding_blockers.append(f"{open_alert_count} open candidate alert(s)")
    if critical_open_alert_count:
        outstanding_blockers.append(
            f"{critical_open_alert_count} critical open candidate alert(s)"
        )
    if overdue_review_deadline_count:
        outstanding_blockers.append(
            f"{overdue_review_deadline_count} overdue review deadline(s)"
        )
    if pipeline_blocked_count:
        outstanding_blockers.append(
            f"{pipeline_blocked_count} pipeline health blocked item(s)"
        )
    if validation_blocking_issue_count:
        outstanding_blockers.append(
            f"{validation_blocking_issue_count} validation readiness blocking issue(s)"
        )
    if curated_intake_blocking_issue_count:
        outstanding_blockers.append(
            f"{curated_intake_blocking_issue_count} curated intake blocking issue(s)"
        )
    if submission_missing_field_count:
        outstanding_blockers.append(
            f"{submission_missing_field_count} missing submission provenance field(s)"
        )
    if route_uncovered_count:
        outstanding_blockers.append(f"{route_uncovered_count} uncovered pathway route(s)")
    if external_submission_approved_count:
        outstanding_blockers.append(
            f"{external_submission_approved_count} external submission approval(s) recorded"
        )
    if network_access_allowed_count:
        outstanding_blockers.append(
            f"{network_access_allowed_count} SQLite log run(s) allowed network access"
        )
    if not sqlite_integrity_ok:
        outstanding_blockers.append("SQLite log integrity is not confirmed")
    if not sqlite_weekly_digest_ok:
        outstanding_blockers.append("SQLite weekly digest is not confirmed")

    if (
        real_data_blocker_count > 0
        or qc_health == "blocked"
        or critical_open_alert_count > 0
        or not sqlite_integrity_ok
    ):
        recommendation = "blocked_for_real_data"
    elif operator_attention_count > 0:
        recommendation = "operator_review_required"
    else:
        recommendation = "local_only_ready"

    readiness_gates = {
        "route_coverage_complete": route_uncovered_count == 0,
        "sqlite_integrity_ok": sqlite_integrity_ok,
        "sqlite_weekly_digest_ok": sqlite_weekly_digest_ok,
        "no_network_access_logged": network_access_allowed_count == 0,
        "no_external_submission_approval_logged": (
            external_submission_approved_count == 0
        ),
        "qc_not_blocked": qc_health != "blocked",
        "no_critical_open_alerts": critical_open_alert_count == 0,
    }
    local_validation_ready = all(readiness_gates.values())

    return {
        "schema_version": OPERATIONS_READINESS_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_READINESS_DISCLAIMER,
        "recommendation": recommendation,
        "local_validation_ready": local_validation_ready,
        "real_data_blocker_count": real_data_blocker_count,
        "operator_attention_count": operator_attention_count,
        "outstanding_blockers": outstanding_blockers,
        "readiness_gates": readiness_gates,
        "qc_overall_health": qc_health,
        "pipeline_capacity_status": capacity_status,
        "open_alert_count": open_alert_count,
        "critical_open_alert_count": critical_open_alert_count,
        "overdue_review_deadline_count": overdue_review_deadline_count,
        "pipeline_health_blocked_count": pipeline_blocked_count,
        "route_uncovered_pathway_count": route_uncovered_count,
        "validation_readiness_blocking_issue_count": validation_blocking_issue_count,
        "curated_intake_blocking_issue_count": curated_intake_blocking_issue_count,
        "submission_missing_provenance_field_count": submission_missing_field_count,
        "submission_blocking_issue_count": submission_blocking_issue_count,
        "external_submission_approved_count": external_submission_approved_count,
        "network_access_allowed_count": network_access_allowed_count,
        "sqlite_log_snapshot": sqlite_snapshot,
    }


def operations_readiness_digest(
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a review-safe Markdown digest for local operator handoff."""

    data = summary or operations_readiness_summary()
    blockers = data.get("outstanding_blockers", [])
    if not isinstance(blockers, list):
        blockers = []
    readiness_gates = data.get("readiness_gates", {})
    sqlite_integrity_ok = (
        bool(readiness_gates.get("sqlite_integrity_ok", False))
        if isinstance(readiness_gates, dict)
        else False
    )
    external_submission_approved_count = int(
        data.get("external_submission_approved_count", 0)
    )

    lines = [
        "# Operations Readiness Digest",
        "",
        OPERATIONS_READINESS_DISCLAIMER,
        "",
        f"- Recommendation: `{data.get('recommendation', 'unknown')}`",
        f"- Local validation ready: `{bool(data.get('local_validation_ready', False))}`",
        f"- Real-data blocker count: `{int(data.get('real_data_blocker_count', 0))}`",
        f"- Operator attention count: `{int(data.get('operator_attention_count', 0))}`",
        f"- Open alerts: `{int(data.get('open_alert_count', 0))}`",
        f"- Overdue review deadlines: `{int(data.get('overdue_review_deadline_count', 0))}`",
        f"- SQLite integrity ok: `{sqlite_integrity_ok}`",
        (
            "- External submission approvals logged: "
            f"`{external_submission_approved_count}`"
        ),
        f"- Network access logged: `{int(data.get('network_access_allowed_count', 0))}`",
        "",
        "## Outstanding Blockers",
    ]
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None recorded in local readiness inputs.")

    lines.extend(
        [
            "",
            "This digest is review-safe: it does not include large data payloads, "
            "API keys, live-provider results, or any claim of a confirmed technosignature.",
        ]
    )

    return {
        "schema_version": OPERATIONS_READINESS_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_READINESS_DISCLAIMER,
        "recommendation": data.get("recommendation", "unknown"),
        "markdown": "\n".join(lines),
    }
