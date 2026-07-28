from techno_search import (
    Candidate,
    Track,
    plot_artifact_summary,
    score_candidate,
    write_candidate_reports,
    write_evidence_plot_artifacts,
)
from techno_search.plotting import PLOT_ARTIFACT_DISCLAIMER


def test_radio_plot_artifact_writes_persisted_feature_summary_svg(tmp_path) -> None:
    scored = score_candidate(
        Candidate(
            candidate_id="radio-plot",
            track=Track.RADIO,
            features={"snr": 30.0, "drift_rate_hz_per_sec": 2.0},
        )
    )

    artifacts = write_evidence_plot_artifacts(scored, tmp_path, filename_prefix="radio-plot")

    assert len(artifacts) == 1
    assert artifacts[0].kind == "radio_scored_feature_summary"
    assert artifacts[0].path.name == "radio-plot-radio-feature-summary.svg"
    assert artifacts[0].synthetic is False
    svg = artifacts[0].path.read_text(encoding="utf-8")
    assert "Radio Scored Feature Summary" in svg
    assert "snr" in svg
    assert "30" in svg
    assert "drift_rate_hz_per_sec" in svg
    assert "2" in svg
    assert PLOT_ARTIFACT_DISCLAIMER in svg


def test_infrared_plot_artifact_writes_persisted_feature_summary_svg(tmp_path) -> None:
    scored = score_candidate(
        Candidate(
            candidate_id="infrared-plot",
            track=Track.INFRARED,
            features={"ir_excess_significance": 4.0, "source_confusion_score": 0.2},
        )
    )

    artifacts = write_evidence_plot_artifacts(
        scored,
        tmp_path,
        filename_prefix="infrared-plot",
    )

    assert artifacts[0].kind == "infrared_scored_feature_summary"
    assert artifacts[0].path.name == "infrared-plot-infrared-feature-summary.svg"
    assert "Infrared Scored Feature Summary" in artifacts[0].path.read_text(
        encoding="utf-8"
    )


def test_anomaly_plot_artifact_writes_persisted_feature_summary_svg(tmp_path) -> None:
    scored = score_candidate(
        Candidate(
            candidate_id="anomaly-plot",
            track=Track.ANOMALY,
            features={"crossmatch_confidence": 0.75, "artifact_score": 0.15},
        )
    )

    artifacts = write_evidence_plot_artifacts(
        scored,
        tmp_path,
        filename_prefix="anomaly-plot",
    )

    assert artifacts[0].kind == "anomaly_scored_feature_summary"
    assert artifacts[0].path.name == "anomaly-plot-anomaly-feature-summary.svg"
    assert "Anomaly Scored Feature Summary" in artifacts[0].path.read_text(
        encoding="utf-8"
    )


def test_plot_artifact_is_omitted_without_persisted_numeric_evidence(tmp_path) -> None:
    scored = score_candidate(
        Candidate(
            candidate_id="radio-no-evidence",
            track=Track.RADIO,
            features={"catalog_status": "unavailable"},
        )
    )

    artifacts = write_evidence_plot_artifacts(
        scored,
        tmp_path,
        filename_prefix="radio-no-evidence",
    )

    assert artifacts == ()
    assert list(tmp_path.iterdir()) == []


def test_plot_artifact_summary_counts_manifest_entries_by_track_and_kind(tmp_path) -> None:
    cases = (
        (
            Candidate(candidate_id="radio-plot", track=Track.RADIO, features={"snr": 30.0}),
            "radio",
            "radio_scored_feature_summary",
        ),
        (
            Candidate(
                candidate_id="infrared-plot",
                track=Track.INFRARED,
                features={"ir_excess_significance": 4.0},
            ),
            "infrared",
            "infrared_scored_feature_summary",
        ),
        (
            Candidate(
                candidate_id="anomaly-plot",
                track=Track.ANOMALY,
                features={"crossmatch_confidence": 0.75},
            ),
            "anomaly",
            "anomaly_scored_feature_summary",
        ),
    )

    for candidate, _track, _kind in cases:
        scored = score_candidate(candidate)
        write_candidate_reports(scored, tmp_path, filename_prefix=candidate.candidate_id)

    summary = plot_artifact_summary(tmp_path)

    assert summary["manifest_count"] == 3
    assert summary["plot_artifact_count"] == 3
    assert summary["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert summary["by_kind"] == {
        "anomaly_scored_feature_summary": 1,
        "infrared_scored_feature_summary": 1,
        "radio_scored_feature_summary": 1,
    }
    assert summary["media_types"] == ["image/svg+xml"]
    assert summary["synthetic_count"] == 0
    assert summary["missing_path_count"] == 0
