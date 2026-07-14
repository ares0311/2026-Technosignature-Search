"""Tests for the Phase 1 real-radio human-review sampler."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import joblib
import pytest

from techno_search.cli import main
from techno_search.radio_review_sampling import (
    REVIEW_COLUMNS,
    build_radio_review_sample,
    select_diverse_review_rows,
)
from techno_search.semisupervised_scorer import SemisupervisedScorer


def _write_dat(path: Path, *, target: str, start_mhz: float, hit_count: int = 10) -> None:
    lines = [
        f"# Source:{target}",
        (
            "# Top_Hit_# \tDrift_Rate \tSNR \tUncorrected_Frequency "
            "\tCorrected_Frequency \tIndex"
        ),
    ]
    for index in range(hit_count):
        frequency_mhz = start_mhz + index * 0.0001
        drift = -5.0 + index
        snr = 12.0 + index
        lines.append(
            f"{index + 1}\t{drift}\t{snr}\t{frequency_mhz}\t{frequency_mhz}\t{index}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _training_hit(index: int) -> dict[str, float]:
    frequency_hz = 1.0e9 + index * 2.0e7
    drift = -4.0 + (index % 9)
    return {
        "snr": 10.0 + index,
        "drift_rate_hz_per_sec": drift,
        "frequency_hz": frequency_hz,
        "bandwidth_hz": 2.79,
        "normalized_drift_hz_s_per_ghz": drift / (frequency_hz / 1e9),
        "relative_snr": 1.0,
        "on_off_consistency_score": 0.0,
        "is_earth_drift_consistent": 0.0,
        "rfi_band_overlap_score": 0.0,
        "frequency_persistence_score": 0.0,
        "on_hit_count": 1.0,
        "off_hit_count": 0.0,
    }


def _write_model(path: Path) -> None:
    scorer = SemisupervisedScorer(n_components=4, n_estimators=10, n_jobs=1)
    scorer.fit([_training_hit(index) for index in range(30)])
    joblib.dump(scorer, path)


def test_select_diverse_review_rows_balances_all_score_deciles_and_targets() -> None:
    rows = [
        {
            "hit_id": f"hit-{decile}-{target}-{index}",
            "target": f"TARGET_{target}",
            "frequency_bin_lower_ghz": target % 3 + 1,
            "score_decile": decile,
        }
        for decile in range(1, 11)
        for target in range(5)
        for index in range(3)
    ]

    selected = select_diverse_review_rows(
        rows, sample_size=50, sampling_seed="stable-test"
    )

    assert len(selected) == 50
    assert {int(row["score_decile"]) for row in selected} == set(range(1, 11))
    assert all(
        sum(1 for row in selected if int(row["score_decile"]) == decile) == 5
        for decile in range(1, 11)
    )
    assert len({str(row["target"]) for row in selected}) == 5


def test_build_radio_review_sample_writes_unlabeled_real_format_queue(
    tmp_path: Path,
) -> None:
    dat_dir = tmp_path / "real_dat"
    dat_dir.mkdir()
    for index in range(12):
        _write_dat(
            dat_dir / f"target_{index}.dat",
            target=f"TARGET_{index}",
            start_mhz=1000.0 + index * 1000.0,
        )
    model_path = tmp_path / "semisupervised_scorer.joblib"
    _write_model(model_path)
    output_path = tmp_path / "radio_review_queue.csv"

    summary = build_radio_review_sample(
        [dat_dir],
        output_csv=output_path,
        semisupervised_model_path=model_path,
        sample_size=100,
        sampling_seed="real-format-test",
    )

    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert summary["ok"] is True
    assert summary["available_hit_count"] == 120
    assert summary["sampled_hit_count"] == 100
    assert summary["sampled_target_count"] == 12
    assert summary["sampled_frequency_bin_count"] >= 10
    assert summary["prepopulated_human_label_count"] == 0
    assert summary["blind_search_reuse_prohibited"] is True
    assert list(rows[0]) == list(REVIEW_COLUMNS)
    assert len(rows) == 100
    assert {int(row["score_decile"]) for row in rows} == set(range(1, 11))
    assert all(row["hit_id"].startswith("radio-hit-") for row in rows)
    assert all(row["review_label"] == "" for row in rows)
    assert all(row["reviewer_id"] == "" for row in rows)
    assert all(row["review_timestamp_utc"] == "" for row in rows)

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        build_radio_review_sample(
            [dat_dir],
            output_csv=output_path,
            semisupervised_model_path=model_path,
            sample_size=100,
        )


def test_radio_review_sample_cli_reports_queue_summary(tmp_path: Path) -> None:
    dat_dir = tmp_path / "real_dat"
    dat_dir.mkdir()
    _write_dat(dat_dir / "target_a.dat", target="TARGET_A", start_mhz=1420.0)
    _write_dat(dat_dir / "target_b.dat", target="TARGET_B", start_mhz=2420.0)
    model_path = tmp_path / "semisupervised_scorer.joblib"
    _write_model(model_path)
    output_path = tmp_path / "review.csv"
    out = io.StringIO()

    exit_code = main(
        [
            "radio-review-sample",
            "--dat-dir",
            str(dat_dir),
            "--output",
            str(output_path),
            "--sample-size",
            "10",
            "--semisupervised-model",
            str(model_path),
        ],
        stdout=out,
    )

    payload = json.loads(out.getvalue())
    assert exit_code == 0
    assert payload["sampled_hit_count"] == 10
    assert payload["score_decile_counts"] == {str(index): 1 for index in range(1, 11)}
    assert output_path.exists()

    second_out = io.StringIO()
    second_exit_code = main(
        [
            "radio-review-sample",
            "--dat-dir",
            str(dat_dir),
            "--output",
            str(output_path),
            "--sample-size",
            "10",
            "--semisupervised-model",
            str(model_path),
        ],
        stdout=second_out,
    )
    second_payload = json.loads(second_out.getvalue())
    assert second_exit_code == 1
    assert second_payload["ok"] is False
    assert "refusing to overwrite" in second_payload["error"]
