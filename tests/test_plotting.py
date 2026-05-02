from techno_search import Candidate, Track, score_candidate, write_synthetic_plot_artifacts
from techno_search.plotting import PLOT_ARTIFACT_DISCLAIMER


def test_radio_plot_artifact_writes_synthetic_waterfall_svg(tmp_path) -> None:
    scored = score_candidate(
        Candidate(
            candidate_id="radio-plot",
            track=Track.RADIO,
            features={"snr": 30.0, "drift_rate_hz_per_sec": 2.0},
        )
    )

    artifacts = write_synthetic_plot_artifacts(scored, tmp_path, filename_prefix="radio-plot")

    assert len(artifacts) == 1
    assert artifacts[0].kind == "synthetic_radio_waterfall"
    assert artifacts[0].path.name == "radio-plot-radio-waterfall.svg"
    svg = artifacts[0].path.read_text(encoding="utf-8")
    assert "Synthetic Radio Waterfall Diagnostic" in svg
    assert PLOT_ARTIFACT_DISCLAIMER in svg


def test_infrared_plot_artifact_writes_synthetic_sed_svg(tmp_path) -> None:
    scored = score_candidate(
        Candidate(
            candidate_id="infrared-plot",
            track=Track.INFRARED,
            features={"ir_excess_significance": 4.0, "source_confusion_score": 0.2},
        )
    )

    artifacts = write_synthetic_plot_artifacts(
        scored,
        tmp_path,
        filename_prefix="infrared-plot",
    )

    assert artifacts[0].kind == "synthetic_infrared_sed"
    assert artifacts[0].path.name == "infrared-plot-infrared-sed.svg"
    assert "Synthetic Infrared SED Diagnostic" in artifacts[0].path.read_text(
        encoding="utf-8"
    )


def test_anomaly_plot_artifact_writes_synthetic_crossmatch_svg(tmp_path) -> None:
    scored = score_candidate(
        Candidate(
            candidate_id="anomaly-plot",
            track=Track.ANOMALY,
            features={"crossmatch_confidence": 0.75, "artifact_score": 0.15},
        )
    )

    artifacts = write_synthetic_plot_artifacts(
        scored,
        tmp_path,
        filename_prefix="anomaly-plot",
    )

    assert artifacts[0].kind == "synthetic_anomaly_crossmatch"
    assert artifacts[0].path.name == "anomaly-plot-anomaly-crossmatch.svg"
    assert "Synthetic Archival Crossmatch Diagnostic" in artifacts[0].path.read_text(
        encoding="utf-8"
    )
