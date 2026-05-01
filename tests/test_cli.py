import json
from io import StringIO

from techno_search.cli import main


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
    assert (output_dir / "batch-cli-radio.md").exists()
    assert (output_dir / "batch-cli-radio-b.md").exists()
    assert len(manifest["reports"]) == 2
