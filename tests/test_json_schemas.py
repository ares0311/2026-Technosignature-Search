import json
from pathlib import Path


def test_json_schema_files_are_parseable_and_named() -> None:
    schema_dir = Path("schemas")
    schema_paths = sorted(schema_dir.glob("*.schema.json"))

    assert {path.name for path in schema_paths} == {
        "background_draft_follow_up_reports.schema.json",
        "background_draft_report_manifest.schema.json",
        "background_follow_up_tests.schema.json",
        "background_needs_follow_up_log.schema.json",
        "background_report_readiness.schema.json",
        "background_reviewed_log.schema.json",
        "background_search_ledger.schema.json",
        "background_targets.schema.json",
        "background_user_decisions.schema.json",
        "batch_manifest.schema.json",
        "benchmark_metadata.schema.json",
        "benchmark_run_results.schema.json",
        "candidate_extraction_handoff.schema.json",
        "candidate_packet.schema.json",
        "consensus_export.schema.json",
        "consensus_labels.schema.json",
        "cross_track_references.schema.json",
        "report_manifest.schema.json",
        "review_queue.schema.json",
        "validation_dataset_manifest.schema.json",
        "validation_promotion_rules.schema.json",
        "validation_readiness.schema.json",
        "baseline_eval.schema.json",
        "baseline_performance_history.schema.json",
        "candidate_lifecycle.schema.json",
        "observation_schedule.schema.json",
        "candidate_triage.schema.json",
        "scoring_config_summary.schema.json",
        "sensitivity_config_summary.schema.json",
        "target_watchlist.schema.json",
        "top_level_sqlite_log_consistency.schema.json",
        "weekly_review_template.schema.json",
        "signal_registry.schema.json",
        "candidate_audit_trail.schema.json",
        "multi_epoch_observations.schema.json",
        "target_priority_snapshots.schema.json",
        "candidate_flags.schema.json",
        "candidate_observation_notes.schema.json",
        "candidate_score_history.schema.json",
        "epoch_plan.schema.json",
        "operator_assignment.schema.json",
        "review_deadlines.schema.json",
        "candidate_annotation.schema.json",
        "candidate_retention.schema.json",
        "candidate_resolution.schema.json",
        "data_quality.schema.json",
        "data_quality_log.schema.json",
        "escalation_log.schema.json",
        "follow_up_request.schema.json",
        "observation_campaign.schema.json",
        "candidate_priority_queue.schema.json",
        "session_log.schema.json",
        "candidate_feature_vector.schema.json",
        "ml_model_registry.schema.json",
        "feature_importance.schema.json",
        "feature_normalization.schema.json",
        "model_architecture.schema.json",
        "model_evaluation.schema.json",
        "model_performance_history.schema.json",
        "model_serving.schema.json",
        "scoring_audit_log.schema.json",
        "curated_dataset_admission.schema.json",
        "curated_dataset_intake.schema.json",
        "candidate_rescore.schema.json",
        "operator_handoff_template.schema.json",
        "pipeline_config.schema.json",
        "submission_readiness.schema.json",
        "candidate_comparison.schema.json",
        "pipeline_telemetry.schema.json",
        "provenance_audit.schema.json",
        "project_status_consistency.schema.json",
        "production_blocker_consistency.schema.json",
        "operations_alert_review_consistency.schema.json",
        "operations_action_resolution_consistency.schema.json",
        "operations_blocker_progress_consistency.schema.json",
        "candidate_alert_log.schema.json",
        "pipeline_replay_log.schema.json",
        "scoring_threshold_audit.schema.json",
        "alert_resolution_log.schema.json",
        "config_version_history.schema.json",
        "operator_escalation_log.schema.json",
        "operations_readiness_summary.schema.json",
        "operations_action_plan.schema.json",
        "operations_action_resolution.schema.json",
        "operations_blocker_detail.schema.json",
        "operations_blocker_followup.schema.json",
        "operations_blocker_followup_progress.schema.json",
        "operations_blocker_progress_execution.schema.json",
        "operations_blocker_progress_execution_followup.schema.json",
        "operations_blocker_progress_execution_review.schema.json",
        "operations_blocker_progress_next_actions.schema.json",
        "operations_blocker_progress_review.schema.json",
        "operations_blocker_review.schema.json",
        "candidate_deduplication_log.schema.json",
        "candidate_export_log.schema.json",
        "candidate_linkage_log.schema.json",
        "candidate_match_log.schema.json",
        "data_gap_log.schema.json",
        "intake_queue_log.schema.json",
        "instrument_log.schema.json",
        "archival_query_log.schema.json",
        "observation_request_log.schema.json",
        "pipeline_error_log.schema.json",
        "quality_gate_log.schema.json",
        "workflow_state_log.schema.json",
        "signal_classification_log.schema.json",
        "rfi_database_admission.schema.json",
        "rfi_database.schema.json",
        "rfi_mitigation_log.schema.json",
        "candidate_annotation_log.schema.json",
        "frequency_channel_log.schema.json",
        "pipeline_checkpoint_log.schema.json",
        "candidate_status_log.schema.json",
        "beam_configuration_log.schema.json",
        "calibration_event_log.schema.json",
        "pipeline_run_log.schema.json",
        "source_catalog_log.schema.json",
        "noise_measurement_log.schema.json",
        "spectral_feature_log.schema.json",
        "polarization_log.schema.json",
        "telescope_status_log.schema.json",
        "observation_parameter_log.schema.json",
        "labeled_candidates.schema.json",
        "target_selection_log.schema.json",
        "doppler_correction_log.schema.json",
        "data_archival_log.schema.json",
        "interference_environment_log.schema.json",
        "receiver_health_log.schema.json",
        "pipeline_version_log.schema.json",
        "real_data_admission_preflight.schema.json",
        "sqlite_operational_log_registry.schema.json",
        "sqlite_operational_log_adapter_plan.schema.json",
        "sqlite_operational_log_adapter_contract.schema.json",
        "sqlite_operational_log_adapter_ddl_preview.schema.json",
        "sqlite_operational_log_adapter_execution_preview.schema.json",
        "sqlite_operational_log_adapter_insert_preview.schema.json",
        "sqlite_operational_log_adapter_row_preview.schema.json",
        "data_transfer_log.schema.json",
        "scheduling_conflict_log.schema.json",
        "system_health_log.schema.json",
        "instrument_configuration_log.schema.json",
        "scan_log.schema.json",
        "time_synchronization_log.schema.json",
        "antenna_pointing_log.schema.json",
        "weather_log.schema.json",
        "power_log.schema.json",
        "cooling_system_log.schema.json",
        "environmental_log.schema.json",
        "hardware_fault_log.schema.json",
        "maintenance_log.schema.json",
        "network_connectivity_log.schema.json",
        "software_update_log.schema.json",
        "access_log.schema.json",
        "security_event_log.schema.json",
        "audit_trail_log.schema.json",
        "incident_response_log.schema.json",
        "change_management_log.schema.json",
        "compliance_report_log.schema.json",
        "risk_assessment_log.schema.json",
        "backup_recovery_log.schema.json",
        "capacity_planning_log.schema.json",
        "software_deployment_log.schema.json",
        "performance_monitoring_log.schema.json",
        "user_activity_log.schema.json",
        "health_check_log.schema.json",
        "license_management_log.schema.json",
        "storage_management_log.schema.json",
        "firmware_update_log.schema.json",
        "configuration_audit_log.schema.json",
        "event_correlation_log.schema.json",
    }
    for path in schema_paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert schema["required"]


