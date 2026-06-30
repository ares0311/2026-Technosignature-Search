from __future__ import annotations

import json
from pathlib import Path

import joblib

from techno_search.cli import main
from techno_search.radio_real_corpus_summary import radio_real_corpus_summary
from techno_search.semisupervised_scorer import SemisupervisedScorer


def _write_dat(path: Path, *, source: str, frequency_mhz: float, drift: float) -> None:
    path.write_text(
        "\n".join(
            [
                "# -------------------------- o --------------------------",
                f"# Source:{source}",
                "# MJD: 57650.782094907408\tRA: 17h10m03.984s\tDEC: 12d10m58.8s",
                "# DELTAT:  18.253611\tDELTAF(Hz):  -2.793968",
                "# --------------------------",
                (
                    "# Top_Hit_# \tDrift_Rate \tSNR \tUncorrected_Frequency "
                    "\tCorrected_Frequency \tIndex \tfreq_start \tfreq_end "
                    "\tSEFD \tSEFD_freq \tCoarse_Channel_Number \tFull_number_of_hits"
                ),
                (
                    f"000001\t {drift}\t 30.0\t {frequency_mhz}\t {frequency_mhz}"
                    "\t739933\t 0.0\t 0.0\t0.0\t0.0\t0\t1"
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_zero_hit_dat(path: Path, *, source: str) -> None:
    path.write_text(
        "\n".join(
            [
                f"# Source:{source}",
                (
                    "# Top_Hit_# \tDrift_Rate \tSNR \tUncorrected_Frequency "
                    "\tCorrected_Frequency \tIndex"
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_hit_ndjson(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _normalized_hit(*, target_id: str, frequency_hz: float, drift: float) -> dict[str, object]:
    return {
        "snr": 25.0,
        "drift_rate_hz_per_sec": drift,
        "frequency_hz": frequency_hz,
        "bandwidth_hz": 2.793968,
        "normalized_drift_hz_s_per_ghz": drift / (frequency_hz / 1e9),
        "relative_snr": 1.0,
        "on_off_consistency_score": 0.0,
        "is_earth_drift_consistent": 1.0,
        "rfi_band_overlap_score": 0.0,
        "frequency_persistence_score": 0.0,
        "on_hit_count": 1,
        "off_hit_count": 0,
        "target_id": target_id,
        "source_artifact": f"{target_id}.h5",
        "corpus_source": "meerkat_bluse_seticore_atlas_2025_11",
    }


def _training_hit(index: int) -> dict[str, float]:
    frequency_hz = 1.0e9 + index * 1.0e6
    drift = 0.01 * index
    return {
        "snr": 10.0 + index,
        "drift_rate_hz_per_sec": drift,
        "frequency_hz": frequency_hz,
        "bandwidth_hz": 2.79,
        "normalized_drift_hz_s_per_ghz": drift / (frequency_hz / 1e9),
        "relative_snr": 1.0,
        "on_off_consistency_score": 0.0,
        "is_earth_drift_consistent": 1.0,
        "rfi_band_overlap_score": 0.0,
        "frequency_persistence_score": 0.0,
        "on_hit_count": 1.0,
        "off_hit_count": 0.0,
    }


def _write_model(path: Path) -> None:
    scorer = SemisupervisedScorer(n_components=4, n_estimators=10, n_jobs=1)
    scorer.fit([_training_hit(index) for index in range(12)])
    joblib.dump(scorer, path)


def test_radio_real_corpus_summary_counts_drift_rfi_and_scorer(tmp_path: Path) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_dat(dat_dir / "target_a.dat", source="TARGET_A", frequency_mhz=1420.0, drift=0.1)
    _write_dat(dat_dir / "target_b.dat", source="TARGET_B", frequency_mhz=1420.0, drift=0.2)
    _write_zero_hit_dat(dat_dir / "target_c.dat", source="TARGET_C")
    model_path = tmp_path / "semisupervised_scorer.joblib"
    _write_model(model_path)

    result = radio_real_corpus_summary([dat_dir], semisupervised_model_path=model_path)

    assert result["ok"] is True
    assert result["dat_file_count"] == 3
    assert result["hit_bearing_dat_file_count"] == 2
    assert result["zero_hit_dat_file_count"] == 1
    assert result["hit_count"] == 2
    assert result["unique_target_count"] == 2
    assert result["hit_bearing_target_count"] == 2
    assert result["validation_readiness"]["phase1_radio_validation_ready"] is True
    assert result["validation_readiness"]["cross_target_rfi_validation_ready"] is True
    assert result["limitations"] == []
    assert result["drift_evidence"]["drift_row_count"] == 2
    assert result["drift_evidence"]["earth_consistent_row_count"] == 2
    assert result["drift_evidence"]["validation_ready"] is True
    assert result["cross_target_rfi"]["flagged_candidate_count"] == 2
    assert result["cross_target_rfi"]["validation_ready"] is True
    assert result["semisupervised_scorer"]["model_used"] is True
    assert result["semisupervised_scorer"]["scored_hit_count"] == 2
    assert "detections" in result["disclaimer"]


def test_radio_real_corpus_summary_includes_real_hit_ndjson(tmp_path: Path) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_zero_hit_dat(dat_dir / "zero_hit.dat", source="ZERO_HIT_TARGET")
    hit_ndjson = tmp_path / "meerkat_normalised_sample.ndjson"
    _write_hit_ndjson(
        hit_ndjson,
        [
            _normalized_hit(target_id="MKT_A", frequency_hz=1_420_000_000.0, drift=0.1),
            _normalized_hit(target_id="MKT_B", frequency_hz=1_420_000_100.0, drift=0.2),
        ],
    )
    model_path = tmp_path / "semisupervised_scorer.joblib"
    _write_model(model_path)

    result = radio_real_corpus_summary(
        [dat_dir],
        hit_ndjson_paths=[hit_ndjson],
        semisupervised_model_path=model_path,
    )

    assert result["ok"] is True
    assert result["dat_file_count"] == 1
    assert result["hit_ndjson_file_count"] == 1
    assert result["hit_ndjson_row_count"] == 2
    assert result["hit_ndjson_row_limit"] is None
    assert result["hit_count"] == 2
    assert result["hit_bearing_target_count"] == 2
    assert result["validation_readiness"]["phase1_radio_validation_ready"] is True
    assert result["cross_target_rfi"]["flagged_candidate_count"] == 2
    assert result["semisupervised_scorer"]["model_used"] is True
    assert result["candidate_review"]["reviewed_candidate_count"] == 2
    assert result["candidate_review"]["follow_up_candidate_count"] == 0
    assert result["candidate_review"]["rfi_rejected_candidate_count"] == 2
    assert result["candidate_review"]["top_review_candidates"] == []
    assert result["candidate_review"]["top_rejected_or_control_candidates"][0]["review_label"] == (
        "likely_cross_target_rfi"
    )


def test_radio_real_corpus_summary_reports_review_survivor(tmp_path: Path) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_zero_hit_dat(dat_dir / "zero_hit.dat", source="ZERO_HIT_TARGET")
    hit_ndjson = tmp_path / "meerkat_normalised_sample.ndjson"
    _write_hit_ndjson(
        hit_ndjson,
        [
            _normalized_hit(target_id="MKT_A", frequency_hz=1_420_000_000.0, drift=0.1),
            _normalized_hit(target_id="MKT_B", frequency_hz=1_421_000_000.0, drift=0.2),
        ],
    )

    result = radio_real_corpus_summary(
        [dat_dir],
        hit_ndjson_paths=[hit_ndjson],
        semisupervised_model_path=tmp_path / "missing_model.joblib",
        candidate_sample_limit=1,
    )

    assert result["cross_target_rfi"]["flagged_candidate_count"] == 0
    assert result["candidate_review"]["reviewed_candidate_count"] == 2
    assert result["candidate_review"]["follow_up_candidate_count"] == 2
    assert result["candidate_review"]["sample_limit"] == 1
    assert len(result["candidate_review"]["top_review_candidates"]) == 1
    candidate = result["candidate_review"]["top_review_candidates"][0]
    assert candidate["survives_current_automated_filters"] is True
    assert candidate["review_label"] == "needs_follow_up_review"
    assert "not detections" in result["candidate_review"]["claim_guardrail"]


def test_radio_real_corpus_summary_keeps_voyager_as_control(tmp_path: Path) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_dat(dat_dir / "voyager1_hits.dat", source="Voyager1", frequency_mhz=8419.0, drift=-0.3)

    result = radio_real_corpus_summary(
        [dat_dir],
        semisupervised_model_path=tmp_path / "missing_model.joblib",
    )

    assert result["candidate_review"]["known_control_candidate_count"] == 1
    assert result["candidate_review"]["follow_up_candidate_count"] == 0
    assert result["candidate_review"]["top_review_candidates"] == []
    candidate = result["candidate_review"]["top_rejected_or_control_candidates"][0]
    assert candidate["known_control_target"] is True
    assert candidate["survives_current_automated_filters"] is False
    assert candidate["review_label"] == "known_spacecraft_or_calibration_control"


def test_radio_real_corpus_summary_separates_stationary_drift(tmp_path: Path) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_zero_hit_dat(dat_dir / "zero_hit.dat", source="ZERO_HIT_TARGET")
    hit_ndjson = tmp_path / "stationary_sample.ndjson"
    _write_hit_ndjson(
        hit_ndjson,
        [_normalized_hit(target_id="MKT_STATIONARY", frequency_hz=1_421_000_000.0, drift=0.0)],
    )

    result = radio_real_corpus_summary(
        [dat_dir],
        hit_ndjson_paths=[hit_ndjson],
        semisupervised_model_path=tmp_path / "missing_model.joblib",
    )

    assert result["candidate_review"]["stationary_drift_candidate_count"] == 1
    assert result["candidate_review"]["follow_up_candidate_count"] == 0
    assert result["candidate_review"]["top_review_candidates"] == []
    candidate = result["candidate_review"]["top_rejected_or_control_candidates"][0]
    assert candidate["is_earth_drift_consistent"] is True
    assert candidate["stationary_drift"] is True
    assert candidate["survives_current_automated_filters"] is False
    assert candidate["review_label"] == "stationary_frequency_review"


def test_cli_radio_real_corpus_summary_outputs_json(tmp_path: Path, capsys) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_dat(dat_dir / "target_a.dat", source="TARGET_A", frequency_mhz=1420.0, drift=0.1)

    exit_code = main(
        [
            "radio-real-corpus-summary",
            "--dat-dir",
            str(dat_dir),
            "--max-files",
            "1",
            "--semisupervised-model",
            str(tmp_path / "missing_model.joblib"),
        ]
    )
    result = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert result["schema_version"] == "radio_real_corpus_summary_v1"
    assert result["dat_file_count"] == 1
    assert result["hit_count"] == 1
    assert result["hit_bearing_target_count"] == 1
    assert result["validation_readiness"]["phase1_radio_validation_ready"] is False
    assert result["validation_readiness"]["cross_target_rfi_validation_ready"] is False
    assert result["cross_target_rfi"]["validation_ready"] is False
    assert result["semisupervised_scorer"]["model_used"] is False
    assert len(result["limitations"]) == 2


def test_cli_radio_real_corpus_summary_accepts_hit_ndjson(tmp_path: Path, capsys) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_zero_hit_dat(dat_dir / "zero_hit.dat", source="ZERO_HIT_TARGET")
    hit_ndjson = tmp_path / "meerkat_normalised_sample.ndjson"
    _write_hit_ndjson(
        hit_ndjson,
        [
            _normalized_hit(target_id="MKT_A", frequency_hz=1_420_000_000.0, drift=0.1),
            _normalized_hit(target_id="MKT_B", frequency_hz=1_420_000_100.0, drift=0.2),
        ],
    )

    exit_code = main(
        [
            "radio-real-corpus-summary",
            "--dat-dir",
            str(dat_dir),
            "--hit-ndjson",
            str(hit_ndjson),
            "--max-hit-rows",
            "2",
            "--candidate-sample-limit",
            "0",
            "--semisupervised-model",
            str(tmp_path / "missing_model.joblib"),
        ]
    )
    result = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert result["hit_ndjson_file_count"] == 1
    assert result["hit_ndjson_row_count"] == 2
    assert result["hit_ndjson_row_limit"] == 2
    assert result["hit_bearing_target_count"] == 2
    assert result["validation_readiness"]["cross_target_rfi_validation_ready"] is True
    assert result["candidate_review"]["sample_limit"] == 0
    assert result["candidate_review"]["top_review_candidates"] == []
    assert result["candidate_review"]["top_rejected_or_control_candidates"] == []
