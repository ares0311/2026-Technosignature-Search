"""Regression checks for bounded stream/process/evict shard isolation."""

from __future__ import annotations

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


def test_explicit_hunter_status_key_keeps_real_acquisition_visible() -> None:
    script = _script_text()

    assert '--status-key) STATUS_KEY="$2"' in script
    assert 'if [[ -n "${STATUS_KEY:-}" ]]; then' in script
    assert "Required Hunter acquisition status record failed" in script
