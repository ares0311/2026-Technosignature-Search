from __future__ import annotations

import json
from pathlib import Path

from techno_search.sqlite_operational_log_adapter_contract import (
    SQLITE_OPERATIONAL_LOG_ADAPTER_CONTRACT_SCHEMA_VERSION,
    load_sqlite_operational_log_adapter_contract_expectations,
    sqlite_operational_log_adapter_contract_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sqlite_operational_log_adapter_contract.json"
REQUIRED_COLUMNS = [
    "log_id",
    "phase_id",
    "event_payload_json",
    "recorded_at_utc",
    "source_fixture_path",
    "sqlite_policy",
    "provenance_hash",
]


def _adapter_plan(
    *,
    ok: bool = True,
    planned_log_count: int = 1,
    candidate_count: int = 1,
) -> dict[str, object]:
    return {
        "ok": ok,
        "planned_log_count": planned_log_count,
        "by_phase": {
            "candidate_and_review": candidate_count,
        },
    }


def _write_contract(
    path: Path,
    *,
    table_name: str = "operational_log_candidate_and_review",
    columns: list[str] | None = None,
    planned_log_count: int = 1,
    mutation_allowed: bool = False,
) -> Path:
    contract_path = path / "contract.json"
    contract_path.write_text(
        json.dumps(
            {
                "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_CONTRACT_SCHEMA_VERSION,
                "expected_contract": {
                    "expected_phase_count": 1,
                    "expected_planned_log_count": planned_log_count,
                    "required_phase_ids": ["candidate_and_review"],
                    "required_columns": REQUIRED_COLUMNS,
                    "require_adapter_plan_ok": True,
                    "require_all_phase_tables": True,
                    "require_required_columns": True,
                    "require_phase_log_counts": True,
                    "mutation_allowed": mutation_allowed,
                    "phase_contracts": [
                        {
                            "phase_id": "candidate_and_review",
                            "table_name": table_name,
                            "planned_log_count": planned_log_count,
                            "required_columns": (
                                columns if columns is not None else REQUIRED_COLUMNS
                            ),
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    return contract_path


def test_load_fixture_expectations() -> None:
    expected = load_sqlite_operational_log_adapter_contract_expectations(FIXTURE_PATH)

    assert expected["expected_phase_count"] == 0
    assert expected["expected_planned_log_count"] == 0
    assert expected["mutation_allowed"] is False


def test_default_project_adapter_contract_passes() -> None:
    summary = sqlite_operational_log_adapter_contract_summary()

    assert summary["schema_version"] == SQLITE_OPERATIONAL_LOG_ADAPTER_CONTRACT_SCHEMA_VERSION
    assert summary["ok"] is True
    assert summary["phase_contract_count"] == 0
    assert summary["planned_log_count"] == 0
    assert summary["missing_table_plan_count"] == 0
    assert summary["missing_required_column_count"] == 0
    assert summary["mutation_allowed"] is False


def test_custom_adapter_plan_passes(tmp_path: Path) -> None:
    contract_path = _write_contract(tmp_path)

    summary = sqlite_operational_log_adapter_contract_summary(
        contract_path,
        adapter_plan_summary=_adapter_plan(),
    )

    assert summary["ok"] is True


def test_detects_adapter_plan_not_ok(tmp_path: Path) -> None:
    contract_path = _write_contract(tmp_path)

    summary = sqlite_operational_log_adapter_contract_summary(
        contract_path,
        adapter_plan_summary=_adapter_plan(ok=False),
    )

    assert summary["ok"] is False
    assert any("adapter plan is not ok" in issue for issue in summary["issues"])


def test_detects_missing_table_plan(tmp_path: Path) -> None:
    contract_path = _write_contract(tmp_path, table_name="")

    summary = sqlite_operational_log_adapter_contract_summary(
        contract_path,
        adapter_plan_summary=_adapter_plan(),
    )

    assert summary["ok"] is False
    assert summary["missing_table_plan_count"] == 1


def test_detects_missing_required_column(tmp_path: Path) -> None:
    contract_path = _write_contract(tmp_path, columns=REQUIRED_COLUMNS[:-1])

    summary = sqlite_operational_log_adapter_contract_summary(
        contract_path,
        adapter_plan_summary=_adapter_plan(),
    )

    assert summary["ok"] is False
    assert summary["missing_required_column_count"] == 1


def test_detects_phase_count_mismatch(tmp_path: Path) -> None:
    contract_path = _write_contract(tmp_path, planned_log_count=2)

    summary = sqlite_operational_log_adapter_contract_summary(
        contract_path,
        adapter_plan_summary=_adapter_plan(candidate_count=1, planned_log_count=2),
    )

    assert summary["ok"] is False
    assert summary["phase_count_mismatch_count"] == 1


def test_detects_mutation_allowed(tmp_path: Path) -> None:
    contract_path = _write_contract(tmp_path, mutation_allowed=True)

    summary = sqlite_operational_log_adapter_contract_summary(
        contract_path,
        adapter_plan_summary=_adapter_plan(),
    )

    assert summary["ok"] is False
    assert summary["mutation_allowed"] is True
