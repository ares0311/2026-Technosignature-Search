from __future__ import annotations

from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / (
    "download_bl_extended_corpus.sh"
)


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_extended_corpus_downloader_discovers_current_bl_urls() -> None:
    script = _script_text()

    assert "breakthroughinitiatives.org/opendatasearch" in script
    assert "bldata\\.berkeley\\.edu" in script
    assert "file_type=HDF5" in script
    assert "blpd0.ssl.berkeley.edu" not in script


def test_extended_corpus_downloader_fails_closed_on_zero_evidence() -> None:
    script = _script_text()

    assert "downloaded=0" in script
    assert 'if [[ "${downloaded}" -eq 0 ]]' in script
    assert "empty directories are not evidence" in script
    assert "exit 1" in script


def test_extended_corpus_downloader_has_non_networked_inspection_mode() -> None:
    script = _script_text()

    assert "--dry-run" in script
    assert "-h|--help" in script
    assert "Dry run complete; no network download attempted" in script


def test_extended_corpus_downloader_preserves_scientific_guardrails() -> None:
    script = _script_text()

    assert "No file or hit table entry constitutes a" in script
    assert "technosignature detection" in script
    assert "authorizes external submission" in script
