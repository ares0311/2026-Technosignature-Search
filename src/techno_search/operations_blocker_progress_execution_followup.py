"""Local follow-up records for operations blocker progress-execution reviews."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.operations_blocker_progress_execution_review import (
    operations_blocker_progress_execution_review_summary,
)

OPERATIONS_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_SCHEMA_VERSION = (
    "operations_blocker_progress_execution_followup_v1"
)

OPERATIONS_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_DISCLAIMER = (
    "Operations blocker progress-execution follow-up records are local workflow "
    "planning notes for progress-execution review IDs only. They preserve "
    "residual blockers, verified-local exclusions, and disabled authorization "
    "gates. Execution follow-up does not clear blockers, authorize live data "
    "access, authorize external submission, or constitute detections, "
    "discoveries, or external validation."
)

ALLOWED_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_STATUSES = frozenset(
    {
        "operator_followup_required",
        "local_note_followup_ready",
        "blocked_pending_real_data",
        "policy_review_pending",
        "no_followup_required",
    }
)

EXPECTED_EXECUTION_FOLLOWUP_STATUSES = {
    "awaiting_operator_reviewed": "operator_followup_required",
    "execution_note_reviewed": "local_note_followup_ready",
    "blocked_pending_real_data_reviewed": "blocked_pending_real_data",
    "policy_review_pending": "policy_review_pending",
    "no_execution_required_reviewed": "no_followup_required",
}


def _default_execution_followup_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "operations_blocker_progress_execution_followup.json"
    )


@dataclass(frozen=True)
class OperationsBlockerProgressExecutionFollowupRecord:
    followup_id: str
    review_id: str
    execution_id: str
    next_action_id: str
    action_id: str
    category: str
    review_status: str
    followup_status: str
    priority_rank: int
    operator_id: str
    planned_utc: str
    followup_note: str
    residual_blocker_count: int
    live_data_authorized: bool
    external_submission_authorized: bool
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "followup_id": self.followup_id,
            "review_id": self.review_id,
            "execution_id": self.execution_id,
            "next_action_id": self.next_action_id,
            "action_id": self.action_id,
            "category": self.category,
            "review_status": self.review_status,
            "followup_status": self.followup_status,
            "priority_rank": self.priority_rank,
            "operator_id": self.operator_id,
            "planned_utc": self.planned_utc,
            "followup_note": self.followup_note,
            "residual_blocker_count": self.residual_blocker_count,
            "live_data_authorized": self.live_data_authorized,
            "external_submission_authorized": self.external_submission_authorized,
            "notes": self.notes,
        }


def load_operations_blocker_progress_execution_followup_records(
    fixture_path: Path | None = None,
) -> list[OperationsBlockerProgressExecutionFollowupRecord]:
    """Load local follow-up records for progress-execution reviews."""

    path = (
        fixture_path
        if fixture_path is not None
        else _default_execution_followup_path()
    )
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for item in raw.get("operations_blocker_progress_execution_followup_records", []):
        records.append(
            OperationsBlockerProgressExecutionFollowupRecord(
                followup_id=str(item["followup_id"]),
                review_id=str(item["review_id"]),
                execution_id=str(item["execution_id"]),
                next_action_id=str(item["next_action_id"]),
                action_id=str(item["action_id"]),
                category=str(item["category"]),
                review_status=str(item["review_status"]),
                followup_status=str(item["followup_status"]),
                priority_rank=int(item["priority_rank"]),
                operator_id=str(item["operator_id"]),
                planned_utc=str(item["planned_utc"]),
                followup_note=str(item["followup_note"]),
                residual_blocker_count=int(item["residual_blocker_count"]),
                live_data_authorized=bool(item["live_data_authorized"]),
                external_submission_authorized=bool(
                    item["external_submission_authorized"]
                ),
                notes=str(item.get("notes", "")),
            )
        )
    return sorted(records, key=lambda record: (record.priority_rank, record.action_id))


def _execution_review_records_by_id(
    execution_review_summary: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(execution_review_summary, dict):
        return {}
    records: dict[str, dict[str, Any]] = {}
    for record in execution_review_summary.get("records", []):
        if not isinstance(record, dict):
            continue
        review_id = str(record.get("review_id", ""))
        if review_id:
            records[review_id] = record
    return records


def operations_blocker_progress_execution_followup_summary(
    fixture_path: Path | None = None,
    *,
    expected_review_ids: Iterable[str] | None = None,
    blocker_progress_execution_review_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize local follow-up planning without clearing blockers."""

    records = load_operations_blocker_progress_execution_followup_records(fixture_path)
    execution_review_summary = (
        blocker_progress_execution_review_summary
        if blocker_progress_execution_review_summary is not None
        else operations_blocker_progress_execution_review_summary()
    )
    review_records = _execution_review_records_by_id(execution_review_summary)
    expected_ids = sorted(
        {
            str(review_id)
            for review_id in (
                expected_review_ids
                if expected_review_ids is not None
                else review_records.keys()
            )
        }
    )
    followup_review_ids = sorted({record.review_id for record in records})
    missing_ids = sorted(set(expected_ids) - set(followup_review_ids))
    stale_ids = (
        sorted(set(followup_review_ids) - set(expected_ids)) if expected_ids else []
    )
    expected_count = len(expected_ids)
    coverage_fraction = (
        round((expected_count - len(missing_ids)) / expected_count, 6)
        if expected_count
        else 1.0
    )

    by_status: dict[str, int] = {}
    by_review_status: dict[str, int] = {}
    by_category: dict[str, int] = {}
    by_operator: dict[str, int] = {}
    residual_blocker_total = 0
    live_authorized_count = 0
    external_authorized_count = 0
    status_mismatches = []
    residual_mismatches = []
    priority_mismatches = []
    priority_ranks = []

    for record in records:
        by_status[record.followup_status] = (
            by_status.get(record.followup_status, 0) + 1
        )
        by_review_status[record.review_status] = (
            by_review_status.get(record.review_status, 0) + 1
        )
        by_category[record.category] = by_category.get(record.category, 0) + 1
        by_operator[record.operator_id] = by_operator.get(record.operator_id, 0) + 1
        residual_blocker_total += record.residual_blocker_count
        priority_ranks.append(record.priority_rank)
        if record.live_data_authorized:
            live_authorized_count += 1
        if record.external_submission_authorized:
            external_authorized_count += 1

        review_record = review_records.get(record.review_id, {})
        expected_status = EXPECTED_EXECUTION_FOLLOWUP_STATUSES.get(
            record.review_status
        )
        review_status = str(review_record.get("review_status", ""))
        if (
            (expected_status and expected_status != record.followup_status)
            or (review_status and review_status != record.review_status)
            or (
                review_record
                and str(review_record.get("execution_id", "")) != record.execution_id
            )
            or (
                review_record
                and str(review_record.get("next_action_id", ""))
                != record.next_action_id
            )
            or (
                review_record
                and str(review_record.get("action_id", "")) != record.action_id
            )
        ):
            status_mismatches.append(
                {
                    "review_id": record.review_id,
                    "execution_id": record.execution_id,
                    "next_action_id": record.next_action_id,
                    "action_id": record.action_id,
                    "expected_followup_status": expected_status,
                    "followup_status": record.followup_status,
                    "expected_review_status": review_status,
                    "followup_review_status": record.review_status,
                }
            )

        expected_residual = review_record.get("residual_blocker_count")
        if expected_residual is not None and int(expected_residual) != (
            record.residual_blocker_count
        ):
            residual_mismatches.append(
                {
                    "review_id": record.review_id,
                    "expected_residual_blocker_count": int(expected_residual),
                    "followup_residual_blocker_count": (
                        record.residual_blocker_count
                    ),
                }
            )

        expected_priority = review_record.get("priority_rank")
        if expected_priority is not None and int(expected_priority) != (
            record.priority_rank
        ):
            priority_mismatches.append(
                {
                    "review_id": record.review_id,
                    "expected_priority_rank": int(expected_priority),
                    "followup_priority_rank": record.priority_rank,
                }
            )

    priority_sequence_ok = priority_ranks == sorted(priority_ranks) and len(
        priority_ranks
    ) == len(set(priority_ranks))
    verified_progress_action_ids = (
        list(execution_review_summary.get("verified_progress_action_ids", []))
        if isinstance(execution_review_summary, dict)
        else []
    )

    return {
        "schema_version": (
            OPERATIONS_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_SCHEMA_VERSION
        ),
        "disclaimer": OPERATIONS_BLOCKER_PROGRESS_EXECUTION_FOLLOWUP_DISCLAIMER,
        "record_count": len(records),
        "operator_followup_required_count": by_status.get(
            "operator_followup_required", 0
        ),
        "local_note_followup_ready_count": by_status.get(
            "local_note_followup_ready", 0
        ),
        "blocked_pending_real_data_count": by_status.get(
            "blocked_pending_real_data", 0
        ),
        "policy_review_pending_count": by_status.get("policy_review_pending", 0),
        "no_followup_required_count": by_status.get("no_followup_required", 0),
        "residual_blocker_total": residual_blocker_total,
        "live_data_authorized_count": live_authorized_count,
        "external_submission_authorized_count": external_authorized_count,
        "all_external_authorization_disabled": (
            live_authorized_count == 0 and external_authorized_count == 0
        ),
        "expected_review_count": expected_count,
        "covered_review_count": len(set(expected_ids) & set(followup_review_ids))
        if expected_ids
        else len(followup_review_ids),
        "missing_review_count": len(missing_ids),
        "stale_followup_count": len(stale_ids),
        "coverage_fraction": coverage_fraction,
        "coverage_complete": not missing_ids,
        "status_mismatch_count": len(status_mismatches),
        "status_mismatches": status_mismatches,
        "residual_mismatch_count": len(residual_mismatches),
        "residual_mismatches": residual_mismatches,
        "priority_mismatch_count": len(priority_mismatches),
        "priority_mismatches": priority_mismatches,
        "priority_sequence_ok": priority_sequence_ok,
        "missing_review_ids": missing_ids,
        "stale_followup_review_ids": stale_ids,
        "followup_ids": [record.followup_id for record in records],
        "review_ids": followup_review_ids,
        "execution_ids": sorted({record.execution_id for record in records}),
        "next_action_ids": sorted({record.next_action_id for record in records}),
        "action_ids": sorted({record.action_id for record in records}),
        "verified_progress_action_ids": verified_progress_action_ids,
        "by_status": dict(sorted(by_status.items())),
        "by_review_status": dict(sorted(by_review_status.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_operator": dict(sorted(by_operator.items())),
        "categories_covered": sorted({record.category for record in records}),
        "records": [record.as_dict() for record in records],
    }
