#!/usr/bin/env python3
"""Launch six isolated stream/process/evict shards from one terminal.

The launcher validates that the shard manifests are disjoint, refuses to
repeat a completed batch by default, checks the worst-case raw-chunk footprint
against the project's hard local-storage cap, and multiplexes all shard output
to one terminal.  The per-shard runner remains responsible for acquisition,
turboSETI, pipeline execution, raw eviction, and status-manifest publication.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import re
import selectors
import shlex
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO, cast

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNNER = REPO_ROOT / "scripts" / "run_stream_process_evict_batch.sh"
DEFAULT_STATUS_FILE = REPO_ROOT / "docs" / "data_collection_status.json"
DEFAULT_LOG_DIR = REPO_ROOT / "data_cache" / "logs"
DEFAULT_LOCK_FILE = REPO_ROOT / "data_cache" / "six_shard_downloads.lock"
DEFAULT_STORAGE_DIRS = (REPO_ROOT / "data", REPO_ROOT / "models", REPO_ROOT / "artifacts")
SHARD_COUNT = 6


class LauncherError(RuntimeError):
    """Raised when a launcher safety check fails."""


@dataclass(frozen=True)
class ShardPlan:
    number: int
    manifest: Path
    target_count: int
    target_ids: tuple[str, ...]
    peak_chunk_gb: float
    log_file: Path


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _nonnegative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def _resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def _manifest_paths(prefix: str | None, explicit: Sequence[str] | None) -> list[Path]:
    if prefix and explicit:
        raise LauncherError("use either MANIFEST_PREFIX or six --manifest options, not both")
    if explicit:
        if len(explicit) != SHARD_COUNT:
            raise LauncherError(f"exactly {SHARD_COUNT} --manifest options are required")
        return [_resolve_path(value) for value in explicit]
    if not prefix:
        raise LauncherError("MANIFEST_PREFIX or six --manifest options are required")
    prefix_path = _resolve_path(prefix)
    return [
        Path(f"{prefix_path}_shard{number}_manifest.json")
        for number in range(1, SHARD_COUNT + 1)
    ]


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LauncherError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LauncherError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise LauncherError(f"expected a JSON object in {path}")
    return payload


def _status_run_is_complete(status_file: Path, manifest: Path, target_count: int) -> bool:
    if not status_file.exists():
        return False
    payload = _read_json_object(status_file)
    runs = payload.get("runs", {})
    if not isinstance(runs, dict):
        return False
    key = f"stream_process_evict_batch__{manifest.stem}"
    run = runs.get(key, {})
    if not isinstance(run, dict):
        return False
    try:
        failed_count = int(run.get("failed_count", -1))
        targets_attempted = int(run.get("targets_attempted", -1))
        completed_count = int(run.get("completed_count", run.get("evicted_count", -1)))
    except (TypeError, ValueError):
        return False
    return bool(
        run.get("ok") is True
        and failed_count == 0
        and targets_attempted >= target_count
        and completed_count >= target_count
    )


def _safe_run_label(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise LauncherError(
            "run label may contain only letters, numbers, dots, underscores, and hyphens"
        )
    return value


def _load_shard_plan(
    number: int,
    manifest: Path,
    *,
    chunk_size: int,
    limit: int,
    log_file: Path,
) -> ShardPlan:
    payload = _read_json_object(manifest)
    if payload.get("acquisition_mode") != "stream_process_evict":
        raise LauncherError(f"shard {number} is not stream_process_evict: {manifest}")
    targets = payload.get("targets")
    if not isinstance(targets, list):
        raise LauncherError(f"shard {number} has no targets list: {manifest}")
    selected = targets[:limit] if limit else targets
    if not selected:
        raise LauncherError(f"shard {number} has no selected targets: {manifest}")

    target_ids: list[str] = []
    sizes: list[float] = []
    for index, row in enumerate(selected, start=1):
        if not isinstance(row, dict):
            raise LauncherError(f"shard {number} target row {index} is not an object")
        target = str(row.get("hip", "")).strip()
        url = str(row.get("source_hdf5_url", "")).strip()
        try:
            size_gb = float(row.get("estimated_download_gb", 0))
        except (TypeError, ValueError) as exc:
            raise LauncherError(
                f"shard {number} target row {index} has invalid estimated_download_gb"
            ) from exc
        if not target or not url or size_gb <= 0:
            raise LauncherError(
                f"shard {number} target row {index} requires hip, source_hdf5_url, "
                "and positive estimated_download_gb"
            )
        target_ids.append(target)
        sizes.append(size_gb)

    if len(set(target_ids)) != len(target_ids):
        raise LauncherError(f"shard {number} contains duplicate target IDs")
    peak_chunk_gb = sum(sorted(sizes, reverse=True)[:chunk_size])
    return ShardPlan(
        number=number,
        manifest=manifest,
        target_count=len(target_ids),
        target_ids=tuple(target_ids),
        peak_chunk_gb=peak_chunk_gb,
        log_file=log_file,
    )


def build_plans(
    manifests: Sequence[Path],
    *,
    chunk_size: int,
    limit: int,
    log_dir: Path,
    run_label: str,
) -> list[ShardPlan]:
    if len(manifests) != SHARD_COUNT:
        raise LauncherError(f"exactly {SHARD_COUNT} shard manifests are required")
    plans = [
        _load_shard_plan(
            number,
            manifest,
            chunk_size=chunk_size,
            limit=limit,
            log_file=log_dir / f"{run_label}_shard{number}.log",
        )
        for number, manifest in enumerate(manifests, start=1)
    ]
    owners: dict[str, int] = {}
    for plan in plans:
        for target in plan.target_ids:
            previous = owners.setdefault(target, plan.number)
            if previous != plan.number:
                raise LauncherError(
                    f"target {target!r} appears in both shard {previous} and shard {plan.number}"
                )
    return plans


def _directory_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except FileNotFoundError:
                continue
    return total


def storage_preflight(
    plans: Sequence[ShardPlan],
    *,
    usage_dirs: Sequence[Path],
    storage_cap_gb: float,
    free_space_reserve_gb: float,
) -> tuple[float, float, float]:
    current_gb = sum(_directory_size_bytes(path) for path in usage_dirs) / 1024**3
    peak_raw_gb = sum(plan.peak_chunk_gb for plan in plans)
    projected_gb = current_gb + peak_raw_gb
    if projected_gb > storage_cap_gb:
        raise LauncherError(
            f"storage preflight failed: current {current_gb:.2f}GB + worst-case concurrent "
            f"chunks {peak_raw_gb:.2f}GB = {projected_gb:.2f}GB, above the "
            f"{storage_cap_gb:.2f}GB cap"
        )
    free_gb = shutil.disk_usage(REPO_ROOT).free / 1024**3
    if free_gb - peak_raw_gb < free_space_reserve_gb:
        raise LauncherError(
            f"free-space preflight failed: {free_gb:.2f}GB free - {peak_raw_gb:.2f}GB "
            f"worst-case chunks would violate the {free_space_reserve_gb:.2f}GB reserve"
        )
    return current_gb, peak_raw_gb, projected_gb


def _build_command(
    plan: ShardPlan,
    *,
    runner: Path,
    chunk_size: int,
    limit: int,
    pipeline_workers_per_shard: int,
) -> list[str]:
    command: list[str] = []
    caffeinate = shutil.which("caffeinate")
    if caffeinate:
        command.extend([caffeinate, "-i"])
    command.extend(
        [
            "bash",
            str(runner),
            "--manifest",
            str(plan.manifest),
            "--chunk-size",
            str(chunk_size),
            "--pipeline-workers",
            str(pipeline_workers_per_shard),
            "--log-file",
            str(plan.log_file),
        ]
    )
    if limit:
        command.extend(["--limit", str(limit)])
    return command


def _terminate_children(processes: dict[int, subprocess.Popen[str]]) -> None:
    active = [process for process in processes.values() if process.poll() is None]
    for process in active:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
    deadline = time.monotonic() + 10
    while any(process.poll() is None for process in active) and time.monotonic() < deadline:
        time.sleep(0.1)
    for process in active:
        if process.poll() is None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)


def _stream_children(processes: dict[int, subprocess.Popen[str]]) -> dict[int, int]:
    selector = selectors.DefaultSelector()
    for shard, process in processes.items():
        if process.stdout is None:
            raise LauncherError(f"shard {shard} has no output pipe")
        selector.register(process.stdout, selectors.EVENT_READ, shard)
    while selector.get_map():
        for key, _ in selector.select(timeout=1):
            stream = cast(TextIO, key.fileobj)
            line = stream.readline()
            if line:
                print(f"[shard{key.data}] {line}", end="", flush=True)
            else:
                selector.unregister(stream)
                stream.close()
    return {shard: process.wait() for shard, process in processes.items()}


def _storage_usage_dirs(explicit: Sequence[str] | None) -> list[Path]:
    if explicit:
        return [_resolve_path(value) for value in explicit]
    configured = os.environ.get("TECHNO_LOCAL_STORAGE_USAGE_DIRS")
    if configured:
        return [_resolve_path(value) for value in shlex.split(configured)]
    return list(DEFAULT_STORAGE_DIRS)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest_prefix",
        nargs="?",
        metavar="MANIFEST_PREFIX",
        help="path before _shard1_manifest.json ... _shard6_manifest.json",
    )
    parser.add_argument(
        "--manifest",
        action="append",
        help="explicit shard manifest; provide exactly six in shard order",
    )
    parser.add_argument("--chunk-size", type=_positive_int, default=10)
    parser.add_argument("--limit", type=_nonnegative_int, default=0)
    parser.add_argument("--pipeline-workers-per-shard", type=_positive_int, default=6)
    parser.add_argument(
        "--max-total-pipeline-workers",
        type=_positive_int,
        default=12,
        help="bounds simultaneous post-processing; default leaves workstation headroom",
    )
    parser.add_argument(
        "--storage-cap-gb",
        type=_positive_float,
        default=float(os.environ.get("TECHNO_LOCAL_STORAGE_CAP_GB", "100")),
    )
    parser.add_argument(
        "--free-space-reserve-gb",
        type=_nonnegative_float,
        default=float(os.environ.get("TECHNO_EXTENDED_CORPUS_FREE_SPACE_RESERVE_GB", "10")),
    )
    parser.add_argument("--storage-usage-dir", action="append")
    parser.add_argument("--status-file", default=str(DEFAULT_STATUS_FILE))
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR))
    parser.add_argument("--run-label")
    parser.add_argument("--rerun-completed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def run(args: argparse.Namespace) -> int:
    manifests = _manifest_paths(args.manifest_prefix, args.manifest)
    log_dir = _resolve_path(args.log_dir)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    prefix_name = Path(args.manifest_prefix).name if args.manifest_prefix else "explicit_manifests"
    run_label = _safe_run_label(args.run_label or f"{prefix_name}_{timestamp}")
    plans = build_plans(
        manifests,
        chunk_size=args.chunk_size,
        limit=args.limit,
        log_dir=log_dir,
        run_label=run_label,
    )

    status_file = _resolve_path(args.status_file)
    completed = [
        plan
        for plan in plans
        if _status_run_is_complete(status_file, plan.manifest, plan.target_count)
    ]
    if completed and not args.rerun_completed:
        numbers = ", ".join(str(plan.number) for plan in completed)
        raise LauncherError(
            f"refusing to re-download completed shard(s) {numbers}; use new manifests or "
            "--rerun-completed only when repetition is intentional"
        )

    usage_dirs = _storage_usage_dirs(args.storage_usage_dir)
    current_gb, peak_raw_gb, projected_gb = storage_preflight(
        plans,
        usage_dirs=usage_dirs,
        storage_cap_gb=args.storage_cap_gb,
        free_space_reserve_gb=args.free_space_reserve_gb,
    )
    processing_slots = max(
        1, args.max_total_pipeline_workers // args.pipeline_workers_per_shard
    )
    processing_slots = min(SHARD_COUNT, processing_slots)

    print("Six-shard stream/process/evict preflight")
    print(f"  shards: {SHARD_COUNT}")
    print(f"  targets: {sum(plan.target_count for plan in plans)}")
    print(f"  pipeline workers per shard: {args.pipeline_workers_per_shard}")
    print(f"  simultaneous processing shards: {processing_slots}")
    print(
        "  maximum simultaneous pipeline workers: "
        f"{processing_slots * args.pipeline_workers_per_shard}"
    )
    print(
        f"  storage: {current_gb:.2f}GB current + {peak_raw_gb:.2f}GB worst-case "
        f"chunks = {projected_gb:.2f}GB / {args.storage_cap_gb:.2f}GB cap"
    )

    runner = DEFAULT_RUNNER
    if not runner.is_file():
        raise LauncherError(f"shard runner not found: {runner}")
    commands = {
        plan.number: _build_command(
            plan,
            runner=runner,
            chunk_size=args.chunk_size,
            limit=args.limit,
            pipeline_workers_per_shard=args.pipeline_workers_per_shard,
        )
        for plan in plans
    }
    if args.dry_run:
        for plan in plans:
            print(f"  shard {plan.number}: {shlex.join(commands[plan.number])}")
        print("Dry run only; no downloads or child processes were started.")
        return 0

    log_dir.mkdir(parents=True, exist_ok=True)
    DEFAULT_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    slot_root = REPO_ROOT / "data_cache" / f"processing_slots_{run_label}_{os.getpid()}"
    slot_root.mkdir(parents=True, exist_ok=False)
    processes: dict[int, subprocess.Popen[str]] = {}
    child_env = os.environ.copy()
    child_env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "TECHNO_STREAM_PROCESS_SLOT_DIR": str(slot_root),
            "TECHNO_STREAM_PROCESS_SLOT_COUNT": str(processing_slots),
        }
    )

    previous_sigterm = signal.getsignal(signal.SIGTERM)

    def _handle_sigterm(_signum: int, _frame: object) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _handle_sigterm)
    try:
        with DEFAULT_LOCK_FILE.open("a+", encoding="utf-8") as lock_handle:
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise LauncherError("another six-shard launcher is already running") from exc
            for plan in plans:
                processes[plan.number] = subprocess.Popen(
                    commands[plan.number],
                    cwd=REPO_ROOT,
                    env=child_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    start_new_session=True,
                )
            print("All six shards started; progress is multiplexed below.", flush=True)
            exit_codes = _stream_children(processes)
    except KeyboardInterrupt:
        print(
            "\nInterrupt received; terminating all shard process groups cleanly.",
            file=sys.stderr,
        )
        _terminate_children(processes)
        return 130
    except BaseException:
        _terminate_children(processes)
        raise
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)
        shutil.rmtree(slot_root, ignore_errors=True)

    failures = {shard: code for shard, code in exit_codes.items() if code != 0}
    if failures:
        detail = ", ".join(f"shard{shard}={code}" for shard, code in sorted(failures.items()))
        print(f"Six-shard run finished with failures: {detail}", file=sys.stderr)
        return 1
    print("All six shards completed successfully.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except LauncherError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
