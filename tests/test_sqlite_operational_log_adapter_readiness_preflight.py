from __future__ import annotations

import json
from pathlib import Path

from techno_search.sqlite_operational_log_adapter_readiness_preflight import (
    SQLITE_OPERATIONAL_LOG_ADAPTER_READINESS_PREFLIGHT_SCHEMA_VERSION,
    load_sqlite_operational_log_adapter_readiness_preflight_expectations,
    sqlite_operational_log_adapter_readiness_preflight_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "sqlite_operational_log_adapter_readiness_preflight.json"
)


def _summary(ok: bool = True, **values: object) -> dict[str, object]:
    data: dict[str, object] = {"ok": ok}
    data.update(values)
    return data


def _write_preflight(
    path: Path,
    *,
    expected_registered_log_count: int = 1,
    expected_planned_count: int = 1,
    expected_phase_count: int = 1,
    expected_ddl_statement_count: int = 1,
    expected_row_count: int = 1,
    expected_insert_count: int = 1,
    expected_execution_operation_count: int = 3,
    expected_schema_count: int = 1,
    readiness_status: str = "preflight_only",
    database_open_allowed: bool = False,
    execution_allowed: bool = False,
    mutation_allowed: bool = False,
    live_data_authorized: bool = False,
    external_submission_authorized: bool = False,
) -> Path:
    preflight_path = path / "preflight.json"
    preflight_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    SQLITE_OPERATIONAL_LOG_ADAPTER_READINESS_PREFLIGHT_SCHEMA_VERSION
                ),
                "expected_preflight": {
                    "expected_registered_log_count": expected_registered_log_count,
                    "expected_planned_count": expected_planned_count,
                    "expected_phase_count": expected_phase_count,
                    "expected_ddl_statement_count": expected_ddl_statement_count,
                    "expected_row_count": expected_row_count,
                    "expected_insert_count": expected_insert_count,
                    "expected_execution_operation_count": (
                        expected_execution_operation_count
                    ),
                    "expected_schema_count": expected_schema_count,
                    "require_all_upstream_gates_ok": True,
                    "readiness_status": readiness_status,
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
    return preflight_path


def _passing_kwargs() -> dict[str, object]:
    return {
        "registry_summary": _summary(registered_count=1),
        "adapter_plan_summary": _summary(planned_count=1, phase_count=1),
        "adapter_contract_summary": _summary(phase_count=1),
        "ddl_preview_summary": _summary(ddl_statement_count=1),
        "row_preview_summary": _summary(row_count=1),
        "insert_preview_summary": _summary(insert_count=1),
        "execution_preview_summary": _summary(operation_count=3),
        "dry_run_manifest_summary": _summary(
            manifest_status="preview_only",
            phase_count=1,
        ),
        "schema_count": 1,
    }


def test_load_fixture_expectations() -> None:
    expected = load_sqlite_operational_log_adapter_readiness_preflight_expectations(
        FIXTURE_PATH
    )

    assert expected["expected_registered_log_count"] == 0
    assert expected["expected_schema_count"] == 102
    assert expected["database_open_allowed"] is False


def test_default_project_readiness_preflight_passes() -> None:
    summary = sqlite_operational_log_adapter_readiness_preflight_summary()

    assert (
        summary["schema_version"]
        == SQLITE_OPERATIONAL_LOG_ADAPTER_READINESS_PREFLIGHT_SCHEMA_VERSION
    )
    assert summary["ok"] is True
    assert summary["readiness_status"] == "preflight_only"
    assert summary["registered_log_count"] == 0
    assert summary["planned_count"] == 0
    assert summary["phase_count"] == 0
    assert summary["ddl_statement_count"] == 0
    assert summary["row_count"] == 0
    assert summary["insert_count"] == 0
    assert summary["execution_operation_count"] == 0
    assert summary["schema_count"] == 102
    assert summary["upstream_gate_failure_count"] == 0
    assert summary["database_open_allowed"] is False
    assert summary["execution_allowed"] is False
    assert summary["mutation_allowed"] is False
    assert summary["live_data_authorized"] is False
    assert summary["external_submission_authorized"] is False


def test_custom_preflight_passes(tmp_path: Path) -> None:
    preflight_path = _write_preflight(tmp_path)

    summary = sqlite_operational_log_adapter_readiness_preflight_summary(
        preflight_path,
        **_passing_kwargs(),
    )

    assert summary["ok"] is True
    assert summary["upstream_gate_count"] == 8


def test_detects_upstream_gate_failures(tmp_path: Path) -> None:
    preflight_path = _write_preflight(tmp_path)
    kwargs = _passing_kwargs()
    kwargs["registry_summary"] = _summary(False, registered_count=1)

    summary = sqlite_operational_log_adapter_readiness_preflight_summary(
        preflight_path,
        **kwargs,
    )

    assert summary["ok"] is False
    assert summary["failed_upstream_gates"] == ["registry"]


def test_detects_count_mismatch(tmp_path: Path) -> None:
    preflight_path = _write_preflight(
        tmp_path,
        expected_registered_log_count=2,
        expected_planned_count=2,
        expected_phase_count=2,
        expected_ddl_statement_count=2,
        expected_row_count=2,
        expected_insert_count=2,
        expected_execution_operation_count=4,
        expected_schema_count=2,
    )

    summary = sqlite_operational_log_adapter_readiness_preflight_summary(
        preflight_path,
        **_passing_kwargs(),
    )

    assert summary["ok"] is False
    assert summary["registered_log_count"] == 1
    assert summary["execution_operation_count"] == 3
    assert summary["schema_count"] == 1


def test_detects_dry_run_manifest_not_preview_only(tmp_path: Path) -> None:
    preflight_path = _write_preflight(tmp_path)
    kwargs = _passing_kwargs()
    kwargs["dry_run_manifest_summary"] = _summary(
        manifest_status="ready_to_execute",
        phase_count=1,
    )

    summary = sqlite_operational_log_adapter_readiness_preflight_summary(
        preflight_path,
        **kwargs,
    )

    assert summary["ok"] is False
    assert any("preview_only" in issue for issue in summary["issues"])


def test_detects_non_preflight_status(tmp_path: Path) -> None:
    preflight_path = _write_preflight(tmp_path, readiness_status="ready_to_execute")

    summary = sqlite_operational_log_adapter_readiness_preflight_summary(
        preflight_path,
        **_passing_kwargs(),
    )

    assert summary["ok"] is False
    assert summary["readiness_status"] == "ready_to_execute"


def test_detects_database_open_allowed(tmp_path: Path) -> None:
    preflight_path = _write_preflight(tmp_path, database_open_allowed=True)

    summary = sqlite_operational_log_adapter_readiness_preflight_summary(
        preflight_path,
        **_passing_kwargs(),
    )

    assert summary["ok"] is False
    assert summary["database_open_allowed"] is True


def test_detects_execution_allowed(tmp_path: Path) -> None:
    preflight_path = _write_preflight(tmp_path, execution_allowed=True)

    summary = sqlite_operational_log_adapter_readiness_preflight_summary(
        preflight_path,
        **_passing_kwargs(),
    )

    assert summary["ok"] is False
    assert summary["execution_allowed"] is True


def test_detects_mutation_allowed(tmp_path: Path) -> None:
    preflight_path = _write_preflight(tmp_path, mutation_allowed=True)

    summary = sqlite_operational_log_adapter_readiness_preflight_summary(
        preflight_path,
        **_passing_kwargs(),
    )

    assert summary["ok"] is False
    assert summary["mutation_allowed"] is True


def test_detects_live_data_authorized(tmp_path: Path) -> None:
    preflight_path = _write_preflight(tmp_path, live_data_authorized=True)

    summary = sqlite_operational_log_adapter_readiness_preflight_summary(
        preflight_path,
        **_passing_kwargs(),
    )

    assert summary["ok"] is False
    assert summary["live_data_authorized"] is True


def test_detects_external_submission_authorized(tmp_path: Path) -> None:
    preflight_path = _write_preflight(tmp_path, external_submission_authorized=True)

    summary = sqlite_operational_log_adapter_readiness_preflight_summary(
        preflight_path,
        **_passing_kwargs(),
    )

    assert summary["ok"] is False
    assert summary["external_submission_authorized"] is True
