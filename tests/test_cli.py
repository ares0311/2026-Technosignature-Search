import json
from io import StringIO

from techno_search.cli import main, score_batch


def _candidate_json() -> dict[str, object]:
    return {
        "candidate_id": "cli-radio",
        "track": "radio",
        "source_ids": ["synthetic-cli"],
        "features": {
            "snr": 35.0,
            "bandwidth_hz": 1.5,
            "drift_rate_hz_per_sec": 2.0,
            "on_target_presence_score": 0.9,
            "off_target_presence_score": 0.05,
            "rfi_band_overlap_score": 0.05,
            "frequency_persistence_score": 0.05,
            "instrumental_artifact_score": 0.05,
            "metadata_completeness_score": 0.9,
            "data_quality_score": 0.9,
            "provenance_completeness_score": 0.9,
        },
        "provenance": {"source_dataset": "synthetic-cli"},
    }


def test_cli_scores_candidate_json_to_stdout(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(["score", str(input_path)], stdout=stdout)
    packet = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert packet["candidate_id"] == "cli-radio"
    assert packet["recommended_pathway"]
    assert packet["disclaimer"]


def test_cli_writes_reports(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    output_dir = tmp_path / "reports"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(
        ["score", str(input_path), "--output-dir", str(output_dir), "--prefix", "cli-radio"],
        stdout=stdout,
    )

    assert exit_code == 0
    assert (output_dir / "cli-radio.md").exists()
    assert (output_dir / "cli-radio.json").exists()
    assert (output_dir / "cli-radio.manifest.json").exists()
    assert "cli-radio.md" in stdout.getvalue()


def test_cli_scores_batch_directory(tmp_path) -> None:
    input_dir = tmp_path / "candidates"
    output_dir = tmp_path / "reports"
    input_dir.mkdir()
    (input_dir / "candidate-a.json").write_text(json.dumps(_candidate_json()), encoding="utf-8")
    candidate_b = _candidate_json() | {"candidate_id": "cli-radio-b"}
    (input_dir / "candidate-b.json").write_text(json.dumps(candidate_b), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(
        ["score-batch", str(input_dir), str(output_dir), "--prefix", "batch-"],
        stdout=stdout,
    )

    manifest_path = output_dir / "batch_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert stdout.getvalue().strip() == str(manifest_path)
    assert manifest["candidate_count"] == 2
    assert manifest["config_version"] == "scoring_v0"
    assert (output_dir / "batch-cli-radio.md").exists()
    assert (output_dir / "batch-cli-radio-b.md").exists()
    assert len(manifest["reports"]) == 2


def test_score_batch_regenerates_expected_example_candidate_set(tmp_path) -> None:
    manifest_path = score_batch("examples/candidates", tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["candidate_count"] == 3
    assert {report["candidate_id"] for report in manifest["reports"]} == {
        "example-radio-clean",
        "example-infrared-clean",
        "example-anomaly-clean",
    }
    for report in manifest["reports"]:
        assert report["config_version"] == "scoring_v0"
        assert (tmp_path / f"{report['candidate_id']}.md").exists()
        assert (tmp_path / f"{report['candidate_id']}.json").exists()
        assert (tmp_path / f"{report['candidate_id']}.manifest.json").exists()


def test_cli_calibration_summary_outputs_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["calibration-summary"], stdout=stdout)
    summary = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert summary["total"] == 15
    assert summary["by_track"] == {"anomaly": 6, "infrared": 5, "radio": 4}
    assert summary["by_expected_pathway"] == {"do_not_submit_false_positive": 15}


def test_cli_validate_candidate_accepts_normalized_candidate(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(["validate-candidate", str(input_path)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["errors"] == []


def test_cli_validate_candidate_rejects_unsupported_language(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    candidate = _candidate_json() | {"candidate_id": "alien signal claim"}
    input_path.write_text(json.dumps(candidate), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(["validate-candidate", str(input_path)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert result["ok"] is False
    assert "alien signal" in result["errors"][0]


def test_cli_validate_reports_accepts_generated_reports(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    output_dir = tmp_path / "reports"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    main(["score", str(input_path), "--output-dir", str(output_dir)], stdout=StringIO())
    stdout = StringIO()

    exit_code = main(["validate-reports", str(output_dir)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["errors"] == []
