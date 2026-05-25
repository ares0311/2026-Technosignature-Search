"""End-to-end pipeline integration tests using real fixture input files."""
from __future__ import annotations

import json
from pathlib import Path

from techno_search.cli import main
from techno_search.pipeline_runner import PipelineRunResult, run_pipeline

RADIO_FIXTURE = Path(__file__).parent / "fixtures" / "radio" / "sample_hits.csv"
INFRARED_FIXTURE = Path(__file__).parent / "fixtures" / "infrared" / "sample_gaia_wise.csv"
ANOMALY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "anomaly" / "sample_archival_anomaly.csv"
)


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


def test_anomaly_pipeline_runs_successfully(tmp_path: Path) -> None:
    result = run_pipeline(ANOMALY_FIXTURE, "anomaly", tmp_path)
    assert result.ok, f"Pipeline failed: {result.error}"
    assert result.track.value == "anomaly"
    assert result.reader_type == "archival_anomaly_csv"
    assert result.row_count == 2
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
    assert "disclaimer" in d
    assert "candidate_id" in d
    assert "track" in d
    assert "pathway" in d
    assert "ok" in d
    assert "input_validation" in d
    assert "reader_type" in d
    assert "row_count" in d
    assert "markdown_path" in d
    assert "json_path" in d


def test_pipeline_ok_false_has_error_key(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.csv"
    result = run_pipeline(missing, "radio", tmp_path)
    d = result.as_dict()
    assert d["ok"] is False
    assert d["error"] is not None
    assert d["input_validation"]["ok"] is False


def test_cli_run_pipeline_outputs_json(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "run-pipeline",
            str(RADIO_FIXTURE),
            "--track",
            "radio",
            "--output-dir",
            str(tmp_path),
            "--candidate-id",
            "cli-radio-pipeline",
        ]
    )
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["ok"] is True
    assert data["candidate_id"] == "cli-radio-pipeline"
    assert data["input_validation"]["ok"] is True
    assert Path(data["json_path"]).exists()


def test_cli_run_pipeline_rejects_invalid_input(tmp_path: Path, capsys) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("Frequency,SNR,Drift_Rate\nnot-a-number,1.0,0.0\n", encoding="utf-8")
    exit_code = main(
        [
            "run-pipeline",
            str(bad),
            "--track",
            "radio",
            "--output-dir",
            str(tmp_path),
        ]
    )
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert data["ok"] is False
    assert data["input_validation"]["ok"] is False
    assert "Input validation failed" in data["error"]
