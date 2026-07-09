from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from techno_search.production_scan import (
    EmptyProductionScanError,
    ProductionConsole,
    production_diagnostics,
    review_dashboard_summary,
    run_production_scan,
)

RUN_ID = "RUN-2026-06-18_201325Z-A7K4-prod-scan"
RUN_PRODUCTION_SCAN_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "run_production_scan.sh"
)


def _write_result_pair(
    base: Path,
    target_name: str,
    candidate_id: str,
    pathway: str,
    score: float,
    *,
    snr: float = 55.0,
) -> None:
    target_dir = base / target_name
    target_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = target_dir / f"{candidate_id}.json"
    candidate_path.write_text(
        json.dumps(
            {
                "candidate_id": candidate_id,
                "recommended_pathway": pathway,
                "features": {
                    "frequency_hz": 1420000000.0,
                    "snr": snr,
                    "drift_rate_hz_per_sec": 0.2,
                    "multi_epoch_persistence_score": 0.4,
                },
                "scores": {"followup_value": score},
                "track": "radio",
            }
        ),
        encoding="utf-8",
    )
    (target_dir / f"{candidate_id}.manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": candidate_id,
                "recommended_pathway": pathway,
                "json_path": candidate_path.name,
            }
        ),
        encoding="utf-8",
    )


def test_plain_console_prints_compact_target_rows() -> None:
    stdout = StringIO()
    console = ProductionConsole(stdout, use_rich=False)

    console.print_target_rows(
        [
            {
                "index_id": "FU-2026-06-18_201325Z-A7K4-001",
                "target_name": "HIP99427",
                "target_kind": "stellar target",
                "follow_up_required": True,
                "composite_score": 0.91,
                "top_pathway": "candidate_review_packet",
            }
        ]
    )

    rendered = stdout.getvalue()
    assert "Completed target evaluations:" in rendered
    assert "HIP99427 | stellar target | follow-up=yes | score=0.910" in rendered
    assert "candidate_review_packet" in rendered


def test_plain_console_prints_explicit_empty_target_rows() -> None:
    stdout = StringIO()
    console = ProductionConsole(stdout, use_rich=False)

    console.print_target_rows([])

    assert stdout.getvalue() == "Completed target evaluations: none\n"


