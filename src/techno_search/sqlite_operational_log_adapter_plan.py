"""Non-destructive SQLite adapter plan for operational log families."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from techno_search.sqlite_operational_log_registry import (
    SQLITE_REQUIRED_POLICY,
    sqlite_operational_log_registry_summary,
)

SQLITE_OPERATIONAL_LOG_ADAPTER_PLAN_SCHEMA_VERSION = (
    "sqlite_operational_log_adapter_plan_v1"
)

SQLITE_OPERATIONAL_LOG_ADAPTER_PLAN_DISCLAIMER = (
    "SQLite operational log adapter plans are local migration planning records "
    "only. They map fixture-backed operational log families to future SQLite "
    "adapter phases without mutating databases, ingesting real observation data, "
    "authorizing live data access, authorizing external submission, or "
    "constituting detections, discoveries, or external validation."
)

PHASE_ORDER = (
    "candidate_and_review",
    "observation_and_signal",
    "pipeline_and_modeling",
    "infrastructure_and_facility",
    "security_and_compliance",
)

PHASE_PREFIXES = {
    "candidate_and_review": (
        "alert_resolution",
        "candidate_",
        "escalation",
        "intake_queue",
        "operator_escalation",
        "quality_gate",
        "review_",
        "session",
        "workflow_state",
    ),
    "observation_and_signal": (
        "antenna_",
        "archival_query",
        "beam_",
        "calibration_",
        "data_archival",
        "data_gap",
        "data_quality",
        "data_transfer",
        "doppler_",
        "event_",
        "frequency_",
        "instrument",
        "interference_",
        "noise_",
        "observation_",
        "polarization",
        "receiver_",
        "rfi_",
        "scan",
        "scheduling_",
        "signal_",
        "source_",
        "spectral_",
        "target_",
        "telescope_",
        "time_",
        "weather",
    ),
    "pipeline_and_modeling": (
        "pipeline_",
        "scoring_",
    ),
    "infrastructure_and_facility": (
        "backup_",
        "capacity_",
        "cooling_",
        "environmental",
        "firmware_",
        "hardware_",
        "health_",
        "license_",
        "maintenance",
        "network_",
        "performance_",
        "power",
        "risk_",
        "software_",
        "storage_",
        "system_",
        "user_",
    ),
    "security_and_compliance": (
        "access_",
        "audit_",
        "change_",
        "compliance_",
        "configuration_",
        "incident_",
        "security_",
    ),
}


@dataclass(frozen=True)
class SqliteOperationalLogAdapterPlanRecord:
    log_id: str
    phase_id: str
    sqlite_policy: str
    mutation_allowed: bool


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_plan_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "sqlite_operational_log_adapter_plan.json"
    )


def load_sqlite_operational_log_adapter_plan_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    plan_path = path if path is not None else _default_plan_path()
    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_plan"])


def _phase_for_log_id(log_id: str) -> str:
    for phase_id in PHASE_ORDER:
        prefixes = PHASE_PREFIXES[phase_id]
        if any(log_id.startswith(prefix) for prefix in prefixes):
            return phase_id
    return "unassigned"


def sqlite_operational_log_adapter_plan_summary(
    path: Path | None = None,
    *,
    registry_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = load_sqlite_operational_log_adapter_plan_expectations(path)
    registry = (
        registry_summary
        if registry_summary is not None
        else sqlite_operational_log_registry_summary()
    )
    registry_records = [
        record
        for record in registry.get("records", [])
        if isinstance(record, dict)
    ]
    mutation_allowed = bool(expected.get("mutation_allowed", False))
    records = [
        SqliteOperationalLogAdapterPlanRecord(
            log_id=str(record.get("log_id", "")),
            phase_id=_phase_for_log_id(str(record.get("log_id", ""))),
            sqlite_policy=str(record.get("sqlite_policy", "")),
            mutation_allowed=mutation_allowed,
        )
        for record in registry_records
    ]

    expected_count = int(expected.get("expected_log_count", len(records)))
    required_phases = [str(phase) for phase in expected.get("required_phase_ids", [])]
    present_phases = sorted({record.phase_id for record in records})
    missing_phases = [phase for phase in required_phases if phase not in present_phases]
    unassigned = [record.log_id for record in records if record.phase_id == "unassigned"]
    policy_mismatch = [
        record.log_id
        for record in records
        if record.sqlite_policy != SQLITE_REQUIRED_POLICY
    ]

    issues: list[str] = []
    if expected.get("require_registry_ok", True) and not bool(registry.get("ok", False)):
        issues.append("SQLite operational log registry is not ok")
    if len(records) != expected_count:
        issues.append(
            f"adapter plan record count {len(records)} != expected {expected_count}"
        )
    if expected.get("require_zero_missing_phase", True) and missing_phases:
        issues.append("missing adapter phase(s): " + ", ".join(missing_phases))
    if expected.get("require_all_registry_logs_planned", True) and unassigned:
        issues.append("unassigned log ID(s): " + ", ".join(unassigned))
    if expected.get("require_sqlite_required_policy", True) and policy_mismatch:
        issues.append("non-required SQLite policy log ID(s): " + ", ".join(policy_mismatch))
    if mutation_allowed:
        issues.append("adapter plan must remain non-mutating")

    return {
        "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_PLAN_SCHEMA_VERSION,
        "disclaimer": SQLITE_OPERATIONAL_LOG_ADAPTER_PLAN_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_log_count": expected_count,
        "planned_log_count": len(records),
        "phase_count": len(present_phases),
        "required_phase_count": len(required_phases),
        "missing_phase_count": len(missing_phases),
        "unassigned_log_count": len(unassigned),
        "sqlite_policy_mismatch_count": len(policy_mismatch),
        "mutation_allowed": mutation_allowed,
        "by_phase": {
            phase: sum(1 for record in records if record.phase_id == phase)
            for phase in PHASE_ORDER
        },
        "records": [record.__dict__ for record in records],
    }
