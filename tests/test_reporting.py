import json

from techno_search import (
    PLOT_ARTIFACT_DISCLAIMER,
    REQUIRED_DISCLAIMER,
    Candidate,
    Track,
    candidate_markdown_report,
    candidate_packet,
    candidate_packet_json,
    score_candidate,
    write_candidate_reports,
)


def _synthetic_radio_candidate() -> Candidate:
    return Candidate(
        candidate_id="radio-report",
        track=Track.RADIO,
        source_ids=("synthetic-on-001", "synthetic-off-001"),
        provenance={
            "source_dataset": "synthetic-fixture",
            "processing_version": "v0",
            "config_version": "scoring_v0",
        },
        features={
            "snr": 38.0,
            "bandwidth_hz": 1.6,
            "drift_rate_hz_per_sec": 2.1,
            "on_target_presence_score": 0.92,
            "off_target_presence_score": 0.08,
            "rfi_band_overlap_score": 0.12,
            "frequency_persistence_score": 0.18,
            "nearby_target_recurrence_score": 0.08,
            "instrumental_artifact_score": 0.06,
            "injection_recovery_score": 0.82,
            "repeat_observation_score": 0.1,
            "metadata_completeness_score": 0.9,
            "data_quality_score": 0.88,
            "provenance_completeness_score": 0.86,
        },
    )


def test_candidate_packet_contains_required_report_fields() -> None:
    scored = score_candidate(_synthetic_radio_candidate())
    packet = candidate_packet(scored)

    assert packet["candidate_id"] == "radio-report"
    assert packet["track"] == "radio"
    assert packet["recommended_pathway"]
    assert packet["posterior"]["technosignature_interest"] >= 0.0
    assert packet["scores"]["false_positive_probability"] >= 0.0
    assert packet["positive_evidence"]
    assert packet["negative_evidence"]
    assert packet["blocking_issues"] == []
    assert packet["provenance"]["source_dataset"] == "synthetic-fixture"
    assert packet["schema_version"] == "techno_search_packet_v1"
    assert packet["config_version"] == "scoring_v0"
    assert packet["disclaimer"] == REQUIRED_DISCLAIMER
    assert packet["operator_review"]["pathway"] == packet["recommended_pathway"]
    assert packet["operator_review"]["detection_claimed"] is False
    assert packet["operator_review"]["external_submission_allowed"] is False
    assert "negative evidence item(s)" in packet["false_positive_discussion"]


def test_candidate_packet_json_is_deterministic_and_parseable() -> None:
    scored = score_candidate(_synthetic_radio_candidate())
    serialized = candidate_packet_json(scored)
    parsed = json.loads(serialized)

    assert parsed["candidate_id"] == "radio-report"
    assert parsed["disclaimer"] == REQUIRED_DISCLAIMER
    assert list(parsed) == sorted(parsed)


def test_candidate_markdown_report_includes_conservative_sections() -> None:
    scored = score_candidate(_synthetic_radio_candidate())
    report = candidate_markdown_report(scored)

    assert report.startswith("# Candidate Review Packet: radio-report")
    assert REQUIRED_DISCLAIMER in report
    assert "## Positive Evidence" in report
    assert "## Negative Evidence" in report
    assert "## Blocking Issues" in report
    assert "## False-Positive Discussion" in report
    assert "## Operator Review" in report
    assert "`external_submission_allowed`: False" in report
    assert "`detection_claimed`: False" in report
    assert "## Provenance" in report
    assert "## Diagnostics" in report
    assert "`source_dataset`: synthetic-fixture" in report
    assert "confirmed technosignature" in report
    assert "alien signal" not in report.lower()


def test_empty_report_sections_are_explicit() -> None:
    scored = score_candidate(
        Candidate(
            candidate_id="empty-ish",
            track=Track.RADIO,
            features={
                "snr": 1.0,
                "metadata_completeness_score": 0.1,
                "data_quality_score": 0.1,
                "provenance_completeness_score": 0.1,
            },
        )
    )

    report = candidate_markdown_report(scored)

    assert "- None recorded" in report


