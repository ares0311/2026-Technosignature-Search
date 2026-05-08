from techno_search.benchmark_metadata import (
    BENCHMARK_METADATA_DISCLAIMER,
    BENCHMARK_RUN_RESULT_DISCLAIMER,
    benchmark_metadata_summary,
    benchmark_run_result_summary,
    load_benchmark_commands,
    load_benchmark_run_results,
)


def test_benchmark_metadata_loads_local_validation_commands() -> None:
    commands = load_benchmark_commands()

    assert len(commands) == 4
    assert {command.command_kind for command in commands} == {
        "future_benchmark_scaffold",
        "lint",
        "test",
        "type_check",
    }
    assert max(command.worker_count for command in commands) == 12
    assert "not a scientific performance claim" in BENCHMARK_METADATA_DISCLAIMER


def test_benchmark_metadata_summary_counts_local_context() -> None:
    summary = benchmark_metadata_summary()

    assert summary["schema_version"] == "local_synthetic_benchmark_metadata_v1"
    assert summary["hardware_profile_path"] == "docs/LOCAL_SYSTEM_PROFILE.md"
    assert summary["chip"] == "Apple M4 Max"
    assert summary["memory_gb"] == 64
    assert summary["cpu_count"] == 16
    assert summary["default_cpu_worker_limit"] == 12
    assert summary["memory_budget_gb"] == 48
    assert summary["command_count"] == 4
    assert summary["by_command_kind"] == {
        "future_benchmark_scaffold": 1,
        "lint": 1,
        "test": 1,
        "type_check": 1,
    }
    assert summary["by_status"] == {"planned_not_implemented": 1, "recommended": 3}


def test_benchmark_run_results_load_local_synthetic_runs() -> None:
    runs = load_benchmark_run_results()

    assert len(runs) == 3
    assert {run.command_kind for run in runs} == {
        "future_benchmark_scaffold",
        "lint",
        "test",
    }
    assert max(run.worker_count for run in runs) == 12
    assert "not scientific performance claims" in BENCHMARK_RUN_RESULT_DISCLAIMER


def test_benchmark_run_result_summary_counts_local_synthetic_runs() -> None:
    summary = benchmark_run_result_summary()

    assert summary["schema_version"] == "synthetic_benchmark_run_result_v1"
    assert summary["run_count"] == 3
    assert summary["input_case_total"] == 171
    assert summary["max_worker_count"] == 12
    assert summary["max_duration_seconds"] == 2.45
    assert summary["by_command_kind"] == {
        "future_benchmark_scaffold": 1,
        "lint": 1,
        "test": 1,
    }
    assert summary["by_status"] == {"passed": 2, "planned_not_implemented": 1}
    assert summary["run_ids"] == [
        "future-calibration-grid-placeholder",
        "pytest-coverage-2026-05-08",
        "ruff-2026-05-08",
    ]
