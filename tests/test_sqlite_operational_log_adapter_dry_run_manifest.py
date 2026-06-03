from __future__ import annotations

import json
from pathlib import Path

from techno_search.sqlite_operational_log_adapter_dry_run_manifest import (
    SQLITE_OPERATIONAL_LOG_ADAPTER_DRY_RUN_MANIFEST_SCHEMA_VERSION,
    load_sqlite_operational_log_adapter_dry_run_manifest_expectations,
    sqlite_operational_log_adapter_dry_run_manifest_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "sqlite_operational_log_adapter_dry_run_manifest.json"
)
DDL_RECORD = {
    "phase_id": "candidate_and_review",
    "table_name": "operational_log_candidate_and_review",
    "ddl_sql": "CREATE TABLE IF NOT EXISTS operational_log_candidate_and_review;",
    "statement_count": 1,
    "execution_allowed": False,
}
EXECUTION_RECORD = {
    "phase_id": "candidate_and_review",
    "table_name": "operational_log_candidate_and_review",
    "begin_statement": "BEGIN IMMEDIATE;",
    "insert_count": 1,
    "commit_statement": "COMMIT;",
    "operation_count": 3,
    "execution_allowed": False,
    "mutation_allowed": False,
}


def _ddl_preview(
    *,
    ok: bool = True,
    records: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    preview_records = records if records is not None else [DDL_RECORD]
    return {
        "ok": ok,
        "ddl_statement_count": len(preview_records),
        "records": preview_records,
    }


def _execution_preview(
    *,
    ok: bool = True,
    records: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    preview_records = records if records is not None else [EXECUTION_RECORD]
    return {
        "ok": ok,
        "insert_count": sum(int(record["insert_count"]) for record in preview_records),
        "phase_count": len(preview_records),
        "operation_count": sum(
            int(record["operation_count"]) for record in preview_records
        ),
        "phase_previews": preview_records,
    }


def _write_manifest(
    path: Path,
    *,
    expected_ddl_statement_count: int = 1,
    expected_insert_count: int = 1,
    expected_phase_count: int = 1,
    expected_execution_operation_count: int = 3,
    manifest_status: str = "preview_only",
    database_open_allowed: bool = False,
    execution_allowed: bool = False,
    mutation_allowed: bool = False,
    live_data_authorized: bool = False,
    external_submission_authorized: bool = False,
) -> Path:
    manifest_path = path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    SQLITE_OPERATIONAL_LOG_ADAPTER_DRY_RUN_MANIFEST_SCHEMA_VERSION
                ),
                "expected_manifest": {
                    "expected_ddl_statement_count": expected_ddl_statement_count,
                    "expected_insert_count": expected_insert_count,
                    "expected_phase_count": expected_phase_count,
                    "expected_execution_operation_count": (
                        expected_execution_operation_count
                    ),
                    "require_ddl_preview_ok": True,
                    "require_execution_preview_ok": True,
                    "require_phase_alignment": True,
                    "manifest_status": manifest_status,
                    "database_open_allowed": database_open_allowed,
                    "execution_allowed": execution_allowed,
                    "mutation_allowed": mutation_allowed,
                    "live_data_authorized": live_data_authorized,
                    "external_submission_authorized": external_submission_authorized,
                },
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_load_fixture_expectations() -> None:
    expected = load_sqlite_operational_log_adapter_dry_run_manifest_expectations(
        FIXTURE_PATH
    )

    assert expected["expected_ddl_statement_count"] == 5
    assert expected["expected_insert_count"] == 74
    assert expected["expected_execution_operation_count"] == 84
    assert expected["database_open_allowed"] is False


def test_default_project_dry_run_manifest_passes() -> None:
    summary = sqlite_operational_log_adapter_dry_run_manifest_summary()

    assert (
        summary["schema_version"]
        == SQLITE_OPERATIONAL_LOG_ADAPTER_DRY_RUN_MANIFEST_SCHEMA_VERSION
    )
    assert summary["ok"] is True
    assert summary["ddl_statement_count"] == 5
    assert summary["insert_count"] == 74
    assert summary["phase_count"] == 5
    assert summary["execution_operation_count"] == 84
    assert summary["phase_alignment_mismatch_count"] == 0
    assert summary["database_open_allowed"] is False
    assert summary["execution_allowed"] is False
    assert summary["mutation_allowed"] is False
    assert summary["live_data_authorized"] is False
    assert summary["external_submission_authorized"] is False


def test_custom_manifest_passes(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path)

    summary = sqlite_operational_log_adapter_dry_run_manifest_summary(
        manifest_path,
        ddl_preview_summary=_ddl_preview(),
        execution_preview_summary=_execution_preview(),
    )

    assert summary["ok"] is True
    assert summary["manifest_entries"][0]["insert_count"] == 1


def test_detects_upstream_preview_failures(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path)

    summary = sqlite_operational_log_adapter_dry_run_manifest_summary(
        manifest_path,
        ddl_preview_summary=_ddl_preview(ok=False),
        execution_preview_summary=_execution_preview(ok=False),
    )

    assert summary["ok"] is False
    assert any("DDL preview is not ok" in issue for issue in summary["issues"])
    assert any("execution preview is not ok" in issue for issue in summary["issues"])


def test_detects_count_mismatch(tmp_path: Path) -> None:
    manifest_path = _write_manifest(
        tmp_path,
        expected_ddl_statement_count=2,
        expected_insert_count=2,
        expected_phase_count=2,
        expected_execution_operation_count=4,
    )

    summary = sqlite_operational_log_adapter_dry_run_manifest_summary(
        manifest_path,
        ddl_preview_summary=_ddl_preview(),
        execution_preview_summary=_execution_preview(),
    )

    assert summary["ok"] is False
    assert summary["ddl_statement_count"] == 1
    assert summary["insert_count"] == 1
    assert summary["phase_count"] == 1
    assert summary["execution_operation_count"] == 3


def test_detects_phase_alignment_mismatch(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path)
    records = [
        {
            **EXECUTION_RECORD,
            "table_name": "operational_log_other_table",
        }
    ]

    summary = sqlite_operational_log_adapter_dry_run_manifest_summary(
        manifest_path,
        ddl_preview_summary=_ddl_preview(),
        execution_preview_summary=_execution_preview(records=records),
    )

    assert summary["ok"] is False
    assert summary["phase_alignment_mismatch_count"] == 1


def test_detects_non_preview_status(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, manifest_status="ready_to_execute")

    summary = sqlite_operational_log_adapter_dry_run_manifest_summary(
        manifest_path,
        ddl_preview_summary=_ddl_preview(),
        execution_preview_summary=_execution_preview(),
    )

    assert summary["ok"] is False
    assert summary["manifest_status"] == "ready_to_execute"


def test_detects_database_open_allowed(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, database_open_allowed=True)

    summary = sqlite_operational_log_adapter_dry_run_manifest_summary(
        manifest_path,
        ddl_preview_summary=_ddl_preview(),
        execution_preview_summary=_execution_preview(),
    )

    assert summary["ok"] is False
    assert summary["database_open_allowed"] is True


def test_detects_execution_allowed(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, execution_allowed=True)

    summary = sqlite_operational_log_adapter_dry_run_manifest_summary(
        manifest_path,
        ddl_preview_summary=_ddl_preview(),
        execution_preview_summary=_execution_preview(),
    )

    assert summary["ok"] is False
    assert summary["execution_allowed"] is True


def test_detects_mutation_allowed(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, mutation_allowed=True)

    summary = sqlite_operational_log_adapter_dry_run_manifest_summary(
        manifest_path,
        ddl_preview_summary=_ddl_preview(),
        execution_preview_summary=_execution_preview(),
    )

    assert summary["ok"] is False
    assert summary["mutation_allowed"] is True


def test_detects_live_data_authorized(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, live_data_authorized=True)

    summary = sqlite_operational_log_adapter_dry_run_manifest_summary(
        manifest_path,
        ddl_preview_summary=_ddl_preview(),
        execution_preview_summary=_execution_preview(),
    )

    assert summary["ok"] is False
    assert summary["live_data_authorized"] is True


def test_detects_external_submission_authorized(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, external_submission_authorized=True)

    summary = sqlite_operational_log_adapter_dry_run_manifest_summary(
        manifest_path,
        ddl_preview_summary=_ddl_preview(),
        execution_preview_summary=_execution_preview(),
    )

    assert summary["ok"] is False
    assert summary["external_submission_authorized"] is True
