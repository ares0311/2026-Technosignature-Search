"""Tests for the six-worker/six-shard validation launcher."""

from __future__ import annotations

import sys

import pytest
from scripts.run_parallel_validation import pytest_command


def test_pytest_command_uses_six_loadfile_shards_by_default_shape() -> None:
    command = pytest_command(6, 6, ["tests/test_version.py"])

    assert command == [
        sys.executable,
        "-m",
        "pytest",
        "-n",
        "6",
        "--dist=loadfile",
        "--tb=short",
        "-q",
        "--cov=techno_search",
        "--cov-report=term-missing",
        "tests/test_version.py",
    ]


def test_pytest_command_rejects_worker_shard_mismatch() -> None:
    with pytest.raises(ValueError, match="must match"):
        pytest_command(6, 5, [])
