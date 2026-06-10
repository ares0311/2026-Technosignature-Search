"""Tests for noise threshold calibration tool."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.noise_threshold_calibration import (
    NOISE_CALIBRATION_DISCLAIMER,
    _percentile,
    _std_dev,
    analyze_hit_directory,
    select_calibration_artifacts,
)
from techno_search.observation_artifact import sha256_file

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "radio"


def test_analyze_fixture_dir_succeeds() -> None:
    result = analyze_hit_directory(FIXTURE_DIR, require_approved_real_data=False)
    assert result["ok"] is True


def test_analyze_returns_snr_stats() -> None:
    result = analyze_hit_directory(FIXTURE_DIR, require_approved_real_data=False)
    stats = result["snr_stats"]
    assert stats["count"] > 0
    assert stats["max"] > stats["min"]


def test_analyze_returns_percentiles() -> None:
    result = analyze_hit_directory(FIXTURE_DIR, require_approved_real_data=False)
    percentiles = result["snr_stats"]["percentiles"]
    assert "p50" in percentiles
    assert "p95" in percentiles
    assert "p99" in percentiles


def test_analyze_returns_suggested_thresholds() -> None:
    result = analyze_hit_directory(FIXTURE_DIR, require_approved_real_data=False)
    thresholds = result["suggested_thresholds"]
    assert "high_interest_snr" in thresholds["snr_thresholds"]
    assert "follow_up_snr" in thresholds["snr_thresholds"]
    assert (
        thresholds["pathway_probability_thresholds"]["status"]
        == "not_derived_by_noise_distribution"
    )
    assert thresholds["review_required"] is True


def test_analyze_nonexistent_dir_returns_error() -> None:
    result = analyze_hit_directory(Path("/nonexistent/path/12345"))
    assert result["ok"] is False
    assert "error" in result


def test_analyze_empty_dir_returns_error(tmp_path: Path) -> None:
    result = analyze_hit_directory(tmp_path)
    assert result["ok"] is False


def test_analyze_dat_format_fixture() -> None:
    """Verify .dat format files are analyzed correctly."""
    result = analyze_hit_directory(FIXTURE_DIR, require_approved_real_data=False)
    assert result["file_count"] >= 2  # at least sample_hits.csv + sample_hits_real_format.dat


def test_disclaimer_is_conservative() -> None:
    assert "must pass" in NOISE_CALIBRATION_DISCLAIMER
    assert "citizen-science review" in NOISE_CALIBRATION_DISCLAIMER
    assert "do not constitute" in NOISE_CALIBRATION_DISCLAIMER


def test_percentile_single_value() -> None:
    assert _percentile([5.0], 50.0) == pytest.approx(5.0)


def test_percentile_empty_returns_zero() -> None:
    assert _percentile([], 50.0) == pytest.approx(0.0)


def test_percentile_median() -> None:
    vals = sorted([1.0, 2.0, 3.0, 4.0, 5.0])
    assert _percentile(vals, 50.0) == pytest.approx(3.0)


def test_std_dev_constant_values() -> None:
    assert _std_dev([5.0, 5.0, 5.0]) == pytest.approx(0.0)


def test_std_dev_known_value() -> None:
    # sample std dev of [1, 3] = sqrt(2) ≈ 1.4142
    vals = [1.0, 3.0]
    assert _std_dev(vals) == pytest.approx(2.0 ** 0.5, rel=1e-4)


def test_cli_noise_threshold_calibration(tmp_path: Path) -> None:
    from techno_search.cli import main

    exit_code = main(
        [
            "noise-threshold-calibration",
            str(FIXTURE_DIR),
            "--allow-development-fixtures",
        ]
    )
    assert exit_code == 0


def _write_approved_dat(
    directory: Path,
    name: str,
    *,
    cadence_id: str,
    target_id: str,
    utc_start: str,
    snr_values: tuple[float, ...] = (10.0, 15.0, 25.0),
) -> Path:
    path = directory / name
    rows = "\n".join(
        f"{index}\t0.1\t{snr}\t1420.0\t1420.0"
        for index, snr in enumerate(snr_values, start=1)
    )
    path.write_text(
        "# Source:"
        f"{target_id}\n# MJD: 60000.0\n"
        "# Top_Hit_#\tDrift_Rate\tSNR\tUncorrected_Frequency"
        "\tCorrected_Frequency\n"
        f"{rows}\n",
        encoding="utf-8",
    )
    provenance = {
        "schema_version": "observation_artifact_provenance_v1",
        "artifact_filename": path.name,
        "sha256": sha256_file(path),
        "classification": "real_observation",
        "source_url": "https://example.org/approved-observation",
        "source_archive": "Test archive",
        "instrument": "Green Bank Telescope",
        "downloaded_utc": "2026-06-10T00:00:00Z",
        "data_use_review_status": "approved",
        "provenance_review_status": "approved",
        "human_approval_status": "approved",
        "approved_for_local_real_data": True,
        "external_submission_authorized": False,
        "cadence_id": cadence_id,
        "target_id": target_id,
        "observation_utc_start": utc_start,
    }
    path.with_name(path.name + ".provenance.json").write_text(
        json.dumps(provenance), encoding="utf-8"
    )
    return path


def test_production_selection_rejects_unapproved_and_tampered_files(
    tmp_path: Path,
) -> None:
    approved = _write_approved_dat(
        tmp_path,
        "approved.dat",
        cadence_id="cadence-1",
        target_id="target-1",
        utc_start="2026-01-01T00:00:00Z",
    )
    unapproved = tmp_path / "unapproved.dat"
    unapproved.write_text(approved.read_text(encoding="utf-8"), encoding="utf-8")
    tampered = _write_approved_dat(
        tmp_path,
        "tampered.dat",
        cadence_id="cadence-2",
        target_id="target-2",
        utc_start="2026-01-02T00:00:00Z",
    )
    tampered.write_text(
        tampered.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8"
    )

    selected, skipped = select_calibration_artifacts(tmp_path)

    assert [artifact.path.name for artifact in selected] == ["approved.dat"]
    skipped_reasons = {item["filename"]: item["reason"] for item in skipped}
    assert "No provenance sidecar" not in skipped_reasons["unapproved.dat"]
    assert "SHA-256" in skipped_reasons["tampered.dat"]


def test_derived_cadence_is_not_double_counted_with_source_dat(
    tmp_path: Path,
) -> None:
    source = _write_approved_dat(
        tmp_path,
        "source.dat",
        cadence_id="cadence-1",
        target_id="target-1",
        utc_start="2026-01-01T00:00:00Z",
    )
    derived = tmp_path / "cadence.csv"
    derived.write_text(
        "frequency_mhz,snr,drift_rate_hz_s\n1420.0,12.0,0.1\n",
        encoding="utf-8",
    )
    derived.with_name(derived.name + ".provenance.json").write_text(
        json.dumps(
            {
                "artifact_filename": derived.name,
                "cadence_id": "cadence-1",
                "classification": "derived_real_observation_cadence",
                "external_submission_authorized": False,
                "sha256": sha256_file(derived),
                "source_artifacts": [
                    {
                        "artifact_filename": source.name,
                        "sha256": sha256_file(source),
                    }
                ],
                "target_id": "target-1",
            }
        ),
        encoding="utf-8",
    )

    selected, skipped = select_calibration_artifacts(tmp_path)

    assert [artifact.path.name for artifact in selected] == ["source.dat"]
    assert skipped == [
        {
            "filename": "cadence.csv",
            "reason": "derived_cadence_overlaps_selected_source_dat",
        }
    ]


def test_single_cadence_reports_diagnostics_and_blocks_promotion(
    tmp_path: Path,
) -> None:
    for index, target in enumerate(("target-1", "target-2", "target-3"), start=1):
        _write_approved_dat(
            tmp_path,
            f"scan-{index}.dat",
            cadence_id="cadence-1",
            target_id=target,
            utc_start="2026-01-01T00:00:00Z",
            snr_values=tuple(float(value) for value in range(10, 60)),
        )

    result = analyze_hit_directory(tmp_path)

    assert result["ok"] is True
    assert result["calibration_ready"] is False
    assert set(result["target_stats"]) == {"target-1", "target-2", "target-3"}
    assert set(result["epoch_stats"]) == {"2026-01-01"}
    assert result["acceptance_gates"]["minimum_cadences"]["passed"] is False
    assert result["leave_one_cadence_out"]["status"] == (
        "blocked_insufficient_cadences"
    )
    assert result["bootstrap_stability"]["seed"] == 20260610
