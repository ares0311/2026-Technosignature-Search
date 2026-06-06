"""Tests for structural pipeline input validation."""

from __future__ import annotations

import json
from pathlib import Path

from techno_search.cli import main
from techno_search.data_quality import DATA_QUALITY_DISCLAIMER, validate_input

RADIO_FIXTURE = Path(__file__).parent / "fixtures" / "radio" / "sample_hits.csv"
INFRARED_FIXTURE = Path(__file__).parent / "fixtures" / "infrared" / "sample_gaia_wise.csv"
ANOMALY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "anomaly" / "sample_archival_anomaly.csv"
)


def test_validate_input_accepts_radio_fixture() -> None:
    result = validate_input(RADIO_FIXTURE, "radio")
    assert result.ok is True
    assert result.row_count == 5
    assert result.as_dict()["disclaimer"] == DATA_QUALITY_DISCLAIMER


def test_validate_input_accepts_infrared_fixture() -> None:
    result = validate_input(INFRARED_FIXTURE, "infrared")
    assert result.ok is True
    assert result.row_count == 3


def test_validate_input_accepts_anomaly_fixture() -> None:
    result = validate_input(ANOMALY_FIXTURE, "anomaly")
    assert result.ok is True
    assert result.row_count == 2


def test_validate_input_reports_missing_file(tmp_path: Path) -> None:
    result = validate_input(tmp_path / "missing.csv", "radio")
    assert result.ok is False
    assert result.row_count == 0
    assert "File not found" in result.issues[0]


def test_validate_input_reports_bad_numeric_value(tmp_path: Path) -> None:
    bad = tmp_path / "bad_radio.csv"
    bad.write_text(
        "Frequency,SNR,Drift_Rate\nnot-a-number,12.0,0.1\n",
        encoding="utf-8",
    )
    result = validate_input(bad, "radio")
    assert result.ok is False
    # Non-numeric frequency causes normalization to skip the row → no valid hits
    assert any(
        "Non-numeric" in issue or "No valid hits" in issue or "normalized" in issue.lower()
        for issue in result.issues
    )


def test_validate_input_reports_empty_anomaly_file(tmp_path: Path) -> None:
    empty = tmp_path / "empty_anomaly.csv"
    empty.write_text("historical_epoch,modern_epoch,historical_magnitude\n", encoding="utf-8")
    result = validate_input(empty, "anomaly")
    assert result.ok is False
    assert "No data rows found" in result.issues[0]


def test_cli_validate_input_outputs_schema_json(capsys) -> None:
    exit_code = main(["validate-input", str(RADIO_FIXTURE), "--track", "radio"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["schema_version"] == "data_quality_v1"
    assert data["ok"] is True
    assert data["row_count"] == 5
