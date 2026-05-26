"""Consistency checks for local operations blocker-progress chains.

These checks keep local blocker-progress review, execution, and follow-up
records aligned without clearing blockers or authorizing live data or external
workflow.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from techno_search.operations_blocker_detail import operations_blocker_detail_summary
from techno_search.operations_blocker_followup import operations_blocker_followup_summary
from techno_search.operations_blocker_followup_progress import (
    operations_blocker_followup_progress_summary,
)
from techno_search.operations_blocker_progress_execution import (
    operations_blocker_progress_execution_summary,
)
from techno_search.operations_blocker_progress_execution_followup import (
    operations_blocker_progress_execution_followup_summary,
)
from techno_search.operations_blocker_progress_execution_review import (
    operations_blocker_progress_execution_review_summary,
)
from techno_search.operations_blocker_progress_next_actions import (
    operations_blocker_progress_next_actions_summary,
)
from techno_search.operations_blocker_progress_review import (
    operations_blocker_progress_review_summary,
)
from techno_search.operations_blocker_review import operations_blocker_review_summary

OPERATIONS_BLOCKER_PROGRESS_CONSISTENCY_SCHEMA_VERSION = (
    "operations_blocker_progress_consistency_v1"
)

OPERATIONS_BLOCKER_PROGRESS_CONSISTENCY_DISCLAIMER = (
    "Operations blocker-progress consistency checks are local workflow "
    "visibility gates only. They compare blocker-detail, review, follow-up, "
    "progress, next-action, execution, execution-review, and execution-follow-up "
    "records without clearing blockers, modifying candidate scores or pathway "
    "routing, authorizing live data access, authorizing external submission, or "
    "constituting detections, discoveries, or external validation."
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_expected_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "operations_blocker_progress_consistency.json"
    )


def load_operations_blocker_progress_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    expectation_path = path if path is not None else _default_expected_path()
    raw = json.loads(expectation_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_progress"])


def _count(summary: dict[str, Any], key: str) -> int:
    return int(summary.get(key, 0))


def _bool(summary: dict[str, Any], key: str) -> bool:
    return bool(summary.get(key, False))


def _strings(summary: dict[str, Any], key: str) -> list[str]:
    values = summary.get(key, [])
    if not isinstance(values, list):
        return []
    return sorted(str(value) for value in values)


def _summed_authorization_counts(
    summaries: list[dict[str, Any]],
) -> tuple[int, int]:
    live_count = 0
    external_count = 0
    for summary in summaries:
        live_count += _count(summary, "live_data_authorized_count")
        live_count += _count(summary, "network_access_allowed_count")
        external_count += _count(summary, "external_submission_authorized_count")
        external_count += _count(summary, "external_submission_approved_count")
    return live_count, external_count


def operations_blocker_progress_consistency_summary(
    expected_path: Path | None = None,
    *,
    blocker_detail: dict[str, Any] | None = None,
    blocker_review: dict[str, Any] | None = None,
    blocker_followup: dict[str, Any] | None = None,
    blocker_followup_progress: dict[str, Any] | None = None,
    blocker_progress_review: dict[str, Any] | None = None,
    blocker_progress_next_actions: dict[str, Any] | None = None,
    blocker_progress_execution: dict[str, Any] | None = None,
    blocker_progress_execution_review: dict[str, Any] | None = None,
    blocker_progress_execution_followup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = load_operations_blocker_progress_expectations(expected_path)

    detail_summary = (
        blocker_detail if blocker_detail is not None else operations_blocker_detail_summary()
    )
    review_summary = (
        blocker_review
        if blocker_review is not None
        else operations_blocker_review_summary(blocker_detail_summary=detail_summary)
    )
    followup_summary = (
        blocker_followup
        if blocker_followup is not None
        else operations_blocker_followup_summary(
            blocker_detail_summary_data=detail_summary,
            blocker_review_summary_data=review_summary,
        )
    )
    progress_summary = (
        blocker_followup_progress
        if blocker_followup_progress is not None
        else operations_blocker_followup_progress_summary(
            blocker_followup_summary=followup_summary,
        )
    )
    progress_review_summary = (
        blocker_progress_review
        if blocker_progress_review is not None
        else operations_blocker_progress_review_summary(
            blocker_followup_progress_summary=progress_summary,
        )
    )
    next_actions_summary = (
        blocker_progress_next_actions
        if blocker_progress_next_actions is not None
        else operations_blocker_progress_next_actions_summary(
            blocker_progress_review_summary=progress_review_summary,
        )
    )
    execution_summary = (
        blocker_progress_execution
        if blocker_progress_execution is not None
        else operations_blocker_progress_execution_summary(
            blocker_progress_next_actions_summary=next_actions_summary,
        )
    )
    execution_review_summary = (
        blocker_progress_execution_review
        if blocker_progress_execution_review is not None
        else operations_blocker_progress_execution_review_summary(
            blocker_progress_execution_summary=execution_summary,
        )
    )
    execution_followup_summary = (
        blocker_progress_execution_followup
        if blocker_progress_execution_followup is not None
        else operations_blocker_progress_execution_followup_summary(
            blocker_progress_execution_review_summary=execution_review_summary,
        )
    )

    progress_summaries = [
        review_summary,
        followup_summary,
        progress_summary,
        progress_review_summary,
        next_actions_summary,
        execution_summary,
        execution_review_summary,
        execution_followup_summary,
    ]
    authorization_summaries = [detail_summary, *progress_summaries]
    live_authorized_total, external_authorized_total = _summed_authorization_counts(
        authorization_summaries
    )

    expected_categories = sorted(str(item) for item in expected["categories_covered"])
    actual_categories = _strings(execution_followup_summary, "categories_covered")
    expected_verified_ids = sorted(
        str(item) for item in expected["verified_progress_action_ids"]
    )
    actual_verified_ids = _strings(
        execution_followup_summary,
        "verified_progress_action_ids",
    )
    expected_residual_total = int(expected["residual_blocker_total"])
    actual_residual_totals = {
        "review": _count(review_summary, "residual_blocker_total"),
        "followup": _count(followup_summary, "residual_blocker_total"),
        "progress": _count(progress_summary, "residual_blocker_total"),
        "progress_review": _count(progress_review_summary, "residual_blocker_total"),
        "next_actions": _count(next_actions_summary, "residual_blocker_total"),
        "execution": _count(execution_summary, "residual_blocker_total"),
        "execution_review": _count(execution_review_summary, "residual_blocker_total"),
        "execution_followup": _count(
            execution_followup_summary,
            "residual_blocker_total",
        ),
    }
    mismatch_total = sum(
        _count(summary, "status_mismatch_count")
        + _count(summary, "residual_mismatch_count")
        + _count(summary, "priority_mismatch_count")
        + _count(summary, "recommendation_mismatch_count")
        for summary in progress_summaries
    )
    coverage_complete = all(
        _bool(summary, "coverage_complete")
        for summary in [
            review_summary,
            followup_summary,
            progress_summary,
            progress_review_summary,
            next_actions_summary,
            execution_summary,
            execution_review_summary,
            execution_followup_summary,
        ]
    )
    priority_sequence_ok = all(
        _bool(summary, "priority_sequence_ok")
        for summary in [
            next_actions_summary,
            execution_summary,
            execution_review_summary,
            execution_followup_summary,
        ]
    )

    actual_counts = {
        "detail_count": _count(detail_summary, "detail_count"),
        "review_record_count": _count(review_summary, "record_count"),
        "followup_action_count": _count(followup_summary, "action_count"),
        "progress_record_count": _count(progress_summary, "record_count"),
        "unresolved_progress_count": _count(
            progress_summary,
            "unresolved_progress_count",
        ),
        "verified_local_count": _count(progress_summary, "verified_local_count"),
        "progress_review_record_count": _count(progress_review_summary, "record_count"),
        "next_action_record_count": _count(next_actions_summary, "record_count"),
        "execution_record_count": _count(execution_summary, "record_count"),
        "execution_review_record_count": _count(
            execution_review_summary,
            "record_count",
        ),
        "execution_followup_record_count": _count(
            execution_followup_summary,
            "record_count",
        ),
        "operator_followup_required_count": _count(
            execution_followup_summary,
            "operator_followup_required_count",
        ),
        "local_note_followup_ready_count": _count(
            execution_followup_summary,
            "local_note_followup_ready_count",
        ),
        "blocked_pending_real_data_count": _count(
            execution_followup_summary,
            "blocked_pending_real_data_count",
        ),
    }
    expected_counts = {
        "detail_count": int(expected["detail_count"]),
        "review_record_count": int(expected["review_record_count"]),
        "followup_action_count": int(expected["followup_action_count"]),
        "progress_record_count": int(expected["progress_record_count"]),
        "unresolved_progress_count": int(expected["unresolved_progress_count"]),
        "verified_local_count": int(expected["verified_local_count"]),
        "progress_review_record_count": int(expected["progress_review_record_count"]),
        "next_action_record_count": int(expected["next_action_record_count"]),
        "execution_record_count": int(expected["execution_record_count"]),
        "execution_review_record_count": int(expected["execution_review_record_count"]),
        "execution_followup_record_count": int(
            expected["execution_followup_record_count"]
        ),
        "operator_followup_required_count": int(
            expected["operator_followup_required_count"]
        ),
        "local_note_followup_ready_count": int(
            expected["local_note_followup_ready_count"]
        ),
        "blocked_pending_real_data_count": int(
            expected["blocked_pending_real_data_count"]
        ),
    }

    issues: list[str] = []
    for key, expected_value in expected_counts.items():
        actual_value = actual_counts[key]
        if actual_value != expected_value:
            issues.append(f"{key} {actual_value} != expected {expected_value}")
    for stage, actual_residual in actual_residual_totals.items():
        if actual_residual != expected_residual_total:
            issues.append(
                f"{stage} residual blocker total {actual_residual} "
                f"!= expected {expected_residual_total}"
            )
    if actual_categories != expected_categories:
        issues.append(
            f"categories covered {actual_categories!r} != expected {expected_categories!r}"
        )
    if actual_verified_ids != expected_verified_ids:
        issues.append(
            "verified progress action IDs "
            f"{actual_verified_ids!r} != expected {expected_verified_ids!r}"
        )
    if bool(expected.get("require_coverage_complete", True)) and not coverage_complete:
        issues.append("blocker-progress coverage is incomplete")
    if bool(expected.get("require_priority_sequence_ok", True)) and not priority_sequence_ok:
        issues.append("blocker-progress priority sequence is not strictly ordered")
    if bool(expected.get("require_zero_mismatches", True)) and mismatch_total:
        issues.append(f"blocker-progress mismatch count is nonzero: {mismatch_total}")
    if (
        bool(expected.get("require_zero_live_data_authorization", True))
        and live_authorized_total != 0
    ):
        issues.append("live data authorization count is nonzero")
    if (
        bool(expected.get("require_zero_external_authorization", True))
        and external_authorized_total != 0
    ):
        issues.append("external submission authorization count is nonzero")

    return {
        "schema_version": OPERATIONS_BLOCKER_PROGRESS_CONSISTENCY_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_BLOCKER_PROGRESS_CONSISTENCY_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_counts": expected_counts,
        "actual_counts": actual_counts,
        "expected_residual_blocker_total": expected_residual_total,
        "actual_residual_blocker_totals": actual_residual_totals,
        "expected_categories_covered": expected_categories,
        "actual_categories_covered": actual_categories,
        "expected_verified_progress_action_ids": expected_verified_ids,
        "actual_verified_progress_action_ids": actual_verified_ids,
        "coverage_complete": coverage_complete,
        "priority_sequence_ok": priority_sequence_ok,
        "mismatch_total": mismatch_total,
        "live_data_authorized_total": live_authorized_total,
        "external_submission_authorized_total": external_authorized_total,
    }
