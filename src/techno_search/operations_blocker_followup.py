"""Local follow-up rollups for reviewed operations blockers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.operations_blocker_detail import operations_blocker_detail_summary
from techno_search.operations_blocker_review import operations_blocker_review_summary

OPERATIONS_BLOCKER_FOLLOWUP_SCHEMA_VERSION = "operations_blocker_followup_v1"

OPERATIONS_BLOCKER_FOLLOWUP_DISCLAIMER = (
    "Operations blocker-followup summaries are local operator planning aids only. "
    "They derive next local actions from blocker-review provenance while preserving "
    "residual blockers, negative evidence, and disabled authorization gates. This "
    "summary does not clear blockers, authorize live data access, authorize "
    "external submission, or constitute detections, discoveries, or external "
    "validation."
)

ALLOWED_BLOCKER_FOLLOWUP_RECOMMENDATIONS = frozenset(
    {
        "operator_attention_required",
        "continue_local_remediation",
        "hold_for_real_data_evidence",
        "monitor_deferred_item",
        "verify_resolved_locally",
        "reopen_residual_blockers",
        "halt_for_authorization_review",
    }
)


@dataclass(frozen=True)
class OperationsBlockerFollowupAction:
    action_id: str
    category: str
    review_status: str
    recommendation: str
    residual_blocker_count: int
    reviewed_evidence_record_count: int
    detail_evidence_record_count: int
    evidence_review_complete: bool
    live_data_authorized: bool
    external_submission_authorized: bool
    note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "category": self.category,
            "review_status": self.review_status,
            "recommendation": self.recommendation,
            "residual_blocker_count": self.residual_blocker_count,
            "reviewed_evidence_record_count": self.reviewed_evidence_record_count,
            "detail_evidence_record_count": self.detail_evidence_record_count,
            "evidence_review_complete": self.evidence_review_complete,
            "live_data_authorized": self.live_data_authorized,
            "external_submission_authorized": self.external_submission_authorized,
            "note": self.note,
        }


def _recommendation_for(record: dict[str, Any]) -> str:
    if record.get("live_data_authorized") or record.get(
        "external_submission_authorized"
    ):
        return "halt_for_authorization_review"

    status = str(record.get("review_status", "open"))
    residual_count = int(record.get("residual_blocker_count", 0))
    if status == "blocked_for_real_data":
        return "hold_for_real_data_evidence"
    if status == "resolved" and residual_count == 0:
        return "verify_resolved_locally"
    if status == "resolved":
        return "reopen_residual_blockers"
    if status == "acknowledged":
        return "continue_local_remediation"
    if status == "deferred":
        return "monitor_deferred_item"
    return "operator_attention_required"


def _note_for(recommendation: str) -> str:
    return {
        "operator_attention_required": (
            "Open blocker-review item requires local operator attention before any "
            "status change is considered."
        ),
        "continue_local_remediation": (
            "Acknowledged blocker remains locally actionable and retains residual "
            "blocking evidence."
        ),
        "hold_for_real_data_evidence": (
            "Real-data intake remains blocked pending provenance, licensing, "
            "labeling, or external-review evidence."
        ),
        "monitor_deferred_item": (
            "Deferred blocker should remain visible in local review until a new "
            "operator decision is recorded."
        ),
        "verify_resolved_locally": (
            "Resolved workflow item is ready for local verification, but this "
            "does not clear scientific or external workflow gates."
        ),
        "reopen_residual_blockers": (
            "Resolved status conflicts with residual blockers and should be "
            "reopened for local review."
        ),
        "halt_for_authorization_review": (
            "Authorization flags are nonzero and require immediate review before "
            "any workflow continues."
        ),
    }[recommendation]


def _detail_counts(blocker_detail: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for detail in blocker_detail.get("details", []):
        if isinstance(detail, dict):
            action_id = str(detail.get("action_id", ""))
            if action_id:
                counts[action_id] = int(detail.get("record_count", 0))
    return counts


def _sort_key(action: OperationsBlockerFollowupAction) -> tuple[int, int, str]:
    priority = {
        "halt_for_authorization_review": 0,
        "operator_attention_required": 1,
        "hold_for_real_data_evidence": 2,
        "continue_local_remediation": 3,
        "reopen_residual_blockers": 4,
        "monitor_deferred_item": 5,
        "verify_resolved_locally": 6,
    }
    return (
        priority[action.recommendation],
        -action.residual_blocker_count,
        action.action_id,
    )


def operations_blocker_followup_summary(
    fixture_path: Path | None = None,
    *,
    blocker_detail_summary_data: dict[str, Any] | None = None,
    blocker_review_summary_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive local follow-up actions from blocker-review provenance."""

    blocker_detail = blocker_detail_summary_data or operations_blocker_detail_summary()
    blocker_review = blocker_review_summary_data or operations_blocker_review_summary(
        fixture_path,
        blocker_detail_summary=blocker_detail,
    )
    detail_counts = _detail_counts(blocker_detail)

    actions: list[OperationsBlockerFollowupAction] = []
    for record in blocker_review.get("records", []):
        if not isinstance(record, dict):
            continue
        action_id = str(record.get("action_id", ""))
        detail_record_count = detail_counts.get(action_id, 0)
        reviewed_record_count = int(record.get("reviewed_evidence_record_count", 0))
        recommendation = _recommendation_for(record)
        actions.append(
            OperationsBlockerFollowupAction(
                action_id=action_id,
                category=str(record.get("category", "")),
                review_status=str(record.get("review_status", "")),
                recommendation=recommendation,
                residual_blocker_count=int(record.get("residual_blocker_count", 0)),
                reviewed_evidence_record_count=reviewed_record_count,
                detail_evidence_record_count=detail_record_count,
                evidence_review_complete=reviewed_record_count >= detail_record_count,
                live_data_authorized=bool(record.get("live_data_authorized", False)),
                external_submission_authorized=bool(
                    record.get("external_submission_authorized", False)
                ),
                note=_note_for(recommendation),
            )
        )

    actions.sort(key=_sort_key)
    by_recommendation: dict[str, int] = {}
    for action in actions:
        by_recommendation[action.recommendation] = (
            by_recommendation.get(action.recommendation, 0) + 1
        )

    live_authorized_count = sum(1 for action in actions if action.live_data_authorized)
    external_authorized_count = sum(
        1 for action in actions if action.external_submission_authorized
    )
    residual_blocker_total = sum(action.residual_blocker_count for action in actions)
    evidence_review_complete = all(
        action.evidence_review_complete for action in actions
    )
    coverage_complete = bool(blocker_review.get("coverage_complete", False))
    all_detail_evidence_reviewed = bool(
        blocker_review.get("all_detail_evidence_reviewed", False)
    )

    return {
        "schema_version": OPERATIONS_BLOCKER_FOLLOWUP_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_BLOCKER_FOLLOWUP_DISCLAIMER,
        "action_count": len(actions),
        "action_required_count": sum(
            1
            for action in actions
            if action.recommendation != "verify_resolved_locally"
        ),
        "operator_attention_required_count": by_recommendation.get(
            "operator_attention_required", 0
        ),
        "local_remediation_count": by_recommendation.get(
            "continue_local_remediation", 0
        ),
        "real_data_hold_count": by_recommendation.get(
            "hold_for_real_data_evidence", 0
        ),
        "deferred_monitoring_count": by_recommendation.get(
            "monitor_deferred_item", 0
        ),
        "verification_ready_count": by_recommendation.get(
            "verify_resolved_locally", 0
        ),
        "reopen_required_count": by_recommendation.get(
            "reopen_residual_blockers", 0
        ),
        "authorization_review_required_count": by_recommendation.get(
            "halt_for_authorization_review", 0
        ),
        "residual_blocker_total": residual_blocker_total,
        "evidence_review_complete": evidence_review_complete,
        "coverage_complete": coverage_complete,
        "all_detail_evidence_reviewed": all_detail_evidence_reviewed,
        "live_data_authorized_count": live_authorized_count,
        "external_submission_authorized_count": external_authorized_count,
        "all_external_authorization_disabled": (
            live_authorized_count == 0 and external_authorized_count == 0
        ),
        "by_recommendation": dict(sorted(by_recommendation.items())),
        "next_action_ids": [
            action.action_id
            for action in actions
            if action.recommendation != "verify_resolved_locally"
        ],
        "verification_ready_action_ids": [
            action.action_id
            for action in actions
            if action.recommendation == "verify_resolved_locally"
        ],
        "real_data_hold_action_ids": [
            action.action_id
            for action in actions
            if action.recommendation == "hold_for_real_data_evidence"
        ],
        "actions": [action.as_dict() for action in actions],
    }
