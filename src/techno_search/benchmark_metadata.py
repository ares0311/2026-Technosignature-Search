"""Local synthetic validation benchmark metadata helpers."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BENCHMARK_METADATA_SCHEMA_VERSION = "local_synthetic_benchmark_metadata_v1"
BENCHMARK_METADATA_DISCLAIMER = (
    "Benchmark metadata records local validation context only; it is not a "
    "scientific performance claim or candidate-quality metric."
)
BENCHMARK_RUN_RESULT_SCHEMA_VERSION = "synthetic_benchmark_run_result_v1"
BENCHMARK_RUN_RESULT_DISCLAIMER = (
    "Benchmark run results record local synthetic execution metadata only; they "
    "are not scientific performance claims or survey sensitivity estimates."
)


@dataclass(frozen=True)
class BenchmarkCommand:
    """One local validation command recorded for benchmark metadata."""

    name: str
    command: str
    command_kind: str
    worker_count: int
    status: str


@dataclass(frozen=True)
class BenchmarkRunResult:
    """One recorded local synthetic benchmark run-result entry."""

    run_id: str
    command_name: str
    command_kind: str
    status: str
    worker_count: int
    input_case_count: int
    duration_seconds: float
    git_commit: str
    config_version: str


def default_benchmark_metadata_path() -> Path:
    """Return the repository-local benchmark metadata fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "benchmark_metadata.json"
    )


def default_benchmark_run_results_path() -> Path:
    """Return the repository-local benchmark run-results fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "benchmark_run_results.json"
    )


def load_benchmark_commands(path: Path | None = None) -> tuple[BenchmarkCommand, ...]:
    """Load benchmark metadata command entries."""

    metadata_path = path or default_benchmark_metadata_path()
    with metadata_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != BENCHMARK_METADATA_SCHEMA_VERSION:
        msg = (
            f"Unsupported benchmark metadata schema version {schema_version!r}; "
            f"expected {BENCHMARK_METADATA_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(_command_from_mapping(command) for command in data["commands"])


def load_benchmark_run_results(path: Path | None = None) -> tuple[BenchmarkRunResult, ...]:
    """Load local synthetic benchmark run-result entries."""

    results_path = path or default_benchmark_run_results_path()
    with results_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != BENCHMARK_RUN_RESULT_SCHEMA_VERSION:
        msg = (
            f"Unsupported benchmark run-result schema version {schema_version!r}; "
            f"expected {BENCHMARK_RUN_RESULT_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(_run_result_from_mapping(result) for result in data["runs"])


def benchmark_metadata_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize local synthetic validation benchmark metadata."""

    metadata_path = path or default_benchmark_metadata_path()
    with metadata_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    commands = load_benchmark_commands(metadata_path)
    hardware_profile = data["hardware_profile"]
    recommended_limits = data["recommended_limits"]

    return {
        "metadata_path": str(metadata_path),
        "schema_version": BENCHMARK_METADATA_SCHEMA_VERSION,
        "disclaimer": BENCHMARK_METADATA_DISCLAIMER,
        "hardware_profile_path": str(hardware_profile["profile_path"]),
        "machine": str(hardware_profile["machine"]),
        "chip": str(hardware_profile["chip"]),
        "memory_gb": int(hardware_profile["memory_gb"]),
        "cpu_count": int(hardware_profile["cpu_count"]),
        "default_cpu_worker_limit": int(recommended_limits["cpu_workers"]),
        "memory_budget_gb": int(recommended_limits["memory_budget_gb"]),
        "command_count": len(commands),
        "by_command_kind": _counter_to_dict(Counter(command.command_kind for command in commands)),
        "by_status": _counter_to_dict(Counter(command.status for command in commands)),
        "max_recorded_worker_count": max((command.worker_count for command in commands), default=0),
        "commands": [command.command for command in commands],
    }


