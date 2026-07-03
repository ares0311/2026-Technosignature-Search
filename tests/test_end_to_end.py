"""End-to-end pipeline integration tests using real fixture input files."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pytest

from techno_search.cli import main
from techno_search.pipeline_runner import PipelineRunResult, run_pipeline
from techno_search.semisupervised_scorer import SemisupervisedScorer

RADIO_FIXTURE = Path(__file__).parent / "fixtures" / "radio" / "sample_hits.csv"
INFRARED_FIXTURE = Path(__file__).parent / "fixtures" / "infrared" / "sample_gaia_wise.csv"
ANOMALY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "anomaly" / "sample_archival_anomaly.csv"
)
PHOTOMETRY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "photometry" / "sample_lightcurve.fits"
)
SPECTROSCOPY_FIXTURE = (
    Path(__file__).parent / "fixtures" / "spectroscopy" / "sample_miri_lrs_x1d.fits"
)


def _semisupervised_training_hit(index: int) -> dict[str, float]:
    frequency_hz = 1.42e9 + index * 10.0
    drift = 0.0 if index % 2 == 0 else 0.1
    return {
        "snr": 6.0 + (index % 5),
        "drift_rate_hz_per_sec": drift,
        "frequency_hz": frequency_hz,
        "bandwidth_hz": 2.79,
        "normalized_drift_hz_s_per_ghz": drift / (frequency_hz / 1e9),
        "relative_snr": 1.0,
        "on_off_consistency_score": 0.5,
        "is_earth_drift_consistent": 1.0,
        "rfi_band_overlap_score": 0.0,
        "frequency_persistence_score": 0.2,
        "on_hit_count": 1.0,
        "off_hit_count": 0.0,
    }


def _write_fitted_semisupervised_model(path: Path) -> None:
    scorer = SemisupervisedScorer(n_estimators=10, n_components=4, n_jobs=1)
    scorer.fit([_semisupervised_training_hit(i) for i in range(20)])
    joblib.dump(scorer, path)


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


def test_radio_pipeline_records_rfi_database_evidence(tmp_path: Path) -> None:
    result = run_pipeline(RADIO_FIXTURE, "radio", tmp_path, candidate_id="radio-rfi-db")
    assert result.ok
    packet = json.loads(result.report_paths.json_path.read_text(encoding="utf-8"))
    features = packet["features"]
    assert features["rfi_database_schema_version"] == "rfi_database_v1"
    assert features["rfi_database_match_count"] == 1
    assert features["rfi_database_match_ids"] == "rfi-db-001"
    assert features["rfi_database_validation_ok"] is True


def test_radio_pipeline_preserves_track_b_position_metadata(tmp_path: Path) -> None:
    result = run_pipeline(RADIO_FIXTURE, "radio", tmp_path, candidate_id="radio-track-b-meta")
    assert result.ok
    packet = json.loads(result.report_paths.json_path.read_text(encoding="utf-8"))

    assert packet["source_ids"]
    assert packet["provenance"]["source_file"] == str(RADIO_FIXTURE)
    assert packet["features"]["ra_deg"] == 83.8221
    assert packet["features"]["dec_deg"] == 22.0145
    assert packet["features"]["observation_mjd"] == 59000.5
    assert packet["features"]["observation_time_utc"] == "2020-05-31T12:00:00Z"


def test_radio_pipeline_injects_semisupervised_model_score(tmp_path: Path) -> None:
    model_path = tmp_path / "semisupervised_scorer.joblib"
    _write_fitted_semisupervised_model(model_path)

    result = run_pipeline(
        RADIO_FIXTURE,
        "radio",
        tmp_path / "reports",
        candidate_id="radio-semisupervised",
        semisupervised_model_path=model_path,
    )

    assert result.ok, f"Pipeline failed: {result.error}"
    packet = json.loads(result.report_paths.json_path.read_text(encoding="utf-8"))
    features = packet["features"]
    provenance = packet["provenance"]
    assert features["semisupervised_model_used"] is True
    assert features["semisupervised_scored_hit_count"] == 5
    assert isinstance(features["semisupervised_anomaly_score"], float)
    assert provenance["semisupervised_model_path"] == str(model_path)
    assert provenance["semisupervised_score_policy"] == "max_hit_score_local_triage_only"


def test_radio_pipeline_routes_known_spacecraft_to_annotation(tmp_path: Path) -> None:
    voyager_dat = tmp_path / "Voyager1.single_coarse.fine_res.dat"
    voyager_dat.write_text(RADIO_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    output_dir = tmp_path / "reports"

    result = run_pipeline(voyager_dat, "radio", output_dir)

    assert result.ok, f"Pipeline failed: {result.error}"
    assert result.pathway == "known_object_annotation"
    packet = json.loads(result.report_paths.json_path.read_text(encoding="utf-8"))
    assert packet["features"]["known_object_score"] == 1.0
    assert packet["features"]["local_known_object_reason"] == (
        "spacecraft_calibration_target"
    )


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


def test_photometry_pipeline_runs_successfully(tmp_path: Path) -> None:
    pytest.importorskip("lightkurve")
    result = run_pipeline(PHOTOMETRY_FIXTURE, "photometry", tmp_path)
    assert isinstance(result, PipelineRunResult)
    assert result.ok, f"Pipeline failed: {result.error}"
    assert result.track.value == "transit_photometry"
    assert result.reader_type == "lightkurve_fits"
    assert result.pathway != "unknown"


def test_photometry_pipeline_recovers_injected_transit(tmp_path: Path) -> None:
    pytest.importorskip("lightkurve")
    result = run_pipeline(PHOTOMETRY_FIXTURE, "photometry", tmp_path)
    assert result.ok
    payload = json.loads(result.report_paths.json_path.read_text(encoding="utf-8"))
    features = payload["features"]
    assert features["bls_period_days"] == pytest.approx(2.2, abs=0.05)
    assert features["bls_depth_snr"] > 10.0
    assert features["blended_eclipsing_binary_score"] < 0.3


def test_photometry_pipeline_writes_report_files(tmp_path: Path) -> None:
    pytest.importorskip("lightkurve")
    result = run_pipeline(PHOTOMETRY_FIXTURE, "photometry", tmp_path)
    assert result.ok
    assert result.report_paths.markdown_path.exists()
    assert result.report_paths.json_path.exists()


def test_spectroscopy_pipeline_runs_successfully(tmp_path: Path) -> None:
    result = run_pipeline(SPECTROSCOPY_FIXTURE, "spectroscopy", tmp_path)
    assert isinstance(result, PipelineRunResult)
    assert result.ok, f"Pipeline failed: {result.error}"
    assert result.track.value == "spectroscopy"
    assert result.reader_type == "jwst_x1d_fits"
    assert result.pathway != "unknown"


def test_spectroscopy_pipeline_detects_injected_sf6_band(tmp_path: Path) -> None:
    result = run_pipeline(SPECTROSCOPY_FIXTURE, "spectroscopy", tmp_path)
    assert result.ok
    payload = json.loads(result.report_paths.json_path.read_text(encoding="utf-8"))
    features = payload["features"]
    assert features["detected_band_count"] >= 1
    assert "SF6" in features["detected_gases"]
    assert features["sf6_10p55um_significance_sigma"] > 5.0


def test_spectroscopy_pipeline_writes_report_files(tmp_path: Path) -> None:
    result = run_pipeline(SPECTROSCOPY_FIXTURE, "spectroscopy", tmp_path)
    assert result.ok
    assert result.report_paths.markdown_path.exists()
    assert result.report_paths.json_path.exists()


def _write_multi_integration_x1dints(path: Path) -> None:
    """Mirrors the real WASP-43 x1dints structure confirmed via direct
    astropy.io.fits inspection: one EXTRACT1D row per integration,
    WAVELENGTH/FLUX/FLUX_ERROR as per-row vector columns."""

    import numpy as np
    from astropy.io import fits

    n_integrations, n_wavelengths = 3, 6
    wavelength = np.tile(np.linspace(7.0, 11.0, n_wavelengths), (n_integrations, 1))
    flux = np.ones((n_integrations, n_wavelengths))
    flux_err = np.full((n_integrations, n_wavelengths), 0.01)

    columns = [
        fits.Column(name="INT_NUM", format="J", array=np.arange(1, n_integrations + 1)),
        fits.Column(name="WAVELENGTH", format=f"{n_wavelengths}D", array=wavelength),
        fits.Column(name="FLUX", format=f"{n_wavelengths}D", array=flux),
        fits.Column(name="FLUX_ERROR", format=f"{n_wavelengths}D", array=flux_err),
    ]
    hdu = fits.BinTableHDU.from_columns(columns, name="EXTRACT1D")
    fits.HDUList([fits.PrimaryHDU(), hdu]).writeto(path)


def test_spectroscopy_pipeline_rejects_multi_integration_without_index(
    tmp_path: Path,
) -> None:
    """Regression test for the real WASP-43 bug: run_pipeline must fail
    closed on a multi-integration x1dints file rather than silently pooling
    all integrations into a spuriously significant band result."""

    fixture = tmp_path / "multi_integration_x1dints.fits"
    _write_multi_integration_x1dints(fixture)

    result = run_pipeline(fixture, "spectroscopy", tmp_path / "out")

    assert not result.ok
    assert result.error is not None
    assert "multi-integration" in result.error


def test_spectroscopy_pipeline_succeeds_with_explicit_integration_index(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "multi_integration_x1dints.fits"
    _write_multi_integration_x1dints(fixture)

    result = run_pipeline(
        fixture, "spectroscopy", tmp_path / "out", jwst_integration_index=1
    )

    assert result.ok, f"Pipeline failed: {result.error}"
    assert result.row_count == 6


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


def test_radio_pipeline_zero_hit_dat_produces_non_detection_manifest(tmp_path: Path) -> None:
    """Zero-hit .dat files (turboSETI found nothing) must produce a manifest, not an error."""
    zero_hit = tmp_path / "HIP66704_zero_hits.dat"
    zero_hit.write_text(
        "# turboSETI output — zero hits above threshold\n"
        "Frequency,SEFD,SNR,Drift_Rate,Source_Name,MJD,RA,DEC,FOFF,Index,top_hit_num\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "reports"
    result = run_pipeline(zero_hit, "radio", output_dir, candidate_id="hip66704-non-detection")
    assert result.ok, f"Zero-hit pipeline should succeed, got error: {result.error}"
    assert result.pathway != "unknown"
    assert result.report_paths.manifest_path.exists()
    manifest = json.loads(result.report_paths.manifest_path.read_text())
    assert manifest["candidate_id"] == "hip66704-non-detection"
    packet = json.loads(result.report_paths.json_path.read_text())
    assert packet["features"]["zero_hit_non_detection"] is True
    assert packet["features"]["turboseti_hit_count"] == 0
    assert packet["provenance"]["non_detection"] is True


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