def test_schema_required_fields_match_example_artifacts() -> None:
    packet_schema = json.loads(
        Path("schemas/candidate_packet.schema.json").read_text(encoding="utf-8")
    )
    manifest_schema = json.loads(
        Path("schemas/report_manifest.schema.json").read_text(encoding="utf-8")
    )
    batch_schema = json.loads(
        Path("schemas/batch_manifest.schema.json").read_text(encoding="utf-8")
    )
    benchmark_schema = json.loads(
        Path("schemas/benchmark_metadata.schema.json").read_text(encoding="utf-8")
    )
    benchmark_run_schema = json.loads(
        Path("schemas/benchmark_run_results.schema.json").read_text(encoding="utf-8")
    )
    background_targets_schema = json.loads(
        Path("schemas/background_targets.schema.json").read_text(encoding="utf-8")
    )
    background_ledger_schema = json.loads(
        Path("schemas/background_search_ledger.schema.json").read_text(
            encoding="utf-8"
        )
    )
    reviewed_log_schema = json.loads(
        Path("schemas/background_reviewed_log.schema.json").read_text(
            encoding="utf-8"
        )
    )
    needs_follow_up_schema = json.loads(
        Path("schemas/background_needs_follow_up_log.schema.json").read_text(
            encoding="utf-8"
        )
    )
    follow_up_tests_schema = json.loads(
        Path("schemas/background_follow_up_tests.schema.json").read_text(
            encoding="utf-8"
        )
    )
    report_readiness_schema = json.loads(
        Path("schemas/background_report_readiness.schema.json").read_text(
            encoding="utf-8"
        )
    )
    draft_reports_schema = json.loads(
        Path("schemas/background_draft_follow_up_reports.schema.json").read_text(
            encoding="utf-8"
        )
    )
    user_decisions_schema = json.loads(
        Path("schemas/background_user_decisions.schema.json").read_text(
            encoding="utf-8"
        )
    )
    handoff_schema = json.loads(
        Path("schemas/candidate_extraction_handoff.schema.json").read_text(
            encoding="utf-8"
        )
    )
    review_queue_schema = json.loads(
        Path("schemas/review_queue.schema.json").read_text(encoding="utf-8")
    )
    consensus_schema = json.loads(
        Path("schemas/consensus_labels.schema.json").read_text(encoding="utf-8")
    )
    consensus_export_schema = json.loads(
        Path("schemas/consensus_export.schema.json").read_text(encoding="utf-8")
    )
    validation_dataset_schema = json.loads(
        Path("schemas/validation_dataset_manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validation_promotion_schema = json.loads(
        Path("schemas/validation_promotion_rules.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validation_readiness_schema = json.loads(
        Path("schemas/validation_readiness.schema.json").read_text(
            encoding="utf-8"
        )
    )
    packet = json.loads(Path("examples/reports/example-radio-clean.json").read_text())
    manifest = json.loads(
        Path("examples/reports/example-radio-clean.manifest.json").read_text()
    )
    batch = json.loads(Path("examples/batch_reports/batch_manifest.json").read_text())
    benchmark = json.loads(Path("tests/fixtures/benchmark_metadata.json").read_text())
    benchmark_runs = json.loads(
        Path("tests/fixtures/benchmark_run_results.json").read_text()
    )
    background_targets = json.loads(
        Path("tests/fixtures/background_targets.json").read_text()
    )
    background_ledger = json.loads(
        Path("tests/fixtures/background_search_ledger.json").read_text()
    )
    reviewed_log = json.loads(
        Path("tests/fixtures/background_reviewed_log.json").read_text()
    )
    needs_follow_up = json.loads(
        Path("tests/fixtures/background_needs_follow_up_log.json").read_text()
    )
    follow_up_tests = json.loads(
        Path("tests/fixtures/background_follow_up_tests.json").read_text()
    )
    report_readiness = json.loads(
        Path("tests/fixtures/background_report_readiness.json").read_text()
    )
    draft_reports = json.loads(
        Path("tests/fixtures/background_draft_follow_up_reports.json").read_text()
    )
    user_decisions = json.loads(
        Path("tests/fixtures/background_user_decisions.json").read_text()
    )
    handoffs = json.loads(
        Path("tests/fixtures/candidate_extraction_handoffs.json").read_text()
    )
    review_queue = json.loads(Path("tests/fixtures/review_queue.json").read_text())
    consensus = json.loads(Path("tests/fixtures/consensus_labels.json").read_text())
    consensus_export = json.loads(Path("tests/fixtures/consensus_exports.json").read_text())
    validation_dataset = json.loads(
        Path("tests/fixtures/validation_dataset_manifest.json").read_text()
    )
    validation_promotion = json.loads(
        Path("tests/fixtures/validation_promotion_rules.json").read_text()
    )
    validation_readiness = json.loads(
        Path("tests/fixtures/validation_readiness.json").read_text()
    )

    assert set(packet_schema["required"]) <= set(packet)
    assert set(manifest_schema["required"]) <= set(manifest)
    assert set(batch_schema["required"]) <= set(batch)
    assert set(benchmark_schema["required"]) <= set(benchmark)
    assert set(benchmark_run_schema["required"]) <= set(benchmark_runs)
    assert set(background_targets_schema["required"]) <= set(background_targets)
    assert set(background_ledger_schema["required"]) <= set(background_ledger)
    assert set(reviewed_log_schema["required"]) <= set(reviewed_log)
    assert set(needs_follow_up_schema["required"]) <= set(needs_follow_up)
    assert set(follow_up_tests_schema["required"]) <= set(follow_up_tests)
    assert set(report_readiness_schema["required"]) <= set(report_readiness)
    assert set(draft_reports_schema["required"]) <= set(draft_reports)
    assert set(user_decisions_schema["required"]) <= set(user_decisions)
    assert set(handoff_schema["required"]) <= set(handoffs)
    assert set(review_queue_schema["required"]) <= set(review_queue)
    assert set(consensus_schema["required"]) <= set(consensus)
    assert set(consensus_export_schema["required"]) <= set(consensus_export)
    assert set(validation_dataset_schema["required"]) <= set(validation_dataset)
    assert set(validation_promotion_schema["required"]) <= set(validation_promotion)
    assert set(validation_readiness_schema["required"]) <= set(validation_readiness)
    assert "schema_version" in packet_schema["required"]
    assert "schema_version" in manifest_schema["required"]
    assert "schema_version" in batch_schema["required"]
    assert "provenance_summary" in manifest_schema["required"]
    assert "plot_artifacts" in manifest_schema["properties"]
    assert "plot_artifact_paths" in batch_schema["properties"]["reports"]["items"]["properties"]
    assert "service_url" in manifest_schema["properties"]["provenance_summary"]["required"]
    assert "cache_key" in manifest_schema["properties"]["provenance_summary"]["required"]
    assert packet["schema_version"] == "techno_search_packet_v1"
    assert manifest["schema_version"] == "techno_search_packet_v1"
    assert manifest["provenance_summary"]["source_dataset"] == "synthetic-example"
    assert manifest["plot_artifacts"][0]["synthetic"] is True
    assert "service_url" in manifest["provenance_summary"]
    assert "cache_key" in manifest["provenance_summary"]
    assert batch["schema_version"] == "techno_search_packet_v1"
    assert packet["config_version"] == "scoring_v0"
    assert batch["config_version"] == "scoring_v0"
    assert benchmark["schema_version"] == "local_synthetic_benchmark_metadata_v1"
    assert benchmark["recommended_limits"]["cpu_workers"] == 12
    assert benchmark_runs["schema_version"] == "synthetic_benchmark_run_result_v1"
    assert len(benchmark_runs["runs"]) == 3
    assert "config_version" in benchmark_run_schema["properties"]["runs"]["items"][
        "required"
    ]
    assert benchmark_runs["runs"][0]["config_version"] == "scoring_v0"
    assert background_targets["schema_version"] == "background_target_priority_v1"
    assert len(background_targets["targets"]) == 4
    assert background_ledger["schema_version"] == "background_search_ledger_v1"
    assert len(background_ledger["ledger_entries"]) == 4
    first_ledger_entry = background_ledger["ledger_entries"][0]
    assert first_ledger_entry["reviewed_workflow_status"] == "candidate_packet_ready"
    assert first_ledger_entry["candidate_packet_ids"] == ["radio-clean-001"]
    assert "reviewed_workflow_status" in background_ledger_schema["properties"][
        "ledger_entries"
    ]["items"]["properties"]
    assert reviewed_log["schema_version"] == "background_reviewed_log_v1"
    assert len(reviewed_log["reviewed_entries"]) == 2
    assert reviewed_log["reviewed_entries"][0]["network_access_allowed"] is False
    assert "network_access_allowed" in reviewed_log_schema["properties"][
        "reviewed_entries"
    ]["items"]["required"]
    assert needs_follow_up["schema_version"] == "background_needs_follow_up_log_v1"
    assert len(needs_follow_up["needs_follow_up_entries"]) == 2
    assert needs_follow_up["needs_follow_up_entries"][0][
        "submission_requires_user_approval"
    ] is True
    assert "submission_requires_user_approval" in needs_follow_up_schema[
        "properties"
    ]["needs_follow_up_entries"]["items"]["required"]
    assert follow_up_tests["schema_version"] == "background_follow_up_tests_v1"
    assert len(follow_up_tests["test_results"]) == 12
    assert follow_up_tests["test_results"][0]["network_access_allowed"] is False
    assert "network_access_allowed" in follow_up_tests_schema["properties"][
        "test_results"
    ]["items"]["required"]
    assert report_readiness["schema_version"] == "background_report_readiness_v1"
    assert len(report_readiness["readiness_records"]) == 2
    assert report_readiness["readiness_records"][0][
        "external_submission_allowed"
    ] is False
    assert len(
        report_readiness["readiness_records"][0]["top_three_recommendations"]
    ) == 3
    assert "top_three_recommendations" in report_readiness_schema["properties"][
        "readiness_records"
    ]["items"]["required"]
    assert draft_reports["schema_version"] == "background_draft_follow_up_reports_v1"
    assert len(draft_reports["draft_reports"]) == 2
    assert draft_reports["draft_reports"][0]["draft_status"] == "draft_ready"
    assert draft_reports["draft_reports"][0]["external_submission_allowed"] is False
    assert "negative_evidence" in draft_reports_schema["properties"][
        "draft_reports"
    ]["items"]["required"]
    assert user_decisions["schema_version"] == "background_user_decisions_v1"
    assert len(user_decisions["decisions"]) == 3
    assert all(
        decision["external_submission_approved"] is False
        for decision in user_decisions["decisions"]
    )
    assert "external_submission_approved" in user_decisions_schema["properties"][
        "decisions"
    ]["items"]["required"]
    assert handoffs["schema_version"] == "candidate_extraction_handoff_v1"
    assert len(handoffs["handoffs"]) == 4
    assert handoffs["handoffs"][0]["network_access_allowed"] is False
    assert "network_access_allowed" in handoff_schema["properties"]["handoffs"][
        "items"
    ]["required"]
    assert review_queue["schema_version"] == "human_review_queue_v1"
    assert sorted(review_queue["allowed_triage_labels"]) == [
        "follow_up_target",
        "insufficient_evidence",
        "known_object_annotation",
        "likely_false_positive",
        "needs_human_review",
    ]
    assert consensus["schema_version"] == "human_review_consensus_labels_v1"
    assert sorted(consensus["allowed_consensus_labels"]) == [
        "follow_up_target",
        "insufficient_evidence",
        "known_object_annotation",
        "likely_false_positive",
        "no_consensus",
    ]
    assert consensus_export["schema_version"] == "human_review_consensus_export_v1"
    assert len(consensus_export["exports"]) == 5
    assert validation_dataset["schema_version"] == "validation_dataset_manifest_v1"
    assert len(validation_dataset["datasets"]) == 3
    assert validation_promotion["schema_version"] == "validation_dataset_promotion_rules_v1"
    assert len(validation_promotion["rules"]) == 3
    assert validation_readiness["schema_version"] == "validation_readiness_v1"
    assert len(validation_readiness["records"]) == 3
