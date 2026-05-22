"""Local execution notes for operations blocker progress next actions."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.operations_blocker_progress_next_actions import (
    operations_blocker_progress_next_actions_summary,
)

OPERATIONS_BLOCKER_PROGRESS_EXECUTION_SCHEMA_VERSION = (
    "operations_blocker_progress_execution_v1"
)

OPERATIONS_BLOCKER_PROGRESS_EXECUTION_DISCLAIMER = (
    "Operations blocker progress-execution records are local workflow execution "
    "notes for progress next-action IDs only. They preserve residual blockers, "
    "verified-local exclusions, and disabled authorization gates. Execution "
    "notes do not clear blockers, authorize live data access, authorize external "
    "submission, or constitute detections, discoveries, or external validation."
)

ALLOWED_BLOCKER_PROGRESS_EXECUTION_STATUSES = frozenset(
    {
        "awaiting_operator",
        "local_note_recorded",
        "blocked_pending_real_data",
        "policy_review_pending",
        "no_execution_required",
    }
)

EXPECTED_EXECUTION_STATUSES = {
    "operator_action_required": "awaiting_operator",
    "local_note_ready": "local_note_recorded",
    "blocked_pending_real_data": "blocked_pending_real_data",
    "policy_review_required": "policy_review_pending",
    "no_action_required": "no_execution_required",
}


def _default_execution_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "operations_blocker_progress_execution.json"
    )


@dataclass(frozen=True)
class OperationsBlockerProgressExecutionRecord:
    execution_id: str
    next_action_id: str
    action_id: str
    category: str
    next_action_status: str
    execution_status: str
    priority_rank: int
    operator_id: str
    executed_utc: str
    execution_note: str
    residual_blocker_count: int
    live_data_authorized: bool
    external_submission_authorized: bool
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "next_action_id": self.next_action_id,
            "action_id": self.action_id,
            "category": self.category,
            "next_action_status": self.next_action_status,
            "execution_status": self.execution_status,
            "priority_rank": self.priority_rank,
            "operator_id": self.operator_id,
            "executed_utc": self.executed_utc,
            "execution_note": self.execution_note,
            "residual_blocker_count": self.residual_blocker_count,
            "live_data_authorized": self.live_data_authorized,
            "external_submission_authorized": self.external_submission_authorized,
            "notes": self.notes,
        }


def load_operations_blocker_progress_execution_records(
    fixture_path: Path | None = None,
) -> list[OperationsBlockerProgressExecutionRecord]:
    """Load local execution records for progress next actions."""

    path = fixture_path if fixture_path is not None else _default_execution_path()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for item in raw.get("operations_blocker_progress_execution_records", []):
        records.append(
            OperationsBlockerProgressExecutionRecord(
                execution_id=str(item["execution_id"]),
                next_action_id=str(item["next_action_id"]),
                action_id=str(item["action_id"]),
                category=str(item["category"]),
                next_action_status=str(item["next_action_status"]),
                execution_status=str(item["execution_status"]),
                priority_rank=int(item["priority_rank"]),
                operator_id=str(item["operator_id"]),
                executed_utc=str(item["executed_utc"]),
                execution_note=str(item["execution_note"]),
                residual_blocker_count=int(item["residual_blocker_count"]),
                live_data_authorized=bool(item["live_data_authorized"]),
                external_submission_authorized=bool(
                    item["external_submission_authorized"]
                ),
                notes=str(item.get("notes", "")),
            )
        )
    return sorted(records, key=lambda record: (record.priority_rank, record.action_id))


def _next_action_records_by_id(
    next_actions_summary: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(next_actions_summary, dict):
        return {}
    records: dict[str, dict[str, Any]] = {}
    for record in next_actions_summary.get("records", []):
        if not isinstance(record, dict):
            continue
        next_action_id = str(record.get("next_action_id", ""))
        if next_action_id:
            records[next_action_id] = record
    return records


def operations_blocker_progress_execution_summary(
    fixture_path: Path | None = None,
    *,
    expected_next_action_ids: Iterable[str] | None = None,
    blocker_progress_next_actions_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize local execution notes without clearing next-action blockers."""

    records = load_operations_blocker_progress_execution_records(fixture_path)
    next_actions = (
        blocker_progress_next_actions_summary
        if blocker_progress_next_actions_summary is not None
        else operations_blocker_progress_next_actions_summary()
    )
    next_records = _next_action_records_by_id(next_actions)
    expected_ids = sorted(
        {
            str(next_action_id)
            for next_action_id in (
                expected_next_action_ids
                if expected_next_action_ids is not None
                else next_records.keys()
            )
        }
    )
    execution_ids = sorted({record.next_action_id for record in records})
    missing_ids = sorted(set(expected_ids) - set(execution_ids))
    stale_ids = sorted(set(execution_ids) - set(expected_ids)) if expected_ids else []
    expected_count = len(expected_ids)
    coverage_fraction = (
        round((expected_count - len(missing_ids)) / expected_count, 6)
        if expected_count
        else 1.0
    )

    by_status: dict[str, int] = {}
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
        by_status[record.execution_status] = (
            by_status.get(record.execution_status, 0) + 1
        )
        by_category[record.category] = by_category.get(record.category, 0) + 1
        by_operator[record.operator_id] = by_operator.get(record.operator_id, 0) + 1
        residual_blocker_total += record.residual_blocker_count
        priority_ranks.append(record.priority_rank)
        if record.live_data_authorized:
            live_authorized_count += 1
        if record.external_submission_authorized:
            external_authorized_count += 1

        next_record = next_records.get(record.next_action_id, {})
        next_status = str(next_record.get("next_action_status", ""))
        expected_status = EXPECTED_EXECUTION_STATUSES.get(record.next_action_status)
        if (
            (expected_status and expected_status != record.execution_status)
            or (next_status and next_status != record.next_action_status)
            or (
                next_record
                and str(next_record.get("action_id", "")) != record.action_id
            )
        ):
            status_mismatches.append(
                {
                    "next_action_id": record.next_action_id,
                    "action_id": record.action_id,
                    "expected_execution_status": expected_status,
                    "execution_status": record.execution_status,
                    "expected_next_action_status": next_status,
                    "execution_next_action_status": record.next_action_status,
                }
            )

        expected_residual = next_record.get("residual_blocker_count")
        if expected_residual is not None and int(expected_residual) != (
            record.residual_blocker_count
        ):
            residual_mismatches.append(
                {
                    "next_action_id": record.next_action_id,
                    "expected_residual_blocker_count": int(expected_residual),
                    "execution_residual_blocker_count": (
                        record.residual_blocker_count
                    ),
                }
            )

        expected_priority = next_record.get("priority_rank")
        if expected_priority is not None and int(expected_priority) != (
            record.priority_rank
        ):
            priority_mismatches.append(
                {
                    "next_action_id": record.next_action_id,
                    "expected_priority_rank": int(expected_priority),
                    "execution_priority_rank": record.priority_rank,
                }
            )

    priority_sequence_ok = priority_ranks == sorted(priority_ranks) and len(
        priority_ranks
    ) == len(set(priority_ranks))
    verified_progress_action_ids = (
        list(next_actions.get("verified_progress_action_ids", []))
        if isinstance(next_actions, dict)
        else []
    )

    return {
        "schema_version": OPERATIONS_BLOCKER_PROGRESS_EXECUTION_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_BLOCKER_PROGRESS_EXECUTION_DISCLAIMER,
        "record_count": len(records),
        "awaiting_operator_count": by_status.get("awaiting_operator", 0),
        "local_note_recorded_count": by_status.get("local_note_recorded", 0),
        "blocked_pending_real_data_count": by_status.get(
            "blocked_pending_real_data", 0
        ),
        "policy_review_pending_count": by_status.get("policy_review_pending", 0),
        "no_execution_required_count": by_status.get("no_execution_required", 0),
        "residual_blocker_total": residual_blocker_total,
        "live_data_authorized_count": live_authorized_count,
        "external_submission_authorized_count": external_authorized_count,
        "all_external_authorization_disabled": (
            live_authorized_count == 0 and external_authorized_count == 0
        ),
        "expected_next_action_count": expected_count,
        "covered_next_action_count": len(set(expected_ids) & set(execution_ids))
        if expected_ids
        else len(execution_ids),
        "missing_next_action_count": len(missing_ids),
        "stale_execution_count": len(stale_ids),
        "coverage_fraction": coverage_fraction,
        "coverage_complete": not missing_ids,
        "status_mismatch_count": len(status_mismatches),
        "status_mismatches": status_mismatches,
        "residual_mismatch_count": len(residual_mismatches),
        "residual_mismatches": residual_mismatches,
        "priority_mismatch_count": len(priority_mismatches),
        "priority_mismatches": priority_mismatches,
        "priority_sequence_ok": priority_sequence_ok,
        "missing_next_action_ids": missing_ids,
        "stale_execution_next_action_ids": stale_ids,
        "execution_ids": [record.execution_id for record in records],
        "next_action_ids": execution_ids,
        "action_ids": sorted({record.action_id for record in records}),
        "verified_progress_action_ids": verified_progress_action_ids,
        "by_status": dict(sorted(by_status.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_operator": dict(sorted(by_operator.items())),
        "categories_covered": sorted({record.category for record in records}),
        "records": [record.as_dict() for record in records],
    }
