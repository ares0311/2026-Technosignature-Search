"""Regression checks for bounded stream/process/evict shard isolation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / (
    "run_stream_process_evict_batch.sh"
)


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_post_processing_is_scoped_to_each_chunk_target() -> None:
    """Concurrent shards must never recursively process the shared corpus."""

    script = _script_text()

    assert '--corpus-dir "${OUT_DIR}/${hip}"' in script
    assert '--dat-dir "${OUT_DIR}/${hip}"' in script
    assert '--corpus-dir "${OUT_DIR}"' not in script
    assert '--dat-dir "${OUT_DIR}" --workers' not in script


def test_status_entries_are_per_shard_and_include_success_details() -> None:
    script = _script_text()

    assert 'STATUS_KEY="${STATUS_KEY:-stream_process_evict_batch__$(basename' in script
    assert '"downloaded_targets": downloaded_names' in script
    assert '"evicted_targets": evicted_names' in script
    assert '"app_version": __version__' in script
    assert '--script "${STATUS_KEY}"' in script


def test_launcher_can_bound_concurrent_post_processing_slots() -> None:
    script = _script_text()

    assert "TECHNO_STREAM_PROCESS_SLOT_DIR" in script
    assert "TECHNO_STREAM_PROCESS_SLOT_COUNT" in script
    assert "acquire_processing_slot" in script
    assert "release_processing_slot" in script
    assert "acquire_processing_slot\n  local hip" in script


def test_completed_targets_are_not_downloaded_again_on_resume() -> None:
    script = _script_text()

    assert "target_has_completed_evidence" in script
    assert "existing .dat and candidate report; no re-download needed" in script
    assert '"already_processed_targets": already_processed_names' in script
    assert '"completed_count": int(os.environ["COMPLETED_COUNT"])' in script


def test_hunter_search_can_isolate_results_and_reuse_existing_hit_tables() -> None:
    script = _script_text()

    assert '--results-dir) RESULTS_DIR="$2"' in script
    assert '--out-dir) OUT_DIR="$2"' in script
    assert '--results-dir "${RESULTS_DIR}"' in script
    assert "target_has_hit_table" in script
    assert "existing .dat will be scored into this search" in script
    assert "source_url_missing_and_no_local_dat" in script
    assert "pipeline_evidence_incomplete" in script
    assert 'EVICTION_OCCURRED=1' in script
    assert 'LOCAL_DAT_REUSE_COUNT=$((LOCAL_DAT_REUSE_COUNT + 1))' in script
    assert 'row.get("source_data_path", "")' in script
    assert 'scoring preserved local evidence' in script
    assert 'COMPLETED_COUNT=$((NEWLY_PROCESSED_COUNT + ALREADY_PROCESSED_COUNT))' in script
    assert '"local_dat_reuse_targets": local_dat_reuse_names' in script


def test_explicit_hunter_status_key_keeps_real_acquisition_visible() -> None:
    script = _script_text()

    assert '--status-key) STATUS_KEY="$2"' in script
    assert 'if [[ -n "${STATUS_KEY:-}" ]]; then' in script
    assert "Required Hunter acquisition status record failed" in script


def test_local_dat_only_manifest_executes_real_dry_run_dispatch(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "targets": [
                    {
                        "hip": "HIP123",
                        "source_hdf5_url": "",
                        "estimated_download_gb": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "bash",
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest),
            "--out-dir",
            str(tmp_path / "data"),
            "--results-dir",
            str(tmp_path / "results"),
            "--log-file",
            str(tmp_path / "run.log"),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "TECHNO_STREAM_PROCESS_PYTHON": sys.executable},
    )

    assert result.returncode == 0, result.stderr
    assert "Would process 1 targets" in result.stdout


def test_completed_local_evidence_is_not_reported_as_raw_eviction(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "targets": [
                    {
                        "hip": "HIP123",
                        "source_hdf5_url": "",
                        "estimated_download_gb": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    target_dir = tmp_path / "data" / "HIP123"
    target_dir.mkdir(parents=True)
    (target_dir / "capture.dat").write_text("", encoding="utf-8")
    report_dir = tmp_path / "results" / "capture"
    report_dir.mkdir(parents=True)
    (report_dir / "capture.manifest.json").write_text("{}\n", encoding="utf-8")

    result = subprocess.run(
        [
            "bash",
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest),
            "--out-dir",
            str(tmp_path / "data"),
            "--results-dir",
            str(tmp_path / "results"),
            "--log-file",
            str(tmp_path / "run.log"),
        ],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "TECHNO_STREAM_PROCESS_PYTHON": sys.executable},
    )

    assert result.returncode == 0, result.stderr
    assert "Newly processed: 0" in result.stdout
    assert "Evicted (raw payload deleted after processing): 0" in result.stdout
    assert "Already processed (download skipped): 1" in result.stdout
