"""Operations blocker-review records for local evidence review provenance."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OPERATIONS_BLOCKER_REVIEW_SCHEMA_VERSION = "operations_blocker_review_v1"

OPERATIONS_BLOCKER_REVIEW_DISCLAIMER = (
    "Operations blocker-review records are local workflow provenance only. "
    "They document operator review status for blocker-detail evidence records. "
    "Review status does not clear blockers, authorize live data access, "
    "authorize external submission, detections, discoveries, or external validation."
)

ALLOWED_BLOCKER_REVIEW_STATUSES = frozenset(
    {"open", "acknowledged", "deferred", "resolved", "blocked_for_real_data"}
)


def _default_review_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "operations_blocker_review.json"
    )


@dataclass(frozen=True)
class OperationsBlockerReviewRecord:
    review_id: str
    action_id: str
    category: str
    review_status: str
    operator_id: str
    review_utc: str
    evidence_record_count: int
    reviewed_evidence_record_count: int
    evidence_note: str
    residual_blocker_count: int
    live_data_authorized: bool
    external_submission_authorized: bool
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "action_id": self.action_id,
            "category": self.category,
            "review_status": self.review_status,
            "operator_id": self.operator_id,
            "review_utc": self.review_utc,
            "evidence_record_count": self.evidence_record_count,
            "reviewed_evidence_record_count": self.reviewed_evidence_record_count,
            "evidence_note": self.evidence_note,
            "residual_blocker_count": self.residual_blocker_count,
            "live_data_authorized": self.live_data_authorized,
            "external_submission_authorized": self.external_submission_authorized,
            "notes": self.notes,
        }


def load_operations_blocker_review_records(
    fixture_path: Path | None = None,
) -> list[OperationsBlockerReviewRecord]:
    """Load local blocker-review records from a JSON fixture."""

    path = fixture_path if fixture_path is not None else _default_review_path()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for item in raw.get("operations_blocker_review_records", []):
        records.append(
            OperationsBlockerReviewRecord(
                review_id=str(item["review_id"]),
                action_id=str(item["action_id"]),
                category=str(item["category"]),
                review_status=str(item["review_status"]),
                operator_id=str(item["operator_id"]),
                review_utc=str(item["review_utc"]),
                evidence_record_count=int(item["evidence_record_count"]),
                reviewed_evidence_record_count=int(
                    item["reviewed_evidence_record_count"]
                ),
                evidence_note=str(item["evidence_note"]),
                residual_blocker_count=int(item["residual_blocker_count"]),
                live_data_authorized=bool(item["live_data_authorized"]),
                external_submission_authorized=bool(
                    item["external_submission_authorized"]
                ),
                notes=str(item.get("notes", "")),
            )
        )
    return records


def _expected_counts_from_detail(
    blocker_detail_summary: dict[str, Any] | None,
) -> dict[str, int]:
    if not isinstance(blocker_detail_summary, dict):
        return {}
    detail_counts: dict[str, int] = {}
    for detail in blocker_detail_summary.get("details", []):
        if not isinstance(detail, dict):
            continue
        action_id = str(detail.get("action_id", ""))
        if action_id:
            detail_counts[action_id] = int(detail.get("record_count", 0))
    return detail_counts


def operations_blocker_review_summary(
    fixture_path: Path | None = None,
    *,
    expected_action_ids: Iterable[str] | None = None,
    blocker_detail_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize local blocker-review status without clearing blockers."""

    records = load_operations_blocker_review_records(fixture_path)
    detail_counts = _expected_counts_from_detail(blocker_detail_summary)
    expected_ids = sorted(
        {str(action_id) for action_id in expected_action_ids or detail_counts}
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
    by_category: dict[str, int] = {}
    by_operator: dict[str, int] = {}
    residual_blocker_total = 0
    evidence_record_count = 0
    reviewed_evidence_record_count = 0
    live_authorized_count = 0
    external_authorized_count = 0

    for record in records:
        by_status[record.review_status] = by_status.get(record.review_status, 0) + 1
        by_category[record.category] = by_category.get(record.category, 0) + 1
        by_operator[record.operator_id] = by_operator.get(record.operator_id, 0) + 1
        residual_blocker_total += record.residual_blocker_count
        evidence_record_count += record.evidence_record_count
        reviewed_evidence_record_count += record.reviewed_evidence_record_count
        if record.live_data_authorized:
            live_authorized_count += 1
        if record.external_submission_authorized:
            external_authorized_count += 1

    detail_evidence_record_count = sum(detail_counts.values())
    unreviewed_evidence_record_count = max(
        detail_evidence_record_count - reviewed_evidence_record_count,
        0,
    )
    evidence_count_mismatches = [
        {
            "action_id": record.action_id,
            "detail_record_count": detail_counts.get(record.action_id, 0),
            "review_record_count": record.evidence_record_count,
        }
        for record in records
        if detail_counts and detail_counts.get(record.action_id, 0)
        != record.evidence_record_count
    ]

    return {
        "schema_version": OPERATIONS_BLOCKER_REVIEW_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_BLOCKER_REVIEW_DISCLAIMER,
        "record_count": len(records),
        "open_count": by_status.get("open", 0),
        "acknowledged_count": by_status.get("acknowledged", 0),
        "deferred_count": by_status.get("deferred", 0),
        "resolved_count": by_status.get("resolved", 0),
        "blocked_for_real_data_count": by_status.get("blocked_for_real_data", 0),
        "residual_blocker_total": residual_blocker_total,
        "evidence_record_count": evidence_record_count,
        "reviewed_evidence_record_count": reviewed_evidence_record_count,
        "detail_evidence_record_count": detail_evidence_record_count,
        "unreviewed_evidence_record_count": unreviewed_evidence_record_count,
        "evidence_count_mismatch_count": len(evidence_count_mismatches),
        "evidence_count_mismatches": evidence_count_mismatches,
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
        "all_detail_evidence_reviewed": (
            not missing_ids
            and not evidence_count_mismatches
            and unreviewed_evidence_record_count == 0
        ),
        "missing_action_ids": missing_ids,
        "stale_review_action_ids": stale_ids,
        "by_status": dict(sorted(by_status.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_operator": dict(sorted(by_operator.items())),
        "action_ids": sorted({record.action_id for record in records}),
        "categories_covered": sorted(by_category),
        "records": [record.as_dict() for record in records],
    }
