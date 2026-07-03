from __future__ import annotations

import json
from pathlib import Path

import joblib
import pytest

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


def _normalized_hit(
    *,
    target_id: str,
    frequency_hz: float,
    drift: float,
    beam: int = 0,
    backend_host: str = "blpn37",
    coarse_channel: int = 10,
    tstart_mjd: float = 60984.176537959574,
    ra_deg: float = 13.255836111111112,
    dec_deg: float = -5.825555555555555,
    source_artifact: str | None = None,
    corpus_source: str = "unit_test_realistic_meerkat_rows",
) -> dict[str, object]:
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
        "beam": beam,
        "backend_host": backend_host,
        "coarse_channel": coarse_channel,
        "tstart_mjd": tstart_mjd,
        "ra_deg": ra_deg,
        "dec_deg": dec_deg,
        "source_artifact": source_artifact or f"{target_id}_{beam}_{coarse_channel}.hits",
        "corpus_source": corpus_source,
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


def test_radio_real_corpus_summary_applies_globular_filter_across_corpus(
    tmp_path: Path,
) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_dat(dat_dir / "target_a.dat", source="TARGET_A", frequency_mhz=1420.0, drift=0.1)
    _write_dat(dat_dir / "target_b.dat", source="TARGET_B", frequency_mhz=1420.0, drift=0.2)

    result = radio_real_corpus_summary([dat_dir])

    globular = result["globular_filter"]
    assert globular["applied"] is True
    assert globular["total_hits"] == 2
    # Fewer hits than DEFAULT_MIN_CLUSTER_SIZE (5) -- real fallback behavior:
    # too few points to cluster, so every hit survives as noise (a candidate),
    # not a spurious RFI cluster.
    assert globular["noise_hits"] == 2
    assert globular["rfi_cluster_hits"] == 0


def test_radio_real_corpus_summary_globular_filter_flags_dense_recurring_signal(
    tmp_path: Path,
) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_zero_hit_dat(dat_dir / "zero_hit.dat", source="ZERO_HIT_TARGET")
    hit_ndjson = tmp_path / "population.ndjson"
    # A real-world-shaped RFI signature: many hits clustered tightly around
    # the same frequency/drift/SNR across many independent targets, plus one
    # hit with a clearly distinct frequency/drift/SNR that should survive as
    # noise (a candidate). Verified directly against apply_globular_filter()
    # with these exact parameters before writing this test -- HDBSCAN's
    # default min_cluster_size=5/min_samples=3 does not reliably form a
    # cluster from only a handful of points, even near-duplicates; this
    # module's own docstring says it is tuned for ~200-hit GBT cadence
    # sizes, so a real test needs a comparably larger population, not a
    # toy few-point example.
    dense_rfi_hits = [
        _normalized_hit(
            target_id=f"RFI_TARGET_{i}",
            frequency_hz=1_420_000_000.0 + (i % 11) - 5,
            drift=0.05 + ((i % 7) - 3) * 0.001,
        )
        for i in range(30)
    ]
    distinct_hit = _normalized_hit(
        target_id="REAL_CANDIDATE_TARGET", frequency_hz=8_419_000_000.0, drift=3.5
    )
    distinct_hit["snr"] = 80.0
    _write_hit_ndjson(hit_ndjson, [*dense_rfi_hits, distinct_hit])

    result = radio_real_corpus_summary([dat_dir], hit_ndjson_paths=[hit_ndjson])

    globular = result["globular_filter"]
    assert globular["applied"] is True
    assert globular["total_hits"] == 31
    assert globular["rfi_cluster_hits"] >= 20
    assert globular["noise_hits"] >= 1