def test_run_production_scan_writes_artifacts_and_compact_output(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    scans_dir = tmp_path / "scans"
    _write_result_pair(
        results_dir,
        "HIP99427",
        "candidate",
        "candidate_review_packet",
        0.9,
    )
    stdout = StringIO()

    result = run_production_scan(
        results_dir=results_dir,
        scans_dir=scans_dir,
        stdout=stdout,
        run_id=RUN_ID,
        use_rich=False,
        validate_func=lambda: {"ok": True},
    )

    run_dir = scans_dir / RUN_ID
    rendered = stdout.getvalue()
    assert result.target_count == 1
    assert result.follow_up_required_count == 1
    assert "Production scan RUN-2026-06-18_201325Z-A7K4-prod-scan" in rendered
    assert "OK validate-all" in rendered
    assert "HIP99427 | stellar target | follow-up=yes | score=0.900" in rendered
    assert (run_dir / "validate_all.json").exists()
    assert (run_dir / f"{RUN_ID}_scan_summary.json").exists()
    assert (run_dir / "cross_target_rfi.json").exists()
    assert (run_dir / "escalations" / "summary.json").exists()
    assert (run_dir / f"{RUN_ID}_review_dashboard.json").exists()
    assert (run_dir / f"{RUN_ID}_target_status.json").exists()
    assert (run_dir / f"{RUN_ID}_terminal_summary.json").exists()
    target_status = json.loads(
        (run_dir / f"{RUN_ID}_target_status.json").read_text(encoding="utf-8")
    )
    dashboard = json.loads(
        (run_dir / f"{RUN_ID}_review_dashboard.json").read_text(encoding="utf-8")
    )
    assert target_status["entries"][0]["index_id"] == "FU-2026-06-18_201325Z-A7K4-001"
    assert target_status["entries"][0]["score_basis"] == "pipeline_score"
    assert target_status["entries"][0]["detection_claimed"] is False
    assert dashboard["schema_version"] == "operator_review_dashboard_v1"
    assert dashboard["needs_attention"] is True
    assert dashboard["follow_up_required_count"] == 1
    assert dashboard["top_follow_up_targets"][0]["target_name"] == "HIP99427"


def test_run_production_scan_sanitizes_project_paths_in_artifacts(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    scans_dir = tmp_path / "scans"
    _write_result_pair(results_dir, "HIP99427", "candidate", "known_object_annotation", 0.1)
    project_path = Path.cwd() / "tests" / "fixtures" / "background_targets.json"
    stdout = StringIO()

    run_production_scan(
        results_dir=results_dir,
        scans_dir=scans_dir,
        stdout=stdout,
        run_id=RUN_ID,
        use_rich=False,
        validate_func=lambda: {
            "ok": True,
            str(project_path): str(project_path),
            "nested": [str(project_path)],
        },
        dashboard_func=lambda: {"needs_attention": False},
    )

    validate_text = (scans_dir / RUN_ID / "validate_all.json").read_text(
        encoding="utf-8"
    )
    assert str(Path.cwd()) not in validate_text
    assert "tests/fixtures/background_targets.json" in validate_text


def test_run_production_scan_fails_closed_without_candidates(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    scans_dir = tmp_path / "scans"
    results_dir.mkdir()
    stdout = StringIO()

    try:
        run_production_scan(
            results_dir=results_dir,
            scans_dir=scans_dir,
            stdout=stdout,
            run_id=RUN_ID,
            use_rich=False,
            validate_func=lambda: {"ok": True},
            dashboard_func=lambda: {"needs_attention": False},
        )
    except EmptyProductionScanError:
        pass
    else:  # pragma: no cover - assertion branch
        raise AssertionError("empty production scan should fail closed")

    rendered = stdout.getvalue()
    assert "ERROR no candidate manifests found" in rendered
    assert "No production run artifacts were written" in rendered
    assert not (scans_dir / RUN_ID).exists()


def test_run_production_scan_ledgers_zero_hit_observation(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    scans_dir = tmp_path / "scans"
    target_dir = results_dir / "HIP17147" / "zero"
    target_dir.mkdir(parents=True)
    (target_dir / "HIP17147__zero.manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "zero_hit_observation_manifest_v1",
                "artifact_kind": "zero_hit_observation_manifest",
                "observation_id": "HIP17147__zero",
                "target_name": "HIP17147",
                "track": "radio",
                "recommended_pathway": "no_follow_up_observation",
                "source_data_path": "HIP17147/zero.dat",
                "hit_row_count": 0,
                "negative_evidence": [
                    "turboSETI hit table contained no hit rows above the configured threshold."
                ],
                "detection_claimed": False,
                "external_submission_allowed": False,
            }
        ),
        encoding="utf-8",
    )
    stdout = StringIO()

    result = run_production_scan(
        results_dir=results_dir,
        scans_dir=scans_dir,
        stdout=stdout,
        run_id=RUN_ID,
        use_rich=False,
        validate_func=lambda: {"ok": True},
        dashboard_func=lambda: {"needs_attention": False},
    )

    non_detections = json.loads(
        (scans_dir / RUN_ID / f"{RUN_ID}_non_detections.json").read_text(
            encoding="utf-8"
        )
    )
    assert result.target_count == 1
    assert result.follow_up_required_count == 0
    assert "HIP17147 | stellar target | follow-up=no | score=0.000" in stdout.getvalue()
    assert non_detections["entries"][0]["reason"] == (
        "zero_hit_observation_no_turboseti_hits"
    )


def test_run_production_scan_allows_empty_only_when_explicit(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    scans_dir = tmp_path / "scans"
    results_dir.mkdir()
    stdout = StringIO()

    result = run_production_scan(
        results_dir=results_dir,
        scans_dir=scans_dir,
        stdout=stdout,
        run_id=RUN_ID,
        use_rich=False,
        allow_empty=True,
        validate_func=lambda: {"ok": True},
        dashboard_func=lambda: {"needs_attention": False},
    )

    assert result.target_count == 0
    assert "Completed target evaluations: none" in stdout.getvalue()
    assert (scans_dir / RUN_ID / f"{RUN_ID}_manifest.json").exists()


def test_review_dashboard_summary_from_candidates_reports_operator_actions(
    tmp_path: Path,
) -> None:
    results_dir = tmp_path / "results"
    _write_result_pair(
        results_dir,
        "HIP99427",
        "candidate",
        "candidate_review_packet",
        0.9,
    )

    dashboard = review_dashboard_summary(results_dir=results_dir)

    assert dashboard["schema_version"] == "operator_review_dashboard_v1"
    assert dashboard["source"] == "candidate_manifests"
    assert dashboard["needs_attention"] is True
    assert dashboard["follow_up_required_count"] == 1
    assert dashboard["candidate_review_packet_count"] == 1
    assert dashboard["detection_claimed"] is False
    assert dashboard["external_submission_allowed"] is False
    assert dashboard["action_items"][0]["action"] == "review_candidate_packets"


def test_run_production_scan_resume_skips_existing_artifacts(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    scans_dir = tmp_path / "scans"
    _write_result_pair(results_dir, "HIP99427", "candidate", "known_object_annotation", 0.1)
    first_stdout = StringIO()
    first = run_production_scan(
        results_dir=results_dir,
        scans_dir=scans_dir,
        stdout=first_stdout,
        run_id=RUN_ID,
        use_rich=False,
        validate_func=lambda: {"ok": True},
        dashboard_func=lambda: {"needs_attention": False},
    )
    second_stdout = StringIO()

    second = run_production_scan(
        results_dir=results_dir,
        scans_dir=scans_dir,
        stdout=second_stdout,
        resume_run_dir=first.run_dir,
        use_rich=False,
        validate_func=lambda: {"ok": False},
        dashboard_func=lambda: {"needs_attention": True},
    )

    rendered = second_stdout.getvalue()
    assert second.run_id == RUN_ID
    assert second.target_count == 1
    assert second.skipped_step_count >= 5
    assert "SKIP validate-all" in rendered
    assert "SKIP prod-write-outcomes" in rendered


def test_production_diagnostics_compact_output(tmp_path: Path) -> None:
    stdout = StringIO()

    diagnostics = production_diagnostics(
        scans_dir=tmp_path,
        stdout=stdout,
        use_rich=False,
        validate_func=lambda: {"ok": True},
        dashboard_func=lambda: {"needs_attention": False},
    )

    assert diagnostics["validate_all_ok"] is True
    assert diagnostics["review_dashboard_needs_attention"] is False
    assert "Diagnostics: validate_all_ok=True needs_attention=False" in stdout.getvalue()


def test_run_production_scan_script_keeps_validate_all_output_compact() -> None:
    script = RUN_PRODUCTION_SCAN_SCRIPT.read_text(encoding="utf-8")

    assert 'tee "${SCAN_DIR}/validate_all.json"' not in script
    assert 'echo "${VALIDATE_JSON}"' not in script
    assert "VALIDATE_JSON_PATH" in script
    assert "_review_safe_json" in script
    assert "validate-all: PASSED (artifact:" in script


def test_run_production_scan_script_bounds_force_rescan_to_one_pass() -> None:
    script = RUN_PRODUCTION_SCAN_SCRIPT.read_text(encoding="utf-8")

    assert "force_rescan_session_history.ndjson" in script
    assert "each currently queued target will be rescanned once" in script
    assert 'QUEUE_HISTORY_FILE="${SCAN_DIR}/force_rescan_session_history.ndjson"' in script
    initial_queue_call = (
        'prod-target-queue \\\n'
        '    --dat-dir "${DAT_DIR}" \\\n'
        '    --history-file "${QUEUE_HISTORY_FILE}"'
    )
    loop_queue_call = (
        'prod-target-queue \\\n'
        '        --dat-dir "${DAT_DIR}" \\\n'
        '        --history-file "${QUEUE_HISTORY_FILE}"'
    )
    assert initial_queue_call in script
    assert loop_queue_call in script
