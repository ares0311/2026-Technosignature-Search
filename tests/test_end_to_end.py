"""End-to-end pipeline integration tests using real fixture input files."""
from __future__ import annotations

from pathlib import Path

from techno_search.pipeline_runner import PipelineRunResult, run_pipeline

RADIO_FIXTURE = Path(__file__).parent / "fixtures" / "radio" / "sample_hits.csv"
INFRARED_FIXTURE = Path(__file__).parent / "fixtures" / "infrared" / "sample_gaia_wise.csv"


def test_radio_pipeline_runs_successfully(tmp_path: Path) -> None:
    result = run_pipeline(RADIO_FIXTURE, "radio", tmp_path)
    assert isinstance(result, PipelineRunResult)
    assert result.ok, f"Pipeline failed: {result.error}"
    assert result.track.value == "radio"
    assert result.pathway != "unknown"


def test_radio_pipeline_writes_report_files(tmp_path: Path) -> None:
    result = run_pipeline(RADIO_FIXTURE, "radio", tmp_path)
    assert result.ok
    assert result.report_paths.markdown_path.exists()
    assert result.report_paths.json_path.exists()
    assert result.report_paths.manifest_path.exists()


def test_radio_pipeline_report_has_disclaimer(tmp_path: Path) -> None:
    result = run_pipeline(RADIO_FIXTURE, "radio", tmp_path)
    assert result.ok
    md_text = result.report_paths.markdown_path.read_text()
    assert (
        "not a detection" in md_text.lower()
        or "not constitute" in md_text.lower()
        or "unconfirmed" in md_text.lower()
        or "disclaimer" in md_text.lower()
    )


def test_radio_pipeline_manifest_has_candidate_id(tmp_path: Path) -> None:
    import json
    result = run_pipeline(RADIO_FIXTURE, "radio", tmp_path, candidate_id="test-radio-e2e")
    assert result.ok
    assert result.candidate_id == "test-radio-e2e"
    manifest = json.loads(result.report_paths.manifest_path.read_text())
    assert manifest["candidate_id"] == "test-radio-e2e"


def test_infrared_pipeline_runs_successfully(tmp_path: Path) -> None:
    result = run_pipeline(INFRARED_FIXTURE, "infrared", tmp_path)
    assert isinstance(result, PipelineRunResult)
    assert result.ok, f"Pipeline failed: {result.error}"
    assert result.track.value == "infrared"
    assert result.pathway != "unknown"


def test_infrared_pipeline_writes_report_files(tmp_path: Path) -> None:
    result = run_pipeline(INFRARED_FIXTURE, "infrared", tmp_path)
    assert result.ok
    assert result.report_paths.markdown_path.exists()
    assert result.report_paths.json_path.exists()


def test_pipeline_invalid_track_returns_error(tmp_path: Path) -> None:
    result = run_pipeline(RADIO_FIXTURE, "invalid_track", tmp_path)
    assert not result.ok
    assert result.error is not None
    assert "unknown track" in result.error.lower()


def test_pipeline_missing_file_returns_error(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.csv"
    result = run_pipeline(missing, "radio", tmp_path)
    assert not result.ok
    assert result.error is not None


def test_pipeline_as_dict_has_required_keys(tmp_path: Path) -> None:
    result = run_pipeline(RADIO_FIXTURE, "radio", tmp_path)
    d = result.as_dict()
    assert "candidate_id" in d
    assert "track" in d
    assert "pathway" in d
    assert "ok" in d
    assert "markdown_path" in d
    assert "json_path" in d


def test_pipeline_ok_false_has_error_key(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.csv"
    result = run_pipeline(missing, "radio", tmp_path)
    d = result.as_dict()
    assert d["ok"] is False
    assert d["error"] is not None
