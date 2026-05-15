import json
from io import StringIO

from techno_search.cli import main
from techno_search.cross_track import (
    CROSS_TRACK_REFERENCE_DISCLAIMER,
    CROSS_TRACK_REFERENCE_SCHEMA_VERSION,
    cross_track_summary,
    load_cross_track_references,
)
from techno_search.scoring import score_candidate


def test_load_cross_track_references_returns_committed_fixture() -> None:
    references = load_cross_track_references()

    assert len(references) >= 4
    kinds = {ref.cross_reference_kind for ref in references}
    assert {
        "operational_cross_reference",
        "conflicting_evidence",
        "single_track_only",
        "known_object_cross_match",
    } <= kinds


def test_cross_track_summary_counts_multi_track_references() -> None:
    summary = cross_track_summary()

    assert summary["schema_version"] == CROSS_TRACK_REFERENCE_SCHEMA_VERSION
    assert summary["disclaimer"] == CROSS_TRACK_REFERENCE_DISCLAIMER
    assert summary["reference_count"] >= 4
    assert summary["multi_track_reference_count"] >= 3
    assert summary["blocking_issue_total"] >= 0
    assert "infrared + radio" in summary["by_track_combination"]


def test_cross_track_references_do_not_modify_candidate_scoring() -> None:
    """Cross-references must remain operational metadata only."""

    from techno_search.schemas import Candidate, Track

    candidate = Candidate(
        candidate_id="example-radio-clean",
        track=Track.RADIO,
        source_ids=("synthetic-radio-001",),
        features={
            "narrowband_signal": 1.0,
            "drift_rate_hz_s": 0.5,
            "off_target_absent": 1.0,
            "rfi_band_overlap": 0.0,
            "snr_relative": 0.85,
            "metadata_completeness": 1.0,
            "provenance_completeness": 1.0,
            "data_quality_score": 0.9,
        },
        provenance={"source_dataset": "synthetic_v0"},
    )

    baseline = score_candidate(candidate)
    references = load_cross_track_references()
    repeated = score_candidate(candidate)

    assert references
    assert baseline.recommended_pathway == repeated.recommended_pathway
    assert baseline.posterior == repeated.posterior


def test_cli_cross_track_summary_outputs_counts() -> None:
    stdout = StringIO()

    exit_code = main(["cross-track-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["reference_count"] >= 4
    assert result["multi_track_reference_count"] >= 3
    assert "uncertainty_and_limitations" in result
