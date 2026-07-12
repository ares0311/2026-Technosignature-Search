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

    assert 'STATUS_KEY="stream_process_evict_batch__$(basename' in script
    assert '"downloaded_targets": downloaded_names' in script
    assert '"evicted_targets": evicted_names' in script
    assert '"app_version": __version__' in script
    assert '--script "${STATUS_KEY}"' in script
