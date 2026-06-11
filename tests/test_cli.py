import json
from io import StringIO
from pathlib import Path

import pytest

from techno_search.cli import main, score_batch


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
    assert summary["total"] == 15
    assert summary["by_track"] == {"anomaly": 6, "infrared": 5, "radio": 4}
    assert summary["by_expected_pathway"] == {"do_not_submit_false_positive": 15}


def test_cli_false_positive_summary_outputs_class_counts() -> None:
    stdout = StringIO()

    exit_code = main(["false-positive-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "synthetic_false_positive_analysis_v1"
    assert result["case_count"] == 15
    assert result["class_count"] == 15
    assert result["by_track"] == {"anomaly": 6, "infrared": 5, "radio": 4}
    assert result["by_class"]["rfi"] == 1


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
    assert result["blocked_count"] == 4
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
    assert result["blocked_count"] == 3
    assert result["real_data_authorized_count"] == 1
    assert result["validation_ok"] is True
    assert "does not authorize unreviewed real observation data" in result["disclaimer"]


def test_cli_project_status_consistency_summary_outputs_drift_gates() -> None:
    stdout = StringIO()

    exit_code = main(["project-status-consistency-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "project_status_consistency_v1"
    assert result["ok"] is True
    assert result["roadmap_latest_milestone"] == 73
    assert result["decisions_latest_decision"] == 124
    assert result["actual_schema_count"] == 103
    assert result["rfi_database_admission_real_data_authorized_count"] == 0
    assert result["curated_dataset_admission_real_data_authorized_count"] == 1


def test_cli_mcp_bootstrap_consistency_summary_outputs_gate_counts() -> None:
    stdout = StringIO()

    exit_code = main(["mcp-bootstrap-consistency-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "mcp_bootstrap_consistency_v1"
    assert result["ok"] is True
    assert result["claude_server_count"] == 3
    assert result["codex_server_count"] == 3
    assert result["forbidden_token_count"] == 0
    assert result["arbitrary_shell_enabled"] is False
    assert result["live_provider_enabled"] is False
    assert result["external_submission_enabled"] is False


def test_cli_mcp_server_policy_summary_outputs_gate_counts() -> None:
    stdout = StringIO()

    exit_code = main(["mcp-server-policy-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "mcp_server_policy_v1"
    assert result["ok"] is True
    assert result["server_kind_count"] == 3
    assert result["git_read_command_count"] == 5
    assert result["techno_guard_command_count"] == 10
    assert result["forbidden_command_token_count"] == 0
    assert result["mutating_git_command_count"] == 0
    assert result["venv_enforced"] is True
    assert result["arbitrary_shell_enabled"] is False
    assert result["live_provider_enabled"] is False
    assert result["external_submission_enabled"] is False


def test_cli_sqlite_operational_log_registry_summary_outputs_gate_counts() -> None:
    stdout = StringIO()

    exit_code = main(["sqlite-operational-log-registry-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "sqlite_operational_log_registry_v1"
    assert result["ok"] is True
    assert result["registered_log_count"] == 0
    assert result["missing_cli_command_count"] == 0
    assert result["missing_schema_key_count"] == 0
    assert result["missing_sqlite_policy_count"] == 0
    assert result["sqlite_required_before_production_count"] == 0
    assert "do not ingest real observation data" in result["disclaimer"]


def test_cli_sqlite_operational_log_adapter_plan_summary_outputs_phase_counts() -> None:
    stdout = StringIO()

    exit_code = main(["sqlite-operational-log-adapter-plan-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "sqlite_operational_log_adapter_plan_v1"
    assert result["ok"] is True
    assert result["planned_log_count"] == 0
    assert result["phase_count"] == 0
    assert result["unassigned_log_count"] == 0
    assert result["sqlite_policy_mismatch_count"] == 0
    assert result["mutation_allowed"] is False
    assert "without mutating databases" in result["disclaimer"]


def test_cli_sqlite_operational_log_adapter_contract_outputs_table_counts() -> None:
    stdout = StringIO()

    exit_code = main(["sqlite-operational-log-adapter-contract-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "sqlite_operational_log_adapter_contract_v1"
    assert result["ok"] is True
    assert result["phase_contract_count"] == 0
    assert result["planned_log_count"] == 0
    assert result["missing_table_plan_count"] == 0
    assert result["missing_required_column_count"] == 0
    assert result["phase_count_mismatch_count"] == 0
    assert result["mutation_allowed"] is False
    assert "without creating tables" in result["disclaimer"]


def test_cli_sqlite_operational_log_adapter_ddl_preview_outputs_sql() -> None:
    stdout = StringIO()

    exit_code = main(["sqlite-operational-log-adapter-ddl-preview-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "sqlite_operational_log_adapter_ddl_preview_v1"
    assert result["ok"] is True
    assert result["ddl_statement_count"] == 0
    assert result["missing_clause_count"] == 0
    assert result["execution_allowed"] is False
    assert result["ddl_statements"] == []
    assert "without executing SQL" in result["disclaimer"]


def test_cli_sqlite_operational_log_adapter_row_preview_outputs_rows() -> None:
    stdout = StringIO()

    exit_code = main(["sqlite-operational-log-adapter-row-preview-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "sqlite_operational_log_adapter_row_preview_v1"
    assert result["ok"] is True
    assert result["row_count"] == 0
    assert result["phase_count"] == 0
    assert result["missing_row_field_count"] == 0
    assert result["execution_allowed"] is False
    assert result["records"] == []
    assert "without inserting rows" in result["disclaimer"]


def test_cli_sqlite_operational_log_adapter_insert_preview_outputs_inserts() -> None:
    stdout = StringIO()

    exit_code = main(
        ["sqlite-operational-log-adapter-insert-preview-summary"],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "sqlite_operational_log_adapter_insert_preview_v1"
    assert result["ok"] is True
    assert result["insert_count"] == 0
    assert result["phase_count"] == 0
    assert result["value_count_mismatch_count"] == 0
    assert result["placeholder_mismatch_count"] == 0
    assert result["non_parameterized_count"] == 0
    assert result["execution_allowed"] is False
    assert result["insert_statements"] == []
    assert "without executing SQL" in result["disclaimer"]


def test_cli_sqlite_operational_log_adapter_execution_preview_outputs_plan() -> None:
    stdout = StringIO()

    exit_code = main(
        ["sqlite-operational-log-adapter-execution-preview-summary"],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert (
        result["schema_version"]
        == "sqlite_operational_log_adapter_execution_preview_v1"
    )
    assert result["ok"] is True
    assert result["insert_count"] == 0
    assert result["phase_count"] == 0
    assert result["operation_count"] == 0
    assert result["missing_transaction_marker_count"] == 0
    assert result["missing_phase_table_count"] == 0
    assert result["execution_allowed"] is False
    assert result["mutation_allowed"] is False
    assert result["begin_statement"] == "BEGIN IMMEDIATE;"
    assert "without opening databases" in result["disclaimer"]


def test_cli_sqlite_operational_log_adapter_dry_run_manifest_outputs_manifest() -> None:
    stdout = StringIO()

    exit_code = main(
        ["sqlite-operational-log-adapter-dry-run-manifest-summary"],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert (
        result["schema_version"]
        == "sqlite_operational_log_adapter_dry_run_manifest_v1"
    )
    assert result["ok"] is True
    assert result["manifest_status"] == "preview_only"
    assert result["ddl_statement_count"] == 0
    assert result["insert_count"] == 0
    assert result["phase_count"] == 0
    assert result["execution_operation_count"] == 0
    assert result["phase_alignment_mismatch_count"] == 0
    assert result["database_open_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["mutation_allowed"] is False
    assert result["live_data_authorized"] is False
    assert result["external_submission_authorized"] is False


def test_cli_sqlite_operational_log_adapter_readiness_preflight_outputs_gate() -> None:
    stdout = StringIO()

    exit_code = main(
        ["sqlite-operational-log-adapter-readiness-preflight-summary"],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert (
        result["schema_version"]
        == "sqlite_operational_log_adapter_readiness_preflight_v1"
    )
    assert result["ok"] is True
    assert result["readiness_status"] == "preflight_only"
    assert result["registered_log_count"] == 0
    assert result["planned_count"] == 0
    assert result["schema_count"] == 103
    assert result["upstream_gate_failure_count"] == 0
    assert result["database_open_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["mutation_allowed"] is False
    assert result["live_data_authorized"] is False
    assert result["external_submission_authorized"] is False


def test_cli_sqlite_operational_log_adapter_authorization_gate_outputs_gate() -> None:
    stdout = StringIO()

    exit_code = main(
        ["sqlite-operational-log-adapter-authorization-gate-summary"],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert (
        result["schema_version"]
        == "sqlite_operational_log_adapter_authorization_gate_v1"
    )
    assert result["ok"] is True
    assert (
        result["authorization_status"]
        == "blocked_pending_explicit_operator_approval"
    )
    assert result["readiness_preflight_ok"] is True
    assert result["readiness_preflight_schema_count"] == 103
    assert result["schema_count"] == 103
    assert result["adapter_implementation_allowed"] is False
    assert result["database_open_allowed"] is False
    assert result["execution_allowed"] is False
    assert result["fixture_migration_allowed"] is False
    assert result["mutation_allowed"] is False
    assert result["live_data_authorized"] is False
    assert result["external_submission_authorized"] is False


def test_cli_production_blocker_consistency_summary_outputs_gate_counts() -> None:
    stdout = StringIO()

    exit_code = main(["production-blocker-consistency-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "production_blocker_consistency_v1"
    assert result["ok"] is True
    assert result["actual_tier1_blocker_count"] == 2
    assert result["rfi_database_admission_blocked_count"] == 4
    assert result["curated_dataset_admission_blocked_count"] == 3
    assert result["real_data_authorized_total"] == 1
    assert result["external_submission_authorized_total"] == 0


def test_cli_operations_alert_review_consistency_summary_outputs_gate_counts() -> None:
    stdout = StringIO()

    exit_code = main(["operations-alert-review-consistency-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "operations_alert_review_consistency_v1"
    assert result["ok"] is True
    assert result["actual_open_alert_count"] == 0
    assert result["actual_critical_open_alert_count"] == 0
    assert result["uncovered_open_alert_count"] == 0
    assert result["external_submission_approved_count"] == 0
    assert result["network_access_allowed_count"] == 0


def test_cli_operations_action_resolution_consistency_summary_outputs_staleness_gates() -> None:
    stdout = StringIO()

    exit_code = main(["operations-action-resolution-consistency-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "operations_action_resolution_consistency_v1"
    assert result["ok"] is True
    assert result["actual_action_count"] == 7
    assert result["actual_record_count"] == 10
    assert result["actual_stale_resolution_count"] == 3
    assert result["actual_stale_resolution_action_ids"] == [
        "ops-action-008",
        "ops-action-009",
        "ops-action-010",
    ]
    assert result["live_data_authorized_count"] == 0
    assert result["external_submission_authorized_count"] == 0


def test_cli_operations_blocker_progress_consistency_summary_outputs_chain_gates() -> None:
    stdout = StringIO()

    exit_code = main(["operations-blocker-progress-consistency-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "operations_blocker_progress_consistency_v1"
    assert result["ok"] is True
    assert result["actual_counts"]["detail_count"] == 7
    assert result["actual_counts"]["execution_followup_record_count"] == 6
    assert result["expected_residual_blocker_total"] == 26
    assert result["coverage_complete"] is True
    assert result["priority_sequence_ok"] is True
    assert result["mismatch_total"] == 0
    assert result["live_data_authorized_total"] == 0
    assert result["external_submission_authorized_total"] == 0


def test_cli_calibration_track_summary_outputs_track_counts() -> None:
    stdout = StringIO()

    exit_code = main(["calibration-track-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "synthetic_calibration_by_track_v1"
    assert result["case_count"] == 15
    assert result["track_count"] == 3
    assert result["minimum_track_case_count"] == 4
    assert result["by_track"]["radio"]["case_count"] == 4
    assert result["by_track"]["infrared"]["case_count"] == 5
    assert result["by_track"]["anomaly"]["case_count"] == 6
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
        "consensus_export",
        "consensus_labels",
        "cross_track_references",
        "curated_dataset_admission",
        "curated_dataset_intake",
        "data_quality",
        "epoch_plan",
        "feature_importance",
        "feature_normalization",
        "follow_up_request",
        "labeled_candidates",
        "labeled_candidates_citizen_science_v1",
        "labeled_candidates_synthetic_v1",
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
        "review_queue",
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
    assert result["consensus_export"].endswith("schemas/consensus_export.schema.json")
    assert result["consensus_labels"].endswith("schemas/consensus_labels.schema.json")
    assert result["review_queue"].endswith("schemas/review_queue.schema.json")
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
    assert result["candidate_count"] == 3
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert result["by_recommended_pathway"] == {"candidate_review_packet": 3}


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


def test_cli_reliability_summary_outputs_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["reliability-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["bin_count"] == 9
    assert result["total_sample_count"] == 150
    assert result["by_track"] == {"anomaly": 3, "infrared": 3, "radio": 3}
    assert result["score_bins"] == ["0.0-0.3", "0.3-0.7", "0.7-1.0"]
    assert result["mean_absolute_calibration_error"] == 0.022933


def test_cli_precision_recall_summary_outputs_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["precision-recall-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["case_count"] == 6
    assert result["by_track"] == {"anomaly": 2, "infrared": 2, "radio": 2}
    assert result["by_truth_class"] == {"candidate": 3, "false_positive": 3}
    assert result["synthetic_precision"] == 0.807692
    assert result["synthetic_recall"] == 0.792453
    assert result["synthetic_f1_score"] == 0.8


def test_cli_review_queue_summary_outputs_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["review-queue-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "human_review_queue_v1"
    assert result["item_count"] == 5
    assert result["note_count"] == 4
    assert result["by_track"] == {"anomaly": 2, "infrared": 1, "radio": 2}
    assert result["by_triage_label"]["needs_human_review"] == 1
    assert result["items_missing_notes"] == ["low-confidence-demo"]
    assert "not discovery claims" in result["disclaimer"]


def test_cli_consensus_summary_outputs_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["consensus-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "human_review_consensus_labels_v1"
    assert result["item_count"] == 5
    assert result["decision_count"] == 13
    assert result["unique_reviewer_count"] == 4
    assert result["by_track"] == {"anomaly": 2, "infrared": 1, "radio": 2}
    assert result["by_consensus_label"]["no_consensus"] == 1
    assert result["by_reviewer_decision_count"] == {"2": 2, "3": 3}
    assert "not discovery claims" in result["disclaimer"]


def test_cli_consensus_export_summary_outputs_fixture_counts() -> None:
    stdout = StringIO()

    exit_code = main(["consensus-export-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "human_review_consensus_export_v1"
    assert result["export_count"] == 5
    assert result["reviewer_decision_total"] == 13
    assert result["negative_evidence_total"] == 16
    assert result["blocking_issue_total"] == 3
    assert result["by_track"] == {"anomaly": 2, "infrared": 1, "radio": 2}
    assert result["by_consensus_label"]["likely_false_positive"] == 1
    assert "not discovery claims" in result["disclaimer"]


def test_cli_validation_dataset_summary_outputs_manifest_counts() -> None:
    stdout = StringIO()

    exit_code = main(["validation-dataset-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "validation_dataset_manifest_v1"
    assert result["dataset_count"] == 3
    assert result["total_case_count"] == 15
    assert result["false_positive_class_count"] == 15
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert result["by_readiness"] == {"synthetic_scaffold": 3}
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


def test_cli_benchmark_metadata_summary_outputs_local_context() -> None:
    stdout = StringIO()

    exit_code = main(["benchmark-metadata-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "local_synthetic_benchmark_metadata_v1"
    assert result["hardware_profile_path"] == "docs/LOCAL_SYSTEM_PROFILE.md"
    assert result["default_cpu_worker_limit"] == 12
    assert result["memory_budget_gb"] == 48
    assert result["command_count"] == 4
    assert result["by_status"] == {"planned_not_implemented": 1, "recommended": 3}
    assert "not a scientific performance claim" in result["disclaimer"]


def test_cli_benchmark_run_summary_outputs_local_run_results() -> None:
    stdout = StringIO()

    exit_code = main(["benchmark-run-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "synthetic_benchmark_run_result_v1"
    assert result["run_count"] == 3
    assert result["input_case_total"] == 171
    assert result["max_worker_count"] == 12
    assert result["by_status"] == {"passed": 2, "planned_not_implemented": 1}
    assert result["by_config_version"] == {
        "benchmark_plan_v0": 1,
        "scoring_v0": 1,
        "tooling_v0": 1,
    }
    assert "not scientific performance claims" in result["disclaimer"]


def test_cli_benchmark_run_append_outputs_updated_summary(tmp_path) -> None:
    results_path = tmp_path / "benchmark_run_results.json"
    stdout = StringIO()

    exit_code = main(
        [
            "benchmark-run-append",
            "--results-path",
            str(results_path),
            "--run-id",
            "cli-benchmark-run-001",
            "--command-name",
            "pytest coverage gate",
            "--command-kind",
            "test",
            "--status",
            "passed",
            "--worker-count",
            "1",
            "--input-case-count",
            "197",
            "--duration-seconds",
            "1.58",
            "--git-commit",
            "abc1234",
            "--config-version",
            "scoring_v0",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["appended_run"]["run_id"] == "cli-benchmark-run-001"
    assert result["appended_run"]["config_version"] == "scoring_v0"
    assert result["summary"]["run_count"] == 1
    assert results_path.exists()


def test_cli_benchmark_run_compare_outputs_repeated_run_deltas(tmp_path) -> None:
    results_path = tmp_path / "benchmark_run_results.json"
    for run_id, duration in (
        ("cli-benchmark-run-001", "2.0"),
        ("cli-benchmark-run-002", "1.5"),
    ):
        main(
            [
                "benchmark-run-append",
                "--results-path",
                str(results_path),
                "--run-id",
                run_id,
                "--command-name",
                "pytest coverage gate",
                "--command-kind",
                "test",
                "--status",
                "passed",
                "--worker-count",
                "1",
                "--input-case-count",
                "197",
                "--duration-seconds",
                duration,
                "--git-commit",
                "abc1234",
                "--config-version",
                "scoring_v0",
            ],
            stdout=StringIO(),
        )
    stdout = StringIO()

    exit_code = main(
        ["benchmark-run-compare", "--results-path", str(results_path)],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["run_count"] == 2
    assert result["repeated_command_count"] == 1
    assert result["comparisons"][0]["duration_delta_seconds"] == -0.5


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


def test_cli_user_decision_record_blocks_unconfirmed_submission(tmp_path) -> None:
    decisions_path = tmp_path / "background_user_decisions.json"
    stdout = StringIO()

    with pytest.raises(ValueError, match="explicit external submission approval"):
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
                "--submission-destination",
                "Internal test destination",
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
    assert consistency["schema_version"] == "top_level_sqlite_log_consistency_v1"
    assert consistency["ok"] is True
    assert consistency["run_count"] == 1
    assert consistency["outcome_count"] == 1
    assert consistency["network_access_allowed_count"] == 0
    assert consistency["external_submission_approved_count"] == 0

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
    assert result["calibration_summary"]["total"] == 15
    assert result["calibration_track_summary"]["track_count"] == 3
    assert result["calibration_track_summary"]["minimum_track_case_count"] == 4
    assert result["calibration_track_summary"]["by_track"]["radio"]["case_count"] == 4
    assert result["false_positive_summary"]["case_count"] == 15
    assert result["false_positive_summary"]["class_count"] == 15
    assert result["false_positive_summary"]["by_track_and_class"]["infrared"] == {
        "agb_like_colors": 1,
        "agn_blend": 1,
        "bad_photometry": 1,
        "dust_or_yso": 1,
        "extragalactic_contaminant": 1,
    }
    assert result["score_regression_summary"]["candidate_count"] == 3
    assert result["catalog_cache_validation"]["ok"] is True
    assert result["provider_normalization_summary"]["case_count"] == 5
    assert result["provider_normalization_summary"]["by_provider"] == {
        "breakthrough_listen": 1,
        "gaia": 1,
        "irsa": 1,
        "simbad": 1,
        "vizier": 1,
    }
    assert result["injection_recovery_summary"]["case_count"] == 6
    assert result["injection_recovery_summary"]["by_track"] == {
        "anomaly": 2,
        "infrared": 2,
        "radio": 2,
    }
    assert result["reliability_summary"]["bin_count"] == 9
    assert result["reliability_summary"]["by_track"] == {
        "anomaly": 3,
        "infrared": 3,
        "radio": 3,
    }
    assert result["precision_recall_summary"]["case_count"] == 6
    assert result["precision_recall_summary"]["by_truth_class"] == {
        "candidate": 3,
        "false_positive": 3,
    }
    assert result["review_queue_summary"]["item_count"] == 5
    assert result["review_queue_summary"]["note_count"] == 4
    assert result["review_queue_summary"]["by_triage_label"] == {
        "follow_up_target": 1,
        "insufficient_evidence": 1,
        "known_object_annotation": 1,
        "likely_false_positive": 1,
        "needs_human_review": 1,
    }
    assert result["consensus_summary"]["item_count"] == 5
    assert result["consensus_summary"]["decision_count"] == 13
    assert result["consensus_summary"]["by_consensus_label"] == {
        "follow_up_target": 1,
        "insufficient_evidence": 1,
        "known_object_annotation": 1,
        "likely_false_positive": 1,
        "no_consensus": 1,
    }
    assert result["consensus_export_summary"]["export_count"] == 5
    assert result["consensus_export_summary"]["blocking_issue_total"] == 3
    assert result["validation_dataset_summary"]["dataset_count"] == 3
    assert result["validation_dataset_summary"]["total_case_count"] == 15
    assert result["validation_dataset_summary"]["by_readiness"] == {
        "synthetic_scaffold": 3
    }
    assert result["validation_promotion_summary"]["rule_count"] == 3
    assert result["validation_promotion_summary"]["blocking_condition_count"] == 9
    assert result["validation_readiness_summary"]["record_count"] == 3
    assert result["validation_readiness_summary"]["ready_count"] == 1
    assert result["validation_readiness_summary"]["blocked_count"] == 1
    assert result["benchmark_metadata_summary"]["command_count"] == 4
    assert result["benchmark_metadata_summary"]["default_cpu_worker_limit"] == 12
    assert result["benchmark_metadata_summary"]["memory_budget_gb"] == 48
    assert result["benchmark_run_summary"]["run_count"] == 3
    assert result["benchmark_run_summary"]["input_case_total"] == 171
    assert result["benchmark_run_summary"]["max_worker_count"] == 12
    assert result["target_priority_summary"]["target_count"] == 4
    assert result["target_priority_summary"]["selected_target_id"] == (
        "target-radio-clean-drift"
    )
    assert result["background_ledger_summary"]["entry_count"] == 4
    assert result["background_ledger_summary"]["candidate_count"] == 2
    assert result["background_review_workflow_summary"]["entry_count"] == 4
    assert result["background_review_workflow_summary"][
        "reviewed_workflow_status_count"
    ] == 4
    assert result["background_review_workflow_summary"][
        "negative_result_logged_count"
    ] == 2
    assert result["background_review_workflow_summary"]["local_only_entry_count"] == 1
    assert result["background_reviewed_log_summary"]["entry_count"] == 2
    assert result["background_reviewed_log_summary"][
        "network_access_allowed_count"
    ] == 0
    assert result["background_needs_follow_up_summary"]["entry_count"] == 2
    assert result["background_needs_follow_up_summary"][
        "submission_requires_user_approval_count"
    ] == 2
    assert result["background_needs_follow_up_summary"][
        "network_access_allowed_count"
    ] == 0
    assert result["background_follow_up_test_summary"]["result_count"] == 12
    assert result["background_follow_up_test_summary"][
        "complete_follow_up_test_set_count"
    ] == 2
    assert result["background_follow_up_test_summary"][
        "network_access_allowed_count"
    ] == 0
    assert result["background_report_readiness_summary"]["record_count"] == 2
    assert result["background_report_readiness_summary"][
        "ready_to_draft_report_count"
    ] == 1
    assert result["background_report_readiness_summary"][
        "external_submission_allowed_count"
    ] == 0
    assert result["background_draft_report_validation"]["ok"] is True
    assert result["background_draft_follow_up_report_summary"][
        "draft_report_count"
    ] == 2
    assert result["background_draft_follow_up_report_summary"][
        "external_submission_allowed_count"
    ] == 0
    assert result["background_user_decision_summary"]["decision_count"] == 3
    assert result["background_user_decision_summary"][
        "external_submission_approved_count"
    ] == 0
    assert result["candidate_extraction_handoff_summary"]["record_count"] == 4
    assert result["candidate_extraction_handoff_summary"]["ready_count"] == 1
    assert result["candidate_extraction_handoff_summary"][
        "network_access_allowed_count"
    ] == 0
    assert result["top_level_sqlite_log_validation"]["ok"] is True
    assert result["top_level_sqlite_log_consistency_summary"]["ok"] is True
    assert result["top_level_sqlite_log_consistency_summary"]["issue_count"] == 0
    assert result["mcp_bootstrap_consistency_summary"]["ok"] is True
    assert result["mcp_bootstrap_consistency_summary"]["issue_count"] == 0
    assert result["mcp_bootstrap_consistency_summary"]["forbidden_token_count"] == 0
    assert result["mcp_server_policy_summary"]["ok"] is True
    assert result["mcp_server_policy_summary"]["issue_count"] == 0
    assert result["mcp_server_policy_summary"]["forbidden_command_token_count"] == 0
    assert result["mcp_server_policy_summary"]["mutating_git_command_count"] == 0
    assert result["production_blocker_consistency_summary"]["ok"] is True
    assert result["production_blocker_consistency_summary"]["issue_count"] == 0
    assert result["production_blocker_consistency_summary"][
        "actual_tier1_blocker_count"
    ] == 2
    assert result["top_level_sqlite_log_integrity_summary"]["ok"] is True
    assert result["top_level_sqlite_log_migration_summary"][
        "migration_required"
    ] is False
    assert result["top_level_sqlite_log_commit_guard"]["ok"] is True
    assert result["top_level_sqlite_log_export"]["summary"]["ok"] is True
    assert result["top_level_sqlite_log_backup"]["ok"] is True
    assert result["top_level_sqlite_log_retention_summary"]["ok"] is True
    assert result["top_level_sqlite_log_retention_summary"]["backup_count"] >= 1
    assert result["top_level_sqlite_log_pragmas"]["ok"] is True
    assert result["top_level_sqlite_log_pragmas"]["integrity_check"] == "ok"
    assert result["top_level_sqlite_log_summary"]["run_count"] >= 1
    assert result["top_level_sqlite_log_summary"]["outcome_count"] == (
        result["top_level_sqlite_log_summary"]["run_count"]
    )
    assert result["top_level_sqlite_log_summary"][
        "network_access_allowed_count"
    ] == 0
    assert result["top_level_sqlite_log_summary"][
        "external_submission_approved_count"
    ] == 0
    assert result["sqlite_operational_log_registry_summary"]["ok"] is True
    assert result["sqlite_operational_log_registry_summary"]["registered_log_count"] == 0
    assert (
        result["sqlite_operational_log_registry_summary"][
            "missing_sqlite_policy_count"
        ]
        == 0
    )
    assert result["sqlite_operational_log_adapter_plan_summary"]["ok"] is True
    assert (
        result["sqlite_operational_log_adapter_plan_summary"]["planned_log_count"]
        == 0
    )
    assert (
        result["sqlite_operational_log_adapter_plan_summary"][
            "unassigned_log_count"
        ]
        == 0
    )
    assert result["sqlite_operational_log_adapter_contract_summary"]["ok"] is True
    assert (
        result["sqlite_operational_log_adapter_contract_summary"][
            "phase_contract_count"
        ]
        == 0
    )
    assert (
        result["sqlite_operational_log_adapter_contract_summary"][
            "missing_required_column_count"
        ]
        == 0
    )
    assert result["sqlite_operational_log_adapter_ddl_preview_summary"]["ok"] is True
    assert (
        result["sqlite_operational_log_adapter_ddl_preview_summary"][
            "ddl_statement_count"
        ]
        == 0
    )
    assert (
        result["sqlite_operational_log_adapter_ddl_preview_summary"][
            "execution_allowed"
        ]
        is False
    )
    assert result["sqlite_operational_log_adapter_row_preview_summary"]["ok"] is True
    assert (
        result["sqlite_operational_log_adapter_row_preview_summary"]["row_count"]
        == 0
    )
    assert (
        result["sqlite_operational_log_adapter_row_preview_summary"][
            "execution_allowed"
        ]
        is False
    )
    assert result["sqlite_operational_log_adapter_insert_preview_summary"]["ok"] is True
    assert (
        result["sqlite_operational_log_adapter_insert_preview_summary"][
            "insert_count"
        ]
        == 0
    )
    assert (
        result["sqlite_operational_log_adapter_insert_preview_summary"][
            "execution_allowed"
        ]
        is False
    )
    assert (
        result["sqlite_operational_log_adapter_execution_preview_summary"]["ok"]
        is True
    )
    assert (
        result["sqlite_operational_log_adapter_execution_preview_summary"][
            "operation_count"
        ]
        == 0
    )
    assert (
        result["sqlite_operational_log_adapter_execution_preview_summary"][
            "mutation_allowed"
        ]
        is False
    )
    assert result["sqlite_operational_log_adapter_dry_run_manifest_summary"]["ok"] is True
    assert (
        result["sqlite_operational_log_adapter_dry_run_manifest_summary"][
            "manifest_status"
        ]
        == "preview_only"
    )
    assert (
        result["sqlite_operational_log_adapter_dry_run_manifest_summary"][
            "phase_alignment_mismatch_count"
        ]
        == 0
    )
    assert (
        result["sqlite_operational_log_adapter_readiness_preflight_summary"]["ok"]
        is True
    )
    assert (
        result["sqlite_operational_log_adapter_readiness_preflight_summary"][
            "readiness_status"
        ]
        == "preflight_only"
    )
    assert (
        result["sqlite_operational_log_adapter_readiness_preflight_summary"][
            "upstream_gate_failure_count"
        ]
        == 0
    )
    assert (
        result["sqlite_operational_log_adapter_authorization_gate_summary"]["ok"]
        is True
    )
    assert (
        result["sqlite_operational_log_adapter_authorization_gate_summary"][
            "authorization_status"
        ]
        == "blocked_pending_explicit_operator_approval"
    )
    assert result["catalog_cache_validation"]["forbidden_roots"] == [
        "data",
        "cache",
        "artifacts",
    ]
    assert all(result["schema_paths_exist"].values())


def test_cli_validation_summary_outputs_concise_health_dashboard() -> None:
    stdout = StringIO()

    exit_code = main(["validation-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["candidate_count"] == 3
    assert result["report_validation_ok"] is True
    assert result["schema_count"] == 103
    assert result["schemas_ok"] is True
    assert result["project_status_consistency_ok"] is True
    assert result["project_status_latest_milestone"] == 73
    assert result["project_status_latest_decision"] == 124
    assert result["project_status_schema_count"] == 103
    assert result["mcp_bootstrap_consistency_ok"] is True
    assert result["mcp_bootstrap_consistency_issue_count"] == 0
    assert result["mcp_bootstrap_claude_server_count"] == 3
    assert result["mcp_bootstrap_codex_server_count"] == 3
    assert result["mcp_bootstrap_forbidden_token_count"] == 0
    assert result["mcp_bootstrap_arbitrary_shell_enabled"] is False
    assert result["mcp_bootstrap_live_provider_enabled"] is False
    assert result["mcp_bootstrap_external_submission_enabled"] is False
    assert result["mcp_server_policy_ok"] is True
    assert result["mcp_server_policy_issue_count"] == 0
    assert result["mcp_server_policy_git_read_command_count"] == 5
    assert result["mcp_server_policy_techno_guard_command_count"] == 10
    assert result["mcp_server_policy_forbidden_command_token_count"] == 0
    assert result["mcp_server_policy_mutating_git_command_count"] == 0
    assert result["mcp_server_policy_venv_enforced"] is True
    assert result["mcp_server_policy_arbitrary_shell_enabled"] is False
    assert result["mcp_server_policy_live_provider_enabled"] is False
    assert result["mcp_server_policy_external_submission_enabled"] is False
    assert result["production_blocker_consistency_ok"] is True
    assert result["production_blocker_consistency_issue_count"] == 0
    assert result["production_blocker_tier1_blocker_count"] == 2
    assert result["production_blocker_real_data_authorized_total"] == 1
    assert result["production_blocker_external_submission_authorized_total"] == 0
    assert result["sqlite_operational_log_registry_ok"] is True
    assert result["sqlite_operational_log_registry_issue_count"] == 0
    assert result["sqlite_operational_log_registered_count"] == 0
    assert result["sqlite_operational_log_missing_cli_command_count"] == 0
    assert result["sqlite_operational_log_missing_sqlite_policy_count"] == 0
    assert (
        result["sqlite_operational_log_sqlite_required_before_production_count"]
        == 0
    )
    assert result["sqlite_operational_log_adapter_plan_ok"] is True
    assert result["sqlite_operational_log_adapter_plan_issue_count"] == 0
    assert result["sqlite_operational_log_adapter_planned_count"] == 0
    assert result["sqlite_operational_log_adapter_phase_count"] == 0
    assert result["sqlite_operational_log_adapter_unassigned_count"] == 0
    assert result["sqlite_operational_log_adapter_policy_mismatch_count"] == 0
    assert result["sqlite_operational_log_adapter_mutation_allowed"] is False
    assert result["sqlite_operational_log_adapter_contract_ok"] is True
    assert result["sqlite_operational_log_adapter_contract_issue_count"] == 0
    assert result["sqlite_operational_log_adapter_contract_phase_count"] == 0
    assert result["sqlite_operational_log_adapter_contract_missing_table_count"] == 0
    assert result["sqlite_operational_log_adapter_contract_missing_column_count"] == 0
    assert result["sqlite_operational_log_adapter_contract_phase_mismatch_count"] == 0
    assert result["sqlite_operational_log_adapter_contract_mutation_allowed"] is False
    assert result["sqlite_operational_log_adapter_ddl_preview_ok"] is True
    assert result["sqlite_operational_log_adapter_ddl_preview_issue_count"] == 0
    assert result["sqlite_operational_log_adapter_ddl_statement_count"] == 0
    assert result["sqlite_operational_log_adapter_ddl_missing_clause_count"] == 0
    assert result["sqlite_operational_log_adapter_ddl_execution_allowed"] is False
    assert result["sqlite_operational_log_adapter_row_preview_ok"] is True
    assert result["sqlite_operational_log_adapter_row_preview_issue_count"] == 0
    assert result["sqlite_operational_log_adapter_row_count"] == 0
    assert result["sqlite_operational_log_adapter_row_phase_count"] == 0
    assert result["sqlite_operational_log_adapter_row_missing_field_count"] == 0
    assert result["sqlite_operational_log_adapter_row_execution_allowed"] is False
    assert result["sqlite_operational_log_adapter_insert_preview_ok"] is True
    assert result["sqlite_operational_log_adapter_insert_preview_issue_count"] == 0
    assert result["sqlite_operational_log_adapter_insert_count"] == 0
    assert result["sqlite_operational_log_adapter_insert_phase_count"] == 0
    assert result["sqlite_operational_log_adapter_insert_value_mismatch_count"] == 0
    assert result["sqlite_operational_log_adapter_insert_execution_allowed"] is False
    assert result["sqlite_operational_log_adapter_execution_preview_ok"] is True
    assert result["sqlite_operational_log_adapter_execution_preview_issue_count"] == 0
    assert result["sqlite_operational_log_adapter_execution_operation_count"] == 0
    assert result["sqlite_operational_log_adapter_execution_phase_count"] == 0
    assert result["sqlite_operational_log_adapter_execution_allowed"] is False
    assert result["sqlite_operational_log_adapter_execution_mutation_allowed"] is False
    assert result["sqlite_operational_log_adapter_dry_run_manifest_ok"] is True
    assert result["sqlite_operational_log_adapter_dry_run_manifest_issue_count"] == 0
    assert (
        result["sqlite_operational_log_adapter_dry_run_manifest_status"]
        == "preview_only"
    )
    assert result["sqlite_operational_log_adapter_dry_run_phase_count"] == 0
    assert result["sqlite_operational_log_adapter_dry_run_phase_mismatch_count"] == 0
    assert (
        result["sqlite_operational_log_adapter_dry_run_database_open_allowed"]
        is False
    )
    assert result["sqlite_operational_log_adapter_dry_run_execution_allowed"] is False
    assert result["sqlite_operational_log_adapter_dry_run_mutation_allowed"] is False
    assert (
        result["sqlite_operational_log_adapter_dry_run_live_data_authorized"]
        is False
    )
    assert (
        result[
            "sqlite_operational_log_adapter_dry_run_external_submission_authorized"
        ]
        is False
    )
    assert result["sqlite_operational_log_adapter_readiness_preflight_ok"] is True
    assert (
        result["sqlite_operational_log_adapter_readiness_preflight_issue_count"]
        == 0
    )
    assert (
        result["sqlite_operational_log_adapter_readiness_preflight_status"]
        == "preflight_only"
    )
    assert (
        result[
            "sqlite_operational_log_adapter_readiness_preflight_failed_gate_count"
        ]
        == 0
    )
    assert (
        result["sqlite_operational_log_adapter_readiness_preflight_schema_count"]
        == 103
    )
    assert (
        result[
            "sqlite_operational_log_adapter_readiness_preflight_database_open_allowed"
        ]
        is False
    )
    assert (
        result["sqlite_operational_log_adapter_readiness_preflight_execution_allowed"]
        is False
    )
    assert (
        result["sqlite_operational_log_adapter_readiness_preflight_mutation_allowed"]
        is False
    )
    assert (
        result[
            "sqlite_operational_log_adapter_readiness_preflight_live_data_authorized"
        ]
        is False
    )
    assert (
        result[
            "sqlite_operational_log_adapter_readiness_preflight_external_submission_authorized"
        ]
        is False
    )
    assert result["sqlite_operational_log_adapter_authorization_gate_ok"] is True
    assert result["sqlite_operational_log_adapter_authorization_gate_issue_count"] == 0
    assert (
        result["sqlite_operational_log_adapter_authorization_status"]
        == "blocked_pending_explicit_operator_approval"
    )
    assert (
        result["sqlite_operational_log_adapter_authorization_gate_schema_count"]
        == 103
    )
    assert (
        result[
            "sqlite_operational_log_adapter_authorization_gate_adapter_implementation_allowed"
        ]
        is False
    )
    assert (
        result[
            "sqlite_operational_log_adapter_authorization_gate_database_open_allowed"
        ]
        is False
    )
    assert (
        result["sqlite_operational_log_adapter_authorization_gate_execution_allowed"]
        is False
    )
    assert (
        result[
            "sqlite_operational_log_adapter_authorization_gate_fixture_migration_allowed"
        ]
        is False
    )
    assert (
        result["sqlite_operational_log_adapter_authorization_gate_mutation_allowed"]
        is False
    )
    assert (
        result[
            "sqlite_operational_log_adapter_authorization_gate_live_data_authorized"
        ]
        is False
    )
    assert (
        result[
            "sqlite_operational_log_adapter_authorization_gate_external_submission_authorized"
        ]
        is False
    )
    assert result["operations_alert_review_consistency_ok"] is True
    assert result["operations_alert_review_open_alert_count"] == 0
    assert result["operations_alert_review_critical_open_alert_count"] == 0
    assert result["operations_alert_review_uncovered_open_alert_count"] == 0
    assert result["operations_action_resolution_consistency_ok"] is True
    assert result["operations_action_resolution_consistency_stale_count"] == 3
    assert result["operations_action_resolution_consistency_stale_action_ids"] == [
        "ops-action-008",
        "ops-action-009",
        "ops-action-010",
    ]
    assert result["operations_action_resolution_consistency_missing_action_count"] == 0
    assert result["operations_blocker_progress_consistency_ok"] is True
    assert result["operations_blocker_progress_consistency_issue_count"] == 0
    assert (
        result["operations_blocker_progress_consistency_residual_blocker_total"]
        == 26
    )
    assert result["operations_blocker_progress_consistency_mismatch_total"] == 0
    assert (
        result["operations_blocker_progress_consistency_live_data_authorized_total"]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_consistency_external_submission_authorized_total"
        ]
        == 0
    )
    assert result["calibration_fixture_count"] == 15
    assert result["calibration_track_count"] == 3
    assert result["calibration_minimum_track_case_count"] == 4
    assert result["false_positive_case_count"] == 15
    assert result["false_positive_class_count"] == 15
    assert result["score_regression_candidate_count"] == 3
    assert result["catalog_cache_ok"] is True
    assert result["provider_normalization_case_count"] == 5
    assert result["injection_recovery_case_count"] == 6
    assert result["synthetic_recovery_rate"] == 0.75
    assert result["synthetic_false_alarm_fraction"] == 0.333333
    assert result["reliability_bin_count"] == 9
    assert result["mean_absolute_calibration_error"] == 0.022933
    assert result["precision_recall_case_count"] == 6
    assert result["synthetic_precision"] == 0.807692
    assert result["synthetic_recall"] == 0.792453
    assert result["review_queue_item_count"] == 5
    assert result["review_queue_note_count"] == 4
    assert result["consensus_item_count"] == 5
    assert result["consensus_decision_count"] == 13
    assert result["consensus_unique_reviewer_count"] == 4
    assert result["consensus_export_count"] == 5
    assert result["consensus_export_blocking_issue_total"] == 3
    assert result["validation_dataset_count"] == 3
    assert result["validation_dataset_case_count"] == 15
    assert result["validation_promotion_rule_count"] == 3
    assert result["validation_promotion_blocking_condition_count"] == 9
    assert result["validation_readiness_record_count"] == 3
    assert result["validation_readiness_ready_count"] == 1
    assert result["validation_readiness_blocked_count"] == 1
    assert result["validation_readiness_not_yet_admissible_count"] == 1
    assert result["validation_readiness_blocking_issue_count"] == 4
    assert result["benchmark_command_count"] == 4
    assert result["benchmark_default_cpu_worker_limit"] == 12
    assert result["benchmark_memory_budget_gb"] == 48
    assert result["benchmark_run_count"] == 3
    assert result["benchmark_run_input_case_total"] == 171
    assert result["benchmark_run_max_worker_count"] == 12
    assert result["target_priority_count"] == 4
    assert result["selected_background_target_id"] == "target-radio-clean-drift"
    assert result["background_ledger_entry_count"] == 4
    assert result["background_ledger_candidate_count"] == 2
    assert result["background_review_workflow_status_count"] == 4
    assert result["background_review_negative_result_logged_count"] == 2
    assert result["background_review_local_only_entry_count"] == 1
    assert result["background_reviewed_log_entry_count"] == 2
    assert result["background_reviewed_log_network_access_allowed_count"] == 0
    assert result["background_needs_follow_up_entry_count"] == 2
    assert result["background_needs_follow_up_required_test_count"] == 12
    assert result["background_needs_follow_up_user_approval_count"] == 2
    assert result["background_needs_follow_up_network_access_allowed_count"] == 0
    assert result["background_follow_up_test_result_count"] == 12
    assert result["background_follow_up_test_complete_set_count"] == 2
    assert result["background_follow_up_test_network_access_allowed_count"] == 0
    assert result["background_report_readiness_record_count"] == 2
    assert result["background_report_readiness_ready_to_draft_count"] == 1
    assert result["background_report_readiness_user_approval_count"] == 2
    assert result["background_report_readiness_external_submission_allowed_count"] == 0
    assert result["background_report_readiness_top_three_recommendation_count"] == 6
    assert result["background_draft_report_count"] == 2
    assert result["background_draft_report_ready_count"] == 1
    assert result["background_draft_report_external_submission_allowed_count"] == 0
    assert result["background_draft_report_validation_ok"] is True
    assert result["background_user_decision_count"] == 3
    assert result["background_user_decision_external_submission_approved_count"] == 0
    assert result["background_user_decision_request_more_tests_count"] == 2
    assert result["background_user_decision_close_as_reviewed_count"] == 1
    assert result["candidate_extraction_handoff_record_count"] == 4
    assert result["candidate_extraction_handoff_ready_count"] == 1
    assert result["candidate_extraction_handoff_blocked_count"] == 1
    assert result[
        "candidate_extraction_handoff_negative_result_required_count"
    ] == 2
    assert result["top_level_sqlite_log_validation_ok"] is True
    assert result["top_level_sqlite_log_consistency_ok"] is True
    assert result["top_level_sqlite_log_consistency_issue_count"] == 0
    assert result["top_level_sqlite_log_integrity_ok"] is True
    assert result["top_level_sqlite_log_migration_required"] is False
    assert result["top_level_sqlite_log_commit_guard_ok"] is True
    assert result["top_level_sqlite_log_backup_ok"] is True
    assert result["top_level_sqlite_log_backup_count"] >= 1
    assert result["top_level_sqlite_log_retention_ok"] is True
    assert result["top_level_sqlite_log_pragmas_ok"] is True
    assert result["top_level_sqlite_log_integrity_check"] == "ok"
    assert result["top_level_sqlite_log_run_count"] >= 1
    assert result["top_level_sqlite_log_outcome_count"] == (
        result["top_level_sqlite_log_run_count"]
    )
    assert result["top_level_sqlite_log_network_access_allowed_count"] == 0
    assert result["top_level_sqlite_log_external_submission_approved_count"] == 0
    assert result["operations_readiness_sqlite_log_present"] is True
    assert result["operations_readiness_sqlite_integrity_ok"] is True
    assert result["operations_readiness_sqlite_weekly_digest_ok"] is True
    assert result["operations_action_resolution_record_count"] == 10
    assert result["operations_action_resolution_expected_action_count"] == 7
    assert result["operations_action_resolution_covered_action_count"] == 7
    assert result["operations_action_resolution_missing_action_count"] == 0
    assert result["operations_action_resolution_stale_resolution_count"] == 3
    assert result["operations_action_resolution_coverage_fraction"] == 1.0
    assert result["operations_action_resolution_coverage_complete"] is True
    assert result["operations_action_resolution_missing_action_ids"] == []
    assert result["operations_action_resolution_stale_resolution_action_ids"] == [
        "ops-action-008",
        "ops-action-009",
        "ops-action-010",
    ]
    assert result["operations_action_resolution_live_data_authorized_count"] == 0
    assert (
        result["operations_action_resolution_external_submission_authorized_count"]
        == 0
    )
    assert result["operations_blocker_detail_count"] == 7
    assert result["operations_blocker_detail_total_evidence_record_count"] >= 7
    assert (
        result["operations_blocker_detail_all_external_authorization_disabled"]
        is True
    )
    assert result["operations_blocker_detail_sqlite_context_is_resolved"] is True
    assert result["operations_blocker_review_record_count"] == 7
    assert result["operations_blocker_review_reviewed_evidence_record_count"] == 26
    assert result["operations_blocker_review_unreviewed_evidence_record_count"] == 0
    assert result["operations_blocker_review_residual_blocker_total"] == 26
    assert result["operations_blocker_review_live_data_authorized_count"] == 0
    assert (
        result["operations_blocker_review_external_submission_authorized_count"] == 0
    )
    assert (
        result["operations_blocker_review_all_external_authorization_disabled"]
        is True
    )
    assert result["operations_blocker_review_coverage_complete"] is True
    assert result["operations_blocker_review_all_detail_evidence_reviewed"] is True
    assert result["operations_blocker_followup_action_count"] == 7
    assert result["operations_blocker_followup_action_required_count"] == 6
    assert result["operations_blocker_followup_real_data_hold_count"] == 2
    assert result["operations_blocker_followup_verification_ready_count"] == 1
    assert result["operations_blocker_followup_residual_blocker_total"] == 26
    assert result["operations_blocker_followup_live_data_authorized_count"] == 0
    assert (
        result["operations_blocker_followup_external_submission_authorized_count"]
        == 0
    )
    assert (
        result["operations_blocker_followup_all_external_authorization_disabled"]
        is True
    )
    assert result["operations_blocker_followup_coverage_complete"] is True
    assert result["operations_blocker_followup_all_detail_evidence_reviewed"] is True
    assert result["operations_blocker_followup_progress_record_count"] == 7
    assert result["operations_blocker_followup_progress_unresolved_count"] == 6
    assert result["operations_blocker_followup_progress_verified_local_count"] == 1
    assert result["operations_blocker_followup_progress_residual_blocker_total"] == 26
    assert result["operations_blocker_followup_progress_live_data_authorized_count"] == 0
    assert (
        result[
            "operations_blocker_followup_progress_external_submission_authorized_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_followup_progress_all_external_authorization_disabled"
        ]
        is True
    )
    assert result["operations_blocker_followup_progress_coverage_complete"] is True
    assert (
        result["operations_blocker_followup_progress_recommendation_mismatch_count"]
        == 0
    )
    assert result["operations_blocker_progress_review_record_count"] == 6
    assert result["operations_blocker_progress_review_needs_operator_action_count"] == 0
    assert (
        result["operations_blocker_progress_review_ready_for_next_local_note_count"]
        == 4
    )
    assert result["operations_blocker_progress_review_blocked_for_real_data_count"] == 2
    assert result["operations_blocker_progress_review_residual_blocker_total"] == 26
    assert result["operations_blocker_progress_review_live_data_authorized_count"] == 0
    assert (
        result[
            "operations_blocker_progress_review_external_submission_authorized_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_review_all_external_authorization_disabled"
        ]
        is True
    )
    assert result["operations_blocker_progress_review_coverage_complete"] is True
    assert result["operations_blocker_progress_review_status_mismatch_count"] == 0
    assert result["operations_blocker_progress_next_actions_record_count"] == 6
    assert (
        result[
            "operations_blocker_progress_next_actions_operator_action_required_count"
        ]
        == 0
    )
    assert (
        result["operations_blocker_progress_next_actions_local_note_ready_count"]
        == 4
    )
    assert (
        result[
            "operations_blocker_progress_next_actions_blocked_pending_real_data_count"
        ]
        == 2
    )
    assert (
        result["operations_blocker_progress_next_actions_residual_blocker_total"]
        == 26
    )
    assert (
        result["operations_blocker_progress_next_actions_live_data_authorized_count"]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_next_actions_external_submission_authorized_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_next_actions_all_external_authorization_disabled"
        ]
        is True
    )
    assert result["operations_blocker_progress_next_actions_coverage_complete"] is True
    assert result["operations_blocker_progress_next_actions_status_mismatch_count"] == 0
    assert result["operations_blocker_progress_next_actions_priority_sequence_ok"] is True
    assert result["operations_blocker_progress_execution_record_count"] == 6
    assert (
        result["operations_blocker_progress_execution_awaiting_operator_count"]
        == 0
    )
    assert (
        result["operations_blocker_progress_execution_local_note_recorded_count"]
        == 4
    )
    assert (
        result[
            "operations_blocker_progress_execution_blocked_pending_real_data_count"
        ]
        == 2
    )
    assert (
        result["operations_blocker_progress_execution_residual_blocker_total"]
        == 26
    )
    assert (
        result["operations_blocker_progress_execution_live_data_authorized_count"]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_external_submission_authorized_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_all_external_authorization_disabled"
        ]
        is True
    )
    assert result["operations_blocker_progress_execution_coverage_complete"] is True
    assert result["operations_blocker_progress_execution_status_mismatch_count"] == 0
    assert result["operations_blocker_progress_execution_residual_mismatch_count"] == 0
    assert result["operations_blocker_progress_execution_priority_mismatch_count"] == 0
    assert result["operations_blocker_progress_execution_priority_sequence_ok"] is True
    assert result["operations_blocker_progress_execution_review_record_count"] == 6
    assert (
        result[
            "operations_blocker_progress_execution_review_awaiting_operator_reviewed_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_review_execution_note_reviewed_count"
        ]
        == 4
    )
    assert (
        result[
            "operations_blocker_progress_execution_review_blocked_pending_real_data_reviewed_count"
        ]
        == 2
    )
    assert (
        result[
            "operations_blocker_progress_execution_review_residual_blocker_total"
        ]
        == 26
    )
    assert (
        result[
            "operations_blocker_progress_execution_review_live_data_authorized_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_review_external_submission_authorized_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_review_all_external_authorization_disabled"
        ]
        is True
    )
    assert (
        result["operations_blocker_progress_execution_review_coverage_complete"]
        is True
    )
    assert (
        result[
            "operations_blocker_progress_execution_review_status_mismatch_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_review_residual_mismatch_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_review_priority_mismatch_count"
        ]
        == 0
    )
    assert (
        result["operations_blocker_progress_execution_review_priority_sequence_ok"]
        is True
    )
    assert result["operations_blocker_progress_execution_followup_record_count"] == 6
    assert (
        result[
            "operations_blocker_progress_execution_followup_operator_followup_required_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_followup_local_note_followup_ready_count"
        ]
        == 4
    )
    assert (
        result[
            "operations_blocker_progress_execution_followup_blocked_pending_real_data_count"
        ]
        == 2
    )
    assert (
        result[
            "operations_blocker_progress_execution_followup_residual_blocker_total"
        ]
        == 26
    )
    assert (
        result[
            "operations_blocker_progress_execution_followup_live_data_authorized_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_followup_external_submission_authorized_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_followup_all_external_authorization_disabled"
        ]
        is True
    )
    assert (
        result["operations_blocker_progress_execution_followup_coverage_complete"]
        is True
    )
    assert (
        result[
            "operations_blocker_progress_execution_followup_status_mismatch_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_followup_residual_mismatch_count"
        ]
        == 0
    )
    assert (
        result[
            "operations_blocker_progress_execution_followup_priority_mismatch_count"
        ]
        == 0
    )
    assert (
        result["operations_blocker_progress_execution_followup_priority_sequence_ok"]
        is True
    )
    assert result["session_log_count"] == 0
    assert result["session_log_completed_count"] == 0
    assert result["priority_queue_depth"] == 5
    assert result["pipeline_capacity_status"] in {"nominal", "strained", "overloaded"}
    assert result["feature_vector_count"] == 5
    assert result["ml_registry_entry_count"] == 3
    assert result["ml_above_baseline_count"] == 2
    assert result["ml_pipeline_status"] in {
        "no_models", "all_above_baseline", "some_below_baseline"
    }
    assert result["normalization_bounds_count"] == 3
    assert result["feature_importance_entry_count"] == 6
    assert result["ml_training_case_count"] >= 0
    assert result["ml_recommended_train_count"] >= 0
    assert result["model_architecture_count"] == 5
    assert result["model_evaluation_count"] == 4
    assert result["model_evaluation_above_baseline_count"] == 3
    assert result["model_performance_snapshot_count"] == 5
    assert result["model_serving_record_count"] == 4
    assert result["model_serving_active_count"] == 1
    assert result["scoring_audit_entry_count"] == 0
    assert result["curated_intake_record_count"] == 4
    assert result["curated_intake_approved_count"] == 1
    assert result["candidate_rescore_event_count"] == 4
    assert result["candidate_rescore_pathway_change_count"] == 1
    assert result["operator_handoff_template_count"] == 4
    assert result["operator_handoff_approved_count"] == 1
    assert result["pipeline_config_count"] == 4
    assert result["pipeline_active_count"] == 1
    assert result["submission_readiness_record_count"] == 4
    assert result["submission_readiness_ready_count"] == 1
    assert result["comparison_record_count"] == 4
    assert result["telemetry_entry_count"] == 6
    assert result["provenance_audit_entry_count"] == 4
    assert result["provenance_audit_consistent_count"] == 1
    assert result["candidate_alert_entry_count"] == 0
    assert result["candidate_alert_open_count"] == 0
    assert result["pipeline_replay_entry_count"] == 0
    assert result["pipeline_replay_matched_count"] == 0
    assert result["scoring_threshold_pass_count"] == 3
    assert result["scoring_threshold_fail_count"] == 0
    assert result["alert_resolution_entry_count"] == 0
    assert result["alert_resolution_open_count"] == 0
    assert result["config_history_entry_count"] == 4
    assert result["operator_escalation_entry_count"] == 0
    assert result["operator_escalation_open_count"] == 0
    assert result["candidate_deduplication_entry_count"] == 0
    assert result["candidate_deduplication_pending_count"] == 0
    assert result["intake_queue_entry_count"] == 0
    assert result["intake_queue_blocked_count"] == 0
    assert result["workflow_state_entry_count"] == 0
    assert result["data_gap_entry_count"] == 0
    assert result["data_gap_unresolved_count"] == 0
    assert result["candidate_match_entry_count"] == 0
    assert result["candidate_match_matched_count"] == 0
    assert result["pipeline_error_entry_count"] == 0
    assert result["pipeline_error_unresolved_count"] == 0
    assert result["observation_request_entry_count"] == 0
    assert result["observation_request_pending_count"] == 0
    assert result["candidate_export_entry_count"] == 0
    assert result["candidate_export_delivered_count"] == 0
    assert result["quality_gate_entry_count"] == 0
    assert result["quality_gate_pass_count"] == 0
    assert result["instrument_log_entry_count"] == 0
    assert result["archival_query_entry_count"] == 0
    assert result["candidate_linkage_entry_count"] == 0
    assert result["candidate_linkage_confirmed_count"] == 0
    assert ".venv/bin/mypy src" in result["recommended_commands"]


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
