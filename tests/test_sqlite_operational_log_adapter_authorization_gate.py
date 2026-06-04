from __future__ import annotations

import json
from pathlib import Path

from techno_search.sqlite_operational_log_adapter_authorization_gate import (
    BLOCKED_AUTHORIZATION_STATUS,
    SQLITE_OPERATIONAL_LOG_ADAPTER_AUTHORIZATION_GATE_SCHEMA_VERSION,
    load_sqlite_operational_log_adapter_authorization_gate_expectations,
    sqlite_operational_log_adapter_authorization_gate_summary,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "sqlite_operational_log_adapter_authorization_gate.json"
)


def _readiness(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "ok": True,
        "readiness_status": "preflight_only",
        "upstream_gate_failure_count": 0,
        "schema_count": 175,
        "database_open_allowed": False,
        "execution_allowed": False,
        "mutation_allowed": False,
        "live_data_authorized": False,
        "external_submission_authorized": False,
    }
    data.update(overrides)
    return data


def _write_gate(
    path: Path,
    *,
    expected_readiness_failed_gate_count: int = 0,
    expected_readiness_schema_count: int = 175,
    expected_schema_count: int = 175,
    authorization_status: str = BLOCKED_AUTHORIZATION_STATUS,
    adapter_implementation_allowed: bool = False,
    database_open_allowed: bool = False,
    execution_allowed: bool = False,
    fixture_migration_allowed: bool = False,
    mutation_allowed: bool = False,
    live_data_authorized: bool = False,
    external_submission_authorized: bool = False,
) -> Path:
    gate_path = path / "authorization_gate.json"
    gate_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    SQLITE_OPERATIONAL_LOG_ADAPTER_AUTHORIZATION_GATE_SCHEMA_VERSION
                ),
                "expected_gate": {
                    "expected_readiness_failed_gate_count": (
                        expected_readiness_failed_gate_count
                    ),
                    "expected_readiness_schema_count": (
                        expected_readiness_schema_count
                    ),
                    "expected_schema_count": expected_schema_count,
                    "require_readiness_preflight_ok": True,
                    "authorization_status": authorization_status,
                    "adapter_implementation_allowed": (
                        adapter_implementation_allowed
                    ),
                    "database_open_allowed": database_open_allowed,
                    "execution_allowed": execution_allowed,
                    "fixture_migration_allowed": fixture_migration_allowed,
                    "mutation_allowed": mutation_allowed,
                    "live_data_authorized": live_data_authorized,
                    "external_submission_authorized": (
                        external_submission_authorized
                    ),
                },
            }
        ),
        encoding="utf-8",
    )
    return gate_path


def test_load_fixture_expectations() -> None:
    expected = load_sqlite_operational_log_adapter_authorization_gate_expectations(
        FIXTURE_PATH
    )

    assert expected["expected_readiness_schema_count"] == 179
    assert expected["expected_schema_count"] == 179
    assert expected["authorization_status"] == BLOCKED_AUTHORIZATION_STATUS
    assert expected["execution_allowed"] is False


def test_default_project_authorization_gate_passes() -> None:
    summary = sqlite_operational_log_adapter_authorization_gate_summary()

    assert (
        summary["schema_version"]
        == SQLITE_OPERATIONAL_LOG_ADAPTER_AUTHORIZATION_GATE_SCHEMA_VERSION
    )
    assert summary["ok"] is True
    assert summary["authorization_status"] == BLOCKED_AUTHORIZATION_STATUS
    assert summary["readiness_preflight_ok"] is True
    assert summary["readiness_preflight_schema_count"] == 179
    assert summary["schema_count"] == 179
    assert summary["adapter_implementation_allowed"] is False
    assert summary["database_open_allowed"] is False
    assert summary["execution_allowed"] is False
    assert summary["fixture_migration_allowed"] is False
    assert summary["mutation_allowed"] is False
    assert summary["live_data_authorized"] is False
    assert summary["external_submission_authorized"] is False


def test_custom_gate_passes(tmp_path: Path) -> None:
    gate_path = _write_gate(tmp_path)

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(),
        schema_count=175,
    )

    assert summary["ok"] is True


def test_detects_failed_readiness_preflight(tmp_path: Path) -> None:
    gate_path = _write_gate(tmp_path)

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(ok=False),
        schema_count=175,
    )

    assert summary["ok"] is False
    assert summary["readiness_preflight_ok"] is False


def test_detects_readiness_count_mismatch(tmp_path: Path) -> None:
    gate_path = _write_gate(
        tmp_path,
        expected_readiness_failed_gate_count=1,
        expected_readiness_schema_count=171,
        expected_schema_count=172,
    )

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(),
        schema_count=175,
    )

    assert summary["ok"] is False
    assert summary["readiness_preflight_failed_gate_count"] == 0
    assert summary["readiness_preflight_schema_count"] == 175
    assert summary["schema_count"] == 175


def test_detects_non_blocked_authorization_status(tmp_path: Path) -> None:
    gate_path = _write_gate(tmp_path, authorization_status="approved_to_execute")

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(),
        schema_count=175,
    )

    assert summary["ok"] is False
    assert summary["authorization_status"] == "approved_to_execute"


def test_detects_adapter_implementation_allowed(tmp_path: Path) -> None:
    gate_path = _write_gate(tmp_path, adapter_implementation_allowed=True)

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(),
        schema_count=175,
    )

    assert summary["ok"] is False
    assert summary["adapter_implementation_allowed"] is True


def test_detects_database_open_allowed(tmp_path: Path) -> None:
    gate_path = _write_gate(tmp_path, database_open_allowed=True)

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(),
        schema_count=175,
    )

    assert summary["ok"] is False
    assert summary["database_open_allowed"] is True


def test_detects_execution_allowed(tmp_path: Path) -> None:
    gate_path = _write_gate(tmp_path, execution_allowed=True)

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(),
        schema_count=175,
    )

    assert summary["ok"] is False
    assert summary["execution_allowed"] is True


def test_detects_fixture_migration_allowed(tmp_path: Path) -> None:
    gate_path = _write_gate(tmp_path, fixture_migration_allowed=True)

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(),
        schema_count=175,
    )

    assert summary["ok"] is False
    assert summary["fixture_migration_allowed"] is True


def test_detects_mutation_allowed(tmp_path: Path) -> None:
    gate_path = _write_gate(tmp_path, mutation_allowed=True)

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(),
        schema_count=175,
    )

    assert summary["ok"] is False
    assert summary["mutation_allowed"] is True


def test_detects_live_data_authorized(tmp_path: Path) -> None:
    gate_path = _write_gate(tmp_path, live_data_authorized=True)

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(),
        schema_count=175,
    )

    assert summary["ok"] is False
    assert summary["live_data_authorized"] is True


def test_detects_external_submission_authorized(tmp_path: Path) -> None:
    gate_path = _write_gate(tmp_path, external_submission_authorized=True)

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(),
        schema_count=175,
    )

    assert summary["ok"] is False
    assert summary["external_submission_authorized"] is True


def test_detects_readiness_safety_flag_drift(tmp_path: Path) -> None:
    gate_path = _write_gate(tmp_path)

    summary = sqlite_operational_log_adapter_authorization_gate_summary(
        gate_path,
        readiness_preflight_summary=_readiness(execution_allowed=True),
        schema_count=175,
    )

    assert summary["ok"] is False
    assert any("execution_allowed" in issue for issue in summary["issues"])
