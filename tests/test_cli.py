import json
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest

import techno_search
from techno_search.cli import main, score_batch
from techno_search.gbt_cadence import load_cadence_manifest, md5_file


def _candidate_json() -> dict[str, object]:
    return {
        "candidate_id": "cli-radio",
        "track": "radio",
        "source_ids": ["synthetic-cli"],
        "features": {
            "snr": 35.0,
            "bandwidth_hz": 1.5,
            "drift_rate_hz_per_sec": 2.0,
            "on_target_presence_score": 0.9,
            "off_target_presence_score": 0.05,
            "rfi_band_overlap_score": 0.05,
            "frequency_persistence_score": 0.05,
            "instrumental_artifact_score": 0.05,
            "metadata_completeness_score": 0.9,
            "data_quality_score": 0.9,
            "provenance_completeness_score": 0.9,
        },
        "provenance": {"source_dataset": "synthetic-cli"},
    }


def _write_cli_turboseti_dat(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Source:HIP_CLI",
                "# MJD: 57650.782094907408\tRA: 17h10m03.984s\tDEC: 12d10m58.8s",
                "# DELTAT:  18.253611\tDELTAF(Hz):  -2.793968",
                "# Top_Hit_# \tDrift_Rate \tSNR \tUncorrected_Frequency \tCorrected_Frequency",
                "000001\t -0.397966\t 30.612337\t 8419.319368\t 8419.319368",
                "000002\t -0.377557\t 45.709641\t 8419.297028\t 8419.297028",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_tiny_cli_cadence(tmp_path: Path) -> tuple[Path, Path]:
    manifest = json.loads(
        json.dumps(
            load_cadence_manifest(Path("configs/gbt_hip99427_cadence_v1.json"))
        )
    )
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    for scan in manifest["scans"]:
        raw_path = raw_dir / scan["filename"]
        raw_path.write_bytes(
            b"\x89HDF\r\n\x1a\n" + f"raw cli scan {scan['sequence_index']}".encode()
        )
        scan["size_bytes"] = raw_path.stat().st_size
        scan["md5"] = md5_file(raw_path)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, raw_dir


def _write_tiny_cli_cadence_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "Corrected_Frequency,Drift_Rate,SNR,scan_role,target_id,source_artifact",
                "1420.0,1.0,21.0,on,HIP99427,a.dat",
                "1420.0,1.0,22.0,on,HIP99427,c.dat",
                "1420.0,1.0,23.0,on,HIP99427,e.dat",
                "1421.0,-2.0,31.0,on,HIP99427,a.dat",
                "1421.0,-2.0,32.0,off,HIP100670,b.dat",
                "1421.0,-2.0,33.0,off,HIP99560,d.dat",
                "1421.0,-2.0,34.0,off,HIP99759,f.dat",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_cli_version_command_reports_package_version() -> None:
    stdout = StringIO()

    exit_code = main(["version"], stdout=stdout)

    assert exit_code == 0
    assert stdout.getvalue().strip() == f"techno-search {techno_search.__version__}"


def test_cli_version_does_not_import_sqlite_in_fresh_process() -> None:
    code = (
        "import io, sys; "
        "from techno_search.cli import main; "
        "out = io.StringIO(); "
        "code = main(['version'], stdout=out); "
        "print(out.getvalue().strip()); "
        "print('sqlite3' in sys.modules); "
        "raise SystemExit(code)"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.splitlines() == [
        f"techno-search {techno_search.__version__}",
        "False",
    ]


def test_cli_scores_candidate_json_to_stdout(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(["score", str(input_path)], stdout=stdout)
    packet = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert packet["candidate_id"] == "cli-radio"
    assert packet["schema_version"] == "techno_search_packet_v1"
    assert packet["recommended_pathway"]
    assert packet["disclaimer"]


def test_cli_gbt_cadence_raw_status_reports_missing_files(tmp_path) -> None:
    manifest_path, _raw_dir = _write_tiny_cli_cadence(tmp_path)
    stdout = StringIO()

    exit_code = main(
        [
            "gbt-cadence-raw-status",
            "--manifest",
            str(manifest_path),
            "--raw-dir",
            str(tmp_path / "missing"),
            "--json",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert result["ok"] is False
    assert result["missing_count"] == 6

    compact_stdout = StringIO()
    main(
        [
            "gbt-cadence-raw-status",
            "--manifest",
            str(manifest_path),
            "--raw-dir",
            str(tmp_path / "missing"),
        ],
        stdout=compact_stdout,
    )
    assert "missing=6" in compact_stdout.getvalue()
    assert "missing_raw_file" in compact_stdout.getvalue()


def test_cli_gbt_cadence_raw_status_verifies_files(tmp_path) -> None:
    manifest_path, raw_dir = _write_tiny_cli_cadence(tmp_path)
    stdout = StringIO()

    exit_code = main(
        [
            "gbt-cadence-raw-status",
            "--manifest",
            str(manifest_path),
            "--raw-dir",
            str(raw_dir),
            "--json",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["verified_count"] == 6

    compact_stdout = StringIO()
    main(
        [
            "gbt-cadence-raw-status",
            "--manifest",
            str(manifest_path),
            "--raw-dir",
            str(raw_dir),
        ],
        stdout=compact_stdout,
    )
    assert "verified=6" in compact_stdout.getvalue()
    assert "ok=True" in compact_stdout.getvalue()


def test_cli_gbt_cadence_abacab_review_summarizes_candidate_outcomes(tmp_path) -> None:
    cadence_csv = tmp_path / "cadence.csv"
    _write_tiny_cli_cadence_csv(cadence_csv)
    stdout = StringIO()

    exit_code = main(
        [
            "gbt-cadence-abacab-review",
            "--cadence-csv",
            str(cadence_csv),
            "--cadence-id",
            "test-cadence",
            "--limit",
            "1",
            "--json",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["triage_outcome_counts"] == {
        "false_positive": 1,
        "follow_up": 1,
    }
    assert result["top_follow_up_candidates"][0]["on_scan_count"] == 3
    assert result["top_follow_up_candidates"][0]["off_scan_count"] == 0
    assert result["detection_claimed"] is False

    compact_stdout = StringIO()
    main(
        [
            "gbt-cadence-abacab-review",
            "--cadence-csv",
            str(cadence_csv),
            "--cadence-id",
            "test-cadence",
            "--limit",
            "1",
        ],
        stdout=compact_stdout,
    )
    assert "follow_up=1" in compact_stdout.getvalue()
    assert "false_positive=1" in compact_stdout.getvalue()
    assert "Independent-rule agreement: 2 agree, 0 disagree" in (
        compact_stdout.getvalue()
    )


def test_cli_track_b_unknown_candidate_gate_combines_explicit_evidence(tmp_path) -> None:
    candidate = _candidate_json()
    candidate["features"] = {
        **candidate["features"],
        "abacab_cadence_score": 1.0,
        "semisupervised_anomaly_score": 0.91,
    }
    candidate_path = tmp_path / "candidate.json"
    crossmatch_path = tmp_path / "crossmatch.json"
    satellite_path = tmp_path / "satellite.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    crossmatch_path.write_text(
        json.dumps({"classification": "no_known_match"}), encoding="utf-8"
    )
    satellite_path.write_text(
        json.dumps({"classification": "no_known_match"}), encoding="utf-8"
    )
    stdout = StringIO()

    exit_code = main(
        [
            "track-b-unknown-candidate-gate",
            str(candidate_path),
            "--crossmatch-json",
            str(crossmatch_path),
            "--satellite-json",
            str(satellite_path),
            "--json",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["candidate_id"] == "cli-radio"
    assert result["eligible_for_unknown_candidate"] is False
    assert result["unresolved_count"] == 1
    anomaly_condition = next(
        c for c in result["conditions"] if c["condition_id"] == "has_high_anomaly_score"
    )
    assert anomaly_condition["satisfied"] is None
    assert "local triage queue state only" in result["disclaimer"]

    compact_stdout = StringIO()
    main(
        [
            "track-b-unknown-candidate-gate",
            str(candidate_path),
            "--crossmatch-json",
            str(crossmatch_path),
            "--satellite-json",
            str(satellite_path),
        ],
        stdout=compact_stdout,
    )
    assert "eligible_for_unknown_candidate=False" in compact_stdout.getvalue()
    assert "has_high_anomaly_score | unresolved" in compact_stdout.getvalue()


def test_cli_track_b_candidate_readiness_reports_missing_inputs(tmp_path) -> None:
    candidate = _candidate_json()
    candidate["source_ids"] = []
    candidate["features"] = {
        **candidate["features"],
        "abacab_cadence_score": 1.0,
        "semisupervised_anomaly_score": 0.91,
        "frequency_hz": 1_420_000_000.0,
    }
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(
        [
            "track-b-candidate-readiness",
            str(candidate_path),
            "--json",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["gate_evaluated"] is False
    assert result["track_a_crossmatch"]["status"] == "missing_inputs"
    assert result["track_a_crossmatch"]["missing_candidate_fields"] == ["ra_deg", "dec_deg"]
    assert "missing_source_ids_or_provenance" in result["blocking_reason_ids"]
    assert result["eligible_for_unknown_candidate"] is False

    compact_stdout = StringIO()
    main(
        ["track-b-candidate-readiness", str(candidate_path)],
        stdout=compact_stdout,
    )
    assert "provenance_ready=False" in compact_stdout.getvalue()
    assert "Track B gate: not computed" in compact_stdout.getvalue()


def test_cli_scan_summary_ranks_candidates(tmp_path: Path) -> None:
    batch_dir = tmp_path / "batch"
    batch_dir.mkdir()
    (batch_dir / "c1_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "c1",
                "score": 0.3,
                "recommended_pathway": "human_review_queue",
                "target_name": "HIP1",
            }
        ),
        encoding="utf-8",
    )
    (batch_dir / "c2_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "c2",
                "score": 0.9,
                "recommended_pathway": "candidate_review_packet",
                "target_name": "HIP2",
            }
        ),
        encoding="utf-8",
    )
    stdout = StringIO()
    exit_code = main(["scan-summary", str(batch_dir), "--json"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["total_candidates"] == 2
    assert result["top_candidates"][0]["candidate_id"] == "c2"

    compact_stdout = StringIO()
    main(["scan-summary", str(batch_dir)], stdout=compact_stdout)
    assert "candidates=2" in compact_stdout.getvalue()
    assert "c2" in compact_stdout.getvalue()


def test_cli_multi_modal_crossmatch_summary_groups_by_position(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "radio.json").write_text(
        json.dumps(
            {
                "candidate_id": "radio-1",
                "track": "radio",
                "features": {"ra_deg": 10.0, "dec_deg": 20.0},
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "photometry.json").write_text(
        json.dumps(
            {
                "candidate_id": "photometry-1",
                "track": "transit_photometry",
                "features": {"ra_deg": 10.001, "dec_deg": 20.001},
            }
        ),
        encoding="utf-8",
    )
    stdout = StringIO()
    exit_code = main(
        ["multi-modal-crossmatch-summary", "--report-dir", str(report_dir), "--json"],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["multi_modal_group_count"] == 1

    compact_stdout = StringIO()
    main(
        ["multi-modal-crossmatch-summary", "--report-dir", str(report_dir)],
        stdout=compact_stdout,
    )
    assert "multi_modal_groups=1" in compact_stdout.getvalue()
    assert "radio-1" in compact_stdout.getvalue()


def test_cli_adversarial_review_dossier_reports_refutations(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "candidate_id": "adv-1",
                "track": "radio",
                "recommended_pathway": "do_not_submit_false_positive",
                "scores": {"false_positive_probability": 0.9},
                "positive_evidence": [],
                "negative_evidence": ["Frequency overlaps known or suspected RFI."],
                "blocking_issues": [],
            }
        ),
        encoding="utf-8",
    )
    stdout = StringIO()
    exit_code = main(
        ["adversarial-review-dossier", str(report_path), "--json"],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["refutation_count"] == 1
    assert result["requires_human_expert_review"] is False

    compact_stdout = StringIO()
    main(["adversarial-review-dossier", str(report_path)], stdout=compact_stdout)
    assert "refutation_count=1" in compact_stdout.getvalue()
    assert "requires_human_expert_review=False" in compact_stdout.getvalue()


def test_cli_writes_reports(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    output_dir = tmp_path / "reports"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(
        ["score", str(input_path), "--output-dir", str(output_dir), "--prefix", "cli-radio"],
        stdout=stdout,
    )

    assert exit_code == 0
    assert (output_dir / "cli-radio.md").exists()
    assert (output_dir / "cli-radio.json").exists()
    assert (output_dir / "cli-radio.manifest.json").exists()
    assert (output_dir / "cli-radio-radio-waterfall.svg").exists()
    assert "cli-radio.md" in stdout.getvalue()
    assert "cli-radio-radio-waterfall.svg" in stdout.getvalue()


def test_cli_can_skip_report_plot_artifacts(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    output_dir = tmp_path / "reports"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(
        [
            "score",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--prefix",
            "cli-radio",
            "--no-plot-artifacts",
        ],
        stdout=stdout,
    )
    manifest = json.loads((output_dir / "cli-radio.manifest.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert manifest["plot_artifacts"] == []
    assert not (output_dir / "cli-radio-radio-waterfall.svg").exists()


def test_cli_scores_batch_directory(tmp_path) -> None:
    input_dir = tmp_path / "candidates"
    output_dir = tmp_path / "reports"
    input_dir.mkdir()
    (input_dir / "candidate-a.json").write_text(json.dumps(_candidate_json()), encoding="utf-8")
    candidate_b = _candidate_json() | {"candidate_id": "cli-radio-b"}
    (input_dir / "candidate-b.json").write_text(json.dumps(candidate_b), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(
        ["score-batch", str(input_dir), str(output_dir), "--prefix", "batch-"],
        stdout=stdout,
    )

    manifest_path = output_dir / "batch_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert stdout.getvalue().strip() == str(manifest_path)
    assert manifest["candidate_count"] == 2
    assert manifest["schema_version"] == "techno_search_packet_v1"
    assert manifest["config_version"] == "scoring_v0"
    assert (output_dir / "batch-cli-radio.md").exists()
    assert (output_dir / "batch-cli-radio-b.md").exists()
    assert len(manifest["reports"]) == 2
    assert all(report["plot_artifact_paths"] for report in manifest["reports"])


def test_score_batch_regenerates_expected_example_candidate_set(tmp_path) -> None:
    manifest_path = score_batch("examples/candidates", tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["candidate_count"] == 3
    assert {report["candidate_id"] for report in manifest["reports"]} == {
        "example-radio-clean",
        "example-infrared-clean",
        "example-anomaly-clean",
    }
    for report in manifest["reports"]:
        assert report["config_version"] == "scoring_v0"
        assert (tmp_path / f"{report['candidate_id']}.md").exists()
        assert (tmp_path / f"{report['candidate_id']}.json").exists()
        assert (tmp_path / f"{report['candidate_id']}.manifest.json").exists()


def test_cli_calibration_summary_outputs_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["calibration-summary"], stdout=stdout)
    summary = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert summary["total"] == 0
    assert summary["by_track"] == {}
    assert summary["by_expected_pathway"] == {}


def test_cli_false_positive_summary_outputs_class_counts() -> None:
    stdout = StringIO()

    exit_code = main(["false-positive-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "synthetic_false_positive_analysis_v1"
    assert result["removed_in_phase_0"] is True
    assert result["case_count"] == 0
    assert result["class_count"] == 0
    assert result["by_track"] == {}
    assert result["by_class"] == {}


def test_cli_rfi_database_summary_outputs_guardrail_counts() -> None:
    stdout = StringIO()

    exit_code = main(["rfi-database-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "rfi_database_v1"
    assert result["record_count"] == 5
    assert result["reviewed_count"] == 3
    assert result["validation_ok"] is True
    assert result["real_record_count"] == 0
    assert result["by_source_class"]["gps"] == 2
    assert "do not calibrate scoring thresholds" in result["disclaimer"]


def test_cli_rfi_database_admission_summary_outputs_gate_counts() -> None:
    stdout = StringIO()

    exit_code = main(["rfi-database-admission-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "rfi_database_admission_v1"
    assert result["record_count"] == 5
    assert result["blocked_count"] == 3
    assert result["real_data_authorized_count"] == 0
    assert result["validation_ok"] is True
    assert "do not ingest real monitoring data" in result["disclaimer"]


def test_cli_curated_dataset_admission_summary_outputs_gate_counts() -> None:
    stdout = StringIO()

    exit_code = main(["curated-dataset-admission-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "curated_dataset_admission_v1"
    assert result["record_count"] == 5
    assert result["blocked_count"] == 4
    assert result["real_data_authorized_count"] == 0
    assert result["validation_ok"] is True
    assert "does not authorize unreviewed real observation data" in result["disclaimer"]

def test_cli_ai_hardening_gate_summary_outputs_open_fail_closed_gate() -> None:
    stdout = StringIO()

    exit_code = main(["ai-hardening-gate-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "ai_hardening_gate_v1"
    assert result["ok"] is True
    assert result["status"] == "open"
    assert result["production_promotion_allowed"] is False
    assert result["production_promotion_scope"] == "blocked"
    assert result["external_submission_allowed"] is False
    assert result["open_blocking_requirement_count"] == 1
    assert result["open_blocking_requirement_ids"] == [
        "adequate_preexisting_row_level_labels"
    ]
    assert result["closure_evidence_bundle_exists"] is True
    assert result["populated_evidence_path_count"] <= result[
        "existing_evidence_path_count"
    ]
    assert result["local_calibration_holdout_gate_closure_ready"] is False

def test_cli_calibration_track_summary_outputs_track_counts() -> None:
    stdout = StringIO()

    exit_code = main(["calibration-track-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "synthetic_calibration_by_track_v1"
    assert result["removed_in_phase_0"] is True
    assert result["case_count"] == 0
    assert result["track_count"] == 0
    assert result["minimum_track_case_count"] == 0
    assert result["by_track"] == {}
    assert "not calibrated per-track survey performance" in result["disclaimer"]


def test_cli_validate_candidate_accepts_normalized_candidate(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(["validate-candidate", str(input_path)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["errors"] == []


def test_cli_validate_candidate_rejects_unsupported_language(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    candidate = _candidate_json() | {"candidate_id": "alien signal claim"}
    input_path.write_text(json.dumps(candidate), encoding="utf-8")
    stdout = StringIO()

    exit_code = main(["validate-candidate", str(input_path)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert result["ok"] is False
    assert "alien signal" in result["errors"][0]


def test_cli_validate_reports_accepts_generated_reports(tmp_path) -> None:
    input_path = tmp_path / "candidate.json"
    output_dir = tmp_path / "reports"
    input_path.write_text(json.dumps(_candidate_json()), encoding="utf-8")
    main(["score", str(input_path), "--output-dir", str(output_dir)], stdout=StringIO())
    stdout = StringIO()

    exit_code = main(["validate-reports", str(output_dir)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["errors"] == []


def test_cli_schema_paths_outputs_schema_artifacts() -> None:
    stdout = StringIO()

    exit_code = main(["schema-paths"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert set(result) == {
        "background_draft_follow_up_reports",
        "background_draft_report_manifest",
        "background_follow_up_tests",
        "background_needs_follow_up_log",
        "background_report_readiness",
        "background_reviewed_log",
        "background_search_ledger",
        "background_targets",
        "background_user_decisions",
        "baseline_eval",
        "baseline_performance_history",
        "batch_manifest",
        "benchmark_metadata",
        "benchmark_run_results",
        "candidate_annotation",
        "candidate_audit_trail",
        "candidate_comparison",
        "candidate_extraction_handoff",
        "candidate_feature_vector",
        "candidate_flags",
        "candidate_lifecycle",
        "candidate_observation_notes",
        "candidate_packet",
        "candidate_priority_queue",
        "candidate_rescore",
        "candidate_resolution",
        "candidate_retention",
        "candidate_score_history",
        "candidate_triage",
        "config_version_history",
        "cross_track_references",
        "curated_dataset_admission",
        "curated_dataset_intake",
        "data_quality",
        "data_release_snapshot",
        "multi_target_scan",
        "scan_summary",
        "candidate_escalation",
        "cross_store_dedup",
        "epoch_plan",
        "feature_importance",
        "feature_normalization",
        "follow_up_request",
        "labeled_candidates",
        "labeled_candidates_citizen_science_v1",
        "mcp_bootstrap_consistency",
        "mcp_server_policy",
        "ml_model_registry",
        "model_architecture",
        "model_evaluation",
        "model_performance_history",
        "model_serving",
        "multi_epoch_observations",
        "observation_campaign",
        "observation_schedule",
        "ai_hardening_gate",
        "operations_action_plan",
        "operations_action_resolution",
        "operations_action_resolution_consistency",
        "operations_alert_review_consistency",
        "operations_blocker_detail",
        "operations_blocker_followup",
        "operations_blocker_followup_progress",
        "operations_blocker_progress_consistency",
        "operations_blocker_progress_execution",
        "operations_blocker_progress_execution_followup",
        "operations_blocker_progress_execution_review",
        "operations_blocker_progress_next_actions",
        "operations_blocker_progress_review",
        "operations_blocker_review",
        "operations_readiness_summary",
        "operator_assignment",
        "operator_handoff_template",
        "pipeline_config",
        "pipeline_telemetry",
        "production_blocker_consistency",
        "project_status_consistency",
        "provenance_audit",
        "real_data_admission_preflight",
        "report_manifest",
        "review_deadlines",
        "rfi_database",
        "rfi_database_admission",
        "scoring_config_summary",
        "scoring_threshold_audit",
        "sensitivity_config_summary",
        "signal_registry",
        "sqlite_operational_log_adapter_authorization_gate",
        "sqlite_operational_log_adapter_contract",
        "sqlite_operational_log_adapter_ddl_preview",
        "sqlite_operational_log_adapter_dry_run_manifest",
        "sqlite_operational_log_adapter_execution_preview",
        "sqlite_operational_log_adapter_insert_preview",
        "sqlite_operational_log_adapter_plan",
        "sqlite_operational_log_adapter_readiness_preflight",
        "sqlite_operational_log_adapter_row_preview",
        "sqlite_operational_log_registry",
        "submission_readiness",
        "target_priority_snapshots",
        "target_watchlist",
        "top_level_sqlite_log_consistency",
        "validation_dataset_manifest",
        "validation_promotion_rules",
        "validation_readiness",
        "weekly_review_template",
    }
    assert result["background_search_ledger"].endswith(
        "schemas/background_search_ledger.schema.json"
    )
    assert result["background_draft_follow_up_reports"].endswith(
        "schemas/background_draft_follow_up_reports.schema.json"
    )
    assert result["background_draft_report_manifest"].endswith(
        "schemas/background_draft_report_manifest.schema.json"
    )
    assert result["background_user_decisions"].endswith(
        "schemas/background_user_decisions.schema.json"
    )
    assert result["background_follow_up_tests"].endswith(
        "schemas/background_follow_up_tests.schema.json"
    )
    assert result["background_needs_follow_up_log"].endswith(
        "schemas/background_needs_follow_up_log.schema.json"
    )
    assert result["background_report_readiness"].endswith(
        "schemas/background_report_readiness.schema.json"
    )
    assert result["background_reviewed_log"].endswith(
        "schemas/background_reviewed_log.schema.json"
    )
    assert result["background_targets"].endswith("schemas/background_targets.schema.json")
    assert result["benchmark_metadata"].endswith("schemas/benchmark_metadata.schema.json")
    assert result["benchmark_run_results"].endswith(
        "schemas/benchmark_run_results.schema.json"
    )
    assert result["candidate_extraction_handoff"].endswith(
        "schemas/candidate_extraction_handoff.schema.json"
    )
    assert result["candidate_packet"].endswith("schemas/candidate_packet.schema.json")
    assert result["validation_dataset_manifest"].endswith(
        "schemas/validation_dataset_manifest.schema.json"
    )
    assert result["validation_promotion_rules"].endswith(
        "schemas/validation_promotion_rules.schema.json"
    )
    assert result["validation_readiness"].endswith(
        "schemas/validation_readiness.schema.json"
    )


def test_cli_score_regression_summary_outputs_snapshot_counts() -> None:
    stdout = StringIO()

    exit_code = main(["score-regression-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["removed_in_phase_0"] is True
    assert result["candidate_count"] == 0
    assert result["by_track"] == {}
    assert result["by_recommended_pathway"] == {}


def test_cli_injection_recovery_summary_outputs_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["injection-recovery-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["case_count"] == 6
    assert result["by_track"] == {"anomaly": 2, "infrared": 2, "radio": 2}
    assert result["by_outcome"] == {"false_alarm": 2, "missed": 1, "recovered": 3}
    assert result["synthetic_recovery_rate"] == 0.75
    assert result["synthetic_false_alarm_fraction"] == 0.333333


def test_cli_validation_dataset_summary_outputs_manifest_counts() -> None:
    stdout = StringIO()

    exit_code = main(["validation-dataset-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "validation_dataset_manifest_v1"
    assert result["dataset_count"] == 0
    assert result["total_case_count"] == 0
    assert result["false_positive_class_count"] == 0
    assert result["by_track"] == {}
    assert result["by_readiness"] == {}
    assert "not calibrated survey performance claims" in result["disclaimer"]


def test_cli_validation_promotion_summary_outputs_rule_counts() -> None:
    stdout = StringIO()

    exit_code = main(["validation-promotion-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "validation_dataset_promotion_rules_v1"
    assert result["rule_count"] == 3
    assert result["required_evidence_count"] == 12
    assert result["blocking_condition_count"] == 9
    assert result["rules_requiring_external_review"] == 3
    assert result["by_from_readiness"] == {"synthetic_scaffold": 3}
    assert "do not certify discoveries" in result["disclaimer"]


def test_cli_validation_readiness_summary_outputs_status_counts() -> None:
    stdout = StringIO()

    exit_code = main(["validation-readiness-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "validation_readiness_v1"
    assert result["record_count"] == 3
    assert result["ready_count"] == 1
    assert result["blocked_count"] == 1
    assert result["not_yet_admissible_count"] == 1
    assert result["blocking_issue_count"] == 4
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert "do not certify discoveries" in result["disclaimer"]

def test_cli_target_priority_summary_outputs_selected_target() -> None:
    stdout = StringIO()

    exit_code = main(["target-priority-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_target_priority_v1"
    assert result["config_version"] == "background_priority_v0"
    assert result["target_count"] == 4
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 2}
    assert result["selected_target_id"] == "target-radio-clean-drift"
    assert result["selected_priority_score"] == 0.7515
    assert result["selected_selection_score"] == 0.8315
    assert result["weights"]["false_positive_probability"] < 0
    assert result["passive_runner_requires_opt_in"] is True
    assert result["network_access_enabled"] is False
    assert "not evidence" in result["disclaimer"]


def test_cli_target_priority_summary_uses_review_history() -> None:
    stdout = StringIO()

    exit_code = main(
        [
            "target-priority-summary",
            "--ledger-path",
            "tests/fixtures/background_search_ledger.json",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["selected_target_id"] == "target-radio-never-reviewed"
    assert result["selected_selection_score"] == 0.7715
    assert result["ranked_targets"][0]["prior_review_count"] == 0


def test_cli_background_ledger_summary_outputs_logged_searches() -> None:
    stdout = StringIO()

    exit_code = main(["background-ledger-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_search_ledger_v1"
    assert result["entry_count"] == 4
    assert result["searched_target_count"] == 3
    assert result["candidate_count"] == 2
    assert result["candidate_packet_id_count"] == 2
    assert result["blocking_issue_count"] == 4
    assert result["negative_result_logged_count"] == 2
    assert result["requires_human_review_count"] == 2
    assert result["scheduling_only_count"] == 1
    assert result["by_status"] == {
        "completed": 1,
        "completed_with_blockers": 1,
        "local_fixture_search_logged": 1,
        "searched_no_candidate": 1,
    }
    assert result["by_reviewed_workflow_status"] == {
        "candidate_packet_ready": 1,
        "local_scheduling_only": 1,
        "negative_search_recorded": 1,
        "review_blocked": 1,
    }


def test_cli_reviewed_log_summary_outputs_reviewed_outcomes() -> None:
    stdout = StringIO()

    exit_code = main(["reviewed-log-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_reviewed_log_v1"
    assert result["entry_count"] == 2
    assert result["negative_evidence_count"] == 4
    assert result["network_access_allowed_count"] == 0
    assert result["by_track"] == {"anomaly": 1, "radio": 1}
    assert "not external validation" in result["disclaimer"]


def test_cli_needs_follow_up_summary_outputs_required_tests() -> None:
    stdout = StringIO()

    exit_code = main(["needs-follow-up-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_needs_follow_up_log_v1"
    assert result["entry_count"] == 2
    assert result["required_test_count"] == 12
    assert result["mandatory_test_coverage_count"] == 6
    assert result["submission_requires_user_approval_count"] == 2
    assert result["network_access_allowed_count"] == 0
    assert "human_review_checklist" in result["required_tests"]
    assert "not detections" in result["disclaimer"]
    assert "not discovery claims" in result["disclaimer"]


def test_cli_follow_up_test_summary_outputs_local_test_results() -> None:
    stdout = StringIO()

    exit_code = main(["follow-up-test-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_follow_up_tests_v1"
    assert result["result_count"] == 12
    assert result["follow_up_count"] == 2
    assert result["complete_follow_up_test_set_count"] == 2
    assert result["mandatory_test_count"] == 6
    assert result["network_access_allowed_count"] == 0
    assert result["by_status"] == {
        "blocked": 2,
        "pass": 7,
        "ready": 1,
        "uncertain": 2,
    }
    assert "human_review_checklist" in result["required_tests"]
    assert "not external validation" in result["disclaimer"]


def test_cli_report_readiness_summary_outputs_submission_gate() -> None:
    stdout = StringIO()

    exit_code = main(["report-readiness-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_report_readiness_v1"
    assert result["record_count"] == 2
    assert result["ready_to_draft_report_count"] == 1
    assert result["blocked_count"] == 1
    assert result["user_approval_required_count"] == 2
    assert result["external_submission_allowed_count"] == 0
    assert result["top_three_recommendation_count"] == 6
    assert result["by_destination_action"] == {
        "do_not_submit_yet": 1,
        "internal_review": 2,
        "request_more_tests": 3,
    }
    assert "not discoveries" in result["disclaimer"]


def test_cli_draft_follow_up_report_summary_generates_conservative_reports() -> None:
    stdout = StringIO()

    exit_code = main(["draft-follow-up-report-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_draft_follow_up_reports_v1"
    assert result["draft_report_count"] == 2
    assert result["draft_ready_count"] == 1
    assert result["blocked_count"] == 1
    assert result["negative_evidence_count"] == 6
    assert result["external_submission_allowed_count"] == 0
    assert result["network_access_allowed_count"] == 0
    assert result["by_draft_status"] == {
        "blocked_not_ready": 1,
        "draft_ready": 1,
    }
    assert "not discoveries" in result["disclaimer"]


def test_cli_draft_report_fixture_summary_outputs_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["draft-report-fixture-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_draft_follow_up_reports_v1"
    assert result["draft_report_count"] == 2
    assert result["draft_ready_count"] == 1
    assert result["external_submission_allowed_count"] == 0


def test_cli_writes_and_validates_draft_follow_up_reports(tmp_path) -> None:
    output_dir = tmp_path / "draft_reports"
    stdout = StringIO()

    exit_code = main(
        ["draft-follow-up-report-write", "--output-dir", str(output_dir)],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["summary"]["draft_report_count"] == 2
    assert Path(result["manifest_path"]).exists()
    assert all(Path(path).exists() for path in result["markdown_paths"])

    validate_stdout = StringIO()
    validate_exit_code = main(
        ["validate-draft-reports", str(output_dir)],
        stdout=validate_stdout,
    )
    validation = json.loads(validate_stdout.getvalue())

    assert validate_exit_code == 0
    assert validation["ok"] is True
    assert validation["errors"] == []


def test_cli_user_decision_summary_outputs_human_gate_counts() -> None:
    stdout = StringIO()

    exit_code = main(["user-decision-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_user_decisions_v1"
    assert result["decision_count"] == 3
    assert result["external_submission_approved_count"] == 0
    assert result["request_more_tests_count"] == 2
    assert result["close_as_reviewed_count"] == 1
    assert result["network_access_allowed_count"] == 0
    assert result["by_decision"] == {
        "close_as_reviewed": 1,
        "request_more_tests": 2,
    }
    assert "do not create external submission approval" in result["disclaimer"]


def test_cli_user_decision_record_appends_request_more_tests(tmp_path) -> None:
    decisions_path = tmp_path / "background_user_decisions.json"
    stdout = StringIO()

    exit_code = main(
        [
            "user-decision-record",
            "--user-decision-path",
            str(decisions_path),
            "--decision-id",
            "decision-cli-001",
            "--readiness-id",
            "readiness-cli",
            "--follow-up-id",
            "follow-up-cli",
            "--target-id",
            "target-cli",
            "--track",
            "radio",
            "--decision",
            "request_more_tests",
            "--rationale",
            "More local review is required.",
            "--required-next-action",
            "repeat local review",
            "--blocking-issue",
            "external submission has not been approved",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["summary"]["decision_count"] == 1
    assert result["summary"]["external_submission_approved_count"] == 0
    assert decisions_path.exists()


def test_cli_user_decision_record_has_no_submission_approval_choice(tmp_path) -> None:
    decisions_path = tmp_path / "background_user_decisions.json"
    stdout = StringIO()

    with pytest.raises(SystemExit):
        main(
            [
                "user-decision-record",
                "--user-decision-path",
                str(decisions_path),
                "--decision-id",
                "decision-cli-approve-001",
                "--readiness-id",
                "readiness-cli",
                "--follow-up-id",
                "follow-up-cli",
                "--target-id",
                "target-cli",
                "--track",
                "radio",
                "--decision",
                "approve_submission",
                "--rationale",
                "User is testing the approval gate.",
            ],
            stdout=stdout,
        )

    assert not decisions_path.exists()


def test_cli_submission_recommendation_summary_aliases_report_readiness() -> None:
    stdout = StringIO()

    exit_code = main(["submission-recommendation-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_report_readiness_v1"
    assert result["top_three_recommendation_count"] == 6
    assert result["external_submission_allowed_count"] == 0


def test_cli_background_reviewed_workflow_summary_outputs_review_state() -> None:
    stdout = StringIO()

    exit_code = main(["background-reviewed-workflow-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_search_ledger_v1"
    assert result["entry_count"] == 4
    assert result["reviewed_workflow_status_count"] == 4
    assert result["target_selection_rationale_count"] == 12
    assert result["negative_result_logged_count"] == 2
    assert result["requires_human_review_count"] == 2
    assert result["local_only_entry_count"] == 1
    assert result["scheduling_only_count"] == 1
    assert result["candidate_packet_id_count"] == 2
    assert result["blocked_entry_count"] == 3
    assert result["by_execution_mode"] == {
        "local_non_network_fixture_runner": 1,
        "synthetic_priority_demo": 3,
    }
    assert result["by_reviewed_workflow_status"] == {
        "candidate_packet_ready": 1,
        "local_scheduling_only": 1,
        "negative_search_recorded": 1,
        "review_blocked": 1,
    }


def test_cli_candidate_extraction_handoff_summary_outputs_contract() -> None:
    stdout = StringIO()

    exit_code = main(["candidate-extraction-handoff-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "candidate_extraction_handoff_v1"
    assert result["record_count"] == 4
    assert result["ready_count"] == 1
    assert result["blocked_count"] == 1
    assert result["no_candidate_expected_count"] == 1
    assert result["scheduling_only_count"] == 1
    assert result["expected_candidate_packet_count"] == 2
    assert result["candidate_fixture_count"] == 2
    assert result["blocking_issue_count"] == 3
    assert result["negative_result_required_count"] == 2
    assert result["requires_human_review_count"] == 2
    assert result["network_access_allowed_count"] == 0
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 2}
    assert result["by_extraction_status"] == {
        "blocked": 1,
        "no_candidate_expected": 1,
        "ready_for_extraction": 1,
        "scheduling_only": 1,
    }
    assert "not detections" in result["disclaimer"]


def test_cli_background_run_once_appends_local_ledger_entry(tmp_path) -> None:
    ledger_path = tmp_path / "background_ledger.json"
    sqlite_log_path = tmp_path / "logs" / "techno_search.sqlite3"
    stdout = StringIO()

    exit_code = main(
        [
            "background-run-once",
            "--ledger-path",
            str(ledger_path),
            "--sqlite-log-path",
            str(sqlite_log_path),
            "--run-id",
            "cli-local-run-001",
            "--code-commit",
            "cli-test",
            "--acknowledge-local-run",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["appended_entry"]["run_id"] == "cli-local-run-001"
    assert result["appended_entry"]["target_id"] == "target-radio-clean-drift"
    assert result["appended_entry"]["status"] == "needs_follow_up_logged"
    assert result["appended_entry"]["execution_mode"] == (
        "local_non_network_fixture_runner"
    )
    assert result["appended_entry"]["negative_result_logged"] is False
    assert result["appended_entry"]["reviewed_workflow_status"] == (
        "needs_follow_up_required"
    )
    assert result["ledger_summary"]["entry_count"] == 1
    assert result["ledger_summary"]["candidate_count"] == 0
    assert result["review_workflow_summary"]["local_only_entry_count"] == 1
    assert result["outcome_log"]["outcome"] == "needs_follow_up"
    assert (tmp_path / "background_needs_follow_up_log.json").exists()
    assert ledger_path.exists()
    assert sqlite_log_path.exists()
    assert result["sqlite_log_path"] == str(sqlite_log_path)


def test_cli_top_level_sqlite_log_commands_validate_background_run(
    tmp_path,
) -> None:
    db_path = tmp_path / "logs" / "techno_search.sqlite3"
    stdout = StringIO()

    init_exit_code = main(
        [
            "init-logs",
            "--db-path",
            str(db_path),
            "--code-commit",
            "cli-test",
            "--config-version",
            "background_priority_v0",
        ],
        stdout=stdout,
    )
    init_result = json.loads(stdout.getvalue())

    assert init_exit_code == 0
    assert init_result["database_exists"] is True
    assert init_result["run_count"] == 0

    stdout = StringIO()
    main(
        [
            "background-run-once",
            "--ledger-path",
            str(tmp_path / "artifacts" / "background_search_ledger.json"),
            "--sqlite-log-path",
            str(db_path),
            "--run-id",
            "cli-sqlite-run-001",
            "--code-commit",
            "cli-test",
            "--acknowledge-local-run",
        ],
        stdout=stdout,
    )

    stdout = StringIO()
    summary_exit_code = main(
        ["sqlite-log-summary", "--db-path", str(db_path)],
        stdout=stdout,
    )
    summary = json.loads(stdout.getvalue())

    assert summary_exit_code == 0
    assert summary["run_count"] == 1
    assert summary["outcome_count"] == 1
    assert summary["network_access_allowed_count"] == 0
    assert summary["external_submission_approved_count"] == 0

    stdout = StringIO()
    validate_exit_code = main(
        ["validate-sqlite-logs", "--db-path", str(db_path)],
        stdout=stdout,
    )
    validation = json.loads(stdout.getvalue())

    assert validate_exit_code == 0
    assert validation["ok"] is True

    stdout = StringIO()
    integrity_exit_code = main(
        ["sqlite-log-integrity-summary", "--db-path", str(db_path)],
        stdout=stdout,
    )
    integrity = json.loads(stdout.getvalue())
    assert integrity_exit_code == 0
    assert integrity["ok"] is True

    stdout = StringIO()
    bootstrap_exit_code = main(
        [
            "sqlite-log-bootstrap-summary",
            "--db-path",
            str(db_path),
            "--code-commit",
            "cli-test",
            "--config-version",
            "background_priority_v0",
        ],
        stdout=stdout,
    )
    bootstrap = json.loads(stdout.getvalue())
    assert bootstrap_exit_code == 0
    assert bootstrap["ok"] is True
    assert bootstrap["sqlite_log_initialized"] is True
    assert bootstrap["sqlite_integrity_ok"] is True
    assert bootstrap["sqlite_weekly_digest_ok"] is True
    assert bootstrap["readiness_sqlite_integrity_ok"] is True
    assert bootstrap["readiness_sqlite_weekly_digest_ok"] is True
    assert bootstrap["network_access_allowed_count"] == 0
    assert bootstrap["external_submission_approved_count"] == 0
    assert bootstrap["validated_action_ids"] == ["ops-action-009", "ops-action-010"]
    assert bootstrap["does_not_mutate_action_resolution_fixture"] is True
    assert bootstrap["readiness_recommendation"] == "blocked_for_real_data"

    stdout = StringIO()
    recent_exit_code = main(
        ["sqlite-recent-runs", "--db-path", str(db_path), "--limit", "1"],
        stdout=stdout,
    )
    recent = json.loads(stdout.getvalue())
    assert recent_exit_code == 0
    assert recent["run_count"] == 1
    assert recent["runs"][0]["run_id"] == "cli-sqlite-run-001"

    stdout = StringIO()
    follow_up_exit_code = main(
        ["sqlite-needs-follow-up", "--db-path", str(db_path), "--limit", "1"],
        stdout=stdout,
    )
    follow_up = json.loads(stdout.getvalue())
    assert follow_up_exit_code == 0
    assert follow_up["needs_follow_up_count"] == 1
    assert follow_up["needs_follow_up"][0]["negative_evidence"]

    stdout = StringIO()
    export_exit_code = main(
        ["sqlite-log-export", "--db-path", str(db_path), "--limit", "1"],
        stdout=stdout,
    )
    exported = json.loads(stdout.getvalue())
    assert export_exit_code == 0
    assert exported["summary"]["ok"] is True
    assert exported["recent_runs"][0]["uncertainty_notes"]

    stdout = StringIO()
    migration_exit_code = main(
        ["sqlite-migration-summary", "--db-path", str(db_path)],
        stdout=stdout,
    )
    migration = json.loads(stdout.getvalue())
    assert migration_exit_code == 0
    assert migration["migration_required"] is False

    stdout = StringIO()
    pragmas_exit_code = main(
        ["sqlite-log-pragmas", "--db-path", str(db_path)],
        stdout=stdout,
    )
    pragmas = json.loads(stdout.getvalue())
    assert pragmas_exit_code == 0
    assert pragmas["ok"] is True
    assert pragmas["integrity_check"] == "ok"

    stdout = StringIO()
    backup_exit_code = main(
        ["sqlite-log-backup", "--db-path", str(db_path)],
        stdout=stdout,
    )
    backup = json.loads(stdout.getvalue())
    assert backup_exit_code == 0
    assert backup["ok"] is True

    stdout = StringIO()
    retention_exit_code = main(
        ["sqlite-log-retention-summary", "--db-path", str(db_path)],
        stdout=stdout,
    )
    retention = json.loads(stdout.getvalue())
    assert retention_exit_code == 0
    assert retention["ok"] is True
    assert retention["backup_count"] >= 1

    stdout = StringIO()
    consistency_exit_code = main(
        ["sqlite-log-consistency-summary", "--db-path", str(db_path)],
        stdout=stdout,
    )
    consistency = json.loads(stdout.getvalue())
    assert consistency_exit_code == 0
    assert consistency["ok"] is True

    stdout = StringIO()
    vacuum_exit_code = main(
        ["sqlite-log-vacuum", "--db-path", str(db_path)],
        stdout=stdout,
    )
    vacuum = json.loads(stdout.getvalue())
    assert vacuum_exit_code == 0
    assert vacuum["ok"] is True


def test_cli_sqlite_log_commit_guard_rejects_generated_logs(tmp_path) -> None:
    stdout = StringIO()

    exit_code = main(
        [
            "sqlite-log-commit-guard",
            "logs/README.md",
            "logs/techno_search.sqlite3",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert result["ok"] is False
    assert result["forbidden_paths"] == ["logs/techno_search.sqlite3"]


def test_cli_scheduler_dry_run_writes_temporary_artifacts(tmp_path) -> None:
    stdout = StringIO()

    exit_code = main(
        [
            "scheduler-dry-run",
            "--artifact-dir",
            str(tmp_path),
            "--run-id",
            "cli-scheduler-dry-run",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["network_access_enabled"] is False
    assert result["external_submission_allowed"] is False
    assert (tmp_path / "background_search_ledger.json").exists()
    assert (tmp_path / "background_needs_follow_up_log.json").exists()
    assert (tmp_path / "background_logs.sqlite3").exists()


def test_cli_validate_all_outputs_local_summary() -> None:
    stdout = StringIO()

    exit_code = main(["validate-all"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["schema_version"] == "phase0_scientific_validate_all_v1"
    assert result["phase"] == "Phase 0 \u2014 Strip & Fix"
    assert "operational_log_summaries" in result["omitted_legacy_payloads"]
    assert "synthetic_training_summaries" in result["omitted_legacy_payloads"]
    assert "calibration_summary" not in result
    assert "false_positive_summary" not in result
    assert "score_regression_summary" not in result
    assert "provider_normalization_summary" not in result
    assert "top_level_sqlite_log_summary" not in result
    assert result["artifact_hygiene"]["catalog_cache_validation"]["ok"] is True
    assert (
        result["artifact_hygiene"]["top_level_sqlite_log_commit_guard"]["ok"]
        is True
    )
    assert result["catalog_cache_validation"]["forbidden_roots"] == [
        "data",
        "cache",
        "artifacts",
    ]
    assert result["top_level_sqlite_log_commit_guard"]["ok"] is True
    assert result["radio_science_summary"]["cross_band_feature_count"] >= 4
    assert result["radio_science_summary"]["globular_feature_count"] >= 13
    assert result["radio_science_summary"]["semisupervised_feature_count"] >= 12
    assert "real_label_accuracy_gate_ok" not in result
    assert "eval_against_labels_summary" not in result
    assert "learned_scoring_model_v1_summary" not in result
    assert result["provenance_chain_validation"]["ok"] is True
    assert result["project_status_consistency_summary"]["ok"] is True
    assert result["ai_hardening_gate_summary"]["ok"] is True
    assert result["real_data_admission_preflight_summary"]["ok"] is True
    assert all(result["schema_paths_exist"].values())


def test_cli_semisupervised_scorer_train_writes_local_artifacts(tmp_path) -> None:
    corpus_path = tmp_path / "meerkat_sample.ndjson"
    rows = []
    for index in range(12):
        rows.append(
            {
                "snr": 8.0 + index,
                "drift_rate_hz_per_sec": 0.0,
                "frequency_hz": 1.0e9 + index * 1.0e6,
                "bandwidth_hz": 2.0,
                "normalized_drift_hz_s_per_ghz": 0.0,
                "relative_snr": 1.0,
                "on_off_consistency_score": 0.8,
                "is_earth_drift_consistent": 1.0,
                "rfi_band_overlap_score": 0.2,
                "frequency_persistence_score": 0.6,
                "on_hit_count": 1,
                "off_hit_count": 1,
            }
        )
    corpus_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    metadata_path = tmp_path / "semisupervised_scorer_metadata.json"
    model_path = tmp_path / "semisupervised_scorer.joblib"
    stdout = StringIO()

    exit_code = main(
        [
            "semisupervised-scorer-train",
            "--corpus",
            str(corpus_path),
            "--max-hits",
            "12",
            "--workers",
            "1",
            "--n-estimators",
            "10",
            "--n-components",
            "4",
            "--output-metadata",
            str(metadata_path),
            "--output-model",
            str(model_path),
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["is_fitted"] is True
    assert result["train_hit_count"] == 12
    assert result["n_jobs"] == 1
    assert result["accelerator"]["used"] == "sklearn_cpu"
    assert metadata_path.exists()
    assert model_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["train_hit_count"] == 12


def test_cli_semisupervised_scorer_summary_reads_local_artifacts(tmp_path) -> None:
    metadata_path = tmp_path / "semisupervised_scorer_metadata.json"
    model_path = tmp_path / "semisupervised_scorer.joblib"
    metadata_path.write_text(
        json.dumps({
            "schema_version": "semisupervised_scorer_v1",
            "feature_names": ["snr", "frequency_hz"],
            "n_components": 2,
            "n_estimators": 10,
            "contamination": 0.01,
            "random_state": 42,
            "n_jobs": 1,
            "train_hit_count": 200000,
        }),
        encoding="utf-8",
    )
    model_path.write_bytes(b"local fitted model placeholder")
    stdout = StringIO()

    exit_code = main(
        [
            "semisupervised-scorer-summary",
            "--metadata",
            str(metadata_path),
            "--model",
            str(model_path),
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["metadata_loaded"] is True
    assert result["model_ready"] is True
    assert result["is_fitted"] is True
    assert result["train_hit_count"] == 200000
    assert result["feature_count"] == 2


def test_cli_semisupervised_corpus_build_from_dat_files(tmp_path) -> None:
    dat_dir = tmp_path / "dat"
    dat_dir.mkdir()
    _write_cli_turboseti_dat(dat_dir / "hits.dat")
    output = tmp_path / "training.ndjson"
    stdout = StringIO()

    exit_code = main(
        [
            "semisupervised-corpus-build",
            "--dat-dir",
            str(dat_dir),
            "--output",
            str(output),
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["hit_count"] == 2
    assert result["corpus_source"] == "real_turboseti_dat"
    assert output.exists()
    assert Path(result["provenance_path"]).exists()


def test_cli_regenerate_examples_writes_relative_example_outputs(tmp_path, monkeypatch) -> None:
    candidate_dir = tmp_path / "examples" / "candidates"
    candidate_dir.mkdir(parents=True)
    (candidate_dir / "candidate.json").write_text(json.dumps(_candidate_json()), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    stdout = StringIO()

    exit_code = main(["regenerate-examples"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["candidate_count"] == 1
    assert result["reports_dir"] == "examples/reports"
    assert (tmp_path / "examples" / "reports" / "cli-radio.json").exists()
    assert (tmp_path / "examples" / "batch_reports" / "batch_manifest.json").exists()


def test_cli_provenance_summary_outputs_example_report_counts() -> None:
    stdout = StringIO()

    exit_code = main(["provenance-summary", "examples/reports"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["manifest_count"] == 3
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert result["by_schema_version"] == {"techno_search_packet_v1": 3}
    assert result["by_config_version"] == {"scoring_v0": 3}


def test_cli_plot_artifact_summary_outputs_example_counts() -> None:
    stdout = StringIO()

    exit_code = main(["plot-artifact-summary", "examples/reports"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["manifest_count"] == 3
    assert result["plot_artifact_count"] == 3
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert result["by_kind"] == {
        "synthetic_anomaly_crossmatch": 1,
        "synthetic_infrared_sed": 1,
        "synthetic_radio_waterfall": 1,
    }
    assert result["missing_path_count"] == 0


def test_cli_provenance_summary_outputs_batch_report_counts() -> None:
    stdout = StringIO()

    exit_code = main(["provenance-summary", "examples/batch_reports"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["manifest_count"] == 3
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert result["by_source_dataset"] == {"synthetic-example": 3}


def test_cli_live_provider_summary_lists_default_off_providers(monkeypatch) -> None:
    monkeypatch.delenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", raising=False)
    stdout = StringIO()

    exit_code = main(["live-provider-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["live_enabled"] is False
    assert result["provider_count"] == 5
    assert {provider["provider_name"] for provider in result["providers"]} == {
        "breakthrough_listen",
        "gaia",
        "irsa",
        "simbad",
        "vizier",
    }


def test_cli_live_cache_summary_outputs_cache_counts(tmp_path) -> None:
    cache_dir = tmp_path / "cache" / "live_providers"
    provider_dir = cache_dir / "gaia"
    provider_dir.mkdir(parents=True)
    (provider_dir / "abc.metadata.json").write_text("{}", encoding="utf-8")
    stdout = StringIO()

    exit_code = main(["live-cache-summary", "--cache-dir", str(cache_dir)], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["cache_dir"] == str(cache_dir)
    assert result["exists"] is True
    assert result["metadata_file_count"] == 1
    assert result["by_provider"] == {"gaia": 1}


def test_cli_live_fixture_summary_outputs_committed_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["live-fixture-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["fixture_schema_version"] == "live_metadata_fixture_v1"
    assert result["fixture_count"] == 10
    assert result["by_provider"] == {
        "breakthrough_listen": 2,
        "gaia": 2,
        "irsa": 2,
        "simbad": 2,
        "vizier": 2,
    }


def test_cli_live_client_summary_outputs_disabled_skeleton_status(monkeypatch) -> None:
    monkeypatch.delenv("TECHNO_SEARCH_ENABLE_LIVE_DATA", raising=False)
    stdout = StringIO()

    exit_code = main(["live-client-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["live_enabled"] is False
    assert result["client_count"] == 5
    assert {client["provider_name"] for client in result["clients"]} == {
        "breakthrough_listen",
        "gaia",
        "irsa",
        "simbad",
        "vizier",
    }
    implemented_by_provider = {
        client["provider_name"]: client["implemented"] for client in result["clients"]
    }
    networked_by_provider = {
        client["provider_name"]: client["networked"] for client in result["clients"]
    }
    local_file_only_by_provider = {
        client["provider_name"]: client["local_file_only"] for client in result["clients"]
    }
    assert implemented_by_provider == {
        "breakthrough_listen": True,
        "gaia": True,
        "irsa": True,
        "simbad": True,
        "vizier": True,
    }
    assert networked_by_provider == {
        "breakthrough_listen": False,
        "gaia": True,
        "irsa": True,
        "simbad": True,
        "vizier": True,
    }
    assert local_file_only_by_provider == {
        "breakthrough_listen": True,
        "gaia": False,
        "irsa": False,
        "simbad": False,
        "vizier": False,
    }
    assert all(client["requires_live_opt_in"] is True for client in result["clients"])


def test_cli_catalog_cache_policy_outputs_policy_without_creating_dir(tmp_path) -> None:
    cache_root = tmp_path / "catalog-cache"
    stdout = StringIO()

    exit_code = main(
        ["catalog-cache-policy", "--cache-root", str(cache_root)],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["cache_root"] == str(cache_root)
    assert result["allowed_suffixes"] == [".metadata.json", ".json"]
    assert result["creates_directories"] is False
    assert result["implements_catalog_ingestion"] is False
    assert not cache_root.exists()


def test_cli_catalog_cache_summary_outputs_empty_cache_without_creating_dir(tmp_path) -> None:
    cache_root = tmp_path / "catalog-cache"
    stdout = StringIO()

    exit_code = main(
        ["catalog-cache-summary", "--cache-root", str(cache_root)],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["cache_root"] == str(cache_root)
    assert result["exists"] is False
    assert result["metadata_file_count"] == 0
    assert result["metadata_total_bytes"] == 0
    assert result["by_provider"] == {}
    assert result["implements_catalog_ingestion"] is False
    assert not cache_root.exists()


def test_cli_catalog_cache_summary_outputs_provider_counts(tmp_path) -> None:
    cache_root = tmp_path / "catalog-cache"
    provider_dir = cache_root / "gaia"
    provider_dir.mkdir(parents=True)
    (provider_dir / "abc.metadata.json").write_text("{}", encoding="utf-8")
    stdout = StringIO()

    exit_code = main(
        ["catalog-cache-summary", "--cache-root", str(cache_root)],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["cache_root"] == str(cache_root)
    assert result["exists"] is True
    assert result["metadata_file_count"] == 1
    assert result["metadata_total_bytes"] == 2
    assert result["by_provider"] == {"gaia": 1}


def test_cli_catalog_cache_validate_accepts_fixture_paths() -> None:
    stdout = StringIO()

    exit_code = main(
        [
            "catalog-cache-validate",
            "tests/fixtures/live_metadata/gaia_cone_search.metadata.json",
            "docs/CATALOG_CACHE_POLICY.md",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["errors"] == []
    assert result["checked_path_count"] == 2


def test_cli_catalog_cache_validate_rejects_forbidden_paths() -> None:
    stdout = StringIO()

    exit_code = main(
        [
            "catalog-cache-validate",
            "cache/catalog_metadata/gaia/example.metadata.json",
            "data/raw/catalog.csv",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert result["ok"] is False
    assert result["errors"] == [
        (
            "Catalog cache path must not be committed: "
            "cache/catalog_metadata/gaia/example.metadata.json"
        ),
        "Catalog cache path must not be committed: data/raw/catalog.csv",
    ]


def test_cli_prod_run_id_accepts_deterministic_token() -> None:
    stdout = StringIO()

    exit_code = main(["prod-run-id", "--token", "a7k4"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["run_id"].startswith("RUN-")
    assert result["run_id"].endswith("-A7K4-prod-scan")


def test_cli_prod_write_and_show_outcomes(tmp_path) -> None:
    run_id = "RUN-2026-06-18_201325Z-A7K4-prod-scan"
    results_dir = tmp_path / "results"
    target_dir = results_dir / "HIP99427"
    target_dir.mkdir(parents=True)
    candidate_json = target_dir / "candidate.json"
    candidate_json.write_text(
        json.dumps(
            {
                "candidate_id": "candidate",
                "recommended_pathway": "candidate_review_packet",
                "features": {
                    "frequency_hz": 1420000000.0,
                    "snr": 55.0,
                    "drift_rate_hz_per_sec": 0.2,
                },
                "scores": {"followup_value": 0.9},
                "track": "radio",
            }
        ),
        encoding="utf-8",
    )
    (target_dir / "candidate.manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "candidate",
                "recommended_pathway": "candidate_review_packet",
                "json_path": candidate_json.name,
            }
        ),
        encoding="utf-8",
    )
    run_dir = results_dir / "scans" / run_id
    stdout = StringIO()

    exit_code = main(
        [
            "prod-write-outcomes",
            "--results-dir",
            str(results_dir),
            "--run-dir",
            str(run_dir),
            "--run-id",
            run_id,
            "--started-at-utc",
            "2026-06-18T20:13:25Z",
        ],
        stdout=stdout,
    )
    written = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert written["follow_up_count"] == 1
    stdout = StringIO()
    assert main(["prod-show", str(run_dir)], stdout=stdout) == 0
    shown = json.loads(stdout.getvalue())
    assert shown["run_id"] == run_id
    assert shown["external_submission_allowed"] is False
    stdout = StringIO()
    assert main(["prod-follow-ups", str(run_dir)], stdout=stdout) == 0
    follow_up_rows = stdout.getvalue()
    assert f"{run_id}: 1 follow-up candidate row(s)" in follow_up_rows
    assert "FU-2026-06-18_201325Z-A7K4-001 | HIP99427 | radio | 0.900" in follow_up_rows
    stdout = StringIO()
    assert main(["prod-follow-ups", str(run_dir), "--json"], stdout=stdout) == 0
    follow_ups = json.loads(stdout.getvalue())
    assert follow_ups["entries"][0]["follow_up_id"] == (
        "FU-2026-06-18_201325Z-A7K4-001"
    )
    stdout = StringIO()
    assert main(["prod-non-detections", str(run_dir)], stdout=stdout) == 0
    assert f"{run_id}: 0 non-detection/no-follow-up row(s)" in stdout.getvalue()
    stdout = StringIO()
    assert main(["prod-non-detections", str(run_dir), "--json"], stdout=stdout) == 0
    non_detections = json.loads(stdout.getvalue())
    assert non_detections["entry_count"] == 0
    stdout = StringIO()
    assert (
        main(
            ["prod-runs", "--scans-dir", str(results_dir / "scans"), "--json"],
            stdout=stdout,
        )
        == 0
    )
    runs = json.loads(stdout.getvalue())
    assert runs["run_count"] == 1
    stdout = StringIO()
    assert main(["prod-runs", "--scans-dir", str(results_dir / "scans")], stdout=stdout) == 0
    run_rows = stdout.getvalue()
    assert "1 run(s)" in run_rows
    assert "Run ID | OK | Targets | Records | Follow-ups | Non-detections" in run_rows
    assert f"{run_id} | yes | 1 | 1 | 1 | 0" in run_rows
    stdout = StringIO()
    assert main(["review-dashboard", "--run-dir", str(run_dir)], stdout=stdout) == 1
    dashboard_text = stdout.getvalue()
    assert "1 follow-up candidate target(s)" in dashboard_text
    assert "needs_attention=yes" in dashboard_text
    assert "review_candidate_packets" in dashboard_text
    stdout = StringIO()
    assert main(["review-dashboard", "--run-dir", str(run_dir), "--json"], stdout=stdout) == 1
    dashboard = json.loads(stdout.getvalue())
    assert dashboard["schema_version"] == "operator_review_dashboard_v1"
    assert dashboard["needs_attention"] is True
    assert dashboard["follow_up_required_count"] == 1
    assert dashboard["action_items"][0]["action"] == "review_candidate_packets"
    assert dashboard["detection_claimed"] is False
    assert dashboard["external_submission_allowed"] is False


def test_cli_prod_scan_routes_to_compact_runner(monkeypatch, tmp_path) -> None:
    calls: dict[str, object] = {}

    def fake_run_production_scan(**kwargs):
        calls.update(kwargs)
        kwargs["stdout"].write("compact scan\n")
        return object()

    monkeypatch.setattr(
        "techno_search.production_scan.run_production_scan",
        fake_run_production_scan,
    )
    stdout = StringIO()

    exit_code = main(
        [
            "prod-scan",
            "--results-dir",
            str(tmp_path / "results"),
            "--scans-dir",
            str(tmp_path / "scans"),
            "--run-id",
            "RUN-2026-06-18_201325Z-A7K4-prod-scan",
            "--no-rich",
        ],
        stdout=stdout,
    )

    assert exit_code == 0
    assert calls["results_dir"] == tmp_path / "results"
    assert calls["scans_dir"] == tmp_path / "scans"
    assert calls["run_id"] == "RUN-2026-06-18_201325Z-A7K4-prod-scan"
    assert calls["use_rich"] is False
    assert "compact scan" in stdout.getvalue()


def test_cli_prod_scan_forwards_allow_empty(monkeypatch, tmp_path) -> None:
    calls: dict[str, object] = {}

    def fake_run_production_scan(**kwargs):
        calls.update(kwargs)
        kwargs["stdout"].write("compact scan\n")
        return object()

    monkeypatch.setattr(
        "techno_search.production_scan.run_production_scan",
        fake_run_production_scan,
    )
    stdout = StringIO()

    exit_code = main(
        [
            "prod-scan",
            "--results-dir",
            str(tmp_path / "results"),
            "--scans-dir",
            str(tmp_path / "scans"),
            "--allow-empty",
        ],
        stdout=stdout,
    )

    assert exit_code == 0
    assert calls["allow_empty"] is True


def test_cli_prod_diagnostics_returns_nonzero_when_attention_needed(monkeypatch, tmp_path) -> None:
    def fake_production_diagnostics(**kwargs):
        kwargs["stdout"].write("diagnostics\n")
        return {
            "validate_all_ok": True,
            "review_dashboard_needs_attention": True,
            "production_run_count": 2,
        }

    monkeypatch.setattr(
        "techno_search.production_scan.production_diagnostics",
        fake_production_diagnostics,
    )
    stdout = StringIO()

    exit_code = main(
        [
            "prod-diagnostics",
            "--scans-dir",
            str(tmp_path / "scans"),
            "--no-rich",
            "--json",
        ],
        stdout=stdout,
    )

    assert exit_code == 1
    rendered = stdout.getvalue()
    assert "diagnostics" in rendered
    assert '"review_dashboard_needs_attention": true' in rendered


def test_cli_prod_target_status_shows_target_status(tmp_path) -> None:
    run_id = "RUN-2026-06-18_201325Z-A7K4-prod-scan"
    results_dir = tmp_path / "results"
    target_dir = results_dir / "HIP99427"
    target_dir.mkdir(parents=True)
    candidate_json = target_dir / "candidate.json"
    candidate_json.write_text(
        json.dumps(
            {
                "candidate_id": "candidate",
                "recommended_pathway": "candidate_review_packet",
                "features": {
                    "frequency_hz": 1420000000.0,
                    "snr": 55.0,
                    "drift_rate_hz_per_sec": 0.2,
                },
                "scores": {"followup_value": 0.9},
                "track": "radio",
            }
        ),
        encoding="utf-8",
    )
    (target_dir / "candidate.manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "candidate",
                "recommended_pathway": "candidate_review_packet",
                "json_path": candidate_json.name,
            }
        ),
        encoding="utf-8",
    )
    run_dir = results_dir / "scans" / run_id
    main(
        [
            "prod-write-outcomes",
            "--results-dir",
            str(results_dir),
            "--run-dir",
            str(run_dir),
            "--run-id",
            run_id,
            "--started-at-utc",
            "2026-06-18T20:13:25Z",
        ],
        stdout=StringIO(),
    )
    stdout = StringIO()

    assert main(["prod-target-status", str(run_dir)], stdout=stdout) == 0
    compact_status = stdout.getvalue()
    assert f"{run_id}: 1 target(s), 1 follow-up candidate target(s)" in compact_status
    assert "Index | Target | Kind | Follow-up | Score | Pathway" in compact_status
    assert (
        "FU-2026-06-18_201325Z-A7K4-001 | HIP99427 | stellar target | yes | 0.900"
        in compact_status
    )

    stdout = StringIO()
    assert main(["prod-target-status", str(run_dir), "--json"], stdout=stdout) == 0
    target_status = json.loads(stdout.getvalue())
    assert target_status["target_count"] == 1
    assert target_status["entries"][0]["follow_up_required"] is True

    stdout = StringIO()
    assert (
        main(
            [
                "prod-target-status",
                "--latest",
                "--scans-dir",
                str(results_dir / "scans"),
                "--json",
            ],
            stdout=stdout,
        )
        == 0
    )
    latest_target_status = json.loads(stdout.getvalue())
    assert latest_target_status["run_id"] == run_id


def test_cli_prod_latest_reports_no_runs_without_placeholder_path(tmp_path) -> None:
    stdout = StringIO()

    assert (
        main(
            [
                "prod-target-status",
                "--latest",
                "--scans-dir",
                str(tmp_path / "scans"),
            ],
            stdout=stdout,
        )
        == 1
    )
    result = json.loads(stdout.getvalue())
    assert result["ok"] is False
    assert "No production runs found" in result["error"]
    assert "run_production_scan.sh" in result["error"]
