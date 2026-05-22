"""Progress notes for local operations blocker follow-up actions."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.operations_blocker_followup import operations_blocker_followup_summary

OPERATIONS_BLOCKER_FOLLOWUP_PROGRESS_SCHEMA_VERSION = (
    "operations_blocker_followup_progress_v1"
)

OPERATIONS_BLOCKER_FOLLOWUP_PROGRESS_DISCLAIMER = (
    "Operations blocker-followup progress records are local workflow notes only. "
    "They track progress against blocker-followup action IDs while preserving "
    "residual blockers and disabled authorization gates. Progress does not clear "
    "blockers, authorize live data access, authorize external submission, or "
    "constitute detections, discoveries, or external validation."
)

ALLOWED_BLOCKER_FOLLOWUP_PROGRESS_STATUSES = frozenset(
    {
        "not_started",
        "in_progress",
        "blocked",
        "waiting_for_real_data",
        "ready_for_local_verification",
        "verified_local",
    }
)


def _default_progress_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "operations_blocker_followup_progress.json"
    )


@dataclass(frozen=True)
class OperationsBlockerFollowupProgressRecord:
    progress_id: str
    action_id: str
    category: str
    recommendation: str
    progress_status: str
    operator_id: str
    progress_utc: str
    evidence_note: str
    residual_blocker_count: int
    live_data_authorized: bool
    external_submission_authorized: bool
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "progress_id": self.progress_id,
            "action_id": self.action_id,
            "category": self.category,
            "recommendation": self.recommendation,
            "progress_status": self.progress_status,
            "operator_id": self.operator_id,
            "progress_utc": self.progress_utc,
            "evidence_note": self.evidence_note,
            "residual_blocker_count": self.residual_blocker_count,
            "live_data_authorized": self.live_data_authorized,
            "external_submission_authorized": self.external_submission_authorized,
            "notes": self.notes,
        }


def load_operations_blocker_followup_progress_records(
    fixture_path: Path | None = None,
) -> list[OperationsBlockerFollowupProgressRecord]:
    """Load local blocker-followup progress records from a JSON fixture."""

    path = fixture_path if fixture_path is not None else _default_progress_path()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for item in raw.get("operations_blocker_followup_progress_records", []):
        records.append(
            OperationsBlockerFollowupProgressRecord(
                progress_id=str(item["progress_id"]),
                action_id=str(item["action_id"]),
                category=str(item["category"]),
                recommendation=str(item["recommendation"]),
                progress_status=str(item["progress_status"]),
                operator_id=str(item["operator_id"]),
                progress_utc=str(item["progress_utc"]),
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


def _expected_recommendations(
    followup_summary: dict[str, Any] | None,
) -> dict[str, str]:
    if not isinstance(followup_summary, dict):
        return {}
    recommendations: dict[str, str] = {}
    for action in followup_summary.get("actions", []):
        if not isinstance(action, dict):
            continue
        action_id = str(action.get("action_id", ""))
        if action_id:
            recommendations[action_id] = str(action.get("recommendation", ""))
    return recommendations


def operations_blocker_followup_progress_summary(
    fixture_path: Path | None = None,
    *,
    expected_action_ids: Iterable[str] | None = None,
    blocker_followup_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize local follow-up progress without clearing blockers."""

    records = load_operations_blocker_followup_progress_records(fixture_path)
    followup = blocker_followup_summary or operations_blocker_followup_summary()
    expected_recs = _expected_recommendations(followup)
    expected_ids = sorted(
        {str(action_id) for action_id in expected_action_ids or expected_recs}
    )
    progress_ids = sorted({record.action_id for record in records})
    missing_ids = sorted(set(expected_ids) - set(progress_ids))
    stale_ids = sorted(set(progress_ids) - set(expected_ids)) if expected_ids else []
    expected_count = len(expected_ids)
    coverage_fraction = (
        round((expected_count - len(missing_ids)) / expected_count, 6)
        if expected_count
        else 1.0
    )

    by_status: dict[str, int] = {}
    by_recommendation: dict[str, int] = {}
    by_operator: dict[str, int] = {}
    residual_blocker_total = 0
    live_authorized_count = 0
    external_authorized_count = 0
    recommendation_mismatches = []

    for record in records:
        by_status[record.progress_status] = (
            by_status.get(record.progress_status, 0) + 1
        )
        by_recommendation[record.recommendation] = (
            by_recommendation.get(record.recommendation, 0) + 1
        )
        by_operator[record.operator_id] = by_operator.get(record.operator_id, 0) + 1
        residual_blocker_total += record.residual_blocker_count
        if record.live_data_authorized:
            live_authorized_count += 1
        if record.external_submission_authorized:
            external_authorized_count += 1
        expected_recommendation = expected_recs.get(record.action_id)
        if expected_recommendation and expected_recommendation != record.recommendation:
            recommendation_mismatches.append(
                {
                    "action_id": record.action_id,
                    "expected_recommendation": expected_recommendation,
                    "progress_recommendation": record.recommendation,
                }
            )

    unresolved_statuses = {
        "not_started",
        "in_progress",
        "blocked",
        "waiting_for_real_data",
        "ready_for_local_verification",
    }
    unresolved_count = sum(by_status.get(status, 0) for status in unresolved_statuses)

    return {
        "schema_version": OPERATIONS_BLOCKER_FOLLOWUP_PROGRESS_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_BLOCKER_FOLLOWUP_PROGRESS_DISCLAIMER,
        "record_count": len(records),
        "not_started_count": by_status.get("not_started", 0),
        "in_progress_count": by_status.get("in_progress", 0),
        "blocked_count": by_status.get("blocked", 0),
        "waiting_for_real_data_count": by_status.get("waiting_for_real_data", 0),
        "ready_for_local_verification_count": by_status.get(
            "ready_for_local_verification", 0
        ),
        "verified_local_count": by_status.get("verified_local", 0),
        "unresolved_progress_count": unresolved_count,
        "residual_blocker_total": residual_blocker_total,
        "live_data_authorized_count": live_authorized_count,
        "external_submission_authorized_count": external_authorized_count,
        "all_external_authorization_disabled": (
            live_authorized_count == 0 and external_authorized_count == 0
        ),
        "expected_action_count": expected_count,
        "covered_action_count": len(set(expected_ids) & set(progress_ids))
        if expected_ids
        else len(progress_ids),
        "missing_action_count": len(missing_ids),
        "stale_progress_count": len(stale_ids),
        "coverage_fraction": coverage_fraction,
        "coverage_complete": not missing_ids,
        "recommendation_mismatch_count": len(recommendation_mismatches),
        "recommendation_mismatches": recommendation_mismatches,
        "missing_action_ids": missing_ids,
        "stale_progress_action_ids": stale_ids,
        "by_status": dict(sorted(by_status.items())),
        "by_recommendation": dict(sorted(by_recommendation.items())),
        "by_operator": dict(sorted(by_operator.items())),
        "action_ids": progress_ids,
        "categories_covered": sorted({record.category for record in records}),
        "records": [record.as_dict() for record in records],
    }
