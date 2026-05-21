"""Local reviews of operations blocker progress-execution notes."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.operations_blocker_progress_execution import (
    operations_blocker_progress_execution_summary,
)

OPERATIONS_BLOCKER_PROGRESS_EXECUTION_REVIEW_SCHEMA_VERSION = (
    "operations_blocker_progress_execution_review_v1"
)

OPERATIONS_BLOCKER_PROGRESS_EXECUTION_REVIEW_DISCLAIMER = (
    "Operations blocker progress-execution review records are local workflow "
    "review notes for progress-execution IDs only. They preserve residual "
    "blockers, verified-local exclusions, and disabled authorization gates. "
    "Execution reviews do not clear blockers, authorize live data access, "
    "authorize external submission, or constitute detections, discoveries, or "
    "external validation."
)

ALLOWED_BLOCKER_PROGRESS_EXECUTION_REVIEW_STATUSES = frozenset(
    {
        "awaiting_operator_reviewed",
        "execution_note_reviewed",
        "blocked_pending_real_data_reviewed",
        "policy_review_pending",
        "no_execution_required_reviewed",
    }
)

EXPECTED_EXECUTION_REVIEW_STATUSES = {
    "awaiting_operator": "awaiting_operator_reviewed",
    "local_note_recorded": "execution_note_reviewed",
    "blocked_pending_real_data": "blocked_pending_real_data_reviewed",
    "policy_review_pending": "policy_review_pending",
    "no_execution_required": "no_execution_required_reviewed",
}


def _default_execution_review_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "operations_blocker_progress_execution_review.json"
    )


@dataclass(frozen=True)
class OperationsBlockerProgressExecutionReviewRecord:
    review_id: str
    execution_id: str
    next_action_id: str
    action_id: str
    category: str
    execution_status: str
    review_status: str
    priority_rank: int
    reviewer_id: str
    reviewed_utc: str
    review_note: str
    residual_blocker_count: int
    live_data_authorized: bool
    external_submission_authorized: bool
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "execution_id": self.execution_id,
            "next_action_id": self.next_action_id,
            "action_id": self.action_id,
            "category": self.category,
            "execution_status": self.execution_status,
            "review_status": self.review_status,
            "priority_rank": self.priority_rank,
            "reviewer_id": self.reviewer_id,
            "reviewed_utc": self.reviewed_utc,
            "review_note": self.review_note,
            "residual_blocker_count": self.residual_blocker_count,
            "live_data_authorized": self.live_data_authorized,
            "external_submission_authorized": self.external_submission_authorized,
            "notes": self.notes,
        }


def load_operations_blocker_progress_execution_review_records(
    fixture_path: Path | None = None,
) -> list[OperationsBlockerProgressExecutionReviewRecord]:
    """Load local reviews for progress-execution records."""

    path = (
        fixture_path
        if fixture_path is not None
        else _default_execution_review_path()
    )
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for item in raw.get("operations_blocker_progress_execution_review_records", []):
        records.append(
            OperationsBlockerProgressExecutionReviewRecord(
                review_id=str(item["review_id"]),
                execution_id=str(item["execution_id"]),
                next_action_id=str(item["next_action_id"]),
                action_id=str(item["action_id"]),
                category=str(item["category"]),
                execution_status=str(item["execution_status"]),
                review_status=str(item["review_status"]),
                priority_rank=int(item["priority_rank"]),
                reviewer_id=str(item["reviewer_id"]),
                reviewed_utc=str(item["reviewed_utc"]),
                review_note=str(item["review_note"]),
                residual_blocker_count=int(item["residual_blocker_count"]),
                live_data_authorized=bool(item["live_data_authorized"]),
                external_submission_authorized=bool(
                    item["external_submission_authorized"]
                ),
                notes=str(item.get("notes", "")),
            )
        )
    return sorted(records, key=lambda record: (record.priority_rank, record.action_id))


def _execution_records_by_id(
    execution_summary: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(execution_summary, dict):
        return {}
    records: dict[str, dict[str, Any]] = {}
    for record in execution_summary.get("records", []):
        if not isinstance(record, dict):
            continue
        execution_id = str(record.get("execution_id", ""))
        if execution_id:
            records[execution_id] = record
    return records


def operations_blocker_progress_execution_review_summary(
    fixture_path: Path | None = None,
    *,
    expected_execution_ids: Iterable[str] | None = None,
    blocker_progress_execution_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize local reviews without clearing execution-note blockers."""

    records = load_operations_blocker_progress_execution_review_records(fixture_path)
    execution_summary = (
        blocker_progress_execution_summary
        if blocker_progress_execution_summary is not None
        else operations_blocker_progress_execution_summary()
    )
    execution_records = _execution_records_by_id(execution_summary)
    expected_ids = sorted(
        {
            str(execution_id)
            for execution_id in (
                expected_execution_ids
                if expected_execution_ids is not None
                else execution_records.keys()
            )
        }
    )
    reviewed_ids = sorted({record.execution_id for record in records})
    missing_ids = sorted(set(expected_ids) - set(reviewed_ids))
    stale_ids = sorted(set(reviewed_ids) - set(expected_ids)) if expected_ids else []
    expected_count = len(expected_ids)
    coverage_fraction = (
        round((expected_count - len(missing_ids)) / expected_count, 6)
        if expected_count
        else 1.0
    )

    by_status: dict[str, int] = {}
    by_execution_status: dict[str, int] = {}
    by_category: dict[str, int] = {}
    by_reviewer: dict[str, int] = {}
    residual_blocker_total = 0
    live_authorized_count = 0
    external_authorized_count = 0
    status_mismatches = []
    residual_mismatches = []
    priority_mismatches = []
    priority_ranks = []

    for record in records:
        by_status[record.review_status] = by_status.get(record.review_status, 0) + 1
        by_execution_status[record.execution_status] = (
            by_execution_status.get(record.execution_status, 0) + 1
        )
        by_category[record.category] = by_category.get(record.category, 0) + 1
        by_reviewer[record.reviewer_id] = by_reviewer.get(record.reviewer_id, 0) + 1
        residual_blocker_total += record.residual_blocker_count
        priority_ranks.append(record.priority_rank)
        if record.live_data_authorized:
            live_authorized_count += 1
        if record.external_submission_authorized:
            external_authorized_count += 1

        execution_record = execution_records.get(record.execution_id, {})
        expected_status = EXPECTED_EXECUTION_REVIEW_STATUSES.get(
            record.execution_status
        )
        execution_status = str(execution_record.get("execution_status", ""))
        if (
            (expected_status and expected_status != record.review_status)
            or (execution_status and execution_status != record.execution_status)
            or (
                execution_record
                and str(execution_record.get("next_action_id", ""))
                != record.next_action_id
            )
            or (
                execution_record
                and str(execution_record.get("action_id", "")) != record.action_id
            )
        ):
            status_mismatches.append(
                {
                    "execution_id": record.execution_id,
                    "next_action_id": record.next_action_id,
                    "action_id": record.action_id,
                    "expected_review_status": expected_status,
                    "review_status": record.review_status,
                    "expected_execution_status": execution_status,
                    "review_execution_status": record.execution_status,
                }
            )

        expected_residual = execution_record.get("residual_blocker_count")
        if expected_residual is not None and int(expected_residual) != (
            record.residual_blocker_count
        ):
            residual_mismatches.append(
                {
                    "execution_id": record.execution_id,
                    "expected_residual_blocker_count": int(expected_residual),
                    "review_residual_blocker_count": (
                        record.residual_blocker_count
                    ),
                }
            )

        expected_priority = execution_record.get("priority_rank")
        if expected_priority is not None and int(expected_priority) != (
            record.priority_rank
        ):
            priority_mismatches.append(
                {
                    "execution_id": record.execution_id,
                    "expected_priority_rank": int(expected_priority),
                    "review_priority_rank": record.priority_rank,
                }
            )

    priority_sequence_ok = priority_ranks == sorted(priority_ranks) and len(
        priority_ranks
    ) == len(set(priority_ranks))
    verified_progress_action_ids = (
        list(execution_summary.get("verified_progress_action_ids", []))
        if isinstance(execution_summary, dict)
        else []
    )

    return {
        "schema_version": (
            OPERATIONS_BLOCKER_PROGRESS_EXECUTION_REVIEW_SCHEMA_VERSION
        ),
        "disclaimer": OPERATIONS_BLOCKER_PROGRESS_EXECUTION_REVIEW_DISCLAIMER,
        "record_count": len(records),
        "awaiting_operator_reviewed_count": by_status.get(
            "awaiting_operator_reviewed", 0
        ),
        "execution_note_reviewed_count": by_status.get(
            "execution_note_reviewed", 0
        ),
        "blocked_pending_real_data_reviewed_count": by_status.get(
            "blocked_pending_real_data_reviewed", 0
        ),
        "policy_review_pending_count": by_status.get("policy_review_pending", 0),
        "no_execution_required_reviewed_count": by_status.get(
            "no_execution_required_reviewed", 0
        ),
        "residual_blocker_total": residual_blocker_total,
        "live_data_authorized_count": live_authorized_count,
        "external_submission_authorized_count": external_authorized_count,
        "all_external_authorization_disabled": (
            live_authorized_count == 0 and external_authorized_count == 0
        ),
        "expected_execution_count": expected_count,
        "covered_execution_count": len(set(expected_ids) & set(reviewed_ids))
        if expected_ids
        else len(reviewed_ids),
        "missing_execution_count": len(missing_ids),
        "stale_review_count": len(stale_ids),
        "coverage_fraction": coverage_fraction,
        "coverage_complete": not missing_ids,
        "status_mismatch_count": len(status_mismatches),
        "status_mismatches": status_mismatches,
        "residual_mismatch_count": len(residual_mismatches),
        "residual_mismatches": residual_mismatches,
        "priority_mismatch_count": len(priority_mismatches),
        "priority_mismatches": priority_mismatches,
        "priority_sequence_ok": priority_sequence_ok,
        "missing_execution_ids": missing_ids,
        "stale_review_execution_ids": stale_ids,
        "review_ids": [record.review_id for record in records],
        "execution_ids": reviewed_ids,
        "next_action_ids": sorted({record.next_action_id for record in records}),
        "action_ids": sorted({record.action_id for record in records}),
        "verified_progress_action_ids": verified_progress_action_ids,
        "by_status": dict(sorted(by_status.items())),
        "by_execution_status": dict(sorted(by_execution_status.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_reviewer": dict(sorted(by_reviewer.items())),
        "categories_covered": sorted({record.category for record in records}),
        "records": [record.as_dict() for record in records],
    }
