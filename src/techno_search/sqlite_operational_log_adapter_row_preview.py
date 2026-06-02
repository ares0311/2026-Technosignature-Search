"""Preview-only SQLite row payloads for future operational log adapters."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from techno_search.sqlite_operational_log_adapter_contract import (
    sqlite_operational_log_adapter_contract_summary,
)
from techno_search.sqlite_operational_log_adapter_plan import (
    sqlite_operational_log_adapter_plan_summary,
)
from techno_search.sqlite_operational_log_registry import (
    sqlite_operational_log_registry_summary,
)

SQLITE_OPERATIONAL_LOG_ADAPTER_ROW_PREVIEW_SCHEMA_VERSION = (
    "sqlite_operational_log_adapter_row_preview_v1"
)

SQLITE_OPERATIONAL_LOG_ADAPTER_ROW_PREVIEW_DISCLAIMER = (
    "SQLite operational log adapter row previews are local planning artifacts "
    "only. They render deterministic row payloads for review without inserting "
    "rows, creating tables, migrating fixture records, mutating databases, "
    "ingesting real observation data, authorizing live data access, authorizing "
    "external submission, or constituting detections, discoveries, or external "
    "validation."
)


@dataclass(frozen=True)
class SqliteOperationalLogAdapterRowPreviewRecord:
    log_id: str
    phase_id: str
    table_name: str
    event_payload_json: str
    recorded_at_utc: str
    source_fixture_path: str
    sqlite_policy: str
    provenance_hash: str
    execution_allowed: bool


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_preview_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "sqlite_operational_log_adapter_row_preview.json"
    )


def load_sqlite_operational_log_adapter_row_preview_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    preview_path = path if path is not None else _default_preview_path()
    raw = json.loads(preview_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_preview"])


def _payload_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _provenance_hash(payload_json: str) -> str:
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def sqlite_operational_log_adapter_row_preview_summary(
    path: Path | None = None,
    *,
    adapter_contract_summary: dict[str, Any] | None = None,
    adapter_plan_summary: dict[str, Any] | None = None,
    registry_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = load_sqlite_operational_log_adapter_row_preview_expectations(path)
    contract = (
        adapter_contract_summary
        if adapter_contract_summary is not None
        else sqlite_operational_log_adapter_contract_summary()
    )
    adapter_plan = (
        adapter_plan_summary
        if adapter_plan_summary is not None
        else sqlite_operational_log_adapter_plan_summary()
    )
    registry = (
        registry_summary
        if registry_summary is not None
        else sqlite_operational_log_registry_summary()
    )

    execution_allowed = bool(expected.get("execution_allowed", False))
    required_row_fields = [
        str(field) for field in expected.get("required_row_fields", [])
    ]
    contract_required_columns = {
        str(column)
        for record in contract.get("records", [])
        if isinstance(record, dict)
        for column in record.get("required_columns", [])
    }
    table_by_phase = {
        str(record.get("phase_id", "")): str(record.get("table_name", ""))
        for record in contract.get("records", [])
        if isinstance(record, dict)
    }
    registry_by_log_id = {
        str(record.get("log_id", "")): record
        for record in registry.get("records", [])
        if isinstance(record, dict)
    }

    records: list[SqliteOperationalLogAdapterRowPreviewRecord] = []
    missing_registry_log_ids: list[str] = []
    invalid_payload_log_ids: list[str] = []
    for plan_record in adapter_plan.get("records", []):
        if not isinstance(plan_record, dict):
            continue
        log_id = str(plan_record.get("log_id", ""))
        phase_id = str(plan_record.get("phase_id", ""))
        registry_record = registry_by_log_id.get(log_id, {})
        if not registry_record:
            missing_registry_log_ids.append(log_id)
        source_fixture_path = str(registry_record.get("fixture_path", ""))
        sqlite_policy = str(
            registry_record.get("sqlite_policy", plan_record.get("sqlite_policy", ""))
        )
        payload = {
            "log_id": log_id,
            "phase_id": phase_id,
            "source_fixture_path": source_fixture_path,
            "sqlite_policy": sqlite_policy,
            "sqlite_backed": bool(registry_record.get("sqlite_backed", False)),
        }
        event_payload_json = _payload_json(payload)
        try:
            json.loads(event_payload_json)
        except json.JSONDecodeError:
            invalid_payload_log_ids.append(log_id)
        records.append(
            SqliteOperationalLogAdapterRowPreviewRecord(
                log_id=log_id,
                phase_id=phase_id,
                table_name=table_by_phase.get(phase_id, ""),
                event_payload_json=event_payload_json,
                recorded_at_utc="preview_only_not_recorded",
                source_fixture_path=source_fixture_path,
                sqlite_policy=sqlite_policy,
                provenance_hash=_provenance_hash(event_payload_json),
                execution_allowed=execution_allowed,
            )
        )

    row_dicts = [record.__dict__ for record in records]
    missing_row_field_pairs = [
        f"{row.get('log_id', '')}:{field}"
        for row in row_dicts
        for field in required_row_fields
        if not row.get(field)
    ]
    missing_contract_column_fields = sorted(
        field for field in required_row_fields if field not in contract_required_columns
    )
    phase_ids = sorted({record.phase_id for record in records if record.phase_id})
    missing_table_phase_ids = sorted(
        {record.phase_id for record in records if record.phase_id and not record.table_name}
    )

    issues: list[str] = []
    if expected.get("require_adapter_contract_ok", True) and not bool(
        contract.get("ok", False)
    ):
        issues.append("SQLite operational log adapter contract is not ok")
    if expected.get("require_adapter_plan_ok", True) and not bool(
        adapter_plan.get("ok", False)
    ):
        issues.append("SQLite operational log adapter plan is not ok")
    if expected.get("require_registry_ok", True) and not bool(registry.get("ok", False)):
        issues.append("SQLite operational log registry is not ok")
    if len(records) != int(expected.get("expected_row_count", 0)):
        issues.append(
            f"row preview count {len(records)} != expected "
            f"{int(expected.get('expected_row_count', 0))}"
        )
    if len(phase_ids) != int(expected.get("expected_phase_count", 0)):
        issues.append(
            f"row preview phase count {len(phase_ids)} != expected "
            f"{int(expected.get('expected_phase_count', 0))}"
        )
    if expected.get("require_contract_columns", True) and missing_contract_column_fields:
        issues.append(
            "missing adapter contract column(s): "
            + ", ".join(missing_contract_column_fields)
        )
    if expected.get("require_row_fields", True) and missing_row_field_pairs:
        issues.append("missing row field(s): " + ", ".join(missing_row_field_pairs))
    if missing_table_phase_ids:
        issues.append("missing table mapping(s): " + ", ".join(missing_table_phase_ids))
    if missing_registry_log_ids:
        issues.append("missing registry log(s): " + ", ".join(missing_registry_log_ids))
    if expected.get("require_json_payloads", True) and invalid_payload_log_ids:
        issues.append("invalid row payload JSON: " + ", ".join(invalid_payload_log_ids))
    if execution_allowed:
        issues.append("row preview must remain non-executing")

    return {
        "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_ROW_PREVIEW_SCHEMA_VERSION,
        "disclaimer": SQLITE_OPERATIONAL_LOG_ADAPTER_ROW_PREVIEW_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_row_count": int(expected.get("expected_row_count", 0)),
        "row_count": len(records),
        "expected_phase_count": int(expected.get("expected_phase_count", 0)),
        "phase_count": len(phase_ids),
        "missing_row_field_count": len(missing_row_field_pairs),
        "missing_contract_column_count": len(missing_contract_column_fields),
        "missing_table_mapping_count": len(missing_table_phase_ids),
        "missing_registry_log_count": len(missing_registry_log_ids),
        "invalid_payload_count": len(invalid_payload_log_ids),
        "execution_allowed": execution_allowed,
        "records": row_dicts,
    }
