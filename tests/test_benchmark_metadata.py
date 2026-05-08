from techno_search.benchmark_metadata import (
    BENCHMARK_METADATA_DISCLAIMER,
    benchmark_metadata_summary,
    load_benchmark_commands,
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
