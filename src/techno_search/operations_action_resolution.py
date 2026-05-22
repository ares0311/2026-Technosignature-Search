"""Operations action-resolution records for local workflow provenance."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OPERATIONS_ACTION_RESOLUTION_SCHEMA_VERSION = "operations_action_resolution_v1"

OPERATIONS_ACTION_RESOLUTION_DISCLAIMER = (
    "Operations action-resolution records are local workflow provenance only. "
    "They document whether action-plan items are open, acknowledged, deferred, "
    "or resolved by an operator. Resolution does not authorize live data access, "
    "external submission, detections, discoveries, or external validation."
)

ALLOWED_ACTION_RESOLUTION_STATUSES = frozenset(
    {"open", "acknowledged", "deferred", "resolved"}
)


def _default_resolution_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "operations_action_resolution.json"
    )


@dataclass(frozen=True)
class OperationsActionResolutionRecord:
    resolution_id: str
    action_id: str
    category: str
    resolution_status: str
    operator_id: str
    resolution_utc: str
    evidence_note: str
    residual_blocker_count: int
    live_data_authorized: bool
    external_submission_authorized: bool
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "resolution_id": self.resolution_id,
            "action_id": self.action_id,
            "category": self.category,
            "resolution_status": self.resolution_status,
            "operator_id": self.operator_id,
            "resolution_utc": self.resolution_utc,
            "evidence_note": self.evidence_note,
            "residual_blocker_count": self.residual_blocker_count,
            "live_data_authorized": self.live_data_authorized,
            "external_submission_authorized": self.external_submission_authorized,
            "notes": self.notes,
        }


def load_operations_action_resolution_records(
    fixture_path: Path | None = None,
) -> list[OperationsActionResolutionRecord]:
    """Load local action-resolution records from a JSON fixture."""

    path = fixture_path if fixture_path is not None else _default_resolution_path()
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for item in raw.get("operations_action_resolution_records", []):
        records.append(
            OperationsActionResolutionRecord(
                resolution_id=str(item["resolution_id"]),
                action_id=str(item["action_id"]),
                category=str(item["category"]),
                resolution_status=str(item["resolution_status"]),
                operator_id=str(item["operator_id"]),
                resolution_utc=str(item["resolution_utc"]),
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


def operations_action_resolution_summary(
    fixture_path: Path | None = None,
    expected_action_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Summarize local action-resolution status without clearing blockers."""

    records = load_operations_action_resolution_records(fixture_path)
    expected_ids = sorted({str(action_id) for action_id in expected_action_ids or []})
    resolved_ids = sorted({record.action_id for record in records})
    missing_ids = sorted(set(expected_ids) - set(resolved_ids))
    stale_ids = sorted(set(resolved_ids) - set(expected_ids)) if expected_ids else []
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

    for record in records:
        by_status[record.resolution_status] = (
            by_status.get(record.resolution_status, 0) + 1
        )
        by_category[record.category] = by_category.get(record.category, 0) + 1
        by_operator[record.operator_id] = by_operator.get(record.operator_id, 0) + 1
        residual_blocker_total += record.residual_blocker_count
        if record.live_data_authorized:
            live_authorized_count += 1
        if record.external_submission_authorized:
            external_authorized_count += 1

    open_count = by_status.get("open", 0)
    acknowledged_count = by_status.get("acknowledged", 0)
    deferred_count = by_status.get("deferred", 0)
    resolved_count = by_status.get("resolved", 0)

    return {
        "schema_version": OPERATIONS_ACTION_RESOLUTION_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_ACTION_RESOLUTION_DISCLAIMER,
        "record_count": len(records),
        "open_count": open_count,
        "acknowledged_count": acknowledged_count,
        "deferred_count": deferred_count,
        "resolved_count": resolved_count,
        "residual_blocker_total": residual_blocker_total,
        "live_data_authorized_count": live_authorized_count,
        "external_submission_authorized_count": external_authorized_count,
        "all_external_authorization_disabled": (
            live_authorized_count == 0 and external_authorized_count == 0
        ),
        "expected_action_count": expected_count,
        "covered_action_count": len(set(expected_ids) & set(resolved_ids))
        if expected_ids
        else len(resolved_ids),
        "missing_action_count": len(missing_ids),
        "stale_resolution_count": len(stale_ids),
        "coverage_fraction": coverage_fraction,
        "coverage_complete": not missing_ids,
        "missing_action_ids": missing_ids,
        "stale_resolution_action_ids": stale_ids,
        "by_status": dict(sorted(by_status.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_operator": dict(sorted(by_operator.items())),
        "action_ids": sorted({record.action_id for record in records}),
        "categories_covered": sorted(by_category),
    }