def test_radio_real_corpus_summary_globular_filter_reports_no_hits(tmp_path: Path) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_zero_hit_dat(dat_dir / "zero_hit.dat", source="ZERO_HIT_TARGET")

    result = radio_real_corpus_summary([dat_dir])

    assert result["globular_filter"]["applied"] is False


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
    assert result["candidate_review"]["escalation_blocked_candidate_count"] == 0
    assert result["candidate_review"]["escalation_ready_candidate_count"] == 2
    assert result["candidate_review"]["independent_escalation_ready_candidate_count"] == 2
    assert result["candidate_review"]["independence_blocked_candidate_count"] == 0
    assert result["candidate_review"]["follow_up_target_count"] == 2
    assert result["candidate_review"]["sample_limit"] == 1
    assert len(result["candidate_review"]["top_review_candidates"]) == 1
    assert len(result["candidate_review"]["top_review_targets"]) == 1
    assert result["candidate_review"]["top_escalation_ready_candidates"] == (
        result["candidate_review"]["top_review_candidates"]
    )
    assert result["candidate_review"]["top_escalation_ready_targets"] == (
        result["candidate_review"]["top_review_targets"]
    )
    ready_context = result["candidate_review"]["escalation_ready_context"]
    assert ready_context["candidate_count"] == 2
    assert ready_context["target_count"] == 2
    assert ready_context["source_artifact_count"] == 2
    assert ready_context["shared_artifact_review_needed"] is False
    assert ready_context["independent_escalation_ready"] is True
    assert ready_context["independent_candidate_count"] == 2
    assert ready_context["independence_blocked_candidate_count"] == 0
    assert [group["candidate_count"] for group in ready_context["source_artifact_groups"]] == [
        1,
        1,
    ]
    candidate = result["candidate_review"]["top_review_candidates"][0]
    assert candidate["survives_current_automated_filters"] is True
    assert candidate["review_label"] == "needs_follow_up_review"
    target_group = result["candidate_review"]["top_review_targets"][0]
    assert target_group["candidate_count"] == 1
    assert target_group["target_name"] in {"MKT_A", "MKT_B"}
    assert target_group["top_candidate_id"] == candidate["candidate_id"]
    assert target_group["source_artifact_count"] == 1
    concentration = result["candidate_review"]["target_concentration"]
    assert concentration["dominant_target_candidate_count"] == 1
    assert concentration["dominant_target_fraction"] == 0.5
    assert concentration["source_context_review_needed"] is False
    assert concentration["candidate_escalation_blocked"] is False
    assert concentration["blocking_review_flags"] == []
    assert "not detections" in result["candidate_review"]["claim_guardrail"]


def test_radio_real_corpus_summary_flags_target_concentration(tmp_path: Path) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_zero_hit_dat(dat_dir / "zero_hit.dat", source="ZERO_HIT_TARGET")
    hit_ndjson = tmp_path / "concentrated_sample.ndjson"
    _write_hit_ndjson(
        hit_ndjson,
        [
            _normalized_hit(target_id="TARGET_DENSE", frequency_hz=1_420_000_000.0, drift=0.1),
            _normalized_hit(
                target_id="TARGET_DENSE",
                frequency_hz=1_421_000_000.0,
                drift=0.2,
                backend_host="blpn38",
                coarse_channel=11,
                tstart_mjd=60984.25,
            ),
            _normalized_hit(target_id="TARGET_SINGLE", frequency_hz=1_422_000_000.0, drift=0.3),
        ],
    )

    result = radio_real_corpus_summary(
        [dat_dir],
        hit_ndjson_paths=[hit_ndjson],
        semisupervised_model_path=tmp_path / "missing_model.joblib",
    )

    concentration = result["candidate_review"]["target_concentration"]
    assert concentration["dominant_target_name"] == "TARGET_DENSE"
    assert concentration["dominant_target_candidate_count"] == 2
    assert concentration["dominant_target_fraction"] == pytest.approx(2 / 3)
    assert result["candidate_review"]["escalation_blocked_candidate_count"] == 2
    assert result["candidate_review"]["escalation_ready_candidate_count"] == 1
    assert result["candidate_review"]["independent_escalation_ready_candidate_count"] == 1
    assert result["candidate_review"]["independence_blocked_candidate_count"] == 0
    assert concentration["source_context_review_needed"] is True
    assert concentration["candidate_escalation_blocked"] is True
    assert concentration["blocking_review_flags"] == [
        "single_beam_survivor_context",
        "multi_backend_survivor_context",
        "multi_coarse_channel_survivor_context",
        "single_sky_position_survivor_context",
    ]
    assert "one target" in concentration["reason"]
    ready_candidates = result["candidate_review"]["top_escalation_ready_candidates"]
    ready_targets = result["candidate_review"]["top_escalation_ready_targets"]
    assert len(ready_candidates) == 1
    assert ready_candidates[0]["target_name"] == "TARGET_SINGLE"
    assert len(ready_targets) == 1
    assert ready_targets[0]["target_name"] == "TARGET_SINGLE"
    ready_context = result["candidate_review"]["escalation_ready_context"]
    assert ready_context["candidate_count"] == 1
    assert ready_context["target_count"] == 1
    assert ready_context["shared_artifact_review_needed"] is False
    assert ready_context["independent_escalation_ready"] is True
    assert ready_context["independent_candidate_count"] == 1
    assert ready_context["independence_blocked_candidate_count"] == 0
    assert ready_context["source_artifact_groups"][0]["targets"] == ["TARGET_SINGLE"]
    dense_group = result["candidate_review"]["top_review_targets"][0]
    assert dense_group["source_artifact_count"] == 2
    assert dense_group["source_context"] == {
        "beam_count": 1,
        "beams": [0],
        "backend_host_count": 2,
        "backend_hosts": ["blpn37", "blpn38"],
        "coarse_channel_count": 2,
        "coarse_channels": [10, 11],
        "min_tstart_mjd": 60984.176537959574,
        "max_tstart_mjd": 60984.25,
        "min_ra_deg": 13.255836111111112,
        "max_ra_deg": 13.255836111111112,
        "min_dec_deg": -5.825555555555555,
        "max_dec_deg": -5.825555555555555,
        "review_flags": [
            "single_beam_survivor_context",
            "multi_backend_survivor_context",
            "multi_coarse_channel_survivor_context",
            "single_sky_position_survivor_context",
        ],
        "candidate_escalation_blocked": True,
        "blocking_review_flags": [
            "single_beam_survivor_context",
            "multi_backend_survivor_context",
            "multi_coarse_channel_survivor_context",
            "single_sky_position_survivor_context",
        ],
    }


