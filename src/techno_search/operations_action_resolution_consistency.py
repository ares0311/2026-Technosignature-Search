"""Consistency checks for local operations action-resolution staleness.

These checks keep stale action-resolution records visible without clearing
blockers, changing action state, or authorizing live data or external work.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from techno_search.operations_action_plan import operations_action_plan_summary
from techno_search.operations_action_resolution import (
    operations_action_resolution_summary,
)

OPERATIONS_ACTION_RESOLUTION_CONSISTENCY_SCHEMA_VERSION = (
    "operations_action_resolution_consistency_v1"
)

OPERATIONS_ACTION_RESOLUTION_CONSISTENCY_DISCLAIMER = (
    "Operations action-resolution consistency checks are local workflow "
    "staleness visibility gates only. They compare current action-plan IDs "
    "against action-resolution records without clearing blockers, modifying "
    "candidate scores or pathway routing, authorizing live data access, "
    "authorizing external submission, or constituting detections, discoveries, "
    "or external validation."
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_expected_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "operations_action_resolution_consistency.json"
    )


def load_operations_action_resolution_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    expectation_path = path if path is not None else _default_expected_path()
    raw = json.loads(expectation_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_resolution"])


def _action_ids_from_plan(action_plan: dict[str, Any]) -> list[str]:
    actions = action_plan.get("actions", [])
    if not isinstance(actions, list):
        return []
    return sorted(
        str(action["action_id"])
        for action in actions
        if isinstance(action, dict) and "action_id" in action
    )


def operations_action_resolution_consistency_summary(
    expected_path: Path | None = None,
    *,
    resolution_fixture_path: Path | None = None,
    action_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = load_operations_action_resolution_expectations(expected_path)
    plan_summary = action_plan if action_plan is not None else operations_action_plan_summary()
    current_action_ids = _action_ids_from_plan(plan_summary)
    resolution_summary = operations_action_resolution_summary(
        resolution_fixture_path,
        expected_action_ids=current_action_ids,
    )

    expected_action_count = int(expected["expected_action_count"])
    expected_record_count = int(expected["record_count"])
    expected_stale_count = int(expected["stale_resolution_count"])
    expected_stale_ids = sorted(str(item) for item in expected["stale_resolution_action_ids"])
    expected_residual_total = int(expected["residual_blocker_total"])
    require_zero_external = bool(expected.get("require_zero_external_authorization", True))
    require_zero_live = bool(expected.get("require_zero_live_data_authorization", True))
    require_coverage_complete = bool(expected.get("require_coverage_complete", True))

    actual_action_count = int(resolution_summary["expected_action_count"])
    actual_record_count = int(resolution_summary["record_count"])
    actual_stale_count = int(resolution_summary["stale_resolution_count"])
    actual_stale_ids = sorted(
        str(item) for item in resolution_summary["stale_resolution_action_ids"]
    )
    actual_residual_total = int(resolution_summary["residual_blocker_total"])
    missing_action_count = int(resolution_summary["missing_action_count"])
    live_authorized_count = int(resolution_summary["live_data_authorized_count"])
    external_authorized_count = int(
        resolution_summary["external_submission_authorized_count"]
    )
    coverage_complete = bool(resolution_summary["coverage_complete"])

    issues: list[str] = []
    if actual_action_count != expected_action_count:
        issues.append(
            f"current action count {actual_action_count} != expected {expected_action_count}"
        )
    if actual_record_count != expected_record_count:
        issues.append(
            f"resolution record count {actual_record_count} != expected {expected_record_count}"
        )
    if actual_stale_count != expected_stale_count:
        issues.append(
            f"stale resolution count {actual_stale_count} != expected {expected_stale_count}"
        )
    if actual_stale_ids != expected_stale_ids:
        issues.append(
            "stale resolution action IDs "
            f"{actual_stale_ids!r} != expected {expected_stale_ids!r}"
        )
    if actual_residual_total != expected_residual_total:
        issues.append(
            "residual blocker total "
            f"{actual_residual_total} != expected {expected_residual_total}"
        )
    if require_coverage_complete and not coverage_complete:
        issues.append("action-resolution coverage is incomplete")
    if missing_action_count:
        issues.append(f"{missing_action_count} current action(s) lack resolution records")
    if require_zero_live and live_authorized_count != 0:
        issues.append("live data authorization count is nonzero")
    if require_zero_external and external_authorized_count != 0:
        issues.append("external submission authorization count is nonzero")

    return {
        "schema_version": OPERATIONS_ACTION_RESOLUTION_CONSISTENCY_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_ACTION_RESOLUTION_CONSISTENCY_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_action_count": expected_action_count,
        "actual_action_count": actual_action_count,
        "expected_record_count": expected_record_count,
        "actual_record_count": actual_record_count,
        "expected_stale_resolution_count": expected_stale_count,
        "actual_stale_resolution_count": actual_stale_count,
        "expected_stale_resolution_action_ids": expected_stale_ids,
        "actual_stale_resolution_action_ids": actual_stale_ids,
        "expected_residual_blocker_total": expected_residual_total,
        "actual_residual_blocker_total": actual_residual_total,
        "coverage_complete": coverage_complete,
        "missing_action_count": missing_action_count,
        "missing_action_ids": resolution_summary["missing_action_ids"],
        "live_data_authorized_count": live_authorized_count,
        "external_submission_authorized_count": external_authorized_count,
        "current_action_ids": current_action_ids,
        "resolution_action_ids": resolution_summary["action_ids"],
    }
