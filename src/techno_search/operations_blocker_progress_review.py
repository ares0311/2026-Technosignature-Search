"""Second-pass review of unresolved operations blocker progress records."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.operations_blocker_followup_progress import (
    operations_blocker_followup_progress_summary,
)

OPERATIONS_BLOCKER_PROGRESS_REVIEW_SCHEMA_VERSION = (
    "operations_blocker_progress_review_v1"
)

OPERATIONS_BLOCKER_PROGRESS_REVIEW_DISCLAIMER = (
    "Operations blocker progress-review records are local workflow review notes "
    "for unresolved blocker-followup progress only. They preserve residual "
    "blockers and disabled authorization gates. Progress review does not clear "
    "blockers, authorize live data access, authorize external submission, or "
    "constitute detections, discoveries, or external validation."
)

ALLOWED_BLOCKER_PROGRESS_REVIEW_STATUSES = frozenset(
    {
        "needs_operator_action",
        "ready_for_next_local_note",
        "waiting_on_policy",
        "blocked_for_real_data",
        "verified_no_action",
    }
)

EXPECTED_PROGRESS_REVIEW_STATUSES = {
    "not_started": "needs_operator_action",
    "blocked": "needs_operator_action",
    "in_progress": "ready_for_next_local_note",
    "ready_for_local_verification": "ready_for_next_local_note",
    "waiting_for_real_data": "blocked_for_real_data",
}


def _default_review_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "operations_blocker_progress_review.json"
    )


@dataclass(frozen=True)
class OperationsBlockerProgressReviewRecord:
    review_id: str
    action_id: str
    progress_id: str
    category: str
    progress_status: str
    review_status: str
    operator_id: str
    reviewed_utc: str
    review_note: str
    residual_blocker_count: int
    live_data_authorized: bool
    external_submission_authorized: bool
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "action_id": self.action_id,
            "progress_id": self.progress_id,
            "category": self.category,
            "progress_status": self.progress_status,
            "review_status": self.review_status,
            "operator_id": self.operator_id,
            "reviewed_utc": self.reviewed_utc,
            "review_note": self.review_note,
            "residual_blocker_count": self.residual_blocker_count,
            "live_data_authorized": self.live_data_authorized,
            "external_submission_authorized": self.external_submission_authorized,
            "notes": self.notes,
        }


def load_operations_blocker_progress_review_records(
    fixture_path: Path | None = None,
) -> list[OperationsBlockerProgressReviewRecord]:
    """Load local second-pass blocker-progress review records."""

    path = fixture_path if fixture_path is not None else _default_review_path()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for item in raw.get("operations_blocker_progress_review_records", []):
        records.append(
            OperationsBlockerProgressReviewRecord(
                review_id=str(item["review_id"]),
                action_id=str(item["action_id"]),
                progress_id=str(item["progress_id"]),
                category=str(item["category"]),
                progress_status=str(item["progress_status"]),
                review_status=str(item["review_status"]),
                operator_id=str(item["operator_id"]),
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
    return records


def _progress_records_by_action(
    progress_summary: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(progress_summary, dict):
        return {}
    records: dict[str, dict[str, Any]] = {}
    for record in progress_summary.get("records", []):
        if not isinstance(record, dict):
            continue
        action_id = str(record.get("action_id", ""))
        if action_id:
            records[action_id] = record
    return records


def _unresolved_action_ids(progress_summary: dict[str, Any] | None) -> list[str]:
    records = _progress_records_by_action(progress_summary)
    return sorted(
        action_id
        for action_id, record in records.items()
        if str(record.get("progress_status", "")) != "verified_local"
    )


def operations_blocker_progress_review_summary(
    fixture_path: Path | None = None,
    *,
    expected_action_ids: Iterable[str] | None = None,
    blocker_followup_progress_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize second-pass review of unresolved progress records."""

    records = load_operations_blocker_progress_review_records(fixture_path)
    progress_summary = (
        blocker_followup_progress_summary
        if blocker_followup_progress_summary is not None
        else operations_blocker_followup_progress_summary()
    )
    progress_records = _progress_records_by_action(progress_summary)
    expected_ids = sorted(
        {
            str(action_id)
            for action_id in (
                expected_action_ids
                if expected_action_ids is not None
                else _unresolved_action_ids(progress_summary)
            )
        }
    )
    reviewed_ids = sorted({record.action_id for record in records})
    missing_ids = sorted(set(expected_ids) - set(reviewed_ids))
    stale_ids = sorted(set(reviewed_ids) - set(expected_ids)) if expected_ids else []
    expected_count = len(expected_ids)
    coverage_fraction = (
        round((expected_count - len(missing_ids)) / expected_count, 6)
        if expected_count
        else 1.0
    )

    by_status: dict[str, int] = {}
    by_progress_status: dict[str, int] = {}
    by_operator: dict[str, int] = {}
    residual_blocker_total = 0
    live_authorized_count = 0
    external_authorized_count = 0
    status_mismatches = []

    for record in records:
        by_status[record.review_status] = by_status.get(record.review_status, 0) + 1
        by_progress_status[record.progress_status] = (
            by_progress_status.get(record.progress_status, 0) + 1
        )
        by_operator[record.operator_id] = by_operator.get(record.operator_id, 0) + 1
        residual_blocker_total += record.residual_blocker_count
        if record.live_data_authorized:
            live_authorized_count += 1
        if record.external_submission_authorized:
            external_authorized_count += 1
        expected_status = EXPECTED_PROGRESS_REVIEW_STATUSES.get(record.progress_status)
        progress_record = progress_records.get(record.action_id, {})
        progress_status = str(progress_record.get("progress_status", ""))
        progress_id = str(progress_record.get("progress_id", ""))
        if (
            expected_status
            and expected_status != record.review_status
            or progress_status
            and progress_status != record.progress_status
            or progress_id
            and progress_id != record.progress_id
        ):
            status_mismatches.append(
                {
                    "action_id": record.action_id,
                    "expected_review_status": expected_status,
                    "review_status": record.review_status,
                    "expected_progress_status": progress_status,
                    "review_progress_status": record.progress_status,
                    "expected_progress_id": progress_id,
                    "review_progress_id": record.progress_id,
                }
            )

    verified_progress_action_ids = sorted(
        action_id
        for action_id, record in progress_records.items()
        if str(record.get("progress_status", "")) == "verified_local"
    )

    return {
        "schema_version": OPERATIONS_BLOCKER_PROGRESS_REVIEW_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_BLOCKER_PROGRESS_REVIEW_DISCLAIMER,
        "record_count": len(records),
        "needs_operator_action_count": by_status.get("needs_operator_action", 0),
        "ready_for_next_local_note_count": by_status.get(
            "ready_for_next_local_note", 0
        ),
        "waiting_on_policy_count": by_status.get("waiting_on_policy", 0),
        "blocked_for_real_data_count": by_status.get("blocked_for_real_data", 0),
        "verified_no_action_count": by_status.get("verified_no_action", 0),
        "residual_blocker_total": residual_blocker_total,
        "live_data_authorized_count": live_authorized_count,
        "external_submission_authorized_count": external_authorized_count,
        "all_external_authorization_disabled": (
            live_authorized_count == 0 and external_authorized_count == 0
        ),
        "expected_action_count": expected_count,
        "covered_action_count": len(set(expected_ids) & set(reviewed_ids))
        if expected_ids
        else len(reviewed_ids),
        "missing_action_count": len(missing_ids),
        "stale_review_count": len(stale_ids),
        "coverage_fraction": coverage_fraction,
        "coverage_complete": not missing_ids,
        "status_mismatch_count": len(status_mismatches),
        "status_mismatches": status_mismatches,
        "missing_action_ids": missing_ids,
        "stale_review_action_ids": stale_ids,
        "reviewed_action_ids": reviewed_ids,
        "verified_progress_action_ids": verified_progress_action_ids,
        "by_status": dict(sorted(by_status.items())),
        "by_progress_status": dict(sorted(by_progress_status.items())),
        "by_operator": dict(sorted(by_operator.items())),
        "categories_covered": sorted({record.category for record in records}),
        "records": [record.as_dict() for record in records],
    }
