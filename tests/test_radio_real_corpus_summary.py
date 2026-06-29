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
    assert result["drift_evidence"]["drift_row_count"] == 2
    assert result["drift_evidence"]["earth_consistent_row_count"] == 2
    assert result["cross_target_rfi"]["flagged_candidate_count"] == 2
    assert result["semisupervised_scorer"]["model_used"] is True
    assert result["semisupervised_scorer"]["scored_hit_count"] == 2
    assert "detections" in result["disclaimer"]


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
    assert result["semisupervised_scorer"]["model_used"] is False
