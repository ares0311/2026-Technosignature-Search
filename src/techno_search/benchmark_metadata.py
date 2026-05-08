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


@dataclass(frozen=True)
class BenchmarkCommand:
    """One local validation command recorded for benchmark metadata."""

    name: str
    command: str
    command_kind: str
    worker_count: int
    status: str


def default_benchmark_metadata_path() -> Path:
    """Return the repository-local benchmark metadata fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "benchmark_metadata.json"
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


def _command_from_mapping(data: dict[str, Any]) -> BenchmarkCommand:
    return BenchmarkCommand(
        name=str(data["name"]),
        command=str(data["command"]),
        command_kind=str(data["command_kind"]),
        worker_count=int(data.get("worker_count", 1)),
        status=str(data["status"]),
    )


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
