"""Local next actions derived from unresolved operations blocker progress reviews."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.operations_blocker_progress_review import (
    operations_blocker_progress_review_summary,
)

OPERATIONS_BLOCKER_PROGRESS_NEXT_ACTIONS_SCHEMA_VERSION = (
    "operations_blocker_progress_next_actions_v1"
)

OPERATIONS_BLOCKER_PROGRESS_NEXT_ACTIONS_DISCLAIMER = (
    "Operations blocker progress next-action records are local workflow tasks "
    "derived from unresolved progress-review records only. They preserve "
    "residual blockers, verified-local exclusions, and disabled authorization "
    "gates. Next actions do not clear blockers, authorize live data access, "
    "authorize external submission, or constitute detections, discoveries, or "
    "external validation."
)

ALLOWED_BLOCKER_PROGRESS_NEXT_ACTION_STATUSES = frozenset(
    {
        "operator_action_required",
        "local_note_ready",
        "blocked_pending_real_data",
        "policy_review_required",
        "no_action_required",
    }
)

EXPECTED_NEXT_ACTION_STATUSES = {
    "needs_operator_action": "operator_action_required",
    "ready_for_next_local_note": "local_note_ready",
    "blocked_for_real_data": "blocked_pending_real_data",
    "waiting_on_policy": "policy_review_required",
    "verified_no_action": "no_action_required",
}


def _default_next_actions_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "operations_blocker_progress_next_actions.json"
    )


@dataclass(frozen=True)
class OperationsBlockerProgressNextActionRecord:
    next_action_id: str
    action_id: str
    review_id: str
    category: str
    review_status: str
    next_action_status: str
    priority_rank: int
    operator_id: str
    action_note: str
    residual_blocker_count: int
    live_data_authorized: bool
    external_submission_authorized: bool
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "next_action_id": self.next_action_id,
            "action_id": self.action_id,
            "review_id": self.review_id,
            "category": self.category,
            "review_status": self.review_status,
            "next_action_status": self.next_action_status,
            "priority_rank": self.priority_rank,
            "operator_id": self.operator_id,
            "action_note": self.action_note,
            "residual_blocker_count": self.residual_blocker_count,
            "live_data_authorized": self.live_data_authorized,
            "external_submission_authorized": self.external_submission_authorized,
            "notes": self.notes,
        }


def load_operations_blocker_progress_next_action_records(
    fixture_path: Path | None = None,
) -> list[OperationsBlockerProgressNextActionRecord]:
    """Load local next-action records derived from progress reviews."""

    path = fixture_path if fixture_path is not None else _default_next_actions_path()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for item in raw.get("operations_blocker_progress_next_action_records", []):
        records.append(
            OperationsBlockerProgressNextActionRecord(
                next_action_id=str(item["next_action_id"]),
                action_id=str(item["action_id"]),
                review_id=str(item["review_id"]),
                category=str(item["category"]),
                review_status=str(item["review_status"]),
                next_action_status=str(item["next_action_status"]),
                priority_rank=int(item["priority_rank"]),
                operator_id=str(item["operator_id"]),
                action_note=str(item["action_note"]),
                residual_blocker_count=int(item["residual_blocker_count"]),
                live_data_authorized=bool(item["live_data_authorized"]),
                external_submission_authorized=bool(
                    item["external_submission_authorized"]
                ),
                notes=str(item.get("notes", "")),
            )
        )
    return sorted(records, key=lambda record: (record.priority_rank, record.action_id))


def _review_records_by_action(
    progress_review_summary: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(progress_review_summary, dict):
        return {}
    records: dict[str, dict[str, Any]] = {}
    for record in progress_review_summary.get("records", []):
        if not isinstance(record, dict):
            continue
        action_id = str(record.get("action_id", ""))
        if action_id:
            records[action_id] = record
    return records


def operations_blocker_progress_next_actions_summary(
    fixture_path: Path | None = None,
    *,
    expected_action_ids: Iterable[str] | None = None,
    blocker_progress_review_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize local next actions without clearing progress-review blockers."""

    records = load_operations_blocker_progress_next_action_records(fixture_path)
    review_summary = (
        blocker_progress_review_summary
        if blocker_progress_review_summary is not None
        else operations_blocker_progress_review_summary()
    )
    review_records = _review_records_by_action(review_summary)
    expected_ids = sorted(
        {
            str(action_id)
            for action_id in (
                expected_action_ids
                if expected_action_ids is not None
                else review_records.keys()
            )
        }
    )
    action_ids = sorted({record.action_id for record in records})
    missing_ids = sorted(set(expected_ids) - set(action_ids))
    stale_ids = sorted(set(action_ids) - set(expected_ids)) if expected_ids else []
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
    priority_ranks = []

    for record in records:
        by_status[record.next_action_status] = (
            by_status.get(record.next_action_status, 0) + 1
        )
        by_category[record.category] = by_category.get(record.category, 0) + 1
        by_operator[record.operator_id] = by_operator.get(record.operator_id, 0) + 1
        residual_blocker_total += record.residual_blocker_count
        priority_ranks.append(record.priority_rank)
        if record.live_data_authorized:
            live_authorized_count += 1
        if record.external_submission_authorized:
            external_authorized_count += 1

        review_record = review_records.get(record.action_id, {})
        review_status = str(review_record.get("review_status", ""))
        review_id = str(review_record.get("review_id", ""))
        expected_status = EXPECTED_NEXT_ACTION_STATUSES.get(record.review_status)
        if (
            (expected_status and expected_status != record.next_action_status)
            or (review_status and review_status != record.review_status)
            or (review_id and review_id != record.review_id)
        ):
            status_mismatches.append(
                {
                    "action_id": record.action_id,
                    "expected_next_action_status": expected_status,
                    "next_action_status": record.next_action_status,
                    "expected_review_status": review_status,
                    "next_action_review_status": record.review_status,
                    "expected_review_id": review_id,
                    "next_action_review_id": record.review_id,
                }
            )

    priority_sequence_ok = priority_ranks == sorted(priority_ranks) and len(
        priority_ranks
    ) == len(set(priority_ranks))

    verified_progress_action_ids = (
        list(review_summary.get("verified_progress_action_ids", []))
        if isinstance(review_summary, dict)
        else []
    )

    return {
        "schema_version": OPERATIONS_BLOCKER_PROGRESS_NEXT_ACTIONS_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_BLOCKER_PROGRESS_NEXT_ACTIONS_DISCLAIMER,
        "record_count": len(records),
        "operator_action_required_count": by_status.get(
            "operator_action_required", 0
        ),
        "local_note_ready_count": by_status.get("local_note_ready", 0),
        "blocked_pending_real_data_count": by_status.get(
            "blocked_pending_real_data", 0
        ),
        "policy_review_required_count": by_status.get("policy_review_required", 0),
        "no_action_required_count": by_status.get("no_action_required", 0),
        "residual_blocker_total": residual_blocker_total,
        "live_data_authorized_count": live_authorized_count,
        "external_submission_authorized_count": external_authorized_count,
        "all_external_authorization_disabled": (
            live_authorized_count == 0 and external_authorized_count == 0
        ),
        "expected_action_count": expected_count,
        "covered_action_count": len(set(expected_ids) & set(action_ids))
        if expected_ids
        else len(action_ids),
        "missing_action_count": len(missing_ids),
        "stale_next_action_count": len(stale_ids),
        "coverage_fraction": coverage_fraction,
        "coverage_complete": not missing_ids,
        "status_mismatch_count": len(status_mismatches),
        "status_mismatches": status_mismatches,
        "priority_sequence_ok": priority_sequence_ok,
        "missing_action_ids": missing_ids,
        "stale_next_action_ids": stale_ids,
        "next_action_ids": [record.next_action_id for record in records],
        "action_ids": action_ids,
        "verified_progress_action_ids": verified_progress_action_ids,
        "by_status": dict(sorted(by_status.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_operator": dict(sorted(by_operator.items())),
        "categories_covered": sorted({record.category for record in records}),
        "records": [record.as_dict() for record in records],
    }
