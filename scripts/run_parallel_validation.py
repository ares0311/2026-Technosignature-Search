#!/usr/bin/env python3
"""Run the repository validation suite with six non-overlapping test shards.

pytest-xdist owns the test scheduling: six workers are six active shards, and
``--dist=loadfile`` keeps every test file on one worker while executing each
collected test exactly once. After pytest succeeds, the independent app-version,
Ruff, mypy, scientific ``validate-all``, directive-parity, no-fake-completion,
and verification-freshness checks run concurrently. This is the canonical,
single entry point for "is this repository state currently verified" — see
AGENTS.md's NO UNSUPPORTED COMPLETION CLAIMS section. On a fully clean pass,
it records the tested commit via
``scripts/check_verification_freshness.py --record-pass``.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import selectors
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO, cast

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKERS = 6
DEFAULT_SHARDS = 6


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def pytest_command(workers: int, shards: int, pytest_args: Sequence[str]) -> list[str]:
    if workers != shards:
        raise ValueError(
            "this launcher defines one non-overlapping xdist test shard per worker; "
            "--workers and --shards must match"
        )
    return [
        sys.executable,
        "-m",
        "pytest",
        "-n",
        str(workers),
        "--dist=loadfile",
        "--tb=short",
        "-q",
        "--cov=techno_search",
        "--cov-report=term-missing",
        *pytest_args,
    ]


def _run_parallel_checks(env: dict[str, str]) -> dict[str, int]:
    commands = {
        "app-version": [sys.executable, "scripts/check_app_version.py"],
        "ruff": [sys.executable, "-m", "ruff", "check", "."],
        "mypy": [sys.executable, "-m", "mypy", "src", "--no-error-summary"],
        "validate-all": [sys.executable, "-m", "techno_search.cli", "validate-all"],
        "directive-parity": [sys.executable, "scripts/check_directive_parity.py"],
        "no-fake-completion": [sys.executable, "scripts/check_no_fake_completion.py"],
    }
    processes: dict[str, subprocess.Popen[str]] = {
        name: subprocess.Popen(
            command,
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for name, command in commands.items()
    }
    selector = selectors.DefaultSelector()
    for name, process in processes.items():
        if process.stdout is None:
            raise RuntimeError(f"{name} has no output pipe")
        selector.register(process.stdout, selectors.EVENT_READ, name)
    while selector.get_map():
        for key, _ in selector.select(timeout=1):
            stream = cast(TextIO, key.fileobj)
            line = stream.readline()
            if line:
                print(f"[{key.data}] {line}", end="", flush=True)
            else:
                selector.unregister(stream)
                stream.close()
    return {name: process.wait() for name, process in processes.items()}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=_positive_int, default=DEFAULT_WORKERS)
    parser.add_argument("--shards", type=_positive_int, default=DEFAULT_SHARDS)
    parser.add_argument(
        "--pytest-only",
        action="store_true",
        help="run the six-shard pytest stage without Ruff, mypy, or validate-all",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="extra pytest arguments after --",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if importlib.util.find_spec("xdist") is None:
        print(
            "ERROR: pytest-xdist is required; install the repository dev extras in the venv.",
            file=sys.stderr,
        )
        return 2
    pytest_args = list(args.pytest_args)
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]
    try:
        command = pytest_command(args.workers, args.shards, pytest_args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    print(
        f"Running pytest with {args.workers} workers / {args.shards} "
        "non-overlapping loadfile shards."
    )
    pytest_result = subprocess.run(command, cwd=REPO_ROOT, env=env, check=False)
    if pytest_result.returncode != 0 or args.pytest_only:
        return pytest_result.returncode

    print(
        "pytest passed; running app-version, Ruff, mypy, validate-all, "
        "directive-parity, and no-fake-completion concurrently."
    )
    results = _run_parallel_checks(env)
    failures = {name: code for name, code in results.items() if code != 0}
    if failures:
        detail = ", ".join(f"{name}={code}" for name, code in sorted(failures.items()))
        print(f"Validation failures: {detail}", file=sys.stderr)
        return 1
    print("All parallel validation checks passed.")

    from check_verification_freshness import _uncommitted_changes, record_verification_pass

    if _uncommitted_changes(REPO_ROOT, ("src", "tests", "scripts", "AGENTS.md", "CLAUDE.md")):
        print(
            "NOTE: working tree has uncommitted changes under watched paths; not "
            "recording a verification-pass marker. Commit, then rerun for a "
            "traceable 'verified as of commit <sha>' record "
            "(scripts/check_verification_freshness.py)."
        )
    else:
        marker_path = record_verification_pass(REPO_ROOT)
        print(f"Recorded verification pass at {marker_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