def test_write_candidate_reports_uses_safe_filenames(tmp_path) -> None:
    candidate = _synthetic_radio_candidate()
    unsafe_candidate = Candidate(
        candidate_id="../radio report/with spaces",
        track=candidate.track,
        source_ids=candidate.source_ids,
        provenance=candidate.provenance,
        features=candidate.features,
    )
    scored = score_candidate(unsafe_candidate)

    paths = write_candidate_reports(scored, tmp_path)

    assert paths.markdown_path == tmp_path / "radio-report-with-spaces.md"
    assert paths.json_path == tmp_path / "radio-report-with-spaces.json"
    assert paths.manifest_path == tmp_path / "radio-report-with-spaces.manifest.json"
    assert paths.plot_artifact_paths == (
        tmp_path / "radio-report-with-spaces-radio-waterfall.svg",
    )
    assert paths.markdown_path.exists()
    assert paths.json_path.exists()
    assert paths.manifest_path.exists()
    assert paths.plot_artifact_paths[0].exists()
    markdown = paths.markdown_path.read_text(encoding="utf-8")
    assert REQUIRED_DISCLAIMER in markdown
    assert "[Synthetic radio waterfall-style diagnostic placeholder.]" in markdown
    assert "radio-report-with-spaces-radio-waterfall.svg" in markdown
    assert "Synthetic illustrative diagnostic for review context only" in markdown
    assert json.loads(paths.json_path.read_text(encoding="utf-8"))["candidate_id"] == (
        "../radio report/with spaces"
    )
    manifest = json.loads(paths.manifest_path.read_text(encoding="utf-8"))
    assert manifest["candidate_id"] == "../radio report/with spaces"
    assert manifest["track"] == "radio"
    assert manifest["schema_version"] == "techno_search_packet_v1"
    assert manifest["config_version"] == "scoring_v0"
    assert manifest["provenance_summary"]["source_dataset"] == "synthetic-fixture"
    assert manifest["provenance_summary"]["source_ids"] == [
        "synthetic-on-001",
        "synthetic-off-001",
    ]
    assert manifest["markdown_path"].endswith("radio-report-with-spaces.md")
    assert manifest["json_path"].endswith("radio-report-with-spaces.json")
    assert manifest["plot_artifacts"][0]["kind"] == "synthetic_radio_waterfall"
    assert manifest["plot_artifacts"][0]["synthetic"] is True
    assert manifest["plot_artifacts"][0]["disclaimer"] == PLOT_ARTIFACT_DISCLAIMER
    assert manifest["generated_at_utc"]


def test_candidate_markdown_report_includes_diagnostic_paths() -> None:
    candidate = Candidate(
        candidate_id="diagnostic-report",
        track=Track.RADIO,
        features={
            "waterfall_plot_path": "reports/diagnostic-waterfall.png",
            "diagnostic_placeholder": "waterfall_not_generated_v0",
        },
    )
    scored = score_candidate(candidate)

    report = candidate_markdown_report(scored)

    assert "`waterfall_plot_path`: reports/diagnostic-waterfall.png" in report
    assert "`diagnostic_placeholder`: waterfall_not_generated_v0" in report
    assert PLOT_ARTIFACT_DISCLAIMER in report


def test_write_candidate_reports_can_skip_plot_artifacts(tmp_path) -> None:
    scored = score_candidate(_synthetic_radio_candidate())

    paths = write_candidate_reports(scored, tmp_path, include_plot_artifacts=False)
    manifest = json.loads(paths.manifest_path.read_text(encoding="utf-8"))

    assert paths.plot_artifact_paths == ()
    assert manifest["plot_artifacts"] == []
    assert "- None generated" in paths.markdown_path.read_text(encoding="utf-8")
