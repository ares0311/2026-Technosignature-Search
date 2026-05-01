import pytest

from techno_search import score_candidate
from techno_search.radio import (
    RadioDiagnosticPaths,
    RfiBand,
    build_radio_candidate,
    parse_hit_table,
    rfi_band_overlap_score,
)
from techno_search.schemas import PosteriorClass, Track


def test_parse_hit_table_normalizes_scan_roles() -> None:
    hits = parse_hit_table(
        [
            {
                "frequency_hz": 1_420_000_000.0,
                "drift_rate_hz_per_sec": 1.2,
                "snr": 18.0,
                "bandwidth_hz": 2.0,
                "scan_role": "ON",
                "target_id": "target-a",
            }
        ]
    )

    assert hits[0].scan_role == "on"
    assert hits[0].metadata_complete is True


def test_rfi_band_overlap_score_uses_supplied_bands() -> None:
    bands = (RfiBand("test_band", 100.0, 110.0),)

    assert rfi_band_overlap_score(105.0, bands) == 1.0
    assert rfi_band_overlap_score(111.0, bands) == 0.0


def test_build_radio_candidate_extracts_on_off_features() -> None:
    candidate = build_radio_candidate(
        "radio-prototype",
        [
            {
                "frequency_hz": 1_420_000_000.0,
                "drift_rate_hz_per_sec": 1.8,
                "snr": 36.0,
                "bandwidth_hz": 1.5,
                "scan_role": "on",
                "target_id": "target-a",
            },
            {
                "frequency_hz": 1_420_000_002.0,
                "drift_rate_hz_per_sec": 0.0,
                "snr": 6.0,
                "bandwidth_hz": 1.7,
                "scan_role": "off",
                "target_id": "target-b",
            },
        ],
        source_ids=("synthetic-hit-table",),
        provenance={"source_dataset": "synthetic-radio"},
    )

    assert candidate.track == Track.RADIO
    assert candidate.features["on_target_presence_score"] == 1.0
    assert candidate.features["off_target_presence_score"] == 0.2
    assert candidate.features["rfi_band_overlap_score"] == 0.0
    assert candidate.features["hit_count"] == 2
    assert candidate.provenance["source_dataset"] == "synthetic-radio"


def test_radio_candidate_accepts_diagnostic_placeholders() -> None:
    candidate = build_radio_candidate(
        "radio-diagnostics",
        [
            {
                "frequency_hz": 1_420_000_000.0,
                "drift_rate_hz_per_sec": 1.8,
                "snr": 36.0,
                "bandwidth_hz": 1.5,
                "scan_role": "on",
                "target_id": "target-a",
            }
        ],
        diagnostics=RadioDiagnosticPaths(
            waterfall_plot_path="reports/radio-diagnostics-waterfall.png",
            hit_table_path="reports/radio-diagnostics-hits.json",
        ),
    )

    assert candidate.features["waterfall_plot_path"] == (
        "reports/radio-diagnostics-waterfall.png"
    )
    assert candidate.features["hit_table_path"] == "reports/radio-diagnostics-hits.json"
    assert candidate.features["diagnostic_placeholder"] == "waterfall_not_generated_v0"


def test_radio_prototype_candidate_scores_better_than_rfi_candidate() -> None:
    clean = build_radio_candidate(
        "radio-clean-prototype",
        [
            {
                "frequency_hz": 1_420_000_000.0,
                "drift_rate_hz_per_sec": 2.0,
                "snr": 40.0,
                "bandwidth_hz": 1.4,
                "scan_role": "on",
                "target_id": "target-a",
            },
            {
                "frequency_hz": 1_420_050_000.0,
                "drift_rate_hz_per_sec": 0.0,
                "snr": 3.0,
                "bandwidth_hz": 2.0,
                "scan_role": "off",
                "target_id": "target-b",
            },
        ],
        provenance={"source_dataset": "synthetic-radio"},
    )
    rfi = build_radio_candidate(
        "radio-rfi-prototype",
        [
            {
                "frequency_hz": 1_575_420_000.0,
                "drift_rate_hz_per_sec": 0.0,
                "snr": 42.0,
                "bandwidth_hz": 1.2,
                "scan_role": "on",
                "target_id": "target-a",
            },
            {
                "frequency_hz": 1_575_420_001.0,
                "drift_rate_hz_per_sec": 0.0,
                "snr": 38.0,
                "bandwidth_hz": 1.3,
                "scan_role": "off",
                "target_id": "target-b",
            },
        ],
        provenance={"source_dataset": "synthetic-radio"},
    )

    clean_score = score_candidate(clean)
    rfi_score = score_candidate(rfi)

    assert (
        clean_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
        > rfi_score.posterior[PosteriorClass.TECHNOSIGNATURE_INTEREST]
    )
    assert rfi_score.posterior[PosteriorClass.HUMAN_INTERFERENCE] > 0.5


def test_parse_hit_table_rejects_invalid_scan_role() -> None:
    with pytest.raises(ValueError, match="scan_role"):
        parse_hit_table(
            [
                {
                    "frequency_hz": 1_420_000_000.0,
                    "drift_rate_hz_per_sec": 1.2,
                    "snr": 18.0,
                    "bandwidth_hz": 2.0,
                    "scan_role": "calibrator",
                    "target_id": "target-a",
                }
            ]
        )