def test_radio_real_corpus_summary_blocks_shared_artifact_independence(
    tmp_path: Path,
) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_zero_hit_dat(dat_dir / "zero_hit.dat", source="ZERO_HIT_TARGET")
    hit_ndjson = tmp_path / "shared_artifact_sample.ndjson"
    _write_hit_ndjson(
        hit_ndjson,
        [
            _normalized_hit(
                target_id="READY_A",
                frequency_hz=1_420_000_000.0,
                drift=0.1,
                source_artifact="shared_source_a.hits",
            ),
            _normalized_hit(
                target_id="READY_B",
                frequency_hz=1_421_000_000.0,
                drift=0.2,
                source_artifact="shared_source_a.hits",
            ),
            _normalized_hit(
                target_id="READY_C",
                frequency_hz=1_422_000_000.0,
                drift=0.3,
                source_artifact="unique_source_c.hits",
            ),
        ],
    )

    result = radio_real_corpus_summary(
        [dat_dir],
        hit_ndjson_paths=[hit_ndjson],
        semisupervised_model_path=tmp_path / "missing_model.joblib",
    )

    review = result["candidate_review"]
    assert review["escalation_blocked_candidate_count"] == 0
    assert review["escalation_ready_candidate_count"] == 3
    assert review["independent_escalation_ready_candidate_count"] == 0
    assert review["independence_blocked_candidate_count"] == 3
    ready_context = review["escalation_ready_context"]
    assert ready_context["candidate_count"] == 3
    assert ready_context["target_count"] == 3
    assert ready_context["source_artifact_count"] == 2
    assert ready_context["shared_artifact_review_needed"] is True
    assert ready_context["independent_escalation_ready"] is False
    assert ready_context["independent_candidate_count"] == 0
    assert ready_context["independence_blocked_candidate_count"] == 3
    assert "share source artifacts" in ready_context["reason"]
    artifact_groups = ready_context["source_artifact_groups"]
    assert artifact_groups[0]["source_artifact"] == "shared_source_a.hits"
    assert artifact_groups[0]["candidate_count"] == 2
    assert artifact_groups[0]["target_count"] == 2
    assert artifact_groups[0]["targets"] == ["READY_A", "READY_B"]
    assert artifact_groups[1]["source_artifact"] == "unique_source_c.hits"
    assert artifact_groups[1]["candidate_count"] == 1
    assert artifact_groups[1]["targets"] == ["READY_C"]


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


def test_radio_real_corpus_summary_rejects_public_null_search_context(
    tmp_path: Path,
) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_zero_hit_dat(dat_dir / "zero_hit.dat", source="ZERO_HIT_TARGET")
    hit_ndjson = tmp_path / "atlas_public_null_sample.ndjson"
    _write_hit_ndjson(
        hit_ndjson,
        [
            _normalized_hit(
                target_id="ATLAS_PUBLIC_NULL",
                frequency_hz=1_420_000_000.0,
                drift=0.1,
                corpus_source="meerkat_bluse_seticore_atlas_2025_11",
            ),
        ],
    )

    result = radio_real_corpus_summary(
        [dat_dir],
        hit_ndjson_paths=[hit_ndjson],
        semisupervised_model_path=tmp_path / "missing_model.joblib",
    )

    review = result["candidate_review"]
    assert review["public_null_search_context_candidate_count"] == 1
    assert review["follow_up_candidate_count"] == 0
    assert review["escalation_ready_candidate_count"] == 0
    candidate = review["top_rejected_or_control_candidates"][0]
    assert candidate["public_null_search_context"] is True
    assert candidate["survives_current_automated_filters"] is False
    assert candidate["review_label"] == "public_null_search_context"


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
    assert result["candidate_review"]["top_review_targets"] == []
    assert result["candidate_review"]["top_rejected_or_control_candidates"] == []
