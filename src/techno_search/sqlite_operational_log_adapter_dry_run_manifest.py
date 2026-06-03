"""Preview-only SQLite adapter dry-run manifest for operational logs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from techno_search.sqlite_operational_log_adapter_ddl_preview import (
    sqlite_operational_log_adapter_ddl_preview_summary,
)
from techno_search.sqlite_operational_log_adapter_execution_preview import (
    sqlite_operational_log_adapter_execution_preview_summary,
)

SQLITE_OPERATIONAL_LOG_ADAPTER_DRY_RUN_MANIFEST_SCHEMA_VERSION = (
    "sqlite_operational_log_adapter_dry_run_manifest_v1"
)

SQLITE_OPERATIONAL_LOG_ADAPTER_DRY_RUN_MANIFEST_DISCLAIMER = (
    "SQLite operational log adapter dry-run manifests are local planning "
    "artifacts only. They reconcile DDL previews with execution previews for "
    "review without opening databases, executing SQL, inserting rows, creating "
    "tables, migrating fixture records, mutating databases, ingesting real "
    "observation data, authorizing live data access, authorizing external "
    "submission, or constituting detections, discoveries, or external "
    "validation."
)


@dataclass(frozen=True)
class SqliteOperationalLogAdapterDryRunManifestEntry:
    phase_id: str
    ddl_table_name: str
    execution_table_name: str
    insert_count: int
    operation_count: int


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_manifest_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "sqlite_operational_log_adapter_dry_run_manifest.json"
    )


def load_sqlite_operational_log_adapter_dry_run_manifest_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    manifest_path = path if path is not None else _default_manifest_path()
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_manifest"])


def sqlite_operational_log_adapter_dry_run_manifest_summary(
    path: Path | None = None,
    *,
    ddl_preview_summary: dict[str, Any] | None = None,
    execution_preview_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = load_sqlite_operational_log_adapter_dry_run_manifest_expectations(path)
    ddl_preview = (
        ddl_preview_summary
        if ddl_preview_summary is not None
        else sqlite_operational_log_adapter_ddl_preview_summary()
    )
    execution_preview = (
        execution_preview_summary
        if execution_preview_summary is not None
        else sqlite_operational_log_adapter_execution_preview_summary()
    )

    ddl_records = [
        record for record in ddl_preview.get("records", []) if isinstance(record, dict)
    ]
    execution_records = [
        record
        for record in execution_preview.get("phase_previews", [])
        if isinstance(record, dict)
    ]
    ddl_by_phase = {str(record.get("phase_id", "")): record for record in ddl_records}
    execution_by_phase = {
        str(record.get("phase_id", "")): record for record in execution_records
    }
    phase_ids = sorted(set(ddl_by_phase) | set(execution_by_phase))
    manifest_entries = [
        SqliteOperationalLogAdapterDryRunManifestEntry(
            phase_id=phase_id,
            ddl_table_name=str(ddl_by_phase.get(phase_id, {}).get("table_name", "")),
            execution_table_name=str(
                execution_by_phase.get(phase_id, {}).get("table_name", "")
            ),
            insert_count=int(execution_by_phase.get(phase_id, {}).get("insert_count", 0)),
            operation_count=int(
                execution_by_phase.get(phase_id, {}).get("operation_count", 0)
            ),
        )
        for phase_id in phase_ids
        if phase_id
    ]
    phase_alignment_mismatch_ids = [
        entry.phase_id
        for entry in manifest_entries
        if not entry.ddl_table_name
        or not entry.execution_table_name
        or entry.ddl_table_name != entry.execution_table_name
    ]

    database_open_allowed = bool(expected.get("database_open_allowed", False))
    execution_allowed = bool(expected.get("execution_allowed", False))
    mutation_allowed = bool(expected.get("mutation_allowed", False))
    live_data_authorized = bool(expected.get("live_data_authorized", False))
    external_submission_authorized = bool(
        expected.get("external_submission_authorized", False)
    )
    manifest_status = str(expected.get("manifest_status", "preview_only"))

    issues: list[str] = []
    if expected.get("require_ddl_preview_ok", True) and not bool(
        ddl_preview.get("ok", False)
    ):
        issues.append("SQLite operational log adapter DDL preview is not ok")
    if expected.get("require_execution_preview_ok", True) and not bool(
        execution_preview.get("ok", False)
    ):
        issues.append("SQLite operational log adapter execution preview is not ok")
    if int(ddl_preview.get("ddl_statement_count", 0)) != int(
        expected.get("expected_ddl_statement_count", 0)
    ):
        issues.append(
            "dry-run manifest DDL statement count "
            f"{int(ddl_preview.get('ddl_statement_count', 0))} != expected "
            f"{int(expected.get('expected_ddl_statement_count', 0))}"
        )
    if int(execution_preview.get("insert_count", 0)) != int(
        expected.get("expected_insert_count", 0)
    ):
        issues.append(
            "dry-run manifest insert count "
            f"{int(execution_preview.get('insert_count', 0))} != expected "
            f"{int(expected.get('expected_insert_count', 0))}"
        )
    if int(execution_preview.get("phase_count", 0)) != int(
        expected.get("expected_phase_count", 0)
    ):
        issues.append(
            "dry-run manifest phase count "
            f"{int(execution_preview.get('phase_count', 0))} != expected "
            f"{int(expected.get('expected_phase_count', 0))}"
        )
    if int(execution_preview.get("operation_count", 0)) != int(
        expected.get("expected_execution_operation_count", 0)
    ):
        issues.append(
            "dry-run manifest execution operation count "
            f"{int(execution_preview.get('operation_count', 0))} != expected "
            f"{int(expected.get('expected_execution_operation_count', 0))}"
        )
    if expected.get("require_phase_alignment", True) and phase_alignment_mismatch_ids:
        issues.append(
            "dry-run manifest phase alignment mismatch(es): "
            + ", ".join(phase_alignment_mismatch_ids)
        )
    if manifest_status != "preview_only":
        issues.append("dry-run manifest status must remain preview_only")
    if database_open_allowed:
        issues.append("dry-run manifest must not allow opening databases")
    if execution_allowed:
        issues.append("dry-run manifest must remain non-executing")
    if mutation_allowed:
        issues.append("dry-run manifest must not authorize mutation")
    if live_data_authorized:
        issues.append("dry-run manifest must not authorize live data")
    if external_submission_authorized:
        issues.append("dry-run manifest must not authorize external submission")

    return {
        "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_DRY_RUN_MANIFEST_SCHEMA_VERSION,
        "disclaimer": SQLITE_OPERATIONAL_LOG_ADAPTER_DRY_RUN_MANIFEST_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "manifest_status": manifest_status,
        "ddl_statement_count": int(ddl_preview.get("ddl_statement_count", 0)),
        "insert_count": int(execution_preview.get("insert_count", 0)),
        "phase_count": int(execution_preview.get("phase_count", 0)),
        "execution_operation_count": int(execution_preview.get("operation_count", 0)),
        "phase_alignment_mismatch_count": len(phase_alignment_mismatch_ids),
        "database_open_allowed": database_open_allowed,
        "execution_allowed": execution_allowed,
        "mutation_allowed": mutation_allowed,
        "live_data_authorized": live_data_authorized,
        "external_submission_authorized": external_submission_authorized,
        "manifest_entries": [entry.__dict__ for entry in manifest_entries],
    }
