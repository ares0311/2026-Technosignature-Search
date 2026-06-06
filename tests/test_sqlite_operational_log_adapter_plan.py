from __future__ import annotations

import json
from pathlib import Path

from techno_search.sqlite_operational_log_adapter_plan import (
    SQLITE_OPERATIONAL_LOG_ADAPTER_PLAN_SCHEMA_VERSION,
    load_sqlite_operational_log_adapter_plan_expectations,
    sqlite_operational_log_adapter_plan_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sqlite_operational_log_adapter_plan.json"


def _write_plan(path: Path, *, expected_count: int = 1, mutation_allowed: bool = False) -> Path:
    plan_path = path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "schema_version": SQLITE_OPERATIONAL_LOG_ADAPTER_PLAN_SCHEMA_VERSION,
                "expected_plan": {
                    "expected_log_count": expected_count,
                    "required_phase_ids": ["candidate_and_review"],
                    "require_registry_ok": True,
                    "require_all_registry_logs_planned": True,
                    "require_zero_missing_phase": True,
                    "require_sqlite_required_policy": True,
                    "mutation_allowed": mutation_allowed,
                },
            }
        ),
        encoding="utf-8",
    )
    return plan_path


def _registry(
    log_id: str = "candidate_alert_log",
    policy: str = "top_level_sqlite_required_before_production",
) -> dict[str, object]:
    return {
        "ok": True,
        "records": [
            {
                "log_id": log_id,
                "sqlite_policy": policy,
            }
        ],
    }


def test_load_fixture_expectations() -> None:
    expected = load_sqlite_operational_log_adapter_plan_expectations(FIXTURE_PATH)

    assert expected["expected_log_count"] == 0
    assert expected["required_phase_ids"] == []
    assert expected["mutation_allowed"] is False


def test_default_project_adapter_plan_passes() -> None:
    summary = sqlite_operational_log_adapter_plan_summary()

    assert summary["schema_version"] == SQLITE_OPERATIONAL_LOG_ADAPTER_PLAN_SCHEMA_VERSION
    assert summary["ok"] is True
    assert summary["planned_log_count"] == 0
    assert summary["phase_count"] == 0
    assert summary["unassigned_log_count"] == 0
    assert summary["sqlite_policy_mismatch_count"] == 0
    assert summary["mutation_allowed"] is False


def test_custom_registry_passes(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path)

    summary = sqlite_operational_log_adapter_plan_summary(
        plan_path,
        registry_summary=_registry(),
    )

    assert summary["ok"] is True
    assert summary["by_phase"]["candidate_and_review"] == 1


def test_detects_unassigned_log(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path)

    summary = sqlite_operational_log_adapter_plan_summary(
        plan_path,
        registry_summary=_registry("unmapped_log"),
    )

    assert summary["ok"] is False
    assert summary["unassigned_log_count"] == 1


def test_detects_policy_mismatch(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path)

    summary = sqlite_operational_log_adapter_plan_summary(
        plan_path,
        registry_summary=_registry(policy="fixture_only"),
    )

    assert summary["ok"] is False
    assert summary["sqlite_policy_mismatch_count"] == 1


def test_detects_count_mismatch(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path, expected_count=2)

    summary = sqlite_operational_log_adapter_plan_summary(
        plan_path,
        registry_summary=_registry(),
    )

    assert summary["ok"] is False
    assert any("record count 1 != expected 2" in issue for issue in summary["issues"])


def test_detects_mutation_allowed(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path, mutation_allowed=True)

    summary = sqlite_operational_log_adapter_plan_summary(
        plan_path,
        registry_summary=_registry(),
    )

    assert summary["ok"] is False
    assert summary["mutation_allowed"] is True
