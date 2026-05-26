"""Consistency checks for local alert and QC operator-review state.

These checks keep alert/QC review blockers visible without clearing blockers,
changing scores, or authorizing live data or external submission.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from techno_search.alert_resolution_log import (
    alert_resolution_summary,
    load_alert_resolution_entries,
)
from techno_search.candidate_alert_log import candidate_alert_summary, load_alert_entries
from techno_search.operations_readiness import operations_readiness_summary
from techno_search.quality_control_summary import quality_control_summary

OPERATIONS_ALERT_REVIEW_CONSISTENCY_SCHEMA_VERSION = (
    "operations_alert_review_consistency_v1"
)

OPERATIONS_ALERT_REVIEW_CONSISTENCY_DISCLAIMER = (
    "Operations alert review consistency checks are local operator-review "
    "visibility gates only. They preserve open-alert, QC, and readiness blocker "
    "state without clearing blockers, modifying candidate scores or pathway "
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
        / "operations_alert_review_consistency.json"
    )


def load_operations_alert_review_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    expectation_path = path if path is not None else _default_expected_path()
    raw = json.loads(expectation_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_review"])


def _int_value(mapping: dict[str, Any], key: str) -> int:
    value = mapping.get(key, 0)
    return int(value) if isinstance(value, (int, float)) else 0


def _str_value(mapping: dict[str, Any], key: str, default: str = "unknown") -> str:
    value = mapping.get(key, default)
    return str(value)


def operations_alert_review_consistency_summary(
    expected_path: Path | None = None,
    *,
    alert_fixture_path: Path | str | None = None,
    resolution_fixture_path: Path | str | None = None,
    quality_control: dict[str, Any] | None = None,
    readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = load_operations_alert_review_expectations(expected_path)
    alerts = candidate_alert_summary(alert_fixture_path)
    resolutions = alert_resolution_summary(resolution_fixture_path)
    alert_entries = load_alert_entries(alert_fixture_path)
    resolution_entries = load_alert_resolution_entries(resolution_fixture_path)
    qc_summary = quality_control if quality_control is not None else quality_control_summary()
    readiness_summary = readiness if readiness is not None else operations_readiness_summary()

    open_alert_ids = sorted(entry.alert_id for entry in alert_entries if not entry.resolved)
    critical_open_alert_ids = sorted(
        entry.alert_id
        for entry in alert_entries
        if entry.severity == "critical" and not entry.resolved
    )
    linked_alert_ids = {
        alert_id for entry in resolution_entries for alert_id in entry.linked_alert_ids
    }
    open_resolution_linked_alert_ids = {
        alert_id
        for entry in resolution_entries
        if entry.status == "open"
        for alert_id in entry.linked_alert_ids
    }
    uncovered_open_alert_ids = [
        alert_id for alert_id in open_alert_ids if alert_id not in linked_alert_ids
    ]
    uncovered_critical_alert_ids = [
        alert_id
        for alert_id in critical_open_alert_ids
        if alert_id not in open_resolution_linked_alert_ids
    ]

    alert_open_count = _int_value(alerts, "open_count")
    alert_critical_open_count = _int_value(alerts, "critical_open_count")
    resolution_open_count = _int_value(resolutions, "open_count")
    qc_health = _str_value(qc_summary, "overall_qc_health")
    readiness_open_count = _int_value(readiness_summary, "open_alert_count")
    readiness_critical_open_count = _int_value(
        readiness_summary, "critical_open_alert_count"
    )
    readiness_recommendation = _str_value(readiness_summary, "recommendation")
    network_access_allowed_count = _int_value(
        readiness_summary, "network_access_allowed_count"
    )
    external_submission_approved_count = _int_value(
        readiness_summary, "external_submission_approved_count"
    )

    expected_open_count = int(expected["open_alert_count"])
    expected_critical_count = int(expected["critical_open_alert_count"])
    expected_resolution_open_count = int(expected["alert_resolution_open_count"])
    expected_qc_health = str(expected["qc_overall_health"])
    expected_recommendation = str(expected["operations_readiness_recommendation"])
    require_zero_external = bool(expected.get("require_zero_external_authorization", True))
    require_zero_network = bool(expected.get("require_zero_network_access", True))
    require_open_alert_coverage = bool(
        expected.get("require_open_alert_resolution_coverage", True)
    )

    issues: list[str] = []
    if alert_open_count != expected_open_count:
        issues.append(
            f"open alert count {alert_open_count} != expected {expected_open_count}"
        )
    if alert_critical_open_count != expected_critical_count:
        issues.append(
            "critical open alert count "
            f"{alert_critical_open_count} != expected {expected_critical_count}"
        )
    if resolution_open_count != expected_resolution_open_count:
        issues.append(
            "alert resolution open count "
            f"{resolution_open_count} != expected {expected_resolution_open_count}"
        )
    if qc_health != expected_qc_health:
        issues.append(f"QC health {qc_health!r} != expected {expected_qc_health!r}")
    if readiness_recommendation != expected_recommendation:
        issues.append(
            "operations readiness recommendation "
            f"{readiness_recommendation!r} != expected {expected_recommendation!r}"
        )
    if readiness_open_count != alert_open_count:
        issues.append(
            "operations readiness open alert count "
            f"{readiness_open_count} != candidate alert count {alert_open_count}"
        )
    if readiness_critical_open_count != alert_critical_open_count:
        issues.append(
            "operations readiness critical open alert count "
            f"{readiness_critical_open_count} != candidate alert count "
            f"{alert_critical_open_count}"
        )
    if require_open_alert_coverage and uncovered_open_alert_ids:
        issues.append(
            "open alert IDs missing any resolution coverage: "
            + ", ".join(uncovered_open_alert_ids)
        )
    if require_open_alert_coverage and uncovered_critical_alert_ids:
        issues.append(
            "critical open alert IDs missing open resolution coverage: "
            + ", ".join(uncovered_critical_alert_ids)
        )
    if require_zero_external and external_submission_approved_count != 0:
        issues.append("external submission approval count is nonzero")
    if require_zero_network and network_access_allowed_count != 0:
        issues.append("network access allowed count is nonzero")

    return {
        "schema_version": OPERATIONS_ALERT_REVIEW_CONSISTENCY_SCHEMA_VERSION,
        "disclaimer": OPERATIONS_ALERT_REVIEW_CONSISTENCY_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_open_alert_count": expected_open_count,
        "actual_open_alert_count": alert_open_count,
        "expected_critical_open_alert_count": expected_critical_count,
        "actual_critical_open_alert_count": alert_critical_open_count,
        "expected_alert_resolution_open_count": expected_resolution_open_count,
        "actual_alert_resolution_open_count": resolution_open_count,
        "expected_qc_overall_health": expected_qc_health,
        "actual_qc_overall_health": qc_health,
        "expected_operations_readiness_recommendation": expected_recommendation,
        "actual_operations_readiness_recommendation": readiness_recommendation,
        "readiness_open_alert_count": readiness_open_count,
        "readiness_critical_open_alert_count": readiness_critical_open_count,
        "open_alert_ids": open_alert_ids,
        "critical_open_alert_ids": critical_open_alert_ids,
        "uncovered_open_alert_ids": uncovered_open_alert_ids,
        "uncovered_critical_alert_ids": uncovered_critical_alert_ids,
        "uncovered_open_alert_count": len(uncovered_open_alert_ids),
        "uncovered_critical_alert_count": len(uncovered_critical_alert_ids),
        "external_submission_approved_count": external_submission_approved_count,
        "network_access_allowed_count": network_access_allowed_count,
    }
