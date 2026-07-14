"""Tests for the one-terminal six-shard acquisition launcher."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.run_six_shard_downloads import LauncherError, build_plans, storage_preflight

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run_six_shard_downloads.py"


def _write_shards(tmp_path: Path, *, duplicate: bool = False) -> Path:
    prefix = tmp_path / "review_batch"
    for shard in range(1, 7):
        target = "HIP_DUPLICATE" if duplicate and shard in {1, 2} else f"HIP{shard}"
        payload = {
            "batch_id": f"review_batch_shard{shard}",
            "project": "technosignatures",
            "role": "live_search",
            "acquisition_mode": "stream_process_evict",
            "targets": [
                {
                    "hip": target,
                    "source_hdf5_url": f"https://example.invalid/{target}.h5",
                    "estimated_download_gb": 0.25,
                }
            ],
        }
        Path(f"{prefix}_shard{shard}_manifest.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
    return prefix


def test_build_plans_rejects_cross_shard_target_overlap(tmp_path: Path) -> None:
    prefix = _write_shards(tmp_path, duplicate=True)
    manifests = [Path(f"{prefix}_shard{shard}_manifest.json") for shard in range(1, 7)]

    with pytest.raises(LauncherError, match="appears in both shard 1 and shard 2"):
        build_plans(
            manifests,
            chunk_size=10,
            limit=0,
            log_dir=tmp_path / "logs",
            run_label="test",
        )


def test_storage_preflight_sums_one_peak_chunk_per_shard(tmp_path: Path) -> None:
    prefix = _write_shards(tmp_path)
    manifests = [Path(f"{prefix}_shard{shard}_manifest.json") for shard in range(1, 7)]
    plans = build_plans(
        manifests,
        chunk_size=10,
        limit=0,
        log_dir=tmp_path / "logs",
        run_label="test",
    )

    current, peak, projected = storage_preflight(
        plans,
        usage_dirs=[tmp_path / "empty_usage"],
        storage_cap_gb=100,
        free_space_reserve_gb=0,
    )

    assert current == 0
    assert peak == pytest.approx(1.5)
    assert projected == pytest.approx(1.5)


def test_dry_run_builds_six_worker_commands_without_starting_downloads(tmp_path: Path) -> None:
    prefix = _write_shards(tmp_path)
    status_file = tmp_path / "status.json"
    status_file.write_text('{"runs": {}}', encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(prefix),
            "--dry-run",
            "--pipeline-workers-per-shard",
            "6",
            "--storage-usage-dir",
            str(tmp_path / "empty_usage"),
            "--free-space-reserve-gb",
            "0",
            "--status-file",
            str(status_file),
            "--log-dir",
            str(tmp_path / "logs"),
            "--run-label",
            "test",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.count("--pipeline-workers 6") == 6
    assert "simultaneous processing shards: 2" in completed.stdout
    assert "maximum simultaneous pipeline workers: 12" in completed.stdout
    assert "Dry run only; no downloads or child processes were started." in completed.stdout


def test_completed_shards_are_not_silently_redownloaded(tmp_path: Path) -> None:
    prefix = _write_shards(tmp_path)
    manifest = Path(f"{prefix}_shard1_manifest.json")
    status = {
        "runs": {
            f"stream_process_evict_batch__{manifest.stem}": {
                "ok": True,
                "failed_count": 0,
                "targets_attempted": 1,
                "evicted_count": 1,
            }
        }
    }
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps(status), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(prefix),
            "--dry-run",
            "--storage-usage-dir",
            str(tmp_path / "empty_usage"),
            "--free-space-reserve-gb",
            "0",
            "--status-file",
            str(status_file),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "refusing to re-download completed shard(s) 1" in completed.stderr
