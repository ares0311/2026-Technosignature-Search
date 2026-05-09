from techno_search.benchmark_metadata import (
    BENCHMARK_METADATA_DISCLAIMER,
    BENCHMARK_RUN_RESULT_DISCLAIMER,
    BenchmarkRunResult,
    append_benchmark_run_result,
    benchmark_metadata_summary,
    benchmark_run_result_comparison,
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
    assert runs[0].config_version == "scoring_v0"
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
    assert summary["by_config_version"] == {
        "benchmark_plan_v0": 1,
        "scoring_v0": 1,
        "tooling_v0": 1,
    }
    assert summary["run_ids"] == [
        "future-calibration-grid-placeholder",
        "pytest-coverage-2026-05-08",
        "ruff-2026-05-08",
    ]


def test_append_benchmark_run_result_preserves_prior_runs(tmp_path) -> None:
    results_path = tmp_path / "benchmark_run_results.json"
    results_path.write_text(
        '{"schema_version": "synthetic_benchmark_run_result_v1", '
        '"description": "temp", '
        '"disclaimer": "Benchmark run results record local synthetic execution '
        'metadata only; they are not scientific performance claims or survey '
        'sensitivity estimates.", '
        '"runs": []}',
        encoding="utf-8",
    )

    result = append_benchmark_run_result(
        results_path,
        BenchmarkRunResult(
            run_id="pytest-coverage-repeat-001",
            command_name="pytest coverage gate",
            command_kind="test",
            status="passed",
            worker_count=1,
            input_case_count=194,
            duration_seconds=1.58,
            git_commit="abc1234",
            config_version="scoring_v0",
        ),
    )

    runs = load_benchmark_run_results(results_path)
    assert result["ok"] is True
    assert len(runs) == 1
    assert runs[0].run_id == "pytest-coverage-repeat-001"
    assert runs[0].config_version == "scoring_v0"
    assert result["summary"]["run_count"] == 1
    assert "not scientific performance claims" in result["disclaimer"]


def test_append_benchmark_run_result_rejects_duplicate_run_id(tmp_path) -> None:
    results_path = tmp_path / "benchmark_run_results.json"
    append_benchmark_run_result(
        results_path,
        BenchmarkRunResult(
            run_id="duplicate-run",
            command_name="pytest coverage gate",
            command_kind="test",
            status="passed",
            worker_count=1,
            input_case_count=10,
            duration_seconds=1.0,
            git_commit="abc1234",
            config_version="scoring_v0",
        ),
    )

    try:
        append_benchmark_run_result(
            results_path,
            BenchmarkRunResult(
                run_id="duplicate-run",
                command_name="pytest coverage gate",
                command_kind="test",
                status="passed",
                worker_count=1,
                input_case_count=11,
                duration_seconds=1.1,
                git_commit="def5678",
                config_version="scoring_v0",
            ),
        )
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("duplicate benchmark run_id should fail")


def test_benchmark_run_result_comparison_reports_repeated_commands(tmp_path) -> None:
    results_path = tmp_path / "benchmark_run_results.json"
    first = BenchmarkRunResult(
        run_id="pytest-coverage-001",
        command_name="pytest coverage gate",
        command_kind="test",
        status="passed",
        worker_count=1,
        input_case_count=188,
        duration_seconds=2.0,
        git_commit="abc1234",
        config_version="scoring_v0",
    )
    second = BenchmarkRunResult(
        run_id="pytest-coverage-002",
        command_name="pytest coverage gate",
        command_kind="test",
        status="passed",
        worker_count=2,
        input_case_count=194,
        duration_seconds=1.5,
        git_commit="def5678",
        config_version="scoring_v0",
    )
    append_benchmark_run_result(results_path, first)
    append_benchmark_run_result(results_path, second)

    comparison = benchmark_run_result_comparison(results_path)

    assert comparison["run_count"] == 2
    assert comparison["repeated_command_count"] == 1
    assert comparison["worker_count_change_count"] == 1
    assert comparison["status_change_count"] == 0
    assert comparison["config_version_change_count"] == 0
    assert comparison["comparisons"] == [
        {
            "command_name": "pytest coverage gate",
            "previous_run_id": "pytest-coverage-001",
            "latest_run_id": "pytest-coverage-002",
            "duration_delta_seconds": -0.5,
            "worker_count_changed": True,
            "status_changed": False,
            "input_case_count_delta": 6,
            "config_version_changed": False,
        }
    ]