def benchmark_run_result_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize local synthetic benchmark run-result fixture coverage."""

    results_path = path or default_benchmark_run_results_path()
    runs = load_benchmark_run_results(results_path)
    durations = [run.duration_seconds for run in runs]

    return {
        "results_path": str(results_path),
        "schema_version": BENCHMARK_RUN_RESULT_SCHEMA_VERSION,
        "disclaimer": BENCHMARK_RUN_RESULT_DISCLAIMER,
        "run_count": len(runs),
        "input_case_total": sum(run.input_case_count for run in runs),
        "max_worker_count": max((run.worker_count for run in runs), default=0),
        "max_duration_seconds": max(durations, default=0.0),
        "by_command_kind": _counter_to_dict(Counter(run.command_kind for run in runs)),
        "by_status": _counter_to_dict(Counter(run.status for run in runs)),
        "by_config_version": _counter_to_dict(
            Counter(run.config_version for run in runs)
        ),
        "run_ids": sorted(run.run_id for run in runs),
        "git_commits": sorted({run.git_commit for run in runs}),
    }


def append_benchmark_run_result(
    path: Path,
    run: BenchmarkRunResult,
) -> dict[str, object]:
    """Append one benchmark run-result entry without overwriting prior runs."""

    results_path = Path(path)
    if results_path.exists():
        with results_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        schema_version = str(data.get("schema_version", ""))
        if schema_version != BENCHMARK_RUN_RESULT_SCHEMA_VERSION:
            msg = (
                f"Unsupported benchmark run-result schema version "
                f"{schema_version!r}; expected "
                f"{BENCHMARK_RUN_RESULT_SCHEMA_VERSION!r}"
            )
            raise ValueError(msg)
        runs = list(data.get("runs", []))
    else:
        data = {
            "schema_version": BENCHMARK_RUN_RESULT_SCHEMA_VERSION,
            "description": (
                "Local synthetic benchmark run-result metadata. Entries record "
                "execution context only, not scientific performance claims."
            ),
            "disclaimer": BENCHMARK_RUN_RESULT_DISCLAIMER,
        }
        runs = []

    existing_run_ids = {str(item["run_id"]) for item in runs}
    if run.run_id in existing_run_ids:
        msg = f"Benchmark run_id {run.run_id!r} already exists."
        raise ValueError(msg)

    runs.append(_run_result_to_mapping(run))
    data["runs"] = runs
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "ok": True,
        "results_path": str(results_path),
        "appended_run": _run_result_to_mapping(run),
        "summary": benchmark_run_result_summary(results_path),
        "disclaimer": BENCHMARK_RUN_RESULT_DISCLAIMER,
    }


def benchmark_run_result_comparison(path: Path | None = None) -> dict[str, object]:
    """Compare repeated benchmark run results grouped by command name."""

    results_path = path or default_benchmark_run_results_path()
    runs = load_benchmark_run_results(results_path)
    by_command: dict[str, list[BenchmarkRunResult]] = {}
    for run in runs:
        by_command.setdefault(run.command_name, []).append(run)

    comparisons = []
    for command_name, command_runs in sorted(by_command.items()):
        ordered = sorted(command_runs, key=lambda run: run.run_id)
        if len(ordered) < 2:
            continue
        previous = ordered[-2]
        latest = ordered[-1]
        comparisons.append(
            {
                "command_name": command_name,
                "previous_run_id": previous.run_id,
                "latest_run_id": latest.run_id,
                "duration_delta_seconds": round(
                    latest.duration_seconds - previous.duration_seconds,
                    6,
                ),
                "worker_count_changed": latest.worker_count != previous.worker_count,
                "status_changed": latest.status != previous.status,
                "input_case_count_delta": latest.input_case_count
                - previous.input_case_count,
                "config_version_changed": latest.config_version
                != previous.config_version,
            }
        )

    return {
        "results_path": str(results_path),
        "schema_version": BENCHMARK_RUN_RESULT_SCHEMA_VERSION,
        "disclaimer": BENCHMARK_RUN_RESULT_DISCLAIMER,
        "run_count": len(runs),
        "repeated_command_count": len(comparisons),
        "worker_count_change_count": sum(
            1 for item in comparisons if item["worker_count_changed"]
        ),
        "status_change_count": sum(1 for item in comparisons if item["status_changed"]),
        "config_version_change_count": sum(
            1 for item in comparisons if item["config_version_changed"]
        ),
        "comparisons": comparisons,
    }


def _command_from_mapping(data: dict[str, Any]) -> BenchmarkCommand:
    return BenchmarkCommand(
        name=str(data["name"]),
        command=str(data["command"]),
        command_kind=str(data["command_kind"]),
        worker_count=int(data.get("worker_count", 1)),
        status=str(data["status"]),
    )


def _run_result_from_mapping(data: dict[str, Any]) -> BenchmarkRunResult:
    return BenchmarkRunResult(
        run_id=str(data["run_id"]),
        command_name=str(data["command_name"]),
        command_kind=str(data["command_kind"]),
        status=str(data["status"]),
        worker_count=int(data["worker_count"]),
        input_case_count=int(data["input_case_count"]),
        duration_seconds=float(data["duration_seconds"]),
        git_commit=str(data["git_commit"]),
        config_version=str(data["config_version"]),
    )


def _run_result_to_mapping(run: BenchmarkRunResult) -> dict[str, object]:
    return {
        "run_id": run.run_id,
        "command_name": run.command_name,
        "command_kind": run.command_kind,
        "status": run.status,
        "worker_count": run.worker_count,
        "input_case_count": run.input_case_count,
        "duration_seconds": run.duration_seconds,
        "git_commit": run.git_commit,
        "config_version": run.config_version,
    }


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
