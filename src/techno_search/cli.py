"""Command-line interface for synthetic candidate scoring."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from techno_search.aggregate_blockers import aggregate_blockers_summary
from techno_search.alert_resolution_log import alert_resolution_summary
from techno_search.archival_query_log import archival_query_summary
from techno_search.artifact_cleanup import (
    apply_artifact_cleanup,
    plan_artifact_cleanup,
)
from techno_search.background_search import (
    BackgroundUserDecisionRecord,
    append_background_user_decision_record,
    background_draft_follow_up_report_summary,
    background_follow_up_test_summary,
    background_needs_follow_up_summary,
    background_report_readiness_summary,
    background_review_workflow_summary,
    background_reviewed_log_summary,
    background_search_ledger_summary,
    background_user_decision_summary,
    candidate_extraction_handoff_summary,
    run_local_background_search_once,
    scheduler_dry_run,
    target_priority_summary,
    write_background_draft_follow_up_reports,
)
from techno_search.baseline_eval import (
    baseline_pathway_drift_summary,
    baseline_performance_history_summary,
    classifier_rule_coverage_summary,
    evaluate_baseline,
    route_coverage_summary,
    score_determinism_check,
)
from techno_search.benchmark_metadata import (
    BenchmarkRunResult,
    append_benchmark_run_result,
    benchmark_metadata_summary,
    benchmark_run_result_comparison,
    benchmark_run_result_summary,
)
from techno_search.calibration import (
    calibration_track_summary,
    false_positive_class_summary,
    load_calibration_fixtures,
    summarize_calibration_fixtures,
)
from techno_search.calibration_metrics import precision_recall_summary, reliability_summary
from techno_search.candidate_alert_log import candidate_alert_summary
from techno_search.candidate_annotation import candidate_annotation_summary
from techno_search.candidate_annotation_log import candidate_annotation_log_summary
from techno_search.candidate_audit_trail import audit_trail_summary
from techno_search.candidate_comparison import candidate_comparison_summary
from techno_search.candidate_deduplication_log import candidate_deduplication_summary
from techno_search.candidate_export_log import candidate_export_summary
from techno_search.candidate_feature_vector import feature_vector_summary
from techno_search.candidate_flags import candidate_flags_summary
from techno_search.candidate_lifecycle import (
    candidate_lifecycle_summary,
    lifecycle_transition_summary,
)
from techno_search.candidate_linkage_log import candidate_linkage_summary
from techno_search.candidate_match_log import candidate_match_summary
from techno_search.candidate_methods_summary import candidate_methods_summary
from techno_search.candidate_observation_notes import observation_notes_summary
from techno_search.candidate_priority_queue import priority_queue_summary
from techno_search.candidate_rescore import candidate_rescore_summary
from techno_search.candidate_resolution import candidate_resolution_summary
from techno_search.candidate_retention import candidate_retention_summary
from techno_search.candidate_score_history import score_history_summary
from techno_search.candidate_status_log import candidate_status_log_summary
from techno_search.candidate_triage import (
    operator_coverage_summary,
    triage_label_completeness_check,
    triage_summary,
)
from techno_search.config_version_history import config_version_history_summary
from techno_search.constants import DEFAULT_SCHEMA_VERSION, DEFAULT_SCORING_CONFIG_VERSION
from techno_search.cross_track import cross_track_summary
from techno_search.curated_dataset_intake import curated_dataset_intake_summary
from techno_search.data_gap_log import data_gap_summary
from techno_search.data_quality_log import data_quality_log_summary
from techno_search.epoch_plan import epoch_plan_summary
from techno_search.escalation_log import escalation_log_summary
from techno_search.feature_importance import feature_importance_summary
from techno_search.feature_normalization import feature_normalization_summary
from techno_search.follow_up_request import follow_up_request_summary
from techno_search.frequency_channel_log import frequency_channel_log_summary
from techno_search.injection_recovery import false_negative_summary, injection_recovery_summary
from techno_search.instrument_log import instrument_log_summary
from techno_search.intake_queue_log import intake_queue_summary
from techno_search.live_data import (
    CatalogCache,
    CatalogCachePolicy,
    LiveProviderCache,
    live_client_summary,
    live_data_enabled,
    live_metadata_fixture_summary,
    provider_adapters,
    provider_normalization_regression_summary,
    validate_catalog_cache_commit_paths,
)
from techno_search.log_store import (
    TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
    apply_sqlite_log_migration,
    default_sqlite_log_path,
    init_sqlite_log_db,
    sqlite_log_backup,
    sqlite_log_export,
    sqlite_log_integrity_summary,
    sqlite_log_migration_plan,
    sqlite_log_migration_summary,
    sqlite_log_pragmas,
    sqlite_log_retention_summary,
    sqlite_log_summary,
    sqlite_log_vacuum,
    sqlite_log_weekly_digest,
    sqlite_needs_follow_up,
    sqlite_recent_runs,
    validate_sqlite_log_commit_paths,
)
from techno_search.ml_model_registry import model_registry_summary
from techno_search.ml_pipeline_diagnostics import ml_pipeline_diagnostics_summary
from techno_search.ml_training_data import ml_training_data_summary
from techno_search.model_architecture import model_architecture_summary
from techno_search.model_evaluation import model_evaluation_summary
from techno_search.model_performance_history import model_performance_history_summary
from techno_search.model_serving import model_serving_summary
from techno_search.multi_epoch_summary import multi_epoch_summary
from techno_search.observation_campaign import observation_campaign_summary
from techno_search.observation_request_log import observation_request_summary
from techno_search.observation_schedule import (
    observation_efficiency_summary,
    observation_gap_analysis,
    observation_schedule_summary,
)
from techno_search.operations_action_plan import operations_action_plan_summary
from techno_search.operations_action_resolution import (
    operations_action_resolution_summary,
)
from techno_search.operations_blocker_detail import operations_blocker_detail_summary
from techno_search.operations_blocker_followup import operations_blocker_followup_summary
from techno_search.operations_blocker_followup_progress import (
    operations_blocker_followup_progress_summary,
)
from techno_search.operations_blocker_progress_execution import (
    operations_blocker_progress_execution_summary,
)
from techno_search.operations_blocker_progress_execution_followup import (
    operations_blocker_progress_execution_followup_summary,
)
from techno_search.operations_blocker_progress_execution_review import (
    operations_blocker_progress_execution_review_summary,
)
from techno_search.operations_blocker_progress_next_actions import (
    operations_blocker_progress_next_actions_summary,
)
from techno_search.operations_blocker_progress_review import (
    operations_blocker_progress_review_summary,
)
from techno_search.operations_blocker_review import operations_blocker_review_summary
from techno_search.operations_readiness import (
    operations_readiness_digest,
    operations_readiness_summary,
)
from techno_search.operator_assignment import operator_assignment_summary
from techno_search.operator_escalation_log import operator_escalation_summary
from techno_search.operator_handoff_template import operator_handoff_summary
from techno_search.operator_performance import operator_performance_summary
from techno_search.pipeline_audit_summary import pipeline_audit_summary
from techno_search.pipeline_bottleneck import pipeline_bottleneck_summary
from techno_search.pipeline_capacity import pipeline_capacity_summary
from techno_search.pipeline_checkpoint_log import pipeline_checkpoint_log_summary
from techno_search.pipeline_config import pipeline_config_summary
from techno_search.pipeline_error_log import pipeline_error_summary
from techno_search.pipeline_health import pipeline_health_summary
from techno_search.pipeline_integration import pipeline_integration_summary
from techno_search.pipeline_replay_log import pipeline_replay_summary
from techno_search.pipeline_telemetry import pipeline_telemetry_summary
from techno_search.pipeline_throughput import pipeline_throughput_summary
from techno_search.plotting import plot_artifact_summary
from techno_search.provenance import provenance_chain_validator
from techno_search.provenance_audit import provenance_audit_summary
from techno_search.quality_control_summary import quality_control_summary
from techno_search.quality_gate_log import quality_gate_summary
from techno_search.reporting import (
    candidate_packet_json,
    write_candidate_reports,
)
from techno_search.reproducibility import verify_report_directory
from techno_search.review_deadlines import review_deadlines_summary
from techno_search.review_queue import (
    consensus_export_summary,
    consensus_summary,
    review_queue_summary,
)
from techno_search.rfi_mitigation_log import rfi_mitigation_summary
from techno_search.schemas import Candidate, Track, candidate_from_mapping
from techno_search.scoring import score_candidate
from techno_search.scoring_audit_log import scoring_audit_log_summary
from techno_search.scoring_config import scoring_config_summary
from techno_search.scoring_threshold_audit import scoring_threshold_audit_summary
from techno_search.sensitivity_config import sensitivity_config_summary
from techno_search.session_log import session_log_summary
from techno_search.signal_classification_log import signal_classification_summary
from techno_search.signal_registry import (
    signal_registry_summary,
    signal_registry_track_summary,
)
from techno_search.submission_readiness import submission_readiness_summary
from techno_search.target_recalibration_summary import target_recalibration_summary
from techno_search.target_watchlist import target_watchlist_summary
from techno_search.track_comparison import track_comparison_summary
from techno_search.validation import (
    validate_candidate_file,
    validate_draft_report_directory,
    validate_report_directory,
    validate_sqlite_log_database,
)
from techno_search.validation_datasets import (
    validation_dataset_summary,
    validation_promotion_summary,
    validation_readiness_summary,
)
from techno_search.weekly_review import build_weekly_review_template, write_weekly_review_template
from techno_search.workflow_state_log import workflow_state_summary

SCHEMA_FILENAMES = {
    "background_draft_follow_up_reports": "background_draft_follow_up_reports.schema.json",
    "background_draft_report_manifest": "background_draft_report_manifest.schema.json",
    "background_follow_up_tests": "background_follow_up_tests.schema.json",
    "background_needs_follow_up_log": "background_needs_follow_up_log.schema.json",
    "background_report_readiness": "background_report_readiness.schema.json",
    "background_reviewed_log": "background_reviewed_log.schema.json",
    "background_search_ledger": "background_search_ledger.schema.json",
    "background_targets": "background_targets.schema.json",
    "background_user_decisions": "background_user_decisions.schema.json",
    "batch_manifest": "batch_manifest.schema.json",
    "benchmark_metadata": "benchmark_metadata.schema.json",
    "benchmark_run_results": "benchmark_run_results.schema.json",
    "candidate_extraction_handoff": "candidate_extraction_handoff.schema.json",
    "candidate_packet": "candidate_packet.schema.json",
    "consensus_export": "consensus_export.schema.json",
    "consensus_labels": "consensus_labels.schema.json",
    "cross_track_references": "cross_track_references.schema.json",
    "report_manifest": "report_manifest.schema.json",
    "review_queue": "review_queue.schema.json",
    "validation_dataset_manifest": "validation_dataset_manifest.schema.json",
    "validation_promotion_rules": "validation_promotion_rules.schema.json",
    "validation_readiness": "validation_readiness.schema.json",
    "target_watchlist": "target_watchlist.schema.json",
    "weekly_review_template": "weekly_review_template.schema.json",
    "baseline_eval": "baseline_eval.schema.json",
    "baseline_performance_history": "baseline_performance_history.schema.json",
    "candidate_lifecycle": "candidate_lifecycle.schema.json",
    "candidate_triage": "candidate_triage.schema.json",
    "observation_schedule": "observation_schedule.schema.json",
    "scoring_config_summary": "scoring_config_summary.schema.json",
    "sensitivity_config_summary": "sensitivity_config_summary.schema.json",
    "signal_registry": "signal_registry.schema.json",
    "candidate_audit_trail": "candidate_audit_trail.schema.json",
    "multi_epoch_observations": "multi_epoch_observations.schema.json",
    "target_priority_snapshots": "target_priority_snapshots.schema.json",
    "candidate_flags": "candidate_flags.schema.json",
    "candidate_observation_notes": "candidate_observation_notes.schema.json",
    "candidate_score_history": "candidate_score_history.schema.json",
    "epoch_plan": "epoch_plan.schema.json",
    "operator_assignment": "operator_assignment.schema.json",
    "candidate_annotation": "candidate_annotation.schema.json",
    "candidate_feature_vector": "candidate_feature_vector.schema.json",
    "candidate_priority_queue": "candidate_priority_queue.schema.json",
    "feature_importance": "feature_importance.schema.json",
    "feature_normalization": "feature_normalization.schema.json",
    "ml_model_registry": "ml_model_registry.schema.json",
    "model_architecture": "model_architecture.schema.json",
    "model_evaluation": "model_evaluation.schema.json",
    "model_performance_history": "model_performance_history.schema.json",
    "model_serving": "model_serving.schema.json",
    "scoring_audit_log": "scoring_audit_log.schema.json",
    "candidate_rescore": "candidate_rescore.schema.json",
    "pipeline_config": "pipeline_config.schema.json",
    "submission_readiness": "submission_readiness.schema.json",
    "candidate_comparison": "candidate_comparison.schema.json",
    "pipeline_telemetry": "pipeline_telemetry.schema.json",
    "provenance_audit": "provenance_audit.schema.json",
    "candidate_alert_log": "candidate_alert_log.schema.json",
    "pipeline_replay_log": "pipeline_replay_log.schema.json",
    "scoring_threshold_audit": "scoring_threshold_audit.schema.json",
    "alert_resolution_log": "alert_resolution_log.schema.json",
    "candidate_deduplication_log": "candidate_deduplication_log.schema.json",
    "candidate_export_log": "candidate_export_log.schema.json",
    "candidate_match_log": "candidate_match_log.schema.json",
    "data_gap_log": "data_gap_log.schema.json",
    "config_version_history": "config_version_history.schema.json",
    "intake_queue_log": "intake_queue_log.schema.json",
    "operator_escalation_log": "operator_escalation_log.schema.json",
    "observation_request_log": "observation_request_log.schema.json",
    "pipeline_error_log": "pipeline_error_log.schema.json",
    "quality_gate_log": "quality_gate_log.schema.json",
    "workflow_state_log": "workflow_state_log.schema.json",
    "curated_dataset_intake": "curated_dataset_intake.schema.json",
    "operator_handoff_template": "operator_handoff_template.schema.json",
    "candidate_resolution": "candidate_resolution.schema.json",
    "candidate_retention": "candidate_retention.schema.json",
    "data_quality_log": "data_quality_log.schema.json",
    "follow_up_request": "follow_up_request.schema.json",
    "session_log": "session_log.schema.json",
    "escalation_log": "escalation_log.schema.json",
    "observation_campaign": "observation_campaign.schema.json",
    "review_deadlines": "review_deadlines.schema.json",
    "operations_readiness_summary": "operations_readiness_summary.schema.json",
    "operations_action_plan": "operations_action_plan.schema.json",
    "operations_action_resolution": "operations_action_resolution.schema.json",
    "operations_blocker_detail": "operations_blocker_detail.schema.json",
    "operations_blocker_followup": "operations_blocker_followup.schema.json",
    "operations_blocker_followup_progress": (
        "operations_blocker_followup_progress.schema.json"
    ),
    "operations_blocker_progress_review": (
        "operations_blocker_progress_review.schema.json"
    ),
    "operations_blocker_progress_next_actions": (
        "operations_blocker_progress_next_actions.schema.json"
    ),
    "operations_blocker_progress_execution": (
        "operations_blocker_progress_execution.schema.json"
    ),
    "operations_blocker_progress_execution_followup": (
        "operations_blocker_progress_execution_followup.schema.json"
    ),
    "operations_blocker_progress_execution_review": (
        "operations_blocker_progress_execution_review.schema.json"
    ),
    "operations_blocker_review": "operations_blocker_review.schema.json",
    "instrument_log": "instrument_log.schema.json",
    "archival_query_log": "archival_query_log.schema.json",
    "candidate_linkage_log": "candidate_linkage_log.schema.json",
    "signal_classification_log": "signal_classification_log.schema.json",
    "rfi_mitigation_log": "rfi_mitigation_log.schema.json",
    "candidate_annotation_log": "candidate_annotation_log.schema.json",
    "frequency_channel_log": "frequency_channel_log.schema.json",
    "pipeline_checkpoint_log": "pipeline_checkpoint_log.schema.json",
    "candidate_status_log": "candidate_status_log.schema.json",
}


def main(argv: list[str] | None = None, stdout: TextIO | None = None) -> int:
    """Run the `techno-search` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    out = stdout or sys.stdout

    if args.command == "score":
        candidate = load_candidate_json(args.input)
        scored = score_candidate(candidate)
        if args.output_dir is not None:
            paths = write_candidate_reports(
                scored,
                args.output_dir,
                filename_prefix=args.prefix,
                include_plot_artifacts=not args.no_plot_artifacts,
            )
            print(str(paths.markdown_path), file=out)
            print(str(paths.json_path), file=out)
            print(str(paths.manifest_path), file=out)
            for plot_path in paths.plot_artifact_paths:
                print(str(plot_path), file=out)
        else:
            print(candidate_packet_json(scored), file=out)
        return 0

    if args.command == "score-batch":
        manifest_path = score_batch(
            args.input_dir,
            args.output_dir,
            prefix=args.prefix,
            include_plot_artifacts=not args.no_plot_artifacts,
        )
        print(str(manifest_path), file=out)
        return 0

    if args.command == "calibration-summary":
        fixtures = load_calibration_fixtures(args.fixture_path)
        summary = summarize_calibration_fixtures(fixtures)
        print(json.dumps(summary.as_dict(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "false-positive-summary":
        print(
            json.dumps(
                false_positive_class_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "calibration-track-summary":
        print(
            json.dumps(
                calibration_track_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "validate-candidate":
        result = validate_candidate_file(args.input)
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if result.ok else 1

    if args.command == "validate-reports":
        result = validate_report_directory(args.report_dir)
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if result.ok else 1

    if args.command == "schema-paths":
        print(json.dumps(schema_paths(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "score-regression-summary":
        print(
            json.dumps(score_regression_summary(args.snapshot_path), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "injection-recovery-summary":
        print(
            json.dumps(
                injection_recovery_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "reliability-summary":
        print(
            json.dumps(
                reliability_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "precision-recall-summary":
        print(
            json.dumps(
                precision_recall_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "validation-dataset-summary":
        print(
            json.dumps(
                validation_dataset_summary(args.manifest_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "validation-promotion-summary":
        print(
            json.dumps(
                validation_promotion_summary(args.rules_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "validation-readiness-summary":
        print(
            json.dumps(
                validation_readiness_summary(args.readiness_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "benchmark-metadata-summary":
        print(
            json.dumps(
                benchmark_metadata_summary(args.metadata_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "benchmark-run-summary":
        print(
            json.dumps(
                benchmark_run_result_summary(args.results_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "benchmark-run-append":
        print(
            json.dumps(
                append_benchmark_run_result(
                    args.results_path,
                    BenchmarkRunResult(
                        run_id=args.run_id,
                        command_name=args.command_name,
                        command_kind=args.command_kind,
                        status=args.status,
                        worker_count=args.worker_count,
                        input_case_count=args.input_case_count,
                        duration_seconds=args.duration_seconds,
                        git_commit=args.git_commit,
                        config_version=args.config_version,
                    ),
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "benchmark-run-compare":
        print(
            json.dumps(
                benchmark_run_result_comparison(args.results_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "target-priority-summary":
        print(
            json.dumps(
                target_priority_summary(
                    args.target_path,
                    args.config_path,
                    args.ledger_path,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "background-ledger-summary":
        print(
            json.dumps(
                background_search_ledger_summary(args.ledger_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "background-reviewed-workflow-summary":
        print(
            json.dumps(
                background_review_workflow_summary(args.ledger_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "reviewed-log-summary":
        print(
            json.dumps(
                background_reviewed_log_summary(args.reviewed_log_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "needs-follow-up-summary":
        print(
            json.dumps(
                background_needs_follow_up_summary(args.needs_follow_up_log_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "follow-up-test-summary":
        print(
            json.dumps(
                background_follow_up_test_summary(args.follow_up_tests_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "report-readiness-summary":
        print(
            json.dumps(
                background_report_readiness_summary(args.report_readiness_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "draft-follow-up-report-summary":
        print(
            json.dumps(
                background_draft_follow_up_report_summary(
                    args.report_readiness_path,
                    from_readiness=True,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "draft-report-fixture-summary":
        print(
            json.dumps(
                background_draft_follow_up_report_summary(args.draft_report_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "draft-follow-up-report-write":
        write_result = write_background_draft_follow_up_reports(
            args.output_dir,
            readiness_path=args.report_readiness_path,
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "output_dir": str(write_result.output_dir),
                    "manifest_path": str(write_result.manifest_path),
                    "markdown_paths": [
                        str(path) for path in write_result.markdown_paths
                    ],
                    "summary": background_draft_follow_up_report_summary(
                        args.report_readiness_path,
                        from_readiness=True,
                    ),
                },
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "validate-draft-reports":
        result = validate_draft_report_directory(args.report_dir)
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if result.ok else 1

    if args.command == "user-decision-summary":
        print(
            json.dumps(
                background_user_decision_summary(args.user_decision_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "user-decision-record":
        external_approved = bool(args.confirm_external_submission_approval)
        record = BackgroundUserDecisionRecord(
            decision_id=args.decision_id,
            readiness_id=args.readiness_id,
            follow_up_id=args.follow_up_id,
            target_id=args.target_id,
            track=Track(args.track),
            decision=args.decision,
            decided_at_utc=args.decided_at_utc
            or datetime.now(UTC).isoformat(),
            rationale=args.rationale,
            required_next_actions=tuple(args.required_next_action or ()),
            external_submission_approved=external_approved,
            request_more_tests=args.decision == "request_more_tests",
            close_as_reviewed=args.decision == "close_as_reviewed",
            submission_destination=args.submission_destination,
            blocking_issues=tuple(args.blocking_issue or ()),
            network_access_allowed=False,
        )
        print(
            json.dumps(
                append_background_user_decision_record(
                    args.user_decision_path,
                    record,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "submission-recommendation-summary":
        print(
            json.dumps(
                background_report_readiness_summary(args.report_readiness_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-extraction-handoff-summary":
        print(
            json.dumps(
                candidate_extraction_handoff_summary(args.handoff_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "background-run-once":
        print(
            json.dumps(
                run_local_background_search_once(
                    args.ledger_path,
                    reviewed_log_path=args.reviewed_log_path,
                    needs_follow_up_log_path=args.needs_follow_up_log_path,
                    sqlite_log_path=args.sqlite_log_path,
                    target_path=args.target_path,
                    config_path=args.config_path,
                    run_id=args.run_id,
                    code_commit=args.code_commit,
                    opt_in=args.acknowledge_local_run,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "init-logs":
        print(
            json.dumps(
                init_sqlite_log_db(
                    args.db_path,
                    code_commit=args.code_commit,
                    config_version=args.config_version,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-summary":
        print(
            json.dumps(
                sqlite_log_summary(args.db_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-integrity-summary":
        print(
            json.dumps(
                sqlite_log_integrity_summary(args.db_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-bootstrap-summary":
        init_result = init_sqlite_log_db(
            args.db_path,
            code_commit=args.code_commit,
            config_version=args.config_version,
        )
        integrity = sqlite_log_integrity_summary(args.db_path)
        weekly_digest = sqlite_log_weekly_digest(
            args.db_path,
            window_days=args.window_days,
        )
        readiness = operations_readiness_summary(sqlite_log_path=args.db_path)
        sqlite_snapshot = readiness["sqlite_log_snapshot"]
        bootstrap_result = {
            "ok": (
                bool(init_result["ok"])
                and bool(integrity["ok"])
                and bool(weekly_digest["ok"])
                and bool(sqlite_snapshot["integrity_ok"])
                and bool(sqlite_snapshot["weekly_digest_ok"])
                and int(sqlite_snapshot["network_access_allowed_count"]) == 0
                and int(sqlite_snapshot["external_submission_approved_count"]) == 0
            ),
            "db_path": str(args.db_path),
            "schema_version": init_result["schema_version"],
            "disclaimer": init_result["disclaimer"],
            "sqlite_log_initialized": bool(init_result["database_exists"]),
            "sqlite_integrity_ok": bool(integrity["ok"]),
            "sqlite_weekly_digest_ok": bool(weekly_digest["ok"]),
            "readiness_sqlite_integrity_ok": bool(sqlite_snapshot["integrity_ok"]),
            "readiness_sqlite_weekly_digest_ok": bool(
                sqlite_snapshot["weekly_digest_ok"]
            ),
            "readiness_recommendation": readiness["recommendation"],
            "readiness_real_data_blocker_count": readiness["real_data_blocker_count"],
            "network_access_allowed_count": int(
                sqlite_snapshot["network_access_allowed_count"]
            ),
            "external_submission_approved_count": int(
                sqlite_snapshot["external_submission_approved_count"]
            ),
            "validated_action_ids": ["ops-action-009", "ops-action-010"],
            "does_not_mutate_action_resolution_fixture": True,
            "uncertainty_and_limitations": [
                "Bootstrap checks restore SQLite visibility for the supplied local database only.",
                "Validated SQLite visibility does not clear non-SQLite operations blockers.",
                "Generated SQLite databases and backups must remain ignored local artifacts.",
            ],
            "init_summary": init_result,
            "integrity_summary": integrity,
            "weekly_digest": weekly_digest,
            "operations_readiness_summary": readiness,
        }
        print(json.dumps(bootstrap_result, indent=2, sort_keys=True), file=out)
        return 0 if bootstrap_result["ok"] else 1

    if args.command == "sqlite-log-export":
        print(
            json.dumps(
                sqlite_log_export(args.db_path, limit=args.limit),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-recent-runs":
        print(
            json.dumps(
                sqlite_recent_runs(args.db_path, limit=args.limit),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-needs-follow-up":
        print(
            json.dumps(
                sqlite_needs_follow_up(args.db_path, limit=args.limit),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-migration-summary":
        print(
            json.dumps(
                sqlite_log_migration_summary(args.db_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-migrate":
        plan = sqlite_log_migration_plan(
            args.db_path,
            target_version=args.target_version,
        )
        if args.apply:
            apply_result = apply_sqlite_log_migration(args.db_path)
            print(json.dumps(apply_result, indent=2, sort_keys=True), file=out)
            return 0 if apply_result.get("ok") else 1
        print(json.dumps(plan, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "sqlite-log-pragmas":
        print(
            json.dumps(
                sqlite_log_pragmas(args.db_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-retention-summary":
        print(
            json.dumps(
                sqlite_log_retention_summary(
                    args.db_path,
                    backup_dir=args.backup_dir,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "sqlite-log-backup":
        backup_result = sqlite_log_backup(args.db_path, backup_dir=args.backup_dir)
        print(json.dumps(backup_result, indent=2, sort_keys=True), file=out)
        return 0 if backup_result["ok"] else 1

    if args.command == "sqlite-log-vacuum":
        vacuum_result = sqlite_log_vacuum(args.db_path)
        print(json.dumps(vacuum_result, indent=2, sort_keys=True), file=out)
        return 0 if vacuum_result["ok"] else 1

    if args.command == "sqlite-log-weekly-digest":
        digest_result = sqlite_log_weekly_digest(
            args.db_path,
            window_days=args.window_days,
        )
        print(json.dumps(digest_result, indent=2, sort_keys=True), file=out)
        return 0 if digest_result.get("ok", False) else 1

    if args.command == "sqlite-log-commit-guard":
        commit_guard_paths = args.paths or git_tracked_paths(default_project_root())
        commit_guard_result = validate_sqlite_log_commit_paths(
            [Path(path) for path in commit_guard_paths],
            project_root=default_project_root(),
        )
        print(json.dumps(commit_guard_result, indent=2, sort_keys=True), file=out)
        return 0 if commit_guard_result["ok"] else 1

    if args.command == "validate-sqlite-logs":
        result = validate_sqlite_log_database(args.db_path)
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if result.ok else 1

    if args.command == "scheduler-dry-run":
        print(
            json.dumps(
                scheduler_dry_run(
                    args.artifact_dir,
                    run_id=args.run_id,
                    code_commit=args.code_commit,
                    sqlite_log_path=args.sqlite_log_path,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "review-queue-summary":
        print(
            json.dumps(
                review_queue_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "consensus-summary":
        print(
            json.dumps(
                consensus_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "consensus-export-summary":
        print(
            json.dumps(
                consensus_export_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "cross-track-summary":
        print(
            json.dumps(
                cross_track_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "verify-report-reproducibility":
        verify_result = verify_report_directory(args.report_dir)
        print(json.dumps(verify_result, indent=2, sort_keys=True), file=out)
        return 0 if verify_result.get("ok", False) else 1

    if args.command == "validate-all":
        all_result = validate_all()
        print(json.dumps(all_result, indent=2, sort_keys=True), file=out)
        return 0 if all_result["ok"] else 1

    if args.command == "validation-summary":
        summary_result = validation_summary()
        print(json.dumps(summary_result, indent=2, sort_keys=True), file=out)
        return 0 if summary_result["ok"] else 1

    if args.command == "regenerate-examples":
        regeneration_result = regenerate_examples()
        print(json.dumps(regeneration_result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "provenance-summary":
        print(
            json.dumps(provenance_summary(args.report_dir), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "plot-artifact-summary":
        print(
            json.dumps(plot_artifact_summary(args.report_dir), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "live-provider-summary":
        print(json.dumps(live_provider_summary(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "live-cache-summary":
        print(
            json.dumps(live_cache_summary(args.cache_dir), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "live-fixture-summary":
        print(
            json.dumps(live_metadata_fixture_summary(args.fixture_dir), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "live-client-summary":
        print(json.dumps(live_client_summary(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "catalog-cache-policy":
        print(
            json.dumps(catalog_cache_policy_summary(args.cache_root), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "catalog-cache-summary":
        print(
            json.dumps(catalog_cache_summary(args.cache_root), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "catalog-cache-validate":
        catalog_result = catalog_cache_validation_summary(args.paths)
        print(json.dumps(catalog_result, indent=2, sort_keys=True), file=out)
        return 0 if catalog_result["ok"] else 1

    if args.command == "baseline-eval-summary":
        eval_result = evaluate_baseline(
            calibration_fixture_path=getattr(args, "calibration_fixture", None),
            example_candidates_dir=getattr(args, "example_candidates_dir", None),
        )
        result_without_details = {
            k: v for k, v in eval_result.items() if k != "results"
        }
        print(json.dumps(result_without_details, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "target-watchlist-summary":
        print(
            json.dumps(
                target_watchlist_summary(args.fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "weekly-review-template":
        _db_path = getattr(args, "db_path", None) or default_sqlite_log_path(
            default_project_root()
        )
        digest = sqlite_log_weekly_digest(_db_path, window_days=args.window_days)
        ct_summary = cross_track_summary(
            getattr(args, "cross_track_fixture", None)
        )
        _wl_summary = target_watchlist_summary()
        template = build_weekly_review_template(
            digest=digest,
            ct_summary=ct_summary,
            window_days=args.window_days,
            operator_notes=args.operator_notes or "",
            watchlist_summary=_wl_summary,
        )
        if args.output_dir is not None:
            md_path, json_path = write_weekly_review_template(
                template,
                args.output_dir,
            )
            print(
                json.dumps(
                    {
                        "ok": True,
                        "markdown_path": str(md_path),
                        "json_path": str(json_path),
                        "network_access_confirmed_zero": template.network_access_confirmed_zero,
                        "external_submission_confirmed_zero": (
                            template.external_submission_confirmed_zero
                        ),
                    },
                    indent=2,
                    sort_keys=True,
                ),
                file=out,
            )
        else:
            print(json.dumps(template.as_dict(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "baseline-performance-history-summary":
        history = baseline_performance_history_summary(
            getattr(args, "history_path", None)
        )
        print(json.dumps(history, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "baseline-pathway-drift-summary":
        drift = baseline_pathway_drift_summary(
            getattr(args, "example_candidates_dir", None)
        )
        print(json.dumps(drift, indent=2, sort_keys=True), file=out)
        return 0 if drift["zero_drift"] else 1

    if args.command == "sqlite-log-track-summary":
        _db_path = getattr(args, "db_path", None) or default_sqlite_log_path(
            default_project_root()
        )
        track_summary = _sqlite_log_track_summary(_db_path)
        print(json.dumps(track_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "health":
        _health = _project_health_summary(out)
        print(json.dumps(_health, indent=2, sort_keys=True), file=out)
        return 0 if _health["all_gates_pass"] else 1

    if args.command == "operations-readiness-summary":
        db_path = getattr(args, "sqlite_log_path", None)
        print(
            json.dumps(
                operations_readiness_summary(sqlite_log_path=db_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-action-plan-summary":
        db_path = getattr(args, "sqlite_log_path", None)
        ops_summary = operations_readiness_summary(sqlite_log_path=db_path)
        print(
            json.dumps(
                operations_action_plan_summary(ops_summary),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-action-resolution-summary":
        fixture_path = getattr(args, "fixture_path", None)
        db_path = getattr(args, "sqlite_log_path", None)
        ops_summary = operations_readiness_summary(sqlite_log_path=db_path)
        ops_action_plan = operations_action_plan_summary(ops_summary)
        expected_action_ids = [
            str(action["action_id"])
            for action in ops_action_plan["actions"]
            if isinstance(action, dict)
        ]
        print(
            json.dumps(
                operations_action_resolution_summary(
                    fixture_path,
                    expected_action_ids=expected_action_ids,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-detail-summary":
        db_path = getattr(args, "sqlite_log_path", None)
        print(
            json.dumps(
                operations_blocker_detail_summary(sqlite_log_path=db_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-review-summary":
        fixture_path = getattr(args, "fixture_path", None)
        db_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
        expected_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        print(
            json.dumps(
                operations_blocker_review_summary(
                    fixture_path,
                    expected_action_ids=expected_action_ids,
                    blocker_detail_summary=blocker_detail,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-followup-summary":
        fixture_path = getattr(args, "fixture_path", None)
        db_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
        expected_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        print(
            json.dumps(
                operations_blocker_followup_summary(
                    fixture_path,
                    blocker_detail_summary_data=blocker_detail,
                    blocker_review_summary_data=blocker_review,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-followup-progress-summary":
        fixture_path = getattr(args, "fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        db_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        print(
            json.dumps(
                operations_blocker_followup_progress_summary(
                    fixture_path,
                    expected_action_ids=expected_action_ids,
                    blocker_followup_summary=blocker_followup,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-progress-review-summary":
        fixture_path = getattr(args, "fixture_path", None)
        progress_fixture_path = getattr(args, "progress_fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        db_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        progress_summary = operations_blocker_followup_progress_summary(
            progress_fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_followup_summary=blocker_followup,
        )
        unresolved_action_ids = [
            str(record["action_id"])
            for record in progress_summary["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ]
        print(
            json.dumps(
                operations_blocker_progress_review_summary(
                    fixture_path,
                    expected_action_ids=unresolved_action_ids,
                    blocker_followup_progress_summary=progress_summary,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-progress-next-actions-summary":
        fixture_path = getattr(args, "fixture_path", None)
        progress_review_fixture_path = getattr(
            args,
            "progress_review_fixture_path",
            None,
        )
        progress_fixture_path = getattr(args, "progress_fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        db_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        progress_summary = operations_blocker_followup_progress_summary(
            progress_fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_followup_summary=blocker_followup,
        )
        unresolved_action_ids = [
            str(record["action_id"])
            for record in progress_summary["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ]
        progress_review_summary = operations_blocker_progress_review_summary(
            progress_review_fixture_path,
            expected_action_ids=unresolved_action_ids,
            blocker_followup_progress_summary=progress_summary,
        )
        expected_next_action_ids = [
            str(record["action_id"])
            for record in progress_review_summary["records"]
            if isinstance(record, dict)
        ]
        print(
            json.dumps(
                operations_blocker_progress_next_actions_summary(
                    fixture_path,
                    expected_action_ids=expected_next_action_ids,
                    blocker_progress_review_summary=progress_review_summary,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-progress-execution-summary":
        fixture_path = getattr(args, "fixture_path", None)
        next_actions_fixture_path = getattr(args, "next_actions_fixture_path", None)
        progress_review_fixture_path = getattr(
            args,
            "progress_review_fixture_path",
            None,
        )
        progress_fixture_path = getattr(args, "progress_fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        db_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        progress_summary = operations_blocker_followup_progress_summary(
            progress_fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_followup_summary=blocker_followup,
        )
        unresolved_action_ids = [
            str(record["action_id"])
            for record in progress_summary["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ]
        progress_review_summary = operations_blocker_progress_review_summary(
            progress_review_fixture_path,
            expected_action_ids=unresolved_action_ids,
            blocker_followup_progress_summary=progress_summary,
        )
        expected_next_action_ids = [
            str(record["action_id"])
            for record in progress_review_summary["records"]
            if isinstance(record, dict)
        ]
        next_actions_summary = operations_blocker_progress_next_actions_summary(
            next_actions_fixture_path,
            expected_action_ids=expected_next_action_ids,
            blocker_progress_review_summary=progress_review_summary,
        )
        expected_execution_ids = [
            str(record["next_action_id"])
            for record in next_actions_summary["records"]
            if isinstance(record, dict)
        ]
        print(
            json.dumps(
                operations_blocker_progress_execution_summary(
                    fixture_path,
                    expected_next_action_ids=expected_execution_ids,
                    blocker_progress_next_actions_summary=next_actions_summary,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-progress-execution-review-summary":
        fixture_path = getattr(args, "fixture_path", None)
        execution_fixture_path = getattr(args, "execution_fixture_path", None)
        next_actions_fixture_path = getattr(args, "next_actions_fixture_path", None)
        progress_review_fixture_path = getattr(
            args,
            "progress_review_fixture_path",
            None,
        )
        progress_fixture_path = getattr(args, "progress_fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        db_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        progress_summary = operations_blocker_followup_progress_summary(
            progress_fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_followup_summary=blocker_followup,
        )
        unresolved_action_ids = [
            str(record["action_id"])
            for record in progress_summary["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ]
        progress_review_summary = operations_blocker_progress_review_summary(
            progress_review_fixture_path,
            expected_action_ids=unresolved_action_ids,
            blocker_followup_progress_summary=progress_summary,
        )
        expected_next_action_ids = [
            str(record["action_id"])
            for record in progress_review_summary["records"]
            if isinstance(record, dict)
        ]
        next_actions_summary = operations_blocker_progress_next_actions_summary(
            next_actions_fixture_path,
            expected_action_ids=expected_next_action_ids,
            blocker_progress_review_summary=progress_review_summary,
        )
        expected_execution_next_action_ids = [
            str(record["next_action_id"])
            for record in next_actions_summary["records"]
            if isinstance(record, dict)
        ]
        execution_summary = operations_blocker_progress_execution_summary(
            execution_fixture_path,
            expected_next_action_ids=expected_execution_next_action_ids,
            blocker_progress_next_actions_summary=next_actions_summary,
        )
        expected_review_execution_ids = [
            str(record["execution_id"])
            for record in execution_summary["records"]
            if isinstance(record, dict)
        ]
        print(
            json.dumps(
                operations_blocker_progress_execution_review_summary(
                    fixture_path,
                    expected_execution_ids=expected_review_execution_ids,
                    blocker_progress_execution_summary=execution_summary,
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-blocker-progress-execution-followup-summary":
        fixture_path = getattr(args, "fixture_path", None)
        execution_review_fixture_path = getattr(
            args,
            "execution_review_fixture_path",
            None,
        )
        execution_fixture_path = getattr(args, "execution_fixture_path", None)
        next_actions_fixture_path = getattr(args, "next_actions_fixture_path", None)
        progress_review_fixture_path = getattr(
            args,
            "progress_review_fixture_path",
            None,
        )
        progress_fixture_path = getattr(args, "progress_fixture_path", None)
        review_fixture_path = getattr(args, "review_fixture_path", None)
        db_path = getattr(args, "sqlite_log_path", None)
        blocker_detail = operations_blocker_detail_summary(sqlite_log_path=db_path)
        expected_detail_action_ids = [
            str(detail["action_id"])
            for detail in blocker_detail["details"]
            if isinstance(detail, dict)
        ]
        blocker_review = operations_blocker_review_summary(
            review_fixture_path,
            expected_action_ids=expected_detail_action_ids,
            blocker_detail_summary=blocker_detail,
        )
        blocker_followup = operations_blocker_followup_summary(
            review_fixture_path,
            blocker_detail_summary_data=blocker_detail,
            blocker_review_summary_data=blocker_review,
        )
        expected_action_ids = [
            str(action["action_id"])
            for action in blocker_followup["actions"]
            if isinstance(action, dict)
        ]
        progress_summary = operations_blocker_followup_progress_summary(
            progress_fixture_path,
            expected_action_ids=expected_action_ids,
            blocker_followup_summary=blocker_followup,
        )
        unresolved_action_ids = [
            str(record["action_id"])
            for record in progress_summary["records"]
            if isinstance(record, dict)
            and str(record.get("progress_status", "")) != "verified_local"
        ]
        progress_review_summary = operations_blocker_progress_review_summary(
            progress_review_fixture_path,
            expected_action_ids=unresolved_action_ids,
            blocker_followup_progress_summary=progress_summary,
        )
        expected_next_action_ids = [
            str(record["action_id"])
            for record in progress_review_summary["records"]
            if isinstance(record, dict)
        ]
        next_actions_summary = operations_blocker_progress_next_actions_summary(
            next_actions_fixture_path,
            expected_action_ids=expected_next_action_ids,
            blocker_progress_review_summary=progress_review_summary,
        )
        expected_execution_next_action_ids = [
            str(record["next_action_id"])
            for record in next_actions_summary["records"]
            if isinstance(record, dict)
        ]
        execution_summary = operations_blocker_progress_execution_summary(
            execution_fixture_path,
            expected_next_action_ids=expected_execution_next_action_ids,
            blocker_progress_next_actions_summary=next_actions_summary,
        )
        expected_review_execution_ids = [
            str(record["execution_id"])
            for record in execution_summary["records"]
            if isinstance(record, dict)
        ]
        execution_review_summary = operations_blocker_progress_execution_review_summary(
            execution_review_fixture_path,
            expected_execution_ids=expected_review_execution_ids,
            blocker_progress_execution_summary=execution_summary,
        )
        expected_followup_review_ids = [
            str(record["review_id"])
            for record in execution_review_summary["records"]
            if isinstance(record, dict)
        ]
        print(
            json.dumps(
                operations_blocker_progress_execution_followup_summary(
                    fixture_path,
                    expected_review_ids=expected_followup_review_ids,
                    blocker_progress_execution_review_summary=(
                        execution_review_summary
                    ),
                ),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operations-readiness-digest":
        db_path = getattr(args, "sqlite_log_path", None)
        ops_summary = operations_readiness_summary(sqlite_log_path=db_path)
        digest = operations_readiness_digest(ops_summary)
        if args.output_path is not None:
            args.output_path.parent.mkdir(parents=True, exist_ok=True)
            args.output_path.write_text(digest["markdown"], encoding="utf-8")
            output = {
                "ok": True,
                "path": str(args.output_path),
                "recommendation": digest["recommendation"],
            }
            print(json.dumps(output, indent=2, sort_keys=True), file=out)
        else:
            print(digest["markdown"], file=out)
        return 0

    if args.command == "baseline-confusion-matrix-summary":
        confusion_result = evaluate_baseline()
        confusion_output = {
            "schema_version": "baseline_eval_v0",
            "disclaimer": confusion_result["disclaimer"],
            "total_cases": confusion_result["total_cases"],
            "confusion_matrix": confusion_result["confusion_matrix"],
            "per_pathway_precision": confusion_result["per_pathway_precision"],
            "per_pathway_recall": confusion_result["per_pathway_recall"],
            "per_pathway_f1": confusion_result["per_pathway_f1"],
        }
        print(json.dumps(confusion_output, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "score-determinism-check":
        candidate_paths = getattr(args, "candidate_paths", None)
        runs = int(getattr(args, "runs", 3))
        if not candidate_paths:
            _default_examples = _default_example_candidates_dir()
            candidate_paths = sorted(_default_examples.glob("*.json"))
        results_det = []
        all_deterministic = True
        for cp in candidate_paths:
            det = score_determinism_check(Path(cp), runs=runs)
            results_det.append(det)
            if not det["deterministic"]:
                all_deterministic = False
        output_det = {
            "all_deterministic": all_deterministic,
            "runs_per_candidate": runs,
            "results": results_det,
        }
        print(json.dumps(output_det, indent=2, sort_keys=True), file=out)
        return 0 if all_deterministic else 1

    if args.command == "candidate-lifecycle-summary":
        fixture_path = getattr(args, "fixture_path", None)
        lifecycle = candidate_lifecycle_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(lifecycle, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "observation-schedule-summary":
        fixture_path = getattr(args, "fixture_path", None)
        schedule = observation_schedule_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(schedule, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "false-negative-summary":
        fixture_path = getattr(args, "fixture_path", None)
        fn_summary = false_negative_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(fn_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "scoring-config-summary":
        config_path = getattr(args, "config_path", None)
        sc_summary = scoring_config_summary(
            Path(config_path) if config_path else None
        )
        print(json.dumps(sc_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "route-coverage-summary":
        rc_summary = route_coverage_summary()
        print(json.dumps(rc_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "lifecycle-transition-summary":
        fixture_path = getattr(args, "fixture_path", None)
        lt_summary = lifecycle_transition_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(lt_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "observation-efficiency-summary":
        fixture_path = getattr(args, "fixture_path", None)
        oe_summary = observation_efficiency_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(oe_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "sensitivity-config-summary":
        config_path = getattr(args, "config_path", None)
        sens_summary = sensitivity_config_summary(
            Path(config_path) if config_path else None
        )
        print(json.dumps(sens_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "triage-summary":
        fixture_path = getattr(args, "fixture_path", None)
        tr_summary = triage_summary(
            Path(fixture_path) if fixture_path else None
        )
        print(json.dumps(tr_summary, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "artifacts-cleanup":
        if args.apply:
            cleanup_result = apply_artifact_cleanup(
                args.artifacts_dir,
                project_root=default_project_root(),
                acknowledge_local_apply=args.acknowledge_local_apply,
            )
        else:
            cleanup_result = plan_artifact_cleanup(
                args.artifacts_dir,
                project_root=default_project_root(),
            )
        print(json.dumps(cleanup_result, indent=2, sort_keys=True), file=out)
        return 0 if cleanup_result.get("ok", False) else 1

    if args.command == "signal-registry-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                signal_registry_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "signal-registry-track-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                signal_registry_track_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "schema-drift-check":
        from techno_search.schema_drift import detect_schema_drift

        print(
            json.dumps(detect_schema_drift(), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "audit-trail-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                audit_trail_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "observation-gap-analysis":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                observation_gap_analysis(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "multi-epoch-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                multi_epoch_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "classifier-rule-coverage":
        print(
            json.dumps(classifier_rule_coverage_summary(), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "target-recalibration-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                target_recalibration_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operator-coverage-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                operator_coverage_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "triage-label-completeness":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                triage_label_completeness_check(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "provenance-chain-validate":
        pc_result = provenance_chain_validator(
            report_dir=default_project_root() / "examples" / "reports",
        )
        print(json.dumps(pc_result, indent=2, sort_keys=True), file=out)
        return 0 if pc_result["ok"] else 1

    if args.command == "observation-notes-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                observation_notes_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "epoch-plan-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                epoch_plan_summary(Path(fixture_path) if fixture_path else None),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "aggregate-blockers-summary":
        print(
            json.dumps(
                aggregate_blockers_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "score-history-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                score_history_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operator-assignment-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                operator_assignment_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-health-summary":
        print(
            json.dumps(
                pipeline_health_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-flags-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                candidate_flags_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "review-deadlines-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                review_deadlines_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-throughput-summary":
        print(
            json.dumps(
                pipeline_throughput_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-retention-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                candidate_retention_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operator-performance-summary":
        print(
            json.dumps(
                operator_performance_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "track-comparison-summary":
        print(
            json.dumps(
                track_comparison_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-resolution-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                candidate_resolution_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "escalation-log-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                escalation_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "quality-control-summary":
        print(
            json.dumps(
                quality_control_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "observation-campaign-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                observation_campaign_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "data-quality-log-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                data_quality_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-audit-summary":
        print(
            json.dumps(
                pipeline_audit_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "follow-up-request-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                follow_up_request_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-bottleneck-summary":
        print(
            json.dumps(
                pipeline_bottleneck_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-annotation-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                candidate_annotation_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "session-log-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                session_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "priority-queue-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                priority_queue_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-capacity-summary":
        print(
            json.dumps(
                pipeline_capacity_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "feature-vector-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                feature_vector_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "model-registry-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                model_registry_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "ml-diagnostics-summary":
        print(
            json.dumps(
                ml_pipeline_diagnostics_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "feature-normalization-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                feature_normalization_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "feature-importance-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                feature_importance_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "ml-training-data-summary":
        print(
            json.dumps(
                ml_training_data_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "model-architecture-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                model_architecture_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "model-evaluation-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                model_evaluation_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "model-performance-history-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                model_performance_history_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "model-serving-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                model_serving_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "scoring-audit-log-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                scoring_audit_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "curated-dataset-intake-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                curated_dataset_intake_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-rescore-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                candidate_rescore_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operator-handoff-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                operator_handoff_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-methods-summary":
        print(
            json.dumps(
                candidate_methods_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-config-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                pipeline_config_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "submission-readiness-summary":
        fixture_path = Path(args.fixture_path) if args.fixture_path else None
        print(
            json.dumps(
                submission_readiness_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-integration-summary":
        print(
            json.dumps(
                pipeline_integration_summary(),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-alert-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_alert_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-replay-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                pipeline_replay_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "scoring-threshold-audit-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                scoring_threshold_audit_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "alert-resolution-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                alert_resolution_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "config-version-history-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                config_version_history_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "operator-escalation-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                operator_escalation_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-deduplication-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_deduplication_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "intake-queue-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                intake_queue_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "workflow-state-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                workflow_state_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "data-gap-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                data_gap_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-match-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_match_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-error-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                pipeline_error_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "observation-request-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                observation_request_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-export-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_export_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "quality-gate-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                quality_gate_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-comparison-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_comparison_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-telemetry-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                pipeline_telemetry_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "provenance-audit-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                provenance_audit_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "instrument-log-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                instrument_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "archival-query-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                archival_query_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-linkage-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_linkage_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "signal-classification-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                signal_classification_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "rfi-mitigation-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                rfi_mitigation_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-annotation-log-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_annotation_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "frequency-channel-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                frequency_channel_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "pipeline-checkpoint-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                pipeline_checkpoint_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    if args.command == "candidate-status-summary":
        fixture_path = getattr(args, "fixture_path", None)
        print(
            json.dumps(
                candidate_status_log_summary(fixture_path),
                indent=2,
                sort_keys=True,
            ),
            file=out,
        )
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def load_candidate_json(path: Path | str) -> Candidate:
    """Load a normalized synthetic candidate JSON file."""

    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    return candidate_from_mapping(data)


def score_batch(
    input_dir: Path | str,
    output_dir: Path | str,
    *,
    prefix: str = "",
    include_plot_artifacts: bool = True,
) -> Path:
    """Score all JSON candidate packets in a directory and write an aggregate manifest."""

    source_dir = Path(input_dir)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, object]] = []
    for candidate_path in sorted(source_dir.glob("*.json")):
        candidate = load_candidate_json(candidate_path)
        scored = score_candidate(candidate)
        report_prefix = f"{prefix}{candidate.candidate_id}" if prefix else candidate.candidate_id
        paths = write_candidate_reports(
            scored,
            destination,
            filename_prefix=report_prefix,
            include_plot_artifacts=include_plot_artifacts,
        )
        entries.append(
            {
                "candidate_id": candidate.candidate_id,
                "track": candidate.track.value,
                "recommended_pathway": scored.recommended_pathway.value,
                "config_version": str(
                    candidate.provenance.get("config_version", DEFAULT_SCORING_CONFIG_VERSION)
                ),
                "input_path": str(candidate_path),
                "markdown_path": str(paths.markdown_path),
                "json_path": str(paths.json_path),
                "manifest_path": str(paths.manifest_path),
                "plot_artifact_paths": [str(path) for path in paths.plot_artifact_paths],
            }
        )

    batch_manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "input_dir": str(source_dir),
        "output_dir": str(destination),
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "config_version": DEFAULT_SCORING_CONFIG_VERSION,
        "candidate_count": len(entries),
        "reports": entries,
    }
    manifest_path = destination / "batch_manifest.json"
    manifest_path.write_text(json.dumps(batch_manifest, indent=2, sort_keys=True) + "\n")
    return manifest_path


def schema_paths() -> dict[str, str]:
    """Return repository-local schema artifact paths."""

    schema_dir = Path(__file__).resolve().parents[2] / "schemas"
    return {
        schema_name: str(schema_dir / filename)
        for schema_name, filename in sorted(SCHEMA_FILENAMES.items())
    }


def default_score_regression_snapshot_path() -> Path:
    """Return the repository-local score regression snapshot path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "score_regressions.json"
    )


def score_regression_summary(snapshot_path: Path | None = None) -> dict[str, object]:
    """Summarize score regression snapshot coverage."""

    path = snapshot_path or default_score_regression_snapshot_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    candidates = data["candidates"]
    return {
        "snapshot_path": str(path),
        "candidate_count": len(candidates),
        "by_track": dict(
            sorted(Counter(candidate["track"] for candidate in candidates.values()).items())
        ),
        "by_recommended_pathway": dict(
            sorted(
                Counter(
                    candidate["recommended_pathway"] for candidate in candidates.values()
                ).items()
            )
        ),
        "candidate_ids": sorted(candidates),
    }


def default_project_root() -> Path:
    """Return the repository root."""

    return Path(__file__).resolve().parents[2]


def _default_example_candidates_dir() -> Path:
    return default_project_root() / "examples" / "candidates"


def regenerate_examples() -> dict[str, object]:
    """Regenerate committed example reports from example candidate JSON files."""

    candidate_dir = Path("examples/candidates")
    reports_dir = Path("examples/reports")
    batch_reports_dir = Path("examples/batch_reports")

    report_paths: list[str] = []
    for candidate_path in sorted(candidate_dir.glob("*.json")):
        candidate = load_candidate_json(candidate_path)
        scored = score_candidate(candidate)
        paths = write_candidate_reports(
            scored,
            reports_dir,
            filename_prefix=candidate.candidate_id,
        )
        report_paths.extend(
            [str(paths.markdown_path), str(paths.json_path), str(paths.manifest_path)]
        )
        report_paths.extend(str(path) for path in paths.plot_artifact_paths)

    batch_manifest_path = score_batch(candidate_dir, batch_reports_dir)
    return {
        "candidate_count": len(list(candidate_dir.glob("*.json"))),
        "reports_dir": str(reports_dir),
        "batch_reports_dir": str(batch_reports_dir),
        "report_paths": sorted(report_paths),
        "batch_manifest_path": str(batch_manifest_path),
    }


def validate_all() -> dict[str, object]:
    """Run local validation summaries that do not require network access."""

    root = default_project_root()
    candidate_results = {
        str(path): validate_candidate_file(path).as_dict()
        for path in sorted((root / "examples" / "candidates").glob("*.json"))
    }
    report_result = validate_report_directory(root / "examples" / "reports").as_dict()
    schemas = schema_paths()
    schema_results = {path: Path(path).exists() for path in schemas.values()}
    calibration = summarize_calibration_fixtures(load_calibration_fixtures()).as_dict()
    calibration_by_track = calibration_track_summary()
    calibration_track_count = calibration_by_track["track_count"]
    calibration_minimum_track_case_count = calibration_by_track["minimum_track_case_count"]
    false_positive_analysis = false_positive_class_summary()
    false_positive_case_count = false_positive_analysis["case_count"]
    false_positive_class_count = false_positive_analysis["class_count"]
    regression = score_regression_summary()
    tracked_paths = git_tracked_paths(root)
    catalog_cache = catalog_cache_validation_summary(tracked_paths, project_root=root)
    sqlite_commit_guard = validate_sqlite_log_commit_paths(
        tracked_paths,
        project_root=root,
    )
    provider_normalization = provider_normalization_regression_summary()
    provider_normalization_case_count = provider_normalization["case_count"]
    injection_recovery = injection_recovery_summary()
    injection_recovery_case_count = injection_recovery["case_count"]
    reliability = reliability_summary()
    reliability_bin_count = reliability["bin_count"]
    precision_recall = precision_recall_summary()
    precision_recall_case_count = precision_recall["case_count"]
    review_queue = review_queue_summary()
    review_queue_item_count = review_queue["item_count"]
    review_queue_note_count = review_queue["note_count"]
    consensus = consensus_summary()
    consensus_item_count = consensus["item_count"]
    consensus_decision_count = consensus["decision_count"]
    consensus_exports = consensus_export_summary()
    consensus_export_count = consensus_exports["export_count"]
    cross_track = cross_track_summary()
    cross_track_reference_count = cross_track["reference_count"]
    cross_track_blocking_issue_total = cross_track["blocking_issue_total"]
    reproducibility = verify_report_directory(root / "examples" / "reports")
    reproducibility_drift_count = reproducibility["drift_count"]
    reproducibility_verified_count = reproducibility["verified_count"]
    validation_datasets = validation_dataset_summary()
    validation_dataset_count = validation_datasets["dataset_count"]
    validation_dataset_case_count = validation_datasets["total_case_count"]
    validation_promotions = validation_promotion_summary()
    validation_promotion_rule_count = validation_promotions["rule_count"]
    validation_readiness = validation_readiness_summary()
    validation_readiness_record_count = validation_readiness["record_count"]
    validation_readiness_ready_count = validation_readiness["ready_count"]
    benchmark_metadata = benchmark_metadata_summary()
    benchmark_command_count = benchmark_metadata["command_count"]
    benchmark_worker_limit = benchmark_metadata["default_cpu_worker_limit"]
    benchmark_runs = benchmark_run_result_summary()
    benchmark_run_count = benchmark_runs["run_count"]
    benchmark_run_worker_limit = benchmark_runs["max_worker_count"]
    target_priorities = target_priority_summary()
    target_count = target_priorities["target_count"]
    background_ledger = background_search_ledger_summary()
    background_ledger_entry_count = background_ledger["entry_count"]
    background_review_workflow = background_review_workflow_summary()
    background_review_status_count = background_review_workflow[
        "reviewed_workflow_status_count"
    ]
    reviewed_log = background_reviewed_log_summary()
    reviewed_log_entry_count = reviewed_log["entry_count"]
    reviewed_log_network_count = reviewed_log["network_access_allowed_count"]
    needs_follow_up_log = background_needs_follow_up_summary()
    needs_follow_up_entry_count = needs_follow_up_log["entry_count"]
    needs_follow_up_approval_count = needs_follow_up_log[
        "submission_requires_user_approval_count"
    ]
    needs_follow_up_network_count = needs_follow_up_log["network_access_allowed_count"]
    follow_up_tests = background_follow_up_test_summary()
    follow_up_test_result_count = follow_up_tests["result_count"]
    follow_up_test_complete_count = follow_up_tests["complete_follow_up_test_set_count"]
    follow_up_test_network_count = follow_up_tests["network_access_allowed_count"]
    report_readiness = background_report_readiness_summary()
    draft_report_output_dir = root / "artifacts" / "validation_draft_reports"
    write_background_draft_follow_up_reports(draft_report_output_dir)
    draft_report_validation = validate_draft_report_directory(
        draft_report_output_dir
    ).as_dict()
    report_readiness_record_count = report_readiness["record_count"]
    report_readiness_ready_count = report_readiness["ready_to_draft_report_count"]
    report_readiness_approval_count = report_readiness["user_approval_required_count"]
    report_readiness_external_allowed_count = report_readiness[
        "external_submission_allowed_count"
    ]
    report_readiness_network_count = report_readiness["network_access_allowed_count"]
    draft_reports = background_draft_follow_up_report_summary(from_readiness=True)
    draft_report_count = draft_reports["draft_report_count"]
    draft_ready_count = draft_reports["draft_ready_count"]
    draft_external_allowed_count = draft_reports[
        "external_submission_allowed_count"
    ]
    draft_network_count = draft_reports["network_access_allowed_count"]
    user_decisions = background_user_decision_summary()
    user_decision_count = user_decisions["decision_count"]
    user_decision_external_approved_count = user_decisions[
        "external_submission_approved_count"
    ]
    user_decision_network_count = user_decisions["network_access_allowed_count"]
    baseline_eval = evaluate_baseline()
    baseline_pathway_accuracy = float(baseline_eval.get("pathway_accuracy", 0.0))
    baseline_total_cases = int(baseline_eval.get("total_cases", 0))
    _baseline_misclassified_count = int(baseline_eval.get("misclassified_count", 0))
    drift_result = baseline_pathway_drift_summary()
    baseline_drift_count = int(drift_result.get("drift_count", 0))
    baseline_drift_zero = bool(drift_result.get("zero_drift", True))
    watchlist = target_watchlist_summary()
    watchlist_entry_count = watchlist["entry_count"]
    watchlist_conflict_count = watchlist["conflict_count"]
    lifecycle = candidate_lifecycle_summary()
    lifecycle_entry_count = int(lifecycle.get("entry_count", 0))
    lifecycle_tracks_covered = list(lifecycle.get("tracks_covered", []))
    schedule = observation_schedule_summary()
    schedule_window_count = int(schedule.get("window_count", 0))
    fn_sum = false_negative_summary()
    _fn_rate = fn_sum.get("synthetic_missed_injection_rate")
    fn_missed_rate = float(_fn_rate) if isinstance(_fn_rate, (int, float)) else 1.0
    scoring_cfg = scoring_config_summary()
    scoring_threshold_count = int(scoring_cfg.get("threshold_count", 0))
    route_coverage = route_coverage_summary()
    route_covered_count = int(route_coverage.get("covered_pathway_count", 0))
    route_uncovered_count = int(route_coverage.get("uncovered_pathway_count", 0))
    lifecycle_transitions = lifecycle_transition_summary()
    lifecycle_invalid_count = int(lifecycle_transitions.get("invalid_transition_count", 0))
    observation_efficiency = observation_efficiency_summary()
    observation_completion_rate_raw = observation_efficiency.get("completion_rate")
    observation_completion_rate = (
        float(observation_completion_rate_raw)
        if isinstance(observation_completion_rate_raw, (int, float))
        else 0.0
    )
    sensitivity_cfg = sensitivity_config_summary()
    sensitivity_track_count = int(sensitivity_cfg.get("track_count", 0))
    triage_notes = triage_summary()
    triage_note_count = int(triage_notes.get("note_count", 0))
    triage_tracks_covered = list(triage_notes.get("tracks_covered", []))
    signal_registry = signal_registry_summary()
    signal_registry_active_count = int(signal_registry.get("active_count", 0))
    audit_trail = audit_trail_summary()
    audit_action_count = int(audit_trail.get("action_count", 0))
    multi_epoch = multi_epoch_summary()
    multi_epoch_target_count = int(multi_epoch.get("multi_epoch_target_count", 0))
    recalibration = target_recalibration_summary()
    recalibration_snapshot_count = int(recalibration.get("snapshot_count", 0))
    operator_coverage = operator_coverage_summary()
    operator_coverage_count = int(operator_coverage.get("operator_count", 0))
    label_completeness = triage_label_completeness_check()
    label_coverage_fraction_raw = label_completeness.get("coverage_fraction")
    label_coverage_fraction = (
        float(label_coverage_fraction_raw)
        if isinstance(label_coverage_fraction_raw, (int, float))
        else 0.0
    )
    rule_coverage = classifier_rule_coverage_summary()
    rule_coverage_fraction_raw = rule_coverage.get("coverage_fraction")
    classifier_rule_coverage_fraction = (
        float(rule_coverage_fraction_raw)
        if isinstance(rule_coverage_fraction_raw, (int, float))
        else 0.0
    )
    provenance_chain = provenance_chain_validator(
        report_dir=root / "examples" / "reports"
    )
    provenance_chain_ok = bool(provenance_chain.get("ok", False))
    obs_gap = observation_gap_analysis()
    from techno_search.schema_drift import detect_schema_drift

    schema_drift = detect_schema_drift()
    schema_drift_count = int(schema_drift.get("drift_count", 0))
    obs_notes = observation_notes_summary()
    obs_notes_count = int(obs_notes.get("note_count", 0))
    epoch_plan = epoch_plan_summary()
    epoch_plan_entry_count = int(epoch_plan.get("entry_count", 0))
    aggregate_blockers = aggregate_blockers_summary()
    aggregate_blocker_count = int(aggregate_blockers.get("total_blocker_count", 0))
    score_history = score_history_summary()
    score_history_entry_count = int(score_history.get("entry_count", 0))
    op_assignments = operator_assignment_summary()
    op_assignment_count = int(op_assignments.get("assignment_count", 0))
    pipeline_health = pipeline_health_summary()
    pipeline_total_blocked = int(pipeline_health.get("total_blocked_count", 0))
    candidate_flags = candidate_flags_summary()
    candidate_flag_count = int(candidate_flags.get("flag_count", 0))
    review_deadlines = review_deadlines_summary()
    review_deadline_count = int(review_deadlines.get("deadline_count", 0))
    pipeline_throughput = pipeline_throughput_summary()
    pipeline_throughput_rate = float(pipeline_throughput.get("throughput_rate", 0.0))
    candidate_retention = candidate_retention_summary()
    candidate_retention_record_count = int(candidate_retention.get("record_count", 0))
    operator_perf = operator_performance_summary()
    operator_perf_count = int(operator_perf.get("operator_count", 0))
    track_comparison = track_comparison_summary()
    track_comparison_open_flags = int(track_comparison.get("total_open_flags", 0))
    candidate_resolution = candidate_resolution_summary()
    candidate_resolution_record_count = int(candidate_resolution.get("record_count", 0))
    escalations = escalation_log_summary()
    escalation_entry_count = int(escalations.get("entry_count", 0))
    qc_summary = quality_control_summary()
    qc_health = str(qc_summary.get("overall_qc_health", "ok"))
    obs_campaigns = observation_campaign_summary()
    obs_campaign_count = int(obs_campaigns.get("campaign_count", 0))
    dq_log = data_quality_log_summary()
    dq_entry_count = int(dq_log.get("entry_count", 0))
    pipeline_audit = pipeline_audit_summary()
    pipeline_audit_action_count = int(pipeline_audit.get("total_audit_actions", 0))
    follow_up_reqs = follow_up_request_summary()
    follow_up_request_count = int(follow_up_reqs.get("request_count", 0))
    pipeline_bottleneck = pipeline_bottleneck_summary()
    pipeline_bottleneck_stalled = int(
        pipeline_bottleneck.get("total_stalled_candidates", 0)
    )
    candidate_annotations = candidate_annotation_summary()
    candidate_annotation_count = int(candidate_annotations.get("annotation_count", 0))
    session_log_data = session_log_summary()
    session_log_count = int(session_log_data.get("session_count", 0))
    priority_queue_data = priority_queue_summary()
    priority_queue_depth = int(priority_queue_data.get("queue_depth", 0))
    pipeline_capacity_data = pipeline_capacity_summary()
    pipeline_capacity_status = str(
        pipeline_capacity_data.get("capacity_status", "nominal")
    )
    feature_vector_data = feature_vector_summary()
    feature_vector_count = int(feature_vector_data.get("vector_count", 0))
    ml_registry_data = model_registry_summary()
    ml_registry_count = int(ml_registry_data.get("registry_count", 0))
    ml_diagnostics_data = ml_pipeline_diagnostics_summary()
    ml_pipeline_status = str(ml_diagnostics_data.get("pipeline_ml_status", "no_models"))
    feat_norm_data = feature_normalization_summary()
    feat_norm_count = int(feat_norm_data.get("bounds_count", 0))
    feat_imp_data = feature_importance_summary()
    feat_imp_count = int(feat_imp_data.get("entry_count", 0))
    ml_training_data = ml_training_data_summary()
    ml_training_case_count = int(ml_training_data.get("total_case_count", 0))
    arch_data = model_architecture_summary()
    arch_count = int(arch_data.get("architecture_count", 0))
    eval_data = model_evaluation_summary()
    eval_count = int(eval_data.get("evaluation_count", 0))
    perf_history_data = model_performance_history_summary()
    perf_snapshot_count = int(perf_history_data.get("snapshot_count", 0))
    serving_data = model_serving_summary()
    serving_record_count = int(serving_data.get("record_count", 0))
    audit_log_data = scoring_audit_log_summary()
    audit_entry_count = int(audit_log_data.get("entry_count", 0))
    intake_data = curated_dataset_intake_summary()
    intake_record_count = int(intake_data.get("record_count", 0))
    rescore_data = candidate_rescore_summary()
    rescore_event_count = int(rescore_data.get("event_count", 0))
    handoff_data = operator_handoff_summary()
    handoff_template_count = int(handoff_data.get("template_count", 0))
    handoff_approved_count = int(handoff_data.get("approved_count", 0))
    alert_data = candidate_alert_summary()
    alert_entry_count = int(alert_data.get("entry_count", 0))
    replay_data = pipeline_replay_summary()
    replay_entry_count = int(replay_data.get("entry_count", 0))
    threshold_audit_data = scoring_threshold_audit_summary()
    threshold_pass_count = int(threshold_audit_data.get("pass_count", 0))
    alert_resolution_data = alert_resolution_summary()
    alert_resolution_entry_count = int(alert_resolution_data.get("entry_count", 0))
    config_history_data = config_version_history_summary()
    config_history_entry_count = int(config_history_data.get("entry_count", 0))
    escalation_data = operator_escalation_summary()
    operator_escalation_entry_count = int(escalation_data.get("entry_count", 0))
    dedup_data = candidate_deduplication_summary()
    dedup_entry_count = int(dedup_data.get("entry_count", 0))
    intake_queue_data = intake_queue_summary()
    intake_queue_entry_count = int(intake_queue_data.get("entry_count", 0))
    workflow_data = workflow_state_summary()
    workflow_entry_count = int(workflow_data.get("entry_count", 0))
    data_gap_data = data_gap_summary()
    data_gap_entry_count = int(data_gap_data.get("entry_count", 0))
    candidate_match_data = candidate_match_summary()
    candidate_match_entry_count = int(candidate_match_data.get("entry_count", 0))
    pipeline_error_data = pipeline_error_summary()
    pipeline_error_entry_count = int(pipeline_error_data.get("entry_count", 0))
    obs_request_data = observation_request_summary()
    obs_request_entry_count = int(obs_request_data.get("entry_count", 0))
    candidate_export_data = candidate_export_summary()
    candidate_export_entry_count = int(candidate_export_data.get("entry_count", 0))
    quality_gate_data = quality_gate_summary()
    quality_gate_entry_count = int(quality_gate_data.get("entry_count", 0))
    quality_gate_pass_count = int(quality_gate_data.get("pass_count", 0))
    instrument_log_data = instrument_log_summary()
    instrument_log_entry_count = instrument_log_data.get("entry_count", 0)
    archival_query_data = archival_query_summary()
    archival_query_entry_count = archival_query_data.get("entry_count", 0)
    candidate_linkage_data = candidate_linkage_summary()
    candidate_linkage_entry_count = int(candidate_linkage_data.get("entry_count", 0))
    _candidate_linkage_confirmed_count = int(candidate_linkage_data.get("confirmed_count", 0))
    signal_classification_data = signal_classification_summary()
    signal_classification_entry_count = int(signal_classification_data.get("entry_count", 0))
    _signal_classification_classified_count = int(
        signal_classification_data.get("classified_count", 0)
    )
    rfi_mitigation_data = rfi_mitigation_summary()
    rfi_mitigation_entry_count = int(rfi_mitigation_data.get("entry_count", 0))
    _rfi_mitigation_flagged_count = int(rfi_mitigation_data.get("flagged_count", 0))
    candidate_annotation_log_data = candidate_annotation_log_summary()
    candidate_annotation_entry_count = int(
        candidate_annotation_log_data.get("entry_count", 0)
    )
    _candidate_annotation_active_count = int(
        candidate_annotation_log_data.get("active_count", 0)
    )
    frequency_channel_data = frequency_channel_log_summary()
    frequency_channel_entry_count = int(frequency_channel_data.get("entry_count", 0))
    _frequency_channel_active_count = int(frequency_channel_data.get("active_count", 0))
    pipeline_checkpoint_data = pipeline_checkpoint_log_summary()
    pipeline_checkpoint_entry_count = int(
        pipeline_checkpoint_data.get("entry_count", 0)
    )
    _pipeline_checkpoint_saved_count = int(
        pipeline_checkpoint_data.get("saved_count", 0)
    )
    candidate_status_log_data = candidate_status_log_summary()
    candidate_status_entry_count = int(candidate_status_log_data.get("entry_count", 0))
    _candidate_status_active_count = int(
        candidate_status_log_data.get("active_count", 0)
    )
    comparison_data = candidate_comparison_summary()
    comparison_count = int(comparison_data.get("record_count", 0))
    telemetry_data = pipeline_telemetry_summary()
    telemetry_entry_count = int(telemetry_data.get("entry_count", 0))
    audit_data = provenance_audit_summary()
    provenance_audit_entry_count = int(audit_data.get("entry_count", 0))
    pipeline_cfg_data = pipeline_config_summary()
    pipeline_config_count = int(pipeline_cfg_data.get("config_count", 0))
    pipeline_active_count = int(pipeline_cfg_data.get("active_count", 0))
    submission_data = submission_readiness_summary()
    submission_record_count = int(submission_data.get("record_count", 0))
    candidate_handoffs = candidate_extraction_handoff_summary()
    candidate_handoff_record_count = candidate_handoffs["record_count"]
    candidate_handoff_network_count = candidate_handoffs[
        "network_access_allowed_count"
    ]
    sqlite_validation_db = root / "logs" / "validation.sqlite3"
    sqlite_validation_artifact_dir = root / "artifacts" / "validation_sqlite_logs"
    sqlite_validation_run_id = (
        "validation-sqlite-" + datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    )
    run_local_background_search_once(
        sqlite_validation_artifact_dir / "background_search_ledger.json",
        reviewed_log_path=sqlite_validation_artifact_dir / "background_reviewed_log.json",
        needs_follow_up_log_path=(
            sqlite_validation_artifact_dir / "background_needs_follow_up_log.json"
        ),
        sqlite_log_path=sqlite_validation_db,
        run_id=sqlite_validation_run_id,
        code_commit="validation-local",
        opt_in=True,
    )
    sqlite_logs = sqlite_log_summary(sqlite_validation_db)
    sqlite_integrity = sqlite_log_integrity_summary(sqlite_validation_db)
    sqlite_migration = sqlite_log_migration_summary(sqlite_validation_db)
    sqlite_migration_plan = sqlite_log_migration_plan(sqlite_validation_db)
    sqlite_weekly_digest = sqlite_log_weekly_digest(sqlite_validation_db)
    sqlite_export = sqlite_log_export(sqlite_validation_db, limit=3)
    sqlite_backup = sqlite_log_backup(sqlite_validation_db)
    sqlite_retention = sqlite_log_retention_summary(sqlite_validation_db)
    sqlite_pragmas = sqlite_log_pragmas(sqlite_validation_db)
    sqlite_export_summary = sqlite_export.get("summary", {})
    sqlite_export_ok = (
        bool(sqlite_export_summary.get("ok"))
        if isinstance(sqlite_export_summary, dict)
        else False
    )
    sqlite_log_validation = validate_sqlite_log_database(sqlite_validation_db).as_dict()
    sqlite_run_count = sqlite_logs["run_count"]
    sqlite_outcome_count = sqlite_logs["outcome_count"]
    sqlite_network_count = sqlite_logs["network_access_allowed_count"]
    sqlite_external_approved_count = sqlite_logs["external_submission_approved_count"]
    operations_readiness = operations_readiness_summary(
        quality_control=qc_summary,
        pipeline_capacity=pipeline_capacity_data,
        candidate_alerts=alert_data,
        review_deadlines=review_deadlines,
        pipeline_health=pipeline_health,
        route_coverage=route_coverage,
        validation_readiness=validation_readiness,
        curated_intake=intake_data,
        submission_readiness=submission_data,
        user_decisions=user_decisions,
        sqlite_logs=sqlite_logs,
        sqlite_integrity=sqlite_integrity,
        sqlite_weekly_digest=sqlite_weekly_digest,
        sqlite_log_path=sqlite_validation_db,
    )
    operations_action_plan = operations_action_plan_summary(operations_readiness)
    operations_action_ids = [
        str(action["action_id"])
        for action in operations_action_plan["actions"]
        if isinstance(action, dict)
    ]
    operations_action_resolution = operations_action_resolution_summary(
        expected_action_ids=operations_action_ids,
    )
    operations_blocker_detail = operations_blocker_detail_summary(
        readiness_summary=operations_readiness,
        action_plan_summary=operations_action_plan,
    )
    operations_blocker_review = operations_blocker_review_summary(
        expected_action_ids=operations_action_ids,
        blocker_detail_summary=operations_blocker_detail,
    )
    operations_blocker_followup = operations_blocker_followup_summary(
        blocker_detail_summary_data=operations_blocker_detail,
        blocker_review_summary_data=operations_blocker_review,
    )
    operations_followup_action_ids = [
        str(action["action_id"])
        for action in operations_blocker_followup["actions"]
        if isinstance(action, dict)
    ]
    operations_blocker_followup_progress = operations_blocker_followup_progress_summary(
        expected_action_ids=operations_followup_action_ids,
        blocker_followup_summary=operations_blocker_followup,
    )
    operations_unresolved_progress_action_ids = [
        str(record["action_id"])
        for record in operations_blocker_followup_progress["records"]
        if isinstance(record, dict)
        and str(record.get("progress_status", "")) != "verified_local"
    ]
    operations_blocker_progress_review = operations_blocker_progress_review_summary(
        expected_action_ids=operations_unresolved_progress_action_ids,
        blocker_followup_progress_summary=operations_blocker_followup_progress,
    )
    operations_progress_review_action_ids = [
        str(record["action_id"])
        for record in operations_blocker_progress_review["records"]
        if isinstance(record, dict)
    ]
    operations_blocker_progress_next_actions = (
        operations_blocker_progress_next_actions_summary(
            expected_action_ids=operations_progress_review_action_ids,
            blocker_progress_review_summary=operations_blocker_progress_review,
        )
    )
    operations_progress_next_action_ids = [
        str(record["next_action_id"])
        for record in operations_blocker_progress_next_actions["records"]
        if isinstance(record, dict)
    ]
    operations_blocker_progress_execution = (
        operations_blocker_progress_execution_summary(
            expected_next_action_ids=operations_progress_next_action_ids,
            blocker_progress_next_actions_summary=(
                operations_blocker_progress_next_actions
            ),
        )
    )
    operations_progress_execution_ids = [
        str(record["execution_id"])
        for record in operations_blocker_progress_execution["records"]
        if isinstance(record, dict)
    ]
    operations_blocker_progress_execution_review = (
        operations_blocker_progress_execution_review_summary(
            expected_execution_ids=operations_progress_execution_ids,
            blocker_progress_execution_summary=(
                operations_blocker_progress_execution
            ),
        )
    )
    operations_progress_execution_review_ids = [
        str(record["review_id"])
        for record in operations_blocker_progress_execution_review["records"]
        if isinstance(record, dict)
    ]
    operations_blocker_progress_execution_followup = (
        operations_blocker_progress_execution_followup_summary(
            expected_review_ids=operations_progress_execution_review_ids,
            blocker_progress_execution_review_summary=(
                operations_blocker_progress_execution_review
            ),
        )
    )
    action_resolution_record_count = int(
        operations_action_resolution["record_count"]
    )
    action_resolution_live_authorized_count = int(
        operations_action_resolution["live_data_authorized_count"]
    )
    action_resolution_external_authorized_count = int(
        operations_action_resolution["external_submission_authorized_count"]
    )
    action_resolution_coverage_complete = bool(
        operations_action_resolution["coverage_complete"]
    )
    blocker_detail_count = int(operations_blocker_detail["detail_count"])
    blocker_detail_network_count = int(
        operations_blocker_detail["network_access_allowed_count"]
    )
    blocker_detail_external_count = int(
        operations_blocker_detail["external_submission_approved_count"]
    )
    blocker_review_record_count = int(operations_blocker_review["record_count"])
    blocker_review_live_authorized_count = int(
        operations_blocker_review["live_data_authorized_count"]
    )
    blocker_review_external_authorized_count = int(
        operations_blocker_review["external_submission_authorized_count"]
    )
    blocker_review_coverage_complete = bool(
        operations_blocker_review["coverage_complete"]
    )
    blocker_review_all_detail_evidence_reviewed = bool(
        operations_blocker_review["all_detail_evidence_reviewed"]
    )
    blocker_followup_action_count = int(operations_blocker_followup["action_count"])
    blocker_followup_live_authorized_count = int(
        operations_blocker_followup["live_data_authorized_count"]
    )
    blocker_followup_external_authorized_count = int(
        operations_blocker_followup["external_submission_authorized_count"]
    )
    blocker_followup_coverage_complete = bool(
        operations_blocker_followup["coverage_complete"]
    )
    blocker_followup_all_detail_evidence_reviewed = bool(
        operations_blocker_followup["all_detail_evidence_reviewed"]
    )
    blocker_followup_residual_blocker_total = int(
        operations_blocker_followup["residual_blocker_total"]
    )
    blocker_progress_record_count = int(
        operations_blocker_followup_progress["record_count"]
    )
    blocker_progress_live_authorized_count = int(
        operations_blocker_followup_progress["live_data_authorized_count"]
    )
    blocker_progress_external_authorized_count = int(
        operations_blocker_followup_progress["external_submission_authorized_count"]
    )
    blocker_progress_coverage_complete = bool(
        operations_blocker_followup_progress["coverage_complete"]
    )
    blocker_progress_recommendation_mismatch_count = int(
        operations_blocker_followup_progress["recommendation_mismatch_count"]
    )
    blocker_progress_review_record_count = int(
        operations_blocker_progress_review["record_count"]
    )
    blocker_progress_review_live_authorized_count = int(
        operations_blocker_progress_review["live_data_authorized_count"]
    )
    blocker_progress_review_external_authorized_count = int(
        operations_blocker_progress_review["external_submission_authorized_count"]
    )
    blocker_progress_review_coverage_complete = bool(
        operations_blocker_progress_review["coverage_complete"]
    )
    blocker_progress_review_status_mismatch_count = int(
        operations_blocker_progress_review["status_mismatch_count"]
    )
    blocker_progress_review_residual_blocker_total = int(
        operations_blocker_progress_review["residual_blocker_total"]
    )
    blocker_progress_next_action_record_count = int(
        operations_blocker_progress_next_actions["record_count"]
    )
    blocker_progress_next_action_live_authorized_count = int(
        operations_blocker_progress_next_actions["live_data_authorized_count"]
    )
    blocker_progress_next_action_external_authorized_count = int(
        operations_blocker_progress_next_actions["external_submission_authorized_count"]
    )
    blocker_progress_next_action_coverage_complete = bool(
        operations_blocker_progress_next_actions["coverage_complete"]
    )
    blocker_progress_next_action_status_mismatch_count = int(
        operations_blocker_progress_next_actions["status_mismatch_count"]
    )
    blocker_progress_next_action_residual_blocker_total = int(
        operations_blocker_progress_next_actions["residual_blocker_total"]
    )
    blocker_progress_next_action_priority_sequence_ok = bool(
        operations_blocker_progress_next_actions["priority_sequence_ok"]
    )
    blocker_progress_execution_record_count = int(
        operations_blocker_progress_execution["record_count"]
    )
    blocker_progress_execution_live_authorized_count = int(
        operations_blocker_progress_execution["live_data_authorized_count"]
    )
    blocker_progress_execution_external_authorized_count = int(
        operations_blocker_progress_execution["external_submission_authorized_count"]
    )
    blocker_progress_execution_coverage_complete = bool(
        operations_blocker_progress_execution["coverage_complete"]
    )
    blocker_progress_execution_status_mismatch_count = int(
        operations_blocker_progress_execution["status_mismatch_count"]
    )
    blocker_progress_execution_residual_mismatch_count = int(
        operations_blocker_progress_execution["residual_mismatch_count"]
    )
    blocker_progress_execution_priority_mismatch_count = int(
        operations_blocker_progress_execution["priority_mismatch_count"]
    )
    blocker_progress_execution_residual_blocker_total = int(
        operations_blocker_progress_execution["residual_blocker_total"]
    )
    blocker_progress_execution_priority_sequence_ok = bool(
        operations_blocker_progress_execution["priority_sequence_ok"]
    )
    blocker_progress_execution_review_record_count = int(
        operations_blocker_progress_execution_review["record_count"]
    )
    blocker_progress_execution_review_live_authorized_count = int(
        operations_blocker_progress_execution_review["live_data_authorized_count"]
    )
    blocker_progress_execution_review_external_authorized_count = int(
        operations_blocker_progress_execution_review[
            "external_submission_authorized_count"
        ]
    )
    blocker_progress_execution_review_coverage_complete = bool(
        operations_blocker_progress_execution_review["coverage_complete"]
    )
    blocker_progress_execution_review_status_mismatch_count = int(
        operations_blocker_progress_execution_review["status_mismatch_count"]
    )
    blocker_progress_execution_review_residual_mismatch_count = int(
        operations_blocker_progress_execution_review["residual_mismatch_count"]
    )
    blocker_progress_execution_review_priority_mismatch_count = int(
        operations_blocker_progress_execution_review["priority_mismatch_count"]
    )
    blocker_progress_execution_review_residual_blocker_total = int(
        operations_blocker_progress_execution_review["residual_blocker_total"]
    )
    blocker_progress_execution_review_priority_sequence_ok = bool(
        operations_blocker_progress_execution_review["priority_sequence_ok"]
    )
    blocker_progress_execution_followup_record_count = int(
        operations_blocker_progress_execution_followup["record_count"]
    )
    blocker_progress_execution_followup_live_authorized_count = int(
        operations_blocker_progress_execution_followup["live_data_authorized_count"]
    )
    blocker_progress_execution_followup_external_authorized_count = int(
        operations_blocker_progress_execution_followup[
            "external_submission_authorized_count"
        ]
    )
    blocker_progress_execution_followup_coverage_complete = bool(
        operations_blocker_progress_execution_followup["coverage_complete"]
    )
    blocker_progress_execution_followup_status_mismatch_count = int(
        operations_blocker_progress_execution_followup["status_mismatch_count"]
    )
    blocker_progress_execution_followup_residual_mismatch_count = int(
        operations_blocker_progress_execution_followup["residual_mismatch_count"]
    )
    blocker_progress_execution_followup_priority_mismatch_count = int(
        operations_blocker_progress_execution_followup["priority_mismatch_count"]
    )
    blocker_progress_execution_followup_residual_blocker_total = int(
        operations_blocker_progress_execution_followup["residual_blocker_total"]
    )
    blocker_progress_execution_followup_priority_sequence_ok = bool(
        operations_blocker_progress_execution_followup["priority_sequence_ok"]
    )

    ok = (
        all(result["ok"] for result in candidate_results.values())
        and bool(report_result["ok"])
        and all(schema_results.values())
        and bool(catalog_cache["ok"])
        and bool(sqlite_commit_guard["ok"])
        and isinstance(calibration_track_count, int)
        and calibration_track_count >= 3
        and isinstance(calibration_minimum_track_case_count, int)
        and calibration_minimum_track_case_count >= 4
        and isinstance(false_positive_case_count, int)
        and false_positive_case_count >= 15
        and isinstance(false_positive_class_count, int)
        and false_positive_class_count >= 15
        and isinstance(provider_normalization_case_count, int)
        and provider_normalization_case_count >= 5
        and isinstance(injection_recovery_case_count, int)
        and injection_recovery_case_count >= 6
        and isinstance(reliability_bin_count, int)
        and reliability_bin_count >= 9
        and isinstance(precision_recall_case_count, int)
        and precision_recall_case_count >= 6
        and isinstance(review_queue_item_count, int)
        and review_queue_item_count >= 5
        and isinstance(review_queue_note_count, int)
        and review_queue_note_count >= 4
        and isinstance(consensus_item_count, int)
        and consensus_item_count >= 5
        and isinstance(consensus_decision_count, int)
        and consensus_decision_count >= 10
        and isinstance(consensus_export_count, int)
        and consensus_export_count >= 5
        and isinstance(cross_track_reference_count, int)
        and cross_track_reference_count >= 4
        and isinstance(cross_track_blocking_issue_total, int)
        and cross_track_blocking_issue_total >= 0
        and isinstance(reproducibility_verified_count, int)
        and reproducibility_verified_count >= 3
        and isinstance(reproducibility_drift_count, int)
        and reproducibility_drift_count == 0
        and isinstance(validation_dataset_count, int)
        and validation_dataset_count >= 3
        and isinstance(validation_dataset_case_count, int)
        and validation_dataset_case_count >= 15
        and isinstance(validation_promotion_rule_count, int)
        and validation_promotion_rule_count >= 3
        and isinstance(validation_readiness_record_count, int)
        and validation_readiness_record_count >= 3
        and isinstance(validation_readiness_ready_count, int)
        and validation_readiness_ready_count >= 1
        and isinstance(benchmark_command_count, int)
        and benchmark_command_count >= 4
        and isinstance(benchmark_worker_limit, int)
        and benchmark_worker_limit <= 12
        and isinstance(benchmark_run_count, int)
        and benchmark_run_count >= 3
        and isinstance(benchmark_run_worker_limit, int)
        and benchmark_run_worker_limit <= 12
        and isinstance(target_count, int)
        and target_count >= 3
        and isinstance(background_ledger_entry_count, int)
        and background_ledger_entry_count >= 4
        and isinstance(background_review_status_count, int)
        and background_review_status_count >= 4
        and isinstance(reviewed_log_entry_count, int)
        and reviewed_log_entry_count >= 2
        and isinstance(reviewed_log_network_count, int)
        and reviewed_log_network_count == 0
        and isinstance(needs_follow_up_entry_count, int)
        and needs_follow_up_entry_count >= 2
        and isinstance(needs_follow_up_approval_count, int)
        and needs_follow_up_approval_count == needs_follow_up_entry_count
        and isinstance(needs_follow_up_network_count, int)
        and needs_follow_up_network_count == 0
        and isinstance(follow_up_test_result_count, int)
        and follow_up_test_result_count >= 12
        and isinstance(follow_up_test_complete_count, int)
        and follow_up_test_complete_count >= 2
        and isinstance(follow_up_test_network_count, int)
        and follow_up_test_network_count == 0
        and isinstance(report_readiness_record_count, int)
        and report_readiness_record_count >= 2
        and isinstance(report_readiness_ready_count, int)
        and report_readiness_ready_count >= 1
        and isinstance(report_readiness_approval_count, int)
        and report_readiness_approval_count == report_readiness_record_count
        and isinstance(report_readiness_external_allowed_count, int)
        and report_readiness_external_allowed_count == 0
        and isinstance(report_readiness_network_count, int)
        and report_readiness_network_count == 0
        and bool(draft_report_validation["ok"])
        and isinstance(draft_report_count, int)
        and draft_report_count >= 2
        and isinstance(draft_ready_count, int)
        and draft_ready_count >= 1
        and isinstance(draft_external_allowed_count, int)
        and draft_external_allowed_count == 0
        and isinstance(draft_network_count, int)
        and draft_network_count == 0
        and isinstance(user_decision_count, int)
        and user_decision_count >= 3
        and isinstance(user_decision_external_approved_count, int)
        and user_decision_external_approved_count == 0
        and isinstance(user_decision_network_count, int)
        and user_decision_network_count == 0
        and isinstance(candidate_handoff_record_count, int)
        and candidate_handoff_record_count >= 4
        and isinstance(candidate_handoff_network_count, int)
        and candidate_handoff_network_count == 0
        and bool(sqlite_log_validation["ok"])
        and bool(sqlite_integrity["ok"])
        and not bool(sqlite_migration["migration_required"])
        and sqlite_export_ok
        and bool(sqlite_backup["ok"])
        and bool(sqlite_retention["ok"])
        and bool(sqlite_pragmas["ok"])
        and bool(sqlite_weekly_digest["ok"])
        and not bool(sqlite_migration_plan["migration_required"])
        and isinstance(sqlite_run_count, int)
        and sqlite_run_count >= 1
        and sqlite_outcome_count == sqlite_run_count
        and isinstance(sqlite_network_count, int)
        and sqlite_network_count == 0
        and isinstance(sqlite_external_approved_count, int)
        and sqlite_external_approved_count == 0
        and isinstance(watchlist_entry_count, int)
        and watchlist_entry_count >= 4
        and isinstance(watchlist_conflict_count, int)
        and watchlist_conflict_count == 0
        and isinstance(baseline_pathway_accuracy, float)
        and baseline_pathway_accuracy >= 0.80
        and isinstance(baseline_total_cases, int)
        and baseline_total_cases >= 3
        and isinstance(baseline_drift_count, int)
        and baseline_drift_zero
        and isinstance(lifecycle_entry_count, int)
        and lifecycle_entry_count >= 3
        and len(lifecycle_tracks_covered) >= 3
        and isinstance(schedule_window_count, int)
        and schedule_window_count >= 4
        and isinstance(fn_missed_rate, float)
        and fn_missed_rate < 1.0
        and isinstance(scoring_threshold_count, int)
        and scoring_threshold_count >= 1
        and isinstance(route_covered_count, int)
        and route_covered_count >= 6
        and isinstance(route_uncovered_count, int)
        and route_uncovered_count == 0
        and isinstance(lifecycle_invalid_count, int)
        and lifecycle_invalid_count == 0
        and isinstance(observation_completion_rate, float)
        and observation_completion_rate >= 0.0
        and isinstance(sensitivity_track_count, int)
        and sensitivity_track_count >= 3
        and isinstance(triage_note_count, int)
        and triage_note_count >= 5
        and len(triage_tracks_covered) >= 3
        and isinstance(signal_registry_active_count, int)
        and signal_registry_active_count >= 4
        and isinstance(audit_action_count, int)
        and audit_action_count >= 6
        and isinstance(multi_epoch_target_count, int)
        and multi_epoch_target_count >= 3
        and isinstance(recalibration_snapshot_count, int)
        and recalibration_snapshot_count >= 2
        and isinstance(operator_coverage_count, int)
        and operator_coverage_count >= 2
        and isinstance(label_coverage_fraction, float)
        and label_coverage_fraction >= 0.5
        and isinstance(classifier_rule_coverage_fraction, float)
        and classifier_rule_coverage_fraction >= 0.5
        and provenance_chain_ok
        and isinstance(schema_drift_count, int)
        and schema_drift_count == 0
        and isinstance(obs_notes_count, int)
        and obs_notes_count >= 5
        and isinstance(epoch_plan_entry_count, int)
        and epoch_plan_entry_count >= 4
        and isinstance(aggregate_blocker_count, int)
        and aggregate_blocker_count >= 0
        and isinstance(score_history_entry_count, int)
        and score_history_entry_count >= 5
        and isinstance(op_assignment_count, int)
        and op_assignment_count >= 4
        and isinstance(pipeline_total_blocked, int)
        and pipeline_total_blocked >= 0
        and isinstance(candidate_flag_count, int)
        and candidate_flag_count >= 5
        and isinstance(review_deadline_count, int)
        and review_deadline_count >= 4
        and isinstance(pipeline_throughput_rate, float)
        and pipeline_throughput_rate >= 0.0
        and isinstance(candidate_retention_record_count, int)
        and candidate_retention_record_count >= 5
        and isinstance(operator_perf_count, int)
        and operator_perf_count >= 2
        and isinstance(track_comparison_open_flags, int)
        and track_comparison_open_flags >= 0
        and isinstance(candidate_resolution_record_count, int)
        and candidate_resolution_record_count >= 5
        and isinstance(escalation_entry_count, int)
        and escalation_entry_count >= 5
        and qc_health in ("ok", "degraded", "blocked")
        and isinstance(obs_campaign_count, int)
        and obs_campaign_count >= 5
        and isinstance(dq_entry_count, int)
        and dq_entry_count >= 5
        and isinstance(pipeline_audit_action_count, int)
        and pipeline_audit_action_count >= 0
        and isinstance(follow_up_request_count, int)
        and follow_up_request_count >= 5
        and isinstance(pipeline_bottleneck_stalled, int)
        and pipeline_bottleneck_stalled >= 0
        and isinstance(candidate_annotation_count, int)
        and candidate_annotation_count >= 5
        and isinstance(session_log_count, int)
        and session_log_count >= 5
        and isinstance(priority_queue_depth, int)
        and priority_queue_depth >= 5
        and pipeline_capacity_status in {"nominal", "strained", "overloaded"}
        and isinstance(feature_vector_count, int)
        and feature_vector_count >= 5
        and isinstance(ml_registry_count, int)
        and ml_registry_count >= 0
        and ml_pipeline_status in {"no_models", "all_above_baseline", "some_below_baseline"}
        and isinstance(feat_norm_count, int)
        and feat_norm_count >= 3
        and isinstance(feat_imp_count, int)
        and feat_imp_count >= 6
        and isinstance(ml_training_case_count, int)
        and ml_training_case_count >= 0
        and isinstance(arch_count, int)
        and arch_count >= 5
        and isinstance(eval_count, int)
        and eval_count >= 4
        and isinstance(perf_snapshot_count, int)
        and perf_snapshot_count >= 5
        and isinstance(serving_record_count, int)
        and serving_record_count >= 1
        and isinstance(audit_entry_count, int)
        and audit_entry_count >= 1
        and isinstance(intake_record_count, int)
        and intake_record_count >= 1
        and isinstance(rescore_event_count, int)
        and rescore_event_count >= 1
        and isinstance(handoff_template_count, int)
        and handoff_template_count >= 1
        and isinstance(handoff_approved_count, int)
        and handoff_approved_count >= 1
        and isinstance(pipeline_config_count, int)
        and pipeline_config_count >= 1
        and isinstance(pipeline_active_count, int)
        and pipeline_active_count >= 1
        and isinstance(submission_record_count, int)
        and submission_record_count >= 1
        and isinstance(comparison_count, int)
        and comparison_count >= 1
        and isinstance(telemetry_entry_count, int)
        and telemetry_entry_count >= 1
        and isinstance(provenance_audit_entry_count, int)
        and provenance_audit_entry_count >= 1
        and isinstance(alert_entry_count, int)
        and alert_entry_count >= 1
        and isinstance(replay_entry_count, int)
        and replay_entry_count >= 1
        and isinstance(threshold_pass_count, int)
        and threshold_pass_count >= 1
        and isinstance(alert_resolution_entry_count, int)
        and alert_resolution_entry_count >= 1
        and isinstance(config_history_entry_count, int)
        and config_history_entry_count >= 1
        and isinstance(operator_escalation_entry_count, int)
        and operator_escalation_entry_count >= 1
        and isinstance(dedup_entry_count, int)
        and dedup_entry_count >= 1
        and isinstance(intake_queue_entry_count, int)
        and intake_queue_entry_count >= 1
        and isinstance(workflow_entry_count, int)
        and workflow_entry_count >= 1
        and isinstance(data_gap_entry_count, int)
        and data_gap_entry_count >= 1
        and isinstance(candidate_match_entry_count, int)
        and candidate_match_entry_count >= 1
        and isinstance(pipeline_error_entry_count, int)
        and pipeline_error_entry_count >= 1
        and isinstance(obs_request_entry_count, int)
        and obs_request_entry_count >= 1
        and isinstance(candidate_export_entry_count, int)
        and candidate_export_entry_count >= 1
        and isinstance(quality_gate_entry_count, int)
        and quality_gate_entry_count >= 1
        and quality_gate_pass_count >= 1
        and instrument_log_entry_count >= 1
        and archival_query_entry_count >= 1
        and candidate_linkage_entry_count >= 1
        and isinstance(signal_classification_entry_count, int)
        and signal_classification_entry_count >= 1
        and isinstance(rfi_mitigation_entry_count, int)
        and rfi_mitigation_entry_count >= 1
        and isinstance(candidate_annotation_entry_count, int)
        and candidate_annotation_entry_count >= 1
        and isinstance(frequency_channel_entry_count, int)
        and frequency_channel_entry_count >= 1
        and isinstance(pipeline_checkpoint_entry_count, int)
        and pipeline_checkpoint_entry_count >= 1
        and isinstance(candidate_status_entry_count, int)
        and candidate_status_entry_count >= 1
        and action_resolution_record_count >= 1
        and action_resolution_live_authorized_count == 0
        and action_resolution_external_authorized_count == 0
        and action_resolution_coverage_complete
        and blocker_detail_count == len(operations_action_ids)
        and blocker_detail_network_count == 0
        and blocker_detail_external_count == 0
        and blocker_review_record_count >= 1
        and blocker_review_live_authorized_count == 0
        and blocker_review_external_authorized_count == 0
        and blocker_review_coverage_complete
        and blocker_review_all_detail_evidence_reviewed
        and blocker_followup_action_count == blocker_review_record_count
        and blocker_followup_live_authorized_count == 0
        and blocker_followup_external_authorized_count == 0
        and blocker_followup_coverage_complete
        and blocker_followup_all_detail_evidence_reviewed
        and (
            blocker_followup_residual_blocker_total
            == int(operations_blocker_review["residual_blocker_total"])
        )
        and blocker_progress_record_count == blocker_followup_action_count
        and blocker_progress_live_authorized_count == 0
        and blocker_progress_external_authorized_count == 0
        and blocker_progress_coverage_complete
        and blocker_progress_recommendation_mismatch_count == 0
        and (
            blocker_progress_review_record_count
            == int(operations_blocker_followup_progress["unresolved_progress_count"])
        )
        and blocker_progress_review_live_authorized_count == 0
        and blocker_progress_review_external_authorized_count == 0
        and blocker_progress_review_coverage_complete
        and blocker_progress_review_status_mismatch_count == 0
        and blocker_progress_review_residual_blocker_total
        == int(operations_blocker_followup_progress["residual_blocker_total"])
        and blocker_progress_next_action_record_count
        == blocker_progress_review_record_count
        and blocker_progress_next_action_live_authorized_count == 0
        and blocker_progress_next_action_external_authorized_count == 0
        and blocker_progress_next_action_coverage_complete
        and blocker_progress_next_action_status_mismatch_count == 0
        and blocker_progress_next_action_residual_blocker_total
        == blocker_progress_review_residual_blocker_total
        and blocker_progress_next_action_priority_sequence_ok
        and blocker_progress_execution_record_count
        == blocker_progress_next_action_record_count
        and blocker_progress_execution_live_authorized_count == 0
        and blocker_progress_execution_external_authorized_count == 0
        and blocker_progress_execution_coverage_complete
        and blocker_progress_execution_status_mismatch_count == 0
        and blocker_progress_execution_residual_mismatch_count == 0
        and blocker_progress_execution_priority_mismatch_count == 0
        and blocker_progress_execution_residual_blocker_total
        == blocker_progress_next_action_residual_blocker_total
        and blocker_progress_execution_priority_sequence_ok
        and blocker_progress_execution_review_record_count
        == blocker_progress_execution_record_count
        and blocker_progress_execution_review_live_authorized_count == 0
        and blocker_progress_execution_review_external_authorized_count == 0
        and blocker_progress_execution_review_coverage_complete
        and blocker_progress_execution_review_status_mismatch_count == 0
        and blocker_progress_execution_review_residual_mismatch_count == 0
        and blocker_progress_execution_review_priority_mismatch_count == 0
        and blocker_progress_execution_review_residual_blocker_total
        == blocker_progress_execution_residual_blocker_total
        and blocker_progress_execution_review_priority_sequence_ok
        and blocker_progress_execution_followup_record_count
        == blocker_progress_execution_review_record_count
        and blocker_progress_execution_followup_live_authorized_count == 0
        and blocker_progress_execution_followup_external_authorized_count == 0
        and blocker_progress_execution_followup_coverage_complete
        and blocker_progress_execution_followup_status_mismatch_count == 0
        and blocker_progress_execution_followup_residual_mismatch_count == 0
        and blocker_progress_execution_followup_priority_mismatch_count == 0
        and blocker_progress_execution_followup_residual_blocker_total
        == blocker_progress_execution_review_residual_blocker_total
        and blocker_progress_execution_followup_priority_sequence_ok
    )
    return {
        "ok": ok,
        "candidates": candidate_results,
        "reports": report_result,
        "schemas": schemas,
        "schema_paths_exist": schema_results,
        "calibration_summary": calibration,
        "calibration_track_summary": calibration_by_track,
        "false_positive_summary": false_positive_analysis,
        "score_regression_summary": regression,
        "catalog_cache_validation": catalog_cache,
        "provider_normalization_summary": provider_normalization,
        "injection_recovery_summary": injection_recovery,
        "reliability_summary": reliability,
        "precision_recall_summary": precision_recall,
        "review_queue_summary": review_queue,
        "consensus_summary": consensus,
        "consensus_export_summary": consensus_exports,
        "cross_track_summary": cross_track,
        "reproducibility_verification": reproducibility,
        "validation_dataset_summary": validation_datasets,
        "validation_promotion_summary": validation_promotions,
        "validation_readiness_summary": validation_readiness,
        "benchmark_metadata_summary": benchmark_metadata,
        "benchmark_run_summary": benchmark_runs,
        "target_priority_summary": target_priorities,
        "background_ledger_summary": background_ledger,
        "background_review_workflow_summary": background_review_workflow,
        "background_reviewed_log_summary": reviewed_log,
        "background_needs_follow_up_summary": needs_follow_up_log,
        "background_follow_up_test_summary": follow_up_tests,
        "background_report_readiness_summary": report_readiness,
        "background_draft_report_validation": draft_report_validation,
        "background_draft_follow_up_report_summary": draft_reports,
        "background_user_decision_summary": user_decisions,
        "candidate_extraction_handoff_summary": candidate_handoffs,
        "top_level_sqlite_log_summary": sqlite_logs,
        "top_level_sqlite_log_integrity_summary": sqlite_integrity,
        "top_level_sqlite_log_migration_summary": sqlite_migration,
        "top_level_sqlite_log_export": sqlite_export,
        "top_level_sqlite_log_backup": sqlite_backup,
        "top_level_sqlite_log_retention_summary": sqlite_retention,
        "top_level_sqlite_log_pragmas": sqlite_pragmas,
        "top_level_sqlite_log_migration_plan": sqlite_migration_plan,
        "top_level_sqlite_log_weekly_digest": sqlite_weekly_digest,
        "top_level_sqlite_log_validation": sqlite_log_validation,
        "top_level_sqlite_log_commit_guard": sqlite_commit_guard,
        "target_watchlist_summary": watchlist,
        "baseline_eval_summary": baseline_eval,
        "baseline_pathway_drift_summary": drift_result,
        "candidate_lifecycle_summary": lifecycle,
        "observation_schedule_summary": schedule,
        "false_negative_summary": fn_sum,
        "scoring_config_summary": scoring_cfg,
        "route_coverage_summary": route_coverage,
        "lifecycle_transition_summary": lifecycle_transitions,
        "observation_efficiency_summary": observation_efficiency,
        "sensitivity_config_summary": sensitivity_cfg,
        "triage_summary": triage_notes,
        "signal_registry_summary": signal_registry,
        "audit_trail_summary": audit_trail,
        "multi_epoch_summary": multi_epoch,
        "target_recalibration_summary": recalibration,
        "operator_coverage_summary": operator_coverage,
        "triage_label_completeness": label_completeness,
        "classifier_rule_coverage_summary": rule_coverage,
        "provenance_chain_validation": provenance_chain,
        "observation_gap_analysis": obs_gap,
        "schema_drift_summary": schema_drift,
        "observation_notes_summary": obs_notes,
        "epoch_plan_summary": epoch_plan,
        "aggregate_blockers_summary": aggregate_blockers,
        "score_history_summary": score_history,
        "operator_assignment_summary": op_assignments,
        "pipeline_health_summary": pipeline_health,
        "candidate_flags_summary": candidate_flags,
        "review_deadlines_summary": review_deadlines,
        "pipeline_throughput_summary": pipeline_throughput,
        "candidate_retention_summary": candidate_retention,
        "operator_performance_summary": operator_perf,
        "track_comparison_summary": track_comparison,
        "candidate_resolution_summary": candidate_resolution,
        "escalation_log_summary": escalations,
        "quality_control_summary": qc_summary,
        "observation_campaign_summary": obs_campaigns,
        "data_quality_log_summary": dq_log,
        "pipeline_audit_summary": pipeline_audit,
        "follow_up_request_summary": follow_up_reqs,
        "pipeline_bottleneck_summary": pipeline_bottleneck,
        "candidate_annotation_summary": candidate_annotations,
        "session_log_summary": session_log_data,
        "priority_queue_summary": priority_queue_data,
        "pipeline_capacity_summary": pipeline_capacity_data,
        "feature_vector_summary": feature_vector_data,
        "ml_model_registry_summary": ml_registry_data,
        "ml_pipeline_diagnostics_summary": ml_diagnostics_data,
        "feature_normalization_summary": feat_norm_data,
        "feature_importance_summary": feat_imp_data,
        "ml_training_data_summary": ml_training_data,
        "model_architecture_summary": arch_data,
        "model_evaluation_summary": eval_data,
        "model_performance_history_summary": perf_history_data,
        "model_serving_summary": serving_data,
        "scoring_audit_log_summary": audit_log_data,
        "curated_dataset_intake_summary": intake_data,
        "candidate_rescore_summary": rescore_data,
        "operator_handoff_summary": handoff_data,
        "pipeline_config_summary": pipeline_cfg_data,
        "submission_readiness_summary": submission_data,
        "candidate_comparison_summary": comparison_data,
        "pipeline_telemetry_summary": telemetry_data,
        "provenance_audit_summary": audit_data,
        "candidate_alert_summary": alert_data,
        "pipeline_replay_summary": replay_data,
        "scoring_threshold_audit_summary": threshold_audit_data,
        "alert_resolution_summary": alert_resolution_data,
        "candidate_deduplication_summary": dedup_data,
        "config_version_history_summary": config_history_data,
        "intake_queue_summary": intake_queue_data,
        "operator_escalation_summary": escalation_data,
        "workflow_state_summary": workflow_data,
        "data_gap_summary": data_gap_data,
        "candidate_match_summary": candidate_match_data,
        "pipeline_error_summary": pipeline_error_data,
        "observation_request_summary": obs_request_data,
        "candidate_export_summary": candidate_export_data,
        "quality_gate_summary": quality_gate_data,
        "instrument_log_summary": instrument_log_data,
        "archival_query_summary": archival_query_data,
        "candidate_linkage_summary": candidate_linkage_data,
        "signal_classification_summary": signal_classification_data,
        "rfi_mitigation_summary": rfi_mitigation_data,
        "candidate_annotation_log_summary": candidate_annotation_log_data,
        "frequency_channel_log_summary": frequency_channel_data,
        "pipeline_checkpoint_log_summary": pipeline_checkpoint_data,
        "candidate_status_log_summary": candidate_status_log_data,
        "operations_readiness_summary": operations_readiness,
        "operations_action_plan_summary": operations_action_plan,
        "operations_action_resolution_summary": operations_action_resolution,
        "operations_blocker_detail_summary": operations_blocker_detail,
        "operations_blocker_review_summary": operations_blocker_review,
        "operations_blocker_followup_summary": operations_blocker_followup,
        "operations_blocker_followup_progress_summary": (
            operations_blocker_followup_progress
        ),
        "operations_blocker_progress_review_summary": (
            operations_blocker_progress_review
        ),
        "operations_blocker_progress_next_actions_summary": (
            operations_blocker_progress_next_actions
        ),
        "operations_blocker_progress_execution_summary": (
            operations_blocker_progress_execution
        ),
        "operations_blocker_progress_execution_review_summary": (
            operations_blocker_progress_execution_review
        ),
        "operations_blocker_progress_execution_followup_summary": (
            operations_blocker_progress_execution_followup
        ),
    }


def validation_summary() -> dict[str, object]:
    """Return a concise local validation dashboard without network access."""

    validation = validate_all()
    candidates = validation["candidates"]
    reports = validation["reports"]
    schemas = validation["schema_paths_exist"]
    calibration = validation["calibration_summary"]
    calibration_by_track = validation["calibration_track_summary"]
    false_positive_analysis = validation["false_positive_summary"]
    regression = validation["score_regression_summary"]
    catalog_cache = validation["catalog_cache_validation"]
    provider_normalization = validation["provider_normalization_summary"]
    injection_recovery = validation["injection_recovery_summary"]
    reliability = validation["reliability_summary"]
    precision_recall = validation["precision_recall_summary"]
    review_queue = validation["review_queue_summary"]
    consensus = validation["consensus_summary"]
    consensus_exports = validation["consensus_export_summary"]
    cross_track = validation["cross_track_summary"]
    reproducibility = validation["reproducibility_verification"]
    sqlite_migration_plan = validation["top_level_sqlite_log_migration_plan"]
    sqlite_weekly_digest = validation["top_level_sqlite_log_weekly_digest"]
    validation_datasets = validation["validation_dataset_summary"]
    validation_promotions = validation["validation_promotion_summary"]
    validation_readiness = validation["validation_readiness_summary"]
    benchmark_metadata = validation["benchmark_metadata_summary"]
    benchmark_runs = validation["benchmark_run_summary"]
    target_priorities = validation["target_priority_summary"]
    background_ledger = validation["background_ledger_summary"]
    background_review_workflow = validation["background_review_workflow_summary"]
    reviewed_log = validation["background_reviewed_log_summary"]
    needs_follow_up_log = validation["background_needs_follow_up_summary"]
    follow_up_tests = validation["background_follow_up_test_summary"]
    report_readiness = validation["background_report_readiness_summary"]
    draft_reports = validation["background_draft_follow_up_report_summary"]
    draft_report_validation = validation["background_draft_report_validation"]
    user_decisions = validation["background_user_decision_summary"]
    candidate_handoffs = validation["candidate_extraction_handoff_summary"]
    sqlite_logs = validation["top_level_sqlite_log_summary"]
    sqlite_integrity = validation["top_level_sqlite_log_integrity_summary"]
    sqlite_migration = validation["top_level_sqlite_log_migration_summary"]
    sqlite_commit_guard = validation["top_level_sqlite_log_commit_guard"]
    sqlite_backup = validation["top_level_sqlite_log_backup"]
    sqlite_retention = validation["top_level_sqlite_log_retention_summary"]
    sqlite_pragmas = validation["top_level_sqlite_log_pragmas"]
    sqlite_log_validation = validation["top_level_sqlite_log_validation"]
    operations_readiness = validation["operations_readiness_summary"]
    operations_action_plan = validation["operations_action_plan_summary"]
    operations_action_resolution = validation["operations_action_resolution_summary"]
    operations_blocker_detail = validation["operations_blocker_detail_summary"]
    operations_blocker_review = validation["operations_blocker_review_summary"]
    operations_blocker_followup = validation["operations_blocker_followup_summary"]
    operations_blocker_followup_progress = validation[
        "operations_blocker_followup_progress_summary"
    ]
    operations_blocker_progress_review = validation[
        "operations_blocker_progress_review_summary"
    ]
    operations_blocker_progress_next_actions = validation[
        "operations_blocker_progress_next_actions_summary"
    ]
    operations_blocker_progress_execution = validation[
        "operations_blocker_progress_execution_summary"
    ]
    operations_blocker_progress_execution_review = validation[
        "operations_blocker_progress_execution_review_summary"
    ]
    operations_blocker_progress_execution_followup = validation[
        "operations_blocker_progress_execution_followup_summary"
    ]
    return {
        "ok": validation["ok"],
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "candidate_count": len(candidates) if isinstance(candidates, dict) else 0,
        "report_validation_ok": bool(reports["ok"]) if isinstance(reports, dict) else False,
        "schema_count": len(schemas) if isinstance(schemas, dict) else 0,
        "schemas_ok": all(schemas.values()) if isinstance(schemas, dict) else False,
        "calibration_fixture_count": calibration["total"]
        if isinstance(calibration, dict)
        else 0,
        "calibration_track_count": calibration_by_track["track_count"]
        if isinstance(calibration_by_track, dict)
        else 0,
        "calibration_minimum_track_case_count": calibration_by_track[
            "minimum_track_case_count"
        ]
        if isinstance(calibration_by_track, dict)
        else 0,
        "false_positive_case_count": false_positive_analysis["case_count"]
        if isinstance(false_positive_analysis, dict)
        else 0,
        "false_positive_class_count": false_positive_analysis["class_count"]
        if isinstance(false_positive_analysis, dict)
        else 0,
        "score_regression_candidate_count": regression["candidate_count"]
        if isinstance(regression, dict)
        else 0,
        "catalog_cache_ok": bool(catalog_cache["ok"])
        if isinstance(catalog_cache, dict)
        else False,
        "provider_normalization_case_count": provider_normalization["case_count"]
        if isinstance(provider_normalization, dict)
        else 0,
        "injection_recovery_case_count": injection_recovery["case_count"]
        if isinstance(injection_recovery, dict)
        else 0,
        "synthetic_recovery_rate": injection_recovery["synthetic_recovery_rate"]
        if isinstance(injection_recovery, dict)
        else 0.0,
        "synthetic_false_alarm_fraction": injection_recovery[
            "synthetic_false_alarm_fraction"
        ]
        if isinstance(injection_recovery, dict)
        else 0.0,
        "reliability_bin_count": reliability["bin_count"]
        if isinstance(reliability, dict)
        else 0,
        "mean_absolute_calibration_error": reliability[
            "mean_absolute_calibration_error"
        ]
        if isinstance(reliability, dict)
        else 0.0,
        "precision_recall_case_count": precision_recall["case_count"]
        if isinstance(precision_recall, dict)
        else 0,
        "synthetic_precision": precision_recall["synthetic_precision"]
        if isinstance(precision_recall, dict)
        else 0.0,
        "synthetic_recall": precision_recall["synthetic_recall"]
        if isinstance(precision_recall, dict)
        else 0.0,
        "review_queue_item_count": review_queue["item_count"]
        if isinstance(review_queue, dict)
        else 0,
        "review_queue_note_count": review_queue["note_count"]
        if isinstance(review_queue, dict)
        else 0,
        "consensus_item_count": consensus["item_count"]
        if isinstance(consensus, dict)
        else 0,
        "consensus_decision_count": consensus["decision_count"]
        if isinstance(consensus, dict)
        else 0,
        "consensus_unique_reviewer_count": consensus["unique_reviewer_count"]
        if isinstance(consensus, dict)
        else 0,
        "consensus_export_count": consensus_exports["export_count"]
        if isinstance(consensus_exports, dict)
        else 0,
        "consensus_export_blocking_issue_total": consensus_exports[
            "blocking_issue_total"
        ]
        if isinstance(consensus_exports, dict)
        else 0,
        "cross_track_reference_count": cross_track["reference_count"]
        if isinstance(cross_track, dict)
        else 0,
        "cross_track_multi_track_reference_count": cross_track[
            "multi_track_reference_count"
        ]
        if isinstance(cross_track, dict)
        else 0,
        "cross_track_blocking_issue_total": cross_track["blocking_issue_total"]
        if isinstance(cross_track, dict)
        else 0,
        "reproducibility_verified_count": reproducibility["verified_count"]
        if isinstance(reproducibility, dict)
        else 0,
        "reproducibility_drift_count": reproducibility["drift_count"]
        if isinstance(reproducibility, dict)
        else 0,
        "top_level_sqlite_log_migration_plan_required": bool(
            sqlite_migration_plan["migration_required"]
        )
        if isinstance(sqlite_migration_plan, dict)
        else False,
        "top_level_sqlite_log_weekly_digest_ok": bool(sqlite_weekly_digest["ok"])
        if isinstance(sqlite_weekly_digest, dict)
        else False,
        "validation_dataset_count": validation_datasets["dataset_count"]
        if isinstance(validation_datasets, dict)
        else 0,
        "validation_dataset_case_count": validation_datasets["total_case_count"]
        if isinstance(validation_datasets, dict)
        else 0,
        "validation_promotion_rule_count": validation_promotions["rule_count"]
        if isinstance(validation_promotions, dict)
        else 0,
        "validation_promotion_blocking_condition_count": validation_promotions[
            "blocking_condition_count"
        ]
        if isinstance(validation_promotions, dict)
        else 0,
        "validation_readiness_record_count": validation_readiness["record_count"]
        if isinstance(validation_readiness, dict)
        else 0,
        "validation_readiness_ready_count": validation_readiness["ready_count"]
        if isinstance(validation_readiness, dict)
        else 0,
        "validation_readiness_blocked_count": validation_readiness["blocked_count"]
        if isinstance(validation_readiness, dict)
        else 0,
        "validation_readiness_not_yet_admissible_count": validation_readiness[
            "not_yet_admissible_count"
        ]
        if isinstance(validation_readiness, dict)
        else 0,
        "validation_readiness_blocking_issue_count": validation_readiness[
            "blocking_issue_count"
        ]
        if isinstance(validation_readiness, dict)
        else 0,
        "benchmark_command_count": benchmark_metadata["command_count"]
        if isinstance(benchmark_metadata, dict)
        else 0,
        "benchmark_default_cpu_worker_limit": benchmark_metadata[
            "default_cpu_worker_limit"
        ]
        if isinstance(benchmark_metadata, dict)
        else 0,
        "benchmark_memory_budget_gb": benchmark_metadata["memory_budget_gb"]
        if isinstance(benchmark_metadata, dict)
        else 0,
        "benchmark_run_count": benchmark_runs["run_count"]
        if isinstance(benchmark_runs, dict)
        else 0,
        "benchmark_run_input_case_total": benchmark_runs["input_case_total"]
        if isinstance(benchmark_runs, dict)
        else 0,
        "benchmark_run_max_worker_count": benchmark_runs["max_worker_count"]
        if isinstance(benchmark_runs, dict)
        else 0,
        "target_priority_count": target_priorities["target_count"]
        if isinstance(target_priorities, dict)
        else 0,
        "selected_background_target_id": target_priorities["selected_target_id"]
        if isinstance(target_priorities, dict)
        else None,
        "background_ledger_entry_count": background_ledger["entry_count"]
        if isinstance(background_ledger, dict)
        else 0,
        "background_ledger_candidate_count": background_ledger["candidate_count"]
        if isinstance(background_ledger, dict)
        else 0,
        "background_review_workflow_status_count": background_review_workflow[
            "reviewed_workflow_status_count"
        ]
        if isinstance(background_review_workflow, dict)
        else 0,
        "background_review_negative_result_logged_count": background_review_workflow[
            "negative_result_logged_count"
        ]
        if isinstance(background_review_workflow, dict)
        else 0,
        "background_review_local_only_entry_count": background_review_workflow[
            "local_only_entry_count"
        ]
        if isinstance(background_review_workflow, dict)
        else 0,
        "background_reviewed_log_entry_count": reviewed_log["entry_count"]
        if isinstance(reviewed_log, dict)
        else 0,
        "background_reviewed_log_network_access_allowed_count": reviewed_log[
            "network_access_allowed_count"
        ]
        if isinstance(reviewed_log, dict)
        else 0,
        "background_needs_follow_up_entry_count": needs_follow_up_log["entry_count"]
        if isinstance(needs_follow_up_log, dict)
        else 0,
        "background_needs_follow_up_required_test_count": needs_follow_up_log[
            "required_test_count"
        ]
        if isinstance(needs_follow_up_log, dict)
        else 0,
        "background_needs_follow_up_user_approval_count": needs_follow_up_log[
            "submission_requires_user_approval_count"
        ]
        if isinstance(needs_follow_up_log, dict)
        else 0,
        "background_needs_follow_up_network_access_allowed_count": needs_follow_up_log[
            "network_access_allowed_count"
        ]
        if isinstance(needs_follow_up_log, dict)
        else 0,
        "background_follow_up_test_result_count": follow_up_tests["result_count"]
        if isinstance(follow_up_tests, dict)
        else 0,
        "background_follow_up_test_complete_set_count": follow_up_tests[
            "complete_follow_up_test_set_count"
        ]
        if isinstance(follow_up_tests, dict)
        else 0,
        "background_follow_up_test_network_access_allowed_count": follow_up_tests[
            "network_access_allowed_count"
        ]
        if isinstance(follow_up_tests, dict)
        else 0,
        "background_report_readiness_record_count": report_readiness["record_count"]
        if isinstance(report_readiness, dict)
        else 0,
        "background_report_readiness_ready_to_draft_count": report_readiness[
            "ready_to_draft_report_count"
        ]
        if isinstance(report_readiness, dict)
        else 0,
        "background_report_readiness_user_approval_count": report_readiness[
            "user_approval_required_count"
        ]
        if isinstance(report_readiness, dict)
        else 0,
        "background_report_readiness_external_submission_allowed_count": (
            report_readiness["external_submission_allowed_count"]
        )
        if isinstance(report_readiness, dict)
        else 0,
        "background_report_readiness_top_three_recommendation_count": (
            report_readiness["top_three_recommendation_count"]
        )
        if isinstance(report_readiness, dict)
        else 0,
        "background_draft_report_count": draft_reports["draft_report_count"]
        if isinstance(draft_reports, dict)
        else 0,
        "background_draft_report_ready_count": draft_reports["draft_ready_count"]
        if isinstance(draft_reports, dict)
        else 0,
        "background_draft_report_external_submission_allowed_count": (
            draft_reports["external_submission_allowed_count"]
        )
        if isinstance(draft_reports, dict)
        else 0,
        "background_draft_report_validation_ok": bool(
            draft_report_validation["ok"]
        )
        if isinstance(draft_report_validation, dict)
        else False,
        "background_user_decision_count": user_decisions["decision_count"]
        if isinstance(user_decisions, dict)
        else 0,
        "background_user_decision_external_submission_approved_count": (
            user_decisions["external_submission_approved_count"]
        )
        if isinstance(user_decisions, dict)
        else 0,
        "background_user_decision_request_more_tests_count": (
            user_decisions["request_more_tests_count"]
        )
        if isinstance(user_decisions, dict)
        else 0,
        "background_user_decision_close_as_reviewed_count": (
            user_decisions["close_as_reviewed_count"]
        )
        if isinstance(user_decisions, dict)
        else 0,
        "candidate_extraction_handoff_record_count": candidate_handoffs["record_count"]
        if isinstance(candidate_handoffs, dict)
        else 0,
        "candidate_extraction_handoff_ready_count": candidate_handoffs["ready_count"]
        if isinstance(candidate_handoffs, dict)
        else 0,
        "candidate_extraction_handoff_blocked_count": candidate_handoffs[
            "blocked_count"
        ]
        if isinstance(candidate_handoffs, dict)
        else 0,
        "candidate_extraction_handoff_negative_result_required_count": (
            candidate_handoffs["negative_result_required_count"]
        )
        if isinstance(candidate_handoffs, dict)
        else 0,
        "top_level_sqlite_log_validation_ok": bool(sqlite_log_validation["ok"])
        if isinstance(sqlite_log_validation, dict)
        else False,
        "top_level_sqlite_log_integrity_ok": bool(sqlite_integrity["ok"])
        if isinstance(sqlite_integrity, dict)
        else False,
        "top_level_sqlite_log_migration_required": bool(
            sqlite_migration["migration_required"]
        )
        if isinstance(sqlite_migration, dict)
        else False,
        "top_level_sqlite_log_commit_guard_ok": bool(sqlite_commit_guard["ok"])
        if isinstance(sqlite_commit_guard, dict)
        else False,
        "top_level_sqlite_log_backup_ok": bool(sqlite_backup["ok"])
        if isinstance(sqlite_backup, dict)
        else False,
        "top_level_sqlite_log_backup_count": sqlite_retention["backup_count"]
        if isinstance(sqlite_retention, dict)
        else 0,
        "top_level_sqlite_log_retention_ok": bool(sqlite_retention["ok"])
        if isinstance(sqlite_retention, dict)
        else False,
        "top_level_sqlite_log_pragmas_ok": bool(sqlite_pragmas["ok"])
        if isinstance(sqlite_pragmas, dict)
        else False,
        "top_level_sqlite_log_integrity_check": sqlite_pragmas["integrity_check"]
        if isinstance(sqlite_pragmas, dict)
        else "missing",
        "top_level_sqlite_log_run_count": sqlite_logs["run_count"]
        if isinstance(sqlite_logs, dict)
        else 0,
        "top_level_sqlite_log_outcome_count": sqlite_logs["outcome_count"]
        if isinstance(sqlite_logs, dict)
        else 0,
        "top_level_sqlite_log_network_access_allowed_count": sqlite_logs[
            "network_access_allowed_count"
        ]
        if isinstance(sqlite_logs, dict)
        else 0,
        "top_level_sqlite_log_external_submission_approved_count": sqlite_logs[
            "external_submission_approved_count"
        ]
        if isinstance(sqlite_logs, dict)
        else 0,
        "operations_readiness_sqlite_log_present": bool(
            operations_readiness["sqlite_log_snapshot"]["present"]
        )
        if isinstance(operations_readiness, dict)
        else False,
        "operations_readiness_sqlite_integrity_ok": bool(
            operations_readiness["sqlite_log_snapshot"]["integrity_ok"]
        )
        if isinstance(operations_readiness, dict)
        else False,
        "operations_readiness_sqlite_weekly_digest_ok": bool(
            operations_readiness["sqlite_log_snapshot"]["weekly_digest_ok"]
        )
        if isinstance(operations_readiness, dict)
        else False,
        "operations_readiness_recommendation": operations_readiness[
            "recommendation"
        ]
        if isinstance(operations_readiness, dict)
        else "unknown",
        "operations_readiness_local_validation_ready": bool(
            operations_readiness["local_validation_ready"]
        )
        if isinstance(operations_readiness, dict)
        else False,
        "operations_readiness_real_data_blocker_count": operations_readiness[
            "real_data_blocker_count"
        ]
        if isinstance(operations_readiness, dict)
        else 0,
        "operations_readiness_operator_attention_count": operations_readiness[
            "operator_attention_count"
        ]
        if isinstance(operations_readiness, dict)
        else 0,
        "operations_readiness_open_alert_count": operations_readiness[
            "open_alert_count"
        ]
        if isinstance(operations_readiness, dict)
        else 0,
        "operations_readiness_overdue_review_deadline_count": operations_readiness[
            "overdue_review_deadline_count"
        ]
        if isinstance(operations_readiness, dict)
        else 0,
        "operations_readiness_external_submission_approved_count": (
            operations_readiness["external_submission_approved_count"]
        )
        if isinstance(operations_readiness, dict)
        else 0,
        "operations_readiness_network_access_allowed_count": operations_readiness[
            "network_access_allowed_count"
        ]
        if isinstance(operations_readiness, dict)
        else 0,
        "operations_action_plan_action_count": operations_action_plan[
            "action_count"
        ]
        if isinstance(operations_action_plan, dict)
        else 0,
        "operations_action_plan_critical_action_count": operations_action_plan[
            "critical_action_count"
        ]
        if isinstance(operations_action_plan, dict)
        else 0,
        "operations_action_plan_real_data_blocking_action_count": (
            operations_action_plan["real_data_blocking_action_count"]
        )
        if isinstance(operations_action_plan, dict)
        else 0,
        "operations_action_plan_operator_review_action_count": (
            operations_action_plan["operator_review_action_count"]
        )
        if isinstance(operations_action_plan, dict)
        else 0,
        "operations_action_resolution_record_count": operations_action_resolution[
            "record_count"
        ]
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_open_count": operations_action_resolution[
            "open_count"
        ]
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_acknowledged_count": (
            operations_action_resolution["acknowledged_count"]
        )
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_deferred_count": operations_action_resolution[
            "deferred_count"
        ]
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_resolved_count": operations_action_resolution[
            "resolved_count"
        ]
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_residual_blocker_total": (
            operations_action_resolution["residual_blocker_total"]
        )
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_live_data_authorized_count": (
            operations_action_resolution["live_data_authorized_count"]
        )
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_external_submission_authorized_count": (
            operations_action_resolution["external_submission_authorized_count"]
        )
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_all_external_authorization_disabled": bool(
            operations_action_resolution["all_external_authorization_disabled"]
        )
        if isinstance(operations_action_resolution, dict)
        else False,
        "operations_action_resolution_expected_action_count": (
            operations_action_resolution["expected_action_count"]
        )
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_covered_action_count": (
            operations_action_resolution["covered_action_count"]
        )
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_missing_action_count": (
            operations_action_resolution["missing_action_count"]
        )
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_stale_resolution_count": (
            operations_action_resolution["stale_resolution_count"]
        )
        if isinstance(operations_action_resolution, dict)
        else 0,
        "operations_action_resolution_coverage_fraction": (
            operations_action_resolution["coverage_fraction"]
        )
        if isinstance(operations_action_resolution, dict)
        else 0.0,
        "operations_action_resolution_coverage_complete": bool(
            operations_action_resolution["coverage_complete"]
        )
        if isinstance(operations_action_resolution, dict)
        else False,
        "operations_action_resolution_missing_action_ids": (
            operations_action_resolution["missing_action_ids"]
        )
        if isinstance(operations_action_resolution, dict)
        else [],
        "operations_action_resolution_stale_resolution_action_ids": (
            operations_action_resolution["stale_resolution_action_ids"]
        )
        if isinstance(operations_action_resolution, dict)
        else [],
        "operations_blocker_detail_count": operations_blocker_detail["detail_count"]
        if isinstance(operations_blocker_detail, dict)
        else 0,
        "operations_blocker_detail_total_evidence_record_count": (
            operations_blocker_detail["total_evidence_record_count"]
        )
        if isinstance(operations_blocker_detail, dict)
        else 0,
        "operations_blocker_detail_all_external_authorization_disabled": bool(
            operations_blocker_detail["all_external_authorization_disabled"]
        )
        if isinstance(operations_blocker_detail, dict)
        else False,
        "operations_blocker_detail_sqlite_context_is_resolved": bool(
            operations_blocker_detail["sqlite_context_is_resolved"]
        )
        if isinstance(operations_blocker_detail, dict)
        else False,
        "operations_blocker_review_record_count": operations_blocker_review[
            "record_count"
        ]
        if isinstance(operations_blocker_review, dict)
        else 0,
        "operations_blocker_review_reviewed_evidence_record_count": (
            operations_blocker_review["reviewed_evidence_record_count"]
        )
        if isinstance(operations_blocker_review, dict)
        else 0,
        "operations_blocker_review_unreviewed_evidence_record_count": (
            operations_blocker_review["unreviewed_evidence_record_count"]
        )
        if isinstance(operations_blocker_review, dict)
        else 0,
        "operations_blocker_review_residual_blocker_total": (
            operations_blocker_review["residual_blocker_total"]
        )
        if isinstance(operations_blocker_review, dict)
        else 0,
        "operations_blocker_review_live_data_authorized_count": (
            operations_blocker_review["live_data_authorized_count"]
        )
        if isinstance(operations_blocker_review, dict)
        else 0,
        "operations_blocker_review_external_submission_authorized_count": (
            operations_blocker_review["external_submission_authorized_count"]
        )
        if isinstance(operations_blocker_review, dict)
        else 0,
        "operations_blocker_review_all_external_authorization_disabled": bool(
            operations_blocker_review["all_external_authorization_disabled"]
        )
        if isinstance(operations_blocker_review, dict)
        else False,
        "operations_blocker_review_coverage_complete": bool(
            operations_blocker_review["coverage_complete"]
        )
        if isinstance(operations_blocker_review, dict)
        else False,
        "operations_blocker_review_all_detail_evidence_reviewed": bool(
            operations_blocker_review["all_detail_evidence_reviewed"]
        )
        if isinstance(operations_blocker_review, dict)
        else False,
        "operations_blocker_followup_action_count": operations_blocker_followup[
            "action_count"
        ]
        if isinstance(operations_blocker_followup, dict)
        else 0,
        "operations_blocker_followup_action_required_count": (
            operations_blocker_followup["action_required_count"]
        )
        if isinstance(operations_blocker_followup, dict)
        else 0,
        "operations_blocker_followup_real_data_hold_count": (
            operations_blocker_followup["real_data_hold_count"]
        )
        if isinstance(operations_blocker_followup, dict)
        else 0,
        "operations_blocker_followup_verification_ready_count": (
            operations_blocker_followup["verification_ready_count"]
        )
        if isinstance(operations_blocker_followup, dict)
        else 0,
        "operations_blocker_followup_residual_blocker_total": (
            operations_blocker_followup["residual_blocker_total"]
        )
        if isinstance(operations_blocker_followup, dict)
        else 0,
        "operations_blocker_followup_live_data_authorized_count": (
            operations_blocker_followup["live_data_authorized_count"]
        )
        if isinstance(operations_blocker_followup, dict)
        else 0,
        "operations_blocker_followup_external_submission_authorized_count": (
            operations_blocker_followup["external_submission_authorized_count"]
        )
        if isinstance(operations_blocker_followup, dict)
        else 0,
        "operations_blocker_followup_all_external_authorization_disabled": bool(
            operations_blocker_followup["all_external_authorization_disabled"]
        )
        if isinstance(operations_blocker_followup, dict)
        else False,
        "operations_blocker_followup_coverage_complete": bool(
            operations_blocker_followup["coverage_complete"]
        )
        if isinstance(operations_blocker_followup, dict)
        else False,
        "operations_blocker_followup_all_detail_evidence_reviewed": bool(
            operations_blocker_followup["all_detail_evidence_reviewed"]
        )
        if isinstance(operations_blocker_followup, dict)
        else False,
        "operations_blocker_followup_progress_record_count": (
            operations_blocker_followup_progress["record_count"]
        )
        if isinstance(operations_blocker_followup_progress, dict)
        else 0,
        "operations_blocker_followup_progress_unresolved_count": (
            operations_blocker_followup_progress["unresolved_progress_count"]
        )
        if isinstance(operations_blocker_followup_progress, dict)
        else 0,
        "operations_blocker_followup_progress_verified_local_count": (
            operations_blocker_followup_progress["verified_local_count"]
        )
        if isinstance(operations_blocker_followup_progress, dict)
        else 0,
        "operations_blocker_followup_progress_residual_blocker_total": (
            operations_blocker_followup_progress["residual_blocker_total"]
        )
        if isinstance(operations_blocker_followup_progress, dict)
        else 0,
        "operations_blocker_followup_progress_live_data_authorized_count": (
            operations_blocker_followup_progress["live_data_authorized_count"]
        )
        if isinstance(operations_blocker_followup_progress, dict)
        else 0,
        "operations_blocker_followup_progress_external_submission_authorized_count": (
            operations_blocker_followup_progress[
                "external_submission_authorized_count"
            ]
        )
        if isinstance(operations_blocker_followup_progress, dict)
        else 0,
        "operations_blocker_followup_progress_all_external_authorization_disabled": (
            bool(
                operations_blocker_followup_progress[
                    "all_external_authorization_disabled"
                ]
            )
        )
        if isinstance(operations_blocker_followup_progress, dict)
        else False,
        "operations_blocker_followup_progress_coverage_complete": bool(
            operations_blocker_followup_progress["coverage_complete"]
        )
        if isinstance(operations_blocker_followup_progress, dict)
        else False,
        "operations_blocker_followup_progress_recommendation_mismatch_count": (
            operations_blocker_followup_progress["recommendation_mismatch_count"]
        )
        if isinstance(operations_blocker_followup_progress, dict)
        else 0,
        "operations_blocker_progress_review_record_count": (
            operations_blocker_progress_review["record_count"]
        )
        if isinstance(operations_blocker_progress_review, dict)
        else 0,
        "operations_blocker_progress_review_needs_operator_action_count": (
            operations_blocker_progress_review["needs_operator_action_count"]
        )
        if isinstance(operations_blocker_progress_review, dict)
        else 0,
        "operations_blocker_progress_review_ready_for_next_local_note_count": (
            operations_blocker_progress_review["ready_for_next_local_note_count"]
        )
        if isinstance(operations_blocker_progress_review, dict)
        else 0,
        "operations_blocker_progress_review_blocked_for_real_data_count": (
            operations_blocker_progress_review["blocked_for_real_data_count"]
        )
        if isinstance(operations_blocker_progress_review, dict)
        else 0,
        "operations_blocker_progress_review_residual_blocker_total": (
            operations_blocker_progress_review["residual_blocker_total"]
        )
        if isinstance(operations_blocker_progress_review, dict)
        else 0,
        "operations_blocker_progress_review_live_data_authorized_count": (
            operations_blocker_progress_review["live_data_authorized_count"]
        )
        if isinstance(operations_blocker_progress_review, dict)
        else 0,
        "operations_blocker_progress_review_external_submission_authorized_count": (
            operations_blocker_progress_review[
                "external_submission_authorized_count"
            ]
        )
        if isinstance(operations_blocker_progress_review, dict)
        else 0,
        "operations_blocker_progress_review_all_external_authorization_disabled": (
            bool(
                operations_blocker_progress_review[
                    "all_external_authorization_disabled"
                ]
            )
        )
        if isinstance(operations_blocker_progress_review, dict)
        else False,
        "operations_blocker_progress_review_coverage_complete": bool(
            operations_blocker_progress_review["coverage_complete"]
        )
        if isinstance(operations_blocker_progress_review, dict)
        else False,
        "operations_blocker_progress_review_status_mismatch_count": (
            operations_blocker_progress_review["status_mismatch_count"]
        )
        if isinstance(operations_blocker_progress_review, dict)
        else 0,
        "operations_blocker_progress_next_actions_record_count": (
            operations_blocker_progress_next_actions["record_count"]
        )
        if isinstance(operations_blocker_progress_next_actions, dict)
        else 0,
        "operations_blocker_progress_next_actions_operator_action_required_count": (
            operations_blocker_progress_next_actions["operator_action_required_count"]
        )
        if isinstance(operations_blocker_progress_next_actions, dict)
        else 0,
        "operations_blocker_progress_next_actions_local_note_ready_count": (
            operations_blocker_progress_next_actions["local_note_ready_count"]
        )
        if isinstance(operations_blocker_progress_next_actions, dict)
        else 0,
        "operations_blocker_progress_next_actions_blocked_pending_real_data_count": (
            operations_blocker_progress_next_actions[
                "blocked_pending_real_data_count"
            ]
        )
        if isinstance(operations_blocker_progress_next_actions, dict)
        else 0,
        "operations_blocker_progress_next_actions_residual_blocker_total": (
            operations_blocker_progress_next_actions["residual_blocker_total"]
        )
        if isinstance(operations_blocker_progress_next_actions, dict)
        else 0,
        "operations_blocker_progress_next_actions_live_data_authorized_count": (
            operations_blocker_progress_next_actions["live_data_authorized_count"]
        )
        if isinstance(operations_blocker_progress_next_actions, dict)
        else 0,
        "operations_blocker_progress_next_actions_external_submission_authorized_count": (
            operations_blocker_progress_next_actions[
                "external_submission_authorized_count"
            ]
        )
        if isinstance(operations_blocker_progress_next_actions, dict)
        else 0,
        "operations_blocker_progress_next_actions_all_external_authorization_disabled": (
            bool(
                operations_blocker_progress_next_actions[
                    "all_external_authorization_disabled"
                ]
            )
        )
        if isinstance(operations_blocker_progress_next_actions, dict)
        else False,
        "operations_blocker_progress_next_actions_coverage_complete": bool(
            operations_blocker_progress_next_actions["coverage_complete"]
        )
        if isinstance(operations_blocker_progress_next_actions, dict)
        else False,
        "operations_blocker_progress_next_actions_status_mismatch_count": (
            operations_blocker_progress_next_actions["status_mismatch_count"]
        )
        if isinstance(operations_blocker_progress_next_actions, dict)
        else 0,
        "operations_blocker_progress_next_actions_priority_sequence_ok": bool(
            operations_blocker_progress_next_actions["priority_sequence_ok"]
        )
        if isinstance(operations_blocker_progress_next_actions, dict)
        else False,
        "operations_blocker_progress_execution_record_count": (
            operations_blocker_progress_execution["record_count"]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else 0,
        "operations_blocker_progress_execution_awaiting_operator_count": (
            operations_blocker_progress_execution["awaiting_operator_count"]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else 0,
        "operations_blocker_progress_execution_local_note_recorded_count": (
            operations_blocker_progress_execution["local_note_recorded_count"]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else 0,
        "operations_blocker_progress_execution_blocked_pending_real_data_count": (
            operations_blocker_progress_execution[
                "blocked_pending_real_data_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else 0,
        "operations_blocker_progress_execution_residual_blocker_total": (
            operations_blocker_progress_execution["residual_blocker_total"]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else 0,
        "operations_blocker_progress_execution_live_data_authorized_count": (
            operations_blocker_progress_execution["live_data_authorized_count"]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else 0,
        "operations_blocker_progress_execution_external_submission_authorized_count": (
            operations_blocker_progress_execution[
                "external_submission_authorized_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else 0,
        "operations_blocker_progress_execution_all_external_authorization_disabled": (
            bool(
                operations_blocker_progress_execution[
                    "all_external_authorization_disabled"
                ]
            )
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else False,
        "operations_blocker_progress_execution_coverage_complete": bool(
            operations_blocker_progress_execution["coverage_complete"]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else False,
        "operations_blocker_progress_execution_status_mismatch_count": (
            operations_blocker_progress_execution["status_mismatch_count"]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else 0,
        "operations_blocker_progress_execution_residual_mismatch_count": (
            operations_blocker_progress_execution["residual_mismatch_count"]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else 0,
        "operations_blocker_progress_execution_priority_mismatch_count": (
            operations_blocker_progress_execution["priority_mismatch_count"]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else 0,
        "operations_blocker_progress_execution_priority_sequence_ok": bool(
            operations_blocker_progress_execution["priority_sequence_ok"]
        )
        if isinstance(operations_blocker_progress_execution, dict)
        else False,
        "operations_blocker_progress_execution_review_record_count": (
            operations_blocker_progress_execution_review["record_count"]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else 0,
        "operations_blocker_progress_execution_review_awaiting_operator_reviewed_count": (
            operations_blocker_progress_execution_review[
                "awaiting_operator_reviewed_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else 0,
        "operations_blocker_progress_execution_review_execution_note_reviewed_count": (
            operations_blocker_progress_execution_review[
                "execution_note_reviewed_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else 0,
        "operations_blocker_progress_execution_review_blocked_pending_real_data_reviewed_count": (
            operations_blocker_progress_execution_review[
                "blocked_pending_real_data_reviewed_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else 0,
        "operations_blocker_progress_execution_review_residual_blocker_total": (
            operations_blocker_progress_execution_review["residual_blocker_total"]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else 0,
        "operations_blocker_progress_execution_review_live_data_authorized_count": (
            operations_blocker_progress_execution_review[
                "live_data_authorized_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else 0,
        "operations_blocker_progress_execution_review_external_submission_authorized_count": (
            operations_blocker_progress_execution_review[
                "external_submission_authorized_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else 0,
        "operations_blocker_progress_execution_review_all_external_authorization_disabled": (
            bool(
                operations_blocker_progress_execution_review[
                    "all_external_authorization_disabled"
                ]
            )
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else False,
        "operations_blocker_progress_execution_review_coverage_complete": bool(
            operations_blocker_progress_execution_review["coverage_complete"]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else False,
        "operations_blocker_progress_execution_review_status_mismatch_count": (
            operations_blocker_progress_execution_review["status_mismatch_count"]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else 0,
        "operations_blocker_progress_execution_review_residual_mismatch_count": (
            operations_blocker_progress_execution_review["residual_mismatch_count"]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else 0,
        "operations_blocker_progress_execution_review_priority_mismatch_count": (
            operations_blocker_progress_execution_review["priority_mismatch_count"]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else 0,
        "operations_blocker_progress_execution_review_priority_sequence_ok": bool(
            operations_blocker_progress_execution_review["priority_sequence_ok"]
        )
        if isinstance(operations_blocker_progress_execution_review, dict)
        else False,
        "operations_blocker_progress_execution_followup_record_count": (
            operations_blocker_progress_execution_followup["record_count"]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else 0,
        "operations_blocker_progress_execution_followup_operator_followup_required_count": (
            operations_blocker_progress_execution_followup[
                "operator_followup_required_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else 0,
        "operations_blocker_progress_execution_followup_local_note_followup_ready_count": (
            operations_blocker_progress_execution_followup[
                "local_note_followup_ready_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else 0,
        "operations_blocker_progress_execution_followup_blocked_pending_real_data_count": (
            operations_blocker_progress_execution_followup[
                "blocked_pending_real_data_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else 0,
        "operations_blocker_progress_execution_followup_residual_blocker_total": (
            operations_blocker_progress_execution_followup["residual_blocker_total"]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else 0,
        "operations_blocker_progress_execution_followup_live_data_authorized_count": (
            operations_blocker_progress_execution_followup[
                "live_data_authorized_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else 0,
        "operations_blocker_progress_execution_followup_external_submission_authorized_count": (
            operations_blocker_progress_execution_followup[
                "external_submission_authorized_count"
            ]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else 0,
        "operations_blocker_progress_execution_followup_all_external_authorization_disabled": (
            bool(
                operations_blocker_progress_execution_followup[
                    "all_external_authorization_disabled"
                ]
            )
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else False,
        "operations_blocker_progress_execution_followup_coverage_complete": bool(
            operations_blocker_progress_execution_followup["coverage_complete"]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else False,
        "operations_blocker_progress_execution_followup_status_mismatch_count": (
            operations_blocker_progress_execution_followup["status_mismatch_count"]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else 0,
        "operations_blocker_progress_execution_followup_residual_mismatch_count": (
            operations_blocker_progress_execution_followup["residual_mismatch_count"]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else 0,
        "operations_blocker_progress_execution_followup_priority_mismatch_count": (
            operations_blocker_progress_execution_followup["priority_mismatch_count"]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else 0,
        "operations_blocker_progress_execution_followup_priority_sequence_ok": bool(
            operations_blocker_progress_execution_followup["priority_sequence_ok"]
        )
        if isinstance(operations_blocker_progress_execution_followup, dict)
        else False,
        "baseline_pathway_accuracy": (
            baseline_eval_s["pathway_accuracy"]
            if isinstance(baseline_eval_s := validation.get("baseline_eval_summary"), dict)
            else 0.0
        ),
        "baseline_false_positive_recall": (
            baseline_eval_s2["false_positive_recall"]
            if isinstance(
                baseline_eval_s2 := validation.get("baseline_eval_summary"), dict
            )
            else 0.0
        ),
        "baseline_total_cases": (
            baseline_eval_s3["total_cases"]
            if isinstance(
                baseline_eval_s3 := validation.get("baseline_eval_summary"), dict
            )
            else 0
        ),
        "target_watchlist_entry_count": (
            wl_s["entry_count"]
            if isinstance(wl_s := validation.get("target_watchlist_summary"), dict)
            else 0
        ),
        "target_watchlist_elevated_count": (
            wl_s2["elevated_count"]
            if isinstance(wl_s2 := validation.get("target_watchlist_summary"), dict)
            else 0
        ),
        "target_watchlist_conflict_count": (
            wl_s3["conflict_count"]
            if isinstance(wl_s3 := validation.get("target_watchlist_summary"), dict)
            else 0
        ),
        "baseline_misclassified_count": (
            be_m["misclassified_count"]
            if isinstance(be_m := validation.get("baseline_eval_summary"), dict)
            else 0
        ),
        "baseline_drift_count": (
            dr_s["drift_count"]
            if isinstance(dr_s := validation.get("baseline_pathway_drift_summary"), dict)
            else 0
        ),
        "candidate_lifecycle_entry_count": (
            lc_s["entry_count"]
            if isinstance(lc_s := validation.get("candidate_lifecycle_summary"), dict)
            else 0
        ),
        "observation_schedule_window_count": (
            os_s["window_count"]
            if isinstance(os_s := validation.get("observation_schedule_summary"), dict)
            else 0
        ),
        "false_negative_case_count": (
            fn_s["missed_count"]
            if isinstance(fn_s := validation.get("false_negative_summary"), dict)
            else 0
        ),
        "synthetic_missed_injection_rate": (
            fn_s2["synthetic_missed_injection_rate"]
            if isinstance(fn_s2 := validation.get("false_negative_summary"), dict)
            else 0.0
        ),
        "scoring_threshold_count": (
            sc_s["threshold_count"]
            if isinstance(sc_s := validation.get("scoring_config_summary"), dict)
            else 0
        ),
        "route_covered_pathway_count": (
            rc_s["covered_pathway_count"]
            if isinstance(rc_s := validation.get("route_coverage_summary"), dict)
            else 0
        ),
        "route_uncovered_pathway_count": (
            rc_s2["uncovered_pathway_count"]
            if isinstance(rc_s2 := validation.get("route_coverage_summary"), dict)
            else 0
        ),
        "lifecycle_invalid_transition_count": (
            lt_s["invalid_transition_count"]
            if isinstance(lt_s := validation.get("lifecycle_transition_summary"), dict)
            else 0
        ),
        "observation_completion_rate": (
            oe_s["completion_rate"]
            if isinstance(oe_s := validation.get("observation_efficiency_summary"), dict)
            else 0.0
        ),
        "observation_cancellation_rate": (
            oe_s2["cancellation_rate"]
            if isinstance(oe_s2 := validation.get("observation_efficiency_summary"), dict)
            else 0.0
        ),
        "sensitivity_track_count": (
            sc_t["track_count"]
            if isinstance(sc_t := validation.get("sensitivity_config_summary"), dict)
            else 0
        ),
        "sensitivity_weight_count": (
            sc_w["weight_count"]
            if isinstance(sc_w := validation.get("sensitivity_config_summary"), dict)
            else 0
        ),
        "triage_note_count": (
            tn_s["note_count"]
            if isinstance(tn_s := validation.get("triage_summary"), dict)
            else 0
        ),
        "triage_tracks_covered_count": (
            len(tn_t["tracks_covered"])
            if isinstance(tn_t := validation.get("triage_summary"), dict)
            else 0
        ),
        "signal_registry_signal_count": (
            sr_s["signal_count"]
            if isinstance(sr_s := validation.get("signal_registry_summary"), dict)
            else 0
        ),
        "signal_registry_active_count": (
            sr_a["active_count"]
            if isinstance(sr_a := validation.get("signal_registry_summary"), dict)
            else 0
        ),
        "audit_trail_action_count": (
            at_s["action_count"]
            if isinstance(at_s := validation.get("audit_trail_summary"), dict)
            else 0
        ),
        "audit_trail_unique_operator_count": (
            at_o["unique_operator_count"]
            if isinstance(at_o := validation.get("audit_trail_summary"), dict)
            else 0
        ),
        "multi_epoch_target_count": (
            me_s["multi_epoch_target_count"]
            if isinstance(me_s := validation.get("multi_epoch_summary"), dict)
            else 0
        ),
        "multi_epoch_consistent_detection_count": (
            me_c["consistent_detection_count"]
            if isinstance(me_c := validation.get("multi_epoch_summary"), dict)
            else 0
        ),
        "target_recalibration_snapshot_count": (
            tr_s["snapshot_count"]
            if isinstance(tr_s := validation.get("target_recalibration_summary"), dict)
            else 0
        ),
        "operator_coverage_count": (
            oc_s["operator_count"]
            if isinstance(oc_s := validation.get("operator_coverage_summary"), dict)
            else 0
        ),
        "triage_label_coverage_fraction": (
            lc_s2["coverage_fraction"]
            if isinstance(lc_s2 := validation.get("triage_label_completeness"), dict)
            else 0.0
        ),
        "classifier_rule_coverage_fraction": (
            rc_s2["coverage_fraction"]
            if isinstance(rc_s2 := validation.get("classifier_rule_coverage_summary"), dict)
            else 0.0
        ),
        "provenance_chain_validation_ok": (
            bool(pc_s["ok"])
            if isinstance(pc_s := validation.get("provenance_chain_validation"), dict)
            else False
        ),
        "schema_drift_count": (
            sd_s["drift_count"]
            if isinstance(sd_s := validation.get("schema_drift_summary"), dict)
            else 0
        ),
        "observation_notes_count": (
            on_s["note_count"]
            if isinstance(on_s := validation.get("observation_notes_summary"), dict)
            else 0
        ),
        "observation_notes_follow_up_count": (
            on_f["follow_up_recommended_count"]
            if isinstance(on_f := validation.get("observation_notes_summary"), dict)
            else 0
        ),
        "epoch_plan_entry_count": (
            ep_s["entry_count"]
            if isinstance(ep_s := validation.get("epoch_plan_summary"), dict)
            else 0
        ),
        "epoch_plan_pending_count": (
            ep_p["pending_count"]
            if isinstance(ep_p := validation.get("epoch_plan_summary"), dict)
            else 0
        ),
        "aggregate_blocker_count": (
            ab_s["total_blocker_count"]
            if isinstance(ab_s := validation.get("aggregate_blockers_summary"), dict)
            else 0
        ),
        "aggregate_blocker_unique_candidate_count": (
            ab_c["unique_candidate_count"]
            if isinstance(ab_c := validation.get("aggregate_blockers_summary"), dict)
            else 0
        ),
        "score_history_entry_count": (
            sh_s["entry_count"]
            if isinstance(sh_s := validation.get("score_history_summary"), dict)
            else 0
        ),
        "score_history_unique_candidate_count": (
            sh_c["unique_candidate_count"]
            if isinstance(sh_c := validation.get("score_history_summary"), dict)
            else 0
        ),
        "operator_assignment_count": (
            oa_s["assignment_count"]
            if isinstance(oa_s := validation.get("operator_assignment_summary"), dict)
            else 0
        ),
        "operator_assignment_escalated_count": (
            oa_e["escalated_count"]
            if isinstance(oa_e := validation.get("operator_assignment_summary"), dict)
            else 0
        ),
        "pipeline_health_total_blocked": (
            ph_s["total_blocked_count"]
            if isinstance(ph_s := validation.get("pipeline_health_summary"), dict)
            else 0
        ),
        "candidate_flag_count": (
            cf_s["flag_count"]
            if isinstance(cf_s := validation.get("candidate_flags_summary"), dict)
            else 0
        ),
        "candidate_flag_open_count": (
            cf_o["open_count"]
            if isinstance(cf_o := validation.get("candidate_flags_summary"), dict)
            else 0
        ),
        "review_deadline_count": (
            rd_s["deadline_count"]
            if isinstance(rd_s := validation.get("review_deadlines_summary"), dict)
            else 0
        ),
        "review_deadline_overdue_count": (
            rd_o["overdue_count"]
            if isinstance(rd_o := validation.get("review_deadlines_summary"), dict)
            else 0
        ),
        "pipeline_throughput_rate": (
            pt_s["throughput_rate"]
            if isinstance(pt_s := validation.get("pipeline_throughput_summary"), dict)
            else 0.0
        ),
        "retention_record_count": (
            cr_s["record_count"]
            if isinstance(cr_s := validation.get("candidate_retention_summary"), dict)
            else 0
        ),
        "retention_active_count": (
            cr_s2["active_count"]
            if isinstance(cr_s2 := validation.get("candidate_retention_summary"), dict)
            else 0
        ),
        "operator_performance_operator_count": (
            op_s["operator_count"]
            if isinstance(op_s := validation.get("operator_performance_summary"), dict)
            else 0
        ),
        "operator_performance_completion_rate": (
            op_s2["overall_completion_rate"]
            if isinstance(op_s2 := validation.get("operator_performance_summary"), dict)
            else 0.0
        ),
        "track_comparison_open_flags": (
            tc_s["total_open_flags"]
            if isinstance(tc_s := validation.get("track_comparison_summary"), dict)
            else 0
        ),
        "resolution_record_count": (
            rs_s["record_count"]
            if isinstance(rs_s := validation.get("candidate_resolution_summary"), dict)
            else 0
        ),
        "resolution_unresolved_count": (
            rs_s2["unresolved_count"]
            if isinstance(rs_s2 := validation.get("candidate_resolution_summary"), dict)
            else 0
        ),
        "escalation_entry_count": (
            es_s["entry_count"]
            if isinstance(es_s := validation.get("escalation_log_summary"), dict)
            else 0
        ),
        "escalation_open_count": (
            es_s2["open_count"]
            if isinstance(es_s2 := validation.get("escalation_log_summary"), dict)
            else 0
        ),
        "qc_overall_health": (
            qc_s["overall_qc_health"]
            if isinstance(qc_s := validation.get("quality_control_summary"), dict)
            else "ok"
        ),
        "observation_campaign_count": (
            oc_s["campaign_count"]
            if isinstance(oc_s := validation.get("observation_campaign_summary"), dict)
            else 0
        ),
        "observation_campaign_active_count": (
            oc_s2["active_count"]
            if isinstance(oc_s2 := validation.get("observation_campaign_summary"), dict)
            else 0
        ),
        "data_quality_entry_count": (
            dq_s["entry_count"]
            if isinstance(dq_s := validation.get("data_quality_log_summary"), dict)
            else 0
        ),
        "data_quality_poor_count": (
            dq_s2["poor_count"]
            if isinstance(dq_s2 := validation.get("data_quality_log_summary"), dict)
            else 0
        ),
        "pipeline_audit_action_count": (
            pa_s["total_audit_actions"]
            if isinstance(pa_s := validation.get("pipeline_audit_summary"), dict)
            else 0
        ),
        "follow_up_request_count": (
            fur_s["request_count"]
            if isinstance(fur_s := validation.get("follow_up_request_summary"), dict)
            else 0
        ),
        "follow_up_request_open_count": (
            fur_s2["open_count"]
            if isinstance(fur_s2 := validation.get("follow_up_request_summary"), dict)
            else 0
        ),
        "pipeline_bottleneck_stalled_count": (
            pb_s["total_stalled_candidates"]
            if isinstance(pb_s := validation.get("pipeline_bottleneck_summary"), dict)
            else 0
        ),
        "candidate_annotation_count": (
            ann_s["annotation_count"]
            if isinstance(ann_s := validation.get("candidate_annotation_summary"), dict)
            else 0
        ),
        "candidate_annotation_unresolved_count": (
            ann_s2["unresolved_count"]
            if isinstance(ann_s2 := validation.get("candidate_annotation_summary"), dict)
            else 0
        ),
        "session_log_count": (
            sl_s["session_count"]
            if isinstance(sl_s := validation.get("session_log_summary"), dict)
            else 0
        ),
        "session_log_completed_count": (
            sl_s2["completed_count"]
            if isinstance(sl_s2 := validation.get("session_log_summary"), dict)
            else 0
        ),
        "priority_queue_depth": (
            pq_s["queue_depth"]
            if isinstance(pq_s := validation.get("priority_queue_summary"), dict)
            else 0
        ),
        "pipeline_capacity_status": (
            pc_s["capacity_status"]
            if isinstance(pc_s := validation.get("pipeline_capacity_summary"), dict)
            else "unknown"
        ),
        "feature_vector_count": (
            fv_s["vector_count"]
            if isinstance(fv_s := validation.get("feature_vector_summary"), dict)
            else 0
        ),
        "ml_registry_entry_count": (
            mr_s["registry_count"]
            if isinstance(mr_s := validation.get("ml_model_registry_summary"), dict)
            else 0
        ),
        "ml_above_baseline_count": (
            mr_s2["above_baseline_count"]
            if isinstance(mr_s2 := validation.get("ml_model_registry_summary"), dict)
            else 0
        ),
        "ml_pipeline_status": (
            md_s["pipeline_ml_status"]
            if isinstance(md_s := validation.get("ml_pipeline_diagnostics_summary"), dict)
            else "unknown"
        ),
        "normalization_bounds_count": (
            fn_s["bounds_count"]
            if isinstance(fn_s := validation.get("feature_normalization_summary"), dict)
            else 0
        ),
        "feature_importance_entry_count": (
            fi_s["entry_count"]
            if isinstance(fi_s := validation.get("feature_importance_summary"), dict)
            else 0
        ),
        "ml_training_case_count": (
            mt_s["total_case_count"]
            if isinstance(mt_s := validation.get("ml_training_data_summary"), dict)
            else 0
        ),
        "ml_recommended_train_count": (
            mt_s2["recommended_train_count"]
            if isinstance(mt_s2 := validation.get("ml_training_data_summary"), dict)
            else 0
        ),
        "model_architecture_count": (
            ma_s["architecture_count"]
            if isinstance(ma_s := validation.get("model_architecture_summary"), dict)
            else 0
        ),
        "model_evaluation_count": (
            me_s["evaluation_count"]
            if isinstance(me_s := validation.get("model_evaluation_summary"), dict)
            else 0
        ),
        "model_evaluation_above_baseline_count": (
            me_s2["above_baseline_count"]
            if isinstance(me_s2 := validation.get("model_evaluation_summary"), dict)
            else 0
        ),
        "model_performance_snapshot_count": (
            ph_s["snapshot_count"]
            if isinstance(ph_s := validation.get("model_performance_history_summary"), dict)
            else 0
        ),
        "model_serving_record_count": (
            sv_s["record_count"]
            if isinstance(sv_s := validation.get("model_serving_summary"), dict)
            else 0
        ),
        "model_serving_active_count": (
            sv_s2["active_count"]
            if isinstance(sv_s2 := validation.get("model_serving_summary"), dict)
            else 0
        ),
        "scoring_audit_entry_count": (
            al_s["entry_count"]
            if isinstance(al_s := validation.get("scoring_audit_log_summary"), dict)
            else 0
        ),
        "curated_intake_record_count": (
            ci_s["record_count"]
            if isinstance(ci_s := validation.get("curated_dataset_intake_summary"), dict)
            else 0
        ),
        "curated_intake_approved_count": (
            ci_s2["approved_count"]
            if isinstance(ci_s2 := validation.get("curated_dataset_intake_summary"), dict)
            else 0
        ),
        "candidate_rescore_event_count": (
            rs_s["event_count"]
            if isinstance(rs_s := validation.get("candidate_rescore_summary"), dict)
            else 0
        ),
        "candidate_rescore_pathway_change_count": (
            rs_s2["pathway_change_count"]
            if isinstance(rs_s2 := validation.get("candidate_rescore_summary"), dict)
            else 0
        ),
        "operator_handoff_template_count": (
            oh_s["template_count"]
            if isinstance(oh_s := validation.get("operator_handoff_summary"), dict)
            else 0
        ),
        "operator_handoff_approved_count": (
            oh_s2["approved_count"]
            if isinstance(oh_s2 := validation.get("operator_handoff_summary"), dict)
            else 0
        ),
        "pipeline_config_count": (
            pc_s["config_count"]
            if isinstance(pc_s := validation.get("pipeline_config_summary"), dict)
            else 0
        ),
        "pipeline_active_count": (
            pc_s2["active_count"]
            if isinstance(pc_s2 := validation.get("pipeline_config_summary"), dict)
            else 0
        ),
        "submission_readiness_record_count": (
            sr_s["record_count"]
            if isinstance(sr_s := validation.get("submission_readiness_summary"), dict)
            else 0
        ),
        "submission_readiness_ready_count": (
            sr_s2["ready_count"]
            if isinstance(sr_s2 := validation.get("submission_readiness_summary"), dict)
            else 0
        ),
        "comparison_record_count": (
            cmp_s["record_count"]
            if isinstance(cmp_s := validation.get("candidate_comparison_summary"), dict)
            else 0
        ),
        "telemetry_entry_count": (
            tel_s["entry_count"]
            if isinstance(tel_s := validation.get("pipeline_telemetry_summary"), dict)
            else 0
        ),
        "provenance_audit_entry_count": (
            pa_s["entry_count"]
            if isinstance(pa_s := validation.get("provenance_audit_summary"), dict)
            else 0
        ),
        "provenance_audit_consistent_count": (
            pa_s2["consistent_count"]
            if isinstance(pa_s2 := validation.get("provenance_audit_summary"), dict)
            else 0
        ),
        "candidate_alert_entry_count": (
            al2_s["entry_count"]
            if isinstance(al2_s := validation.get("candidate_alert_summary"), dict)
            else 0
        ),
        "candidate_alert_open_count": (
            al2_s2["open_count"]
            if isinstance(al2_s2 := validation.get("candidate_alert_summary"), dict)
            else 0
        ),
        "pipeline_replay_entry_count": (
            rpl_s["entry_count"]
            if isinstance(rpl_s := validation.get("pipeline_replay_summary"), dict)
            else 0
        ),
        "pipeline_replay_matched_count": (
            rpl_s2["matched_count"]
            if isinstance(rpl_s2 := validation.get("pipeline_replay_summary"), dict)
            else 0
        ),
        "scoring_threshold_pass_count": (
            thr_s["pass_count"]
            if isinstance(thr_s := validation.get("scoring_threshold_audit_summary"), dict)
            else 0
        ),
        "scoring_threshold_fail_count": (
            thr_s2["fail_count"]
            if isinstance(thr_s2 := validation.get("scoring_threshold_audit_summary"), dict)
            else 0
        ),
        "alert_resolution_entry_count": (
            ares_s["entry_count"]
            if isinstance(ares_s := validation.get("alert_resolution_summary"), dict)
            else 0
        ),
        "alert_resolution_open_count": (
            ares_s2["open_count"]
            if isinstance(ares_s2 := validation.get("alert_resolution_summary"), dict)
            else 0
        ),
        "config_history_entry_count": (
            cfgh_s["entry_count"]
            if isinstance(cfgh_s := validation.get("config_version_history_summary"), dict)
            else 0
        ),
        "operator_escalation_entry_count": (
            esc_s["entry_count"]
            if isinstance(esc_s := validation.get("operator_escalation_summary"), dict)
            else 0
        ),
        "operator_escalation_open_count": (
            esc_s2["open_count"]
            if isinstance(esc_s2 := validation.get("operator_escalation_summary"), dict)
            else 0
        ),
        "candidate_deduplication_entry_count": (
            dd_s["entry_count"]
            if isinstance(dd_s := validation.get("candidate_deduplication_summary"), dict)
            else 0
        ),
        "candidate_deduplication_pending_count": (
            dd_s2["pending_count"]
            if isinstance(dd_s2 := validation.get("candidate_deduplication_summary"), dict)
            else 0
        ),
        "intake_queue_entry_count": (
            iq_s["entry_count"]
            if isinstance(iq_s := validation.get("intake_queue_summary"), dict)
            else 0
        ),
        "intake_queue_blocked_count": (
            iq_s2["blocked_count"]
            if isinstance(iq_s2 := validation.get("intake_queue_summary"), dict)
            else 0
        ),
        "workflow_state_entry_count": (
            wf_s["entry_count"]
            if isinstance(wf_s := validation.get("workflow_state_summary"), dict)
            else 0
        ),
        "data_gap_entry_count": (
            dg_s["entry_count"]
            if isinstance(dg_s := validation.get("data_gap_summary"), dict)
            else 0
        ),
        "data_gap_unresolved_count": (
            dg_s2["unresolved_count"]
            if isinstance(dg_s2 := validation.get("data_gap_summary"), dict)
            else 0
        ),
        "candidate_match_entry_count": (
            cm_s["entry_count"]
            if isinstance(cm_s := validation.get("candidate_match_summary"), dict)
            else 0
        ),
        "candidate_match_matched_count": (
            cm_s2["matched_count"]
            if isinstance(cm_s2 := validation.get("candidate_match_summary"), dict)
            else 0
        ),
        "pipeline_error_entry_count": (
            pe_s["entry_count"]
            if isinstance(pe_s := validation.get("pipeline_error_summary"), dict)
            else 0
        ),
        "pipeline_error_unresolved_count": (
            pe_s2["unresolved_count"]
            if isinstance(pe_s2 := validation.get("pipeline_error_summary"), dict)
            else 0
        ),
        "observation_request_entry_count": (
            or_s["entry_count"]
            if isinstance(or_s := validation.get("observation_request_summary"), dict)
            else 0
        ),
        "observation_request_pending_count": (
            or_s2["pending_count"]
            if isinstance(or_s2 := validation.get("observation_request_summary"), dict)
            else 0
        ),
        "candidate_export_entry_count": (
            ce_s["entry_count"]
            if isinstance(ce_s := validation.get("candidate_export_summary"), dict)
            else 0
        ),
        "candidate_export_delivered_count": (
            ce_s2["delivered_count"]
            if isinstance(ce_s2 := validation.get("candidate_export_summary"), dict)
            else 0
        ),
        "quality_gate_entry_count": (
            qg_s["entry_count"]
            if isinstance(qg_s := validation.get("quality_gate_summary"), dict)
            else 0
        ),
        "quality_gate_pass_count": (
            qg_s2["pass_count"]
            if isinstance(qg_s2 := validation.get("quality_gate_summary"), dict)
            else 0
        ),
        "instrument_log_entry_count": (
            il_s["entry_count"]
            if isinstance(il_s := validation.get("instrument_log_summary"), dict)
            else 0
        ),
        "archival_query_entry_count": (
            aq_s["entry_count"]
            if isinstance(aq_s := validation.get("archival_query_summary"), dict)
            else 0
        ),
        "candidate_linkage_entry_count": (
            cl_s["entry_count"]
            if isinstance(cl_s := validation.get("candidate_linkage_summary"), dict)
            else 0
        ),
        "candidate_linkage_confirmed_count": (
            cl_s2["confirmed_count"]
            if isinstance(cl_s2 := validation.get("candidate_linkage_summary"), dict)
            else 0
        ),
        "signal_classification_entry_count": (
            sc_s["entry_count"]
            if isinstance(sc_s := validation.get("signal_classification_summary"), dict)
            else 0
        ),
        "signal_classification_classified_count": (
            sc_s2["classified_count"]
            if isinstance(sc_s2 := validation.get("signal_classification_summary"), dict)
            else 0
        ),
        "rfi_mitigation_entry_count": (
            rm_s["entry_count"]
            if isinstance(rm_s := validation.get("rfi_mitigation_summary"), dict)
            else 0
        ),
        "rfi_mitigation_flagged_count": (
            rm_s2["flagged_count"]
            if isinstance(rm_s2 := validation.get("rfi_mitigation_summary"), dict)
            else 0
        ),
        "candidate_annotation_entry_count": (
            cal_s["entry_count"]
            if isinstance(cal_s := validation.get("candidate_annotation_log_summary"), dict)
            else 0
        ),
        "candidate_annotation_active_count": (
            cal_s2["active_count"]
            if isinstance(cal_s2 := validation.get("candidate_annotation_log_summary"), dict)
            else 0
        ),
        "frequency_channel_entry_count": (
            fc_s["entry_count"]
            if isinstance(fc_s := validation.get("frequency_channel_log_summary"), dict)
            else 0
        ),
        "frequency_channel_active_count": (
            fc_s2["active_count"]
            if isinstance(fc_s2 := validation.get("frequency_channel_log_summary"), dict)
            else 0
        ),
        "pipeline_checkpoint_entry_count": (
            pck_s["entry_count"]
            if isinstance(pck_s := validation.get("pipeline_checkpoint_log_summary"), dict)
            else 0
        ),
        "pipeline_checkpoint_saved_count": (
            pck_s2["saved_count"]
            if isinstance(pck_s2 := validation.get("pipeline_checkpoint_log_summary"), dict)
            else 0
        ),
        "candidate_status_entry_count": (
            csl_s["entry_count"]
            if isinstance(csl_s := validation.get("candidate_status_log_summary"), dict)
            else 0
        ),
        "candidate_status_active_count": (
            csl_s2["active_count"]
            if isinstance(csl_s2 := validation.get("candidate_status_log_summary"), dict)
            else 0
        ),
        "recommended_commands": [
            ".venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing",
            ".venv/bin/ruff check .",
            ".venv/bin/mypy src",
            "git diff --check",
        ],
    }


def provenance_summary(report_dir: Path | str) -> dict[str, object]:
    """Summarize provenance across per-candidate report manifests."""

    directory = Path(report_dir)
    manifest_paths = sorted(directory.glob("*.manifest.json"))
    manifests = []
    for path in manifest_paths:
        with path.open(encoding="utf-8") as handle:
            manifests.append(json.load(handle))

    return {
        "report_dir": str(directory),
        "manifest_count": len(manifests),
        "candidate_ids": sorted(str(manifest["candidate_id"]) for manifest in manifests),
        "by_track": dict(sorted(Counter(str(manifest["track"]) for manifest in manifests).items())),
        "by_schema_version": dict(
            sorted(Counter(str(manifest["schema_version"]) for manifest in manifests).items())
        ),
        "by_config_version": dict(
            sorted(Counter(str(manifest["config_version"]) for manifest in manifests).items())
        ),
        "by_source_dataset": dict(
            sorted(
                Counter(
                    str(manifest.get("provenance_summary", {}).get("source_dataset", "unknown"))
                    for manifest in manifests
                ).items()
            )
        ),
    }


def live_provider_summary() -> dict[str, object]:
    """Return configured live-provider adapter metadata without network access."""

    adapters = provider_adapters()
    return {
        "live_enabled": live_data_enabled(),
        "provider_count": len(adapters),
        "providers": [
            {
                "provider_name": adapter.provider_name,
                "service_url": adapter.service_url,
            }
            for adapter in adapters
        ],
    }


def live_cache_summary(cache_dir: Path | None = None) -> dict[str, object]:
    """Return configured live-provider cache metadata without network access."""

    cache = LiveProviderCache.from_config() if cache_dir is None else LiveProviderCache(cache_dir)
    return cache.summary()


def catalog_cache_policy_summary(cache_root: Path | None = None) -> dict[str, object]:
    """Return catalog cache policy metadata without creating cache files."""

    policy = (
        CatalogCachePolicy.from_config()
        if cache_root is None
        else CatalogCachePolicy(cache_root)
    )
    return policy.as_dict()


def catalog_cache_summary(cache_root: Path | None = None) -> dict[str, object]:
    """Return local catalog cache metadata counts without reading payloads."""

    cache = (
        CatalogCache.from_config()
        if cache_root is None
        else CatalogCache(CatalogCachePolicy(cache_root))
    )
    return cache.summary()


def catalog_cache_validation_summary(
    paths: Sequence[Path | str],
    *,
    project_root: Path | str | None = None,
) -> dict[str, object]:
    """Validate catalog cache commit paths for release and pre-commit checks."""

    return validate_catalog_cache_commit_paths(paths, project_root=project_root)


def git_tracked_paths(project_root: Path | str) -> list[Path]:
    """Return Git-tracked paths for repository-scoped release checks."""

    root = Path(project_root)
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [root / line for line in result.stdout.splitlines() if line]


def _sqlite_log_track_summary(db_path: Path) -> dict[str, object]:
    """Return run/outcome counts broken down by track from the SQLite log."""
    import sqlite3
    from contextlib import closing

    if not db_path.exists():
        return {
            "ok": False,
            "error": "database does not exist",
            "by_track": {},
        }
    try:
        with closing(sqlite3.connect(db_path)) as conn:
            rows = conn.execute(
                "SELECT track, COUNT(*) FROM background_runs GROUP BY track"
            ).fetchall()
            by_track = {str(row[0]): int(row[1]) for row in rows}
        return {"ok": True, "by_track": by_track, "track_count": len(by_track)}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "by_track": {}}


def _project_health_summary(out: TextIO | None = None) -> dict[str, object]:
    """Concise health dashboard combining key gate statuses."""
    baseline = evaluate_baseline()
    wl = target_watchlist_summary()
    schema_count = len(schema_paths())
    baseline_accuracy = float(baseline.get("pathway_accuracy", 0.0))
    baseline_ok = baseline_accuracy >= 0.80
    watchlist_conflicts = int(wl.get("conflict_count", 0))
    watchlist_ok = watchlist_conflicts == 0
    drift = baseline_pathway_drift_summary()
    drift_ok = bool(drift.get("zero_drift", True))
    all_gates = baseline_ok and watchlist_ok and drift_ok
    return {
        "all_gates_pass": all_gates,
        "schema_count": schema_count,
        "baseline_pathway_accuracy": baseline_accuracy,
        "baseline_accuracy_gate_ok": baseline_ok,
        "watchlist_conflict_count": watchlist_conflicts,
        "watchlist_gate_ok": watchlist_ok,
        "baseline_drift_count": drift.get("drift_count", 0),
        "baseline_drift_gate_ok": drift_ok,
        "recommended_action": (
            "Run `techno-search validate-all` for detailed diagnostics."
            if not all_gates
            else "All health gates pass."
        ),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="techno-search",
        description="Score synthetic technosignature-interest candidate packets.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    score_parser = subparsers.add_parser(
        "score",
        help="Score a normalized synthetic candidate JSON file.",
    )
    score_parser.add_argument("input", type=Path, help="Input candidate JSON path.")
    score_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional directory for Markdown and JSON review packets.",
    )
    score_parser.add_argument(
        "--prefix",
        help="Optional safe filename prefix for written reports.",
    )
    score_parser.add_argument(
        "--no-plot-artifacts",
        action="store_true",
        help="Skip dependency-free synthetic SVG diagnostic artifacts.",
    )
    batch_parser = subparsers.add_parser(
        "score-batch",
        help="Score all normalized synthetic candidate JSON files in a directory.",
    )
    batch_parser.add_argument("input_dir", type=Path, help="Input candidate JSON directory.")
    batch_parser.add_argument("output_dir", type=Path, help="Output report directory.")
    batch_parser.add_argument(
        "--prefix",
        default="",
        help="Optional filename prefix prepended to each candidate ID.",
    )
    batch_parser.add_argument(
        "--no-plot-artifacts",
        action="store_true",
        help="Skip dependency-free synthetic SVG diagnostic artifacts.",
    )
    calibration_parser = subparsers.add_parser(
        "calibration-summary",
        help="Summarize synthetic calibration fixture coverage.",
    )
    calibration_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional calibration fixture JSON path.",
    )
    false_positive_parser = subparsers.add_parser(
        "false-positive-summary",
        help="Summarize synthetic false-positive classes by track.",
    )
    false_positive_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional calibration fixture JSON path.",
    )
    calibration_track_parser = subparsers.add_parser(
        "calibration-track-summary",
        help="Summarize synthetic calibration fixture coverage within each track.",
    )
    calibration_track_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional calibration fixture JSON path.",
    )
    validate_candidate_parser = subparsers.add_parser(
        "validate-candidate",
        help="Validate a normalized synthetic candidate JSON file.",
    )
    validate_candidate_parser.add_argument("input", type=Path, help="Input candidate JSON path.")
    validate_reports_parser = subparsers.add_parser(
        "validate-reports",
        help="Validate generated candidate report packets and manifests in a directory.",
    )
    validate_reports_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing generated candidate reports.",
    )
    subparsers.add_parser(
        "schema-paths",
        help="Print local JSON schema artifact paths.",
    )
    score_regression_parser = subparsers.add_parser(
        "score-regression-summary",
        help="Summarize score regression snapshot coverage.",
    )
    score_regression_parser.add_argument(
        "--snapshot-path",
        type=Path,
        help="Optional score regression snapshot JSON path.",
    )
    injection_recovery_parser = subparsers.add_parser(
        "injection-recovery-summary",
        help="Summarize synthetic injection-recovery fixture coverage.",
    )
    injection_recovery_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic injection-recovery fixture JSON path.",
    )
    reliability_parser = subparsers.add_parser(
        "reliability-summary",
        help="Summarize synthetic reliability curve fixture coverage.",
    )
    reliability_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic reliability fixture JSON path.",
    )
    precision_recall_parser = subparsers.add_parser(
        "precision-recall-summary",
        help="Summarize synthetic precision-recall fixture coverage.",
    )
    precision_recall_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic precision-recall fixture JSON path.",
    )
    review_queue_parser = subparsers.add_parser(
        "review-queue-summary",
        help="Summarize synthetic human-review queue fixture coverage.",
    )
    review_queue_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic human-review queue fixture JSON path.",
    )
    consensus_parser = subparsers.add_parser(
        "consensus-summary",
        help="Summarize synthetic human-review consensus label fixture coverage.",
    )
    consensus_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic human-review consensus fixture JSON path.",
    )
    consensus_export_parser = subparsers.add_parser(
        "consensus-export-summary",
        help="Summarize synthetic human-review consensus export fixture coverage.",
    )
    consensus_export_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional synthetic human-review consensus export fixture JSON path.",
    )
    cross_track_parser = subparsers.add_parser(
        "cross-track-summary",
        help=(
            "Summarize cross-track candidate cross-reference fixture coverage. "
            "Cross-references are operational metadata only and never modify "
            "candidate scores or pathways."
        ),
    )
    cross_track_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional cross-track reference fixture JSON path.",
    )
    verify_repro_parser = subparsers.add_parser(
        "verify-report-reproducibility",
        help=(
            "Re-score persisted candidate packets and report drift vs. their "
            "manifests. Read-only; never auto-corrects historical artifacts."
        ),
    )
    verify_repro_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing per-candidate manifests and JSON packets.",
    )
    validation_dataset_parser = subparsers.add_parser(
        "validation-dataset-summary",
        help="Summarize validation dataset manifest coverage.",
    )
    validation_dataset_parser.add_argument(
        "--manifest-path",
        type=Path,
        help="Optional validation dataset manifest JSON path.",
    )
    validation_promotion_parser = subparsers.add_parser(
        "validation-promotion-summary",
        help="Summarize validation dataset promotion rule coverage.",
    )
    validation_promotion_parser.add_argument(
        "--rules-path",
        type=Path,
        help="Optional validation promotion rules JSON path.",
    )
    validation_readiness_parser = subparsers.add_parser(
        "validation-readiness-summary",
        help="Summarize validation dataset readiness review coverage.",
    )
    validation_readiness_parser.add_argument(
        "--readiness-path",
        type=Path,
        help="Optional validation readiness JSON path.",
    )
    benchmark_metadata_parser = subparsers.add_parser(
        "benchmark-metadata-summary",
        help="Summarize local synthetic validation benchmark metadata.",
    )
    benchmark_metadata_parser.add_argument(
        "--metadata-path",
        type=Path,
        help="Optional benchmark metadata JSON path.",
    )
    benchmark_run_parser = subparsers.add_parser(
        "benchmark-run-summary",
        help="Summarize local synthetic benchmark run-result metadata.",
    )
    benchmark_run_parser.add_argument(
        "--results-path",
        type=Path,
        help="Optional benchmark run-result JSON path.",
    )
    benchmark_append_parser = subparsers.add_parser(
        "benchmark-run-append",
        help="Append one local synthetic benchmark run-result entry.",
    )
    benchmark_append_parser.add_argument(
        "--results-path",
        type=Path,
        required=True,
        help="Benchmark run-result JSON path to create or append.",
    )
    benchmark_append_parser.add_argument("--run-id", required=True)
    benchmark_append_parser.add_argument("--command-name", required=True)
    benchmark_append_parser.add_argument("--command-kind", required=True)
    benchmark_append_parser.add_argument("--status", required=True)
    benchmark_append_parser.add_argument("--worker-count", type=int, required=True)
    benchmark_append_parser.add_argument("--input-case-count", type=int, required=True)
    benchmark_append_parser.add_argument("--duration-seconds", type=float, required=True)
    benchmark_append_parser.add_argument("--git-commit", required=True)
    benchmark_append_parser.add_argument("--config-version", required=True)
    benchmark_compare_parser = subparsers.add_parser(
        "benchmark-run-compare",
        help="Compare repeated local synthetic benchmark run-result entries.",
    )
    benchmark_compare_parser.add_argument(
        "--results-path",
        type=Path,
        help="Optional benchmark run-result JSON path.",
    )
    target_priority_parser = subparsers.add_parser(
        "target-priority-summary",
        help="Summarize background target-priority fixture coverage.",
    )
    target_priority_parser.add_argument(
        "--target-path",
        type=Path,
        help="Optional background target-priority JSON path.",
    )
    target_priority_parser.add_argument(
        "--config-path",
        type=Path,
        help="Optional background priority config JSON path.",
    )
    target_priority_parser.add_argument(
        "--ledger-path",
        type=Path,
        help="Optional background search ledger path for review-history scoring.",
    )
    background_ledger_parser = subparsers.add_parser(
        "background-ledger-summary",
        help="Summarize passive/background search ledger fixture coverage.",
    )
    background_ledger_parser.add_argument(
        "--ledger-path",
        type=Path,
        help="Optional background search ledger JSON path.",
    )
    background_review_parser = subparsers.add_parser(
        "background-reviewed-workflow-summary",
        help="Summarize reviewed workflow semantics in the background ledger.",
    )
    background_review_parser.add_argument(
        "--ledger-path",
        type=Path,
        help="Optional background search ledger JSON path.",
    )
    reviewed_log_parser = subparsers.add_parser(
        "reviewed-log-summary",
        help="Summarize reviewed background-search outcome records.",
    )
    reviewed_log_parser.add_argument(
        "--reviewed-log-path",
        type=Path,
        help="Optional reviewed background-search log JSON path.",
    )
    needs_follow_up_parser = subparsers.add_parser(
        "needs-follow-up-summary",
        help="Summarize background-search outcomes that require follow-up.",
    )
    needs_follow_up_parser.add_argument(
        "--needs-follow-up-log-path",
        type=Path,
        help="Optional needs-follow-up background-search log JSON path.",
    )
    follow_up_tests_parser = subparsers.add_parser(
        "follow-up-test-summary",
        help="Summarize deterministic local follow-up test results.",
    )
    follow_up_tests_parser.add_argument(
        "--follow-up-tests-path",
        type=Path,
        help="Optional background follow-up test result JSON path.",
    )
    report_readiness_parser = subparsers.add_parser(
        "report-readiness-summary",
        help="Summarize report-readiness gates for follow-up records.",
    )
    report_readiness_parser.add_argument(
        "--report-readiness-path",
        type=Path,
        help="Optional background report-readiness JSON path.",
    )
    draft_report_parser = subparsers.add_parser(
        "draft-follow-up-report-summary",
        help="Generate conservative draft report summaries from readiness records.",
    )
    draft_report_parser.add_argument(
        "--report-readiness-path",
        type=Path,
        help="Optional background report-readiness JSON path.",
    )
    draft_write_parser = subparsers.add_parser(
        "draft-follow-up-report-write",
        help="Write conservative draft follow-up reports as Markdown files.",
    )
    draft_write_parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for draft Markdown reports and manifest.",
    )
    draft_write_parser.add_argument(
        "--report-readiness-path",
        type=Path,
        help="Optional background report-readiness JSON path.",
    )
    validate_draft_parser = subparsers.add_parser(
        "validate-draft-reports",
        help="Validate persisted conservative draft follow-up reports.",
    )
    validate_draft_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing draft report Markdown and manifest.",
    )
    draft_fixture_parser = subparsers.add_parser(
        "draft-report-fixture-summary",
        help="Summarize committed conservative draft follow-up report fixtures.",
    )
    draft_fixture_parser.add_argument(
        "--draft-report-path",
        type=Path,
        help="Optional background draft follow-up report JSON path.",
    )
    user_decision_parser = subparsers.add_parser(
        "user-decision-summary",
        help="Summarize explicit user decision records for background reports.",
    )
    user_decision_parser.add_argument(
        "--user-decision-path",
        type=Path,
        help="Optional background user decision JSON path.",
    )
    user_decision_record_parser = subparsers.add_parser(
        "user-decision-record",
        help="Append one explicit local user decision record.",
    )
    user_decision_record_parser.add_argument(
        "--user-decision-path",
        type=Path,
        required=True,
        help="User decision JSON path to create or append.",
    )
    user_decision_record_parser.add_argument("--decision-id", required=True)
    user_decision_record_parser.add_argument("--readiness-id", required=True)
    user_decision_record_parser.add_argument("--follow-up-id", required=True)
    user_decision_record_parser.add_argument("--target-id", required=True)
    user_decision_record_parser.add_argument(
        "--track",
        required=True,
        choices=["radio", "infrared", "anomaly"],
    )
    user_decision_record_parser.add_argument(
        "--decision",
        required=True,
        choices=["approve_submission", "request_more_tests", "close_as_reviewed"],
    )
    user_decision_record_parser.add_argument("--rationale", required=True)
    user_decision_record_parser.add_argument("--decided-at-utc")
    user_decision_record_parser.add_argument(
        "--required-next-action",
        action="append",
        default=[],
    )
    user_decision_record_parser.add_argument(
        "--blocking-issue",
        action="append",
        default=[],
    )
    user_decision_record_parser.add_argument("--submission-destination")
    user_decision_record_parser.add_argument(
        "--confirm-external-submission-approval",
        action="store_true",
        help=(
            "Explicitly approve external submission. Required with "
            "approve_submission and never inferred for other decisions."
        ),
    )
    submission_recommendation_parser = subparsers.add_parser(
        "submission-recommendation-summary",
        help="Summarize top-three conservative submission recommendations.",
    )
    submission_recommendation_parser.add_argument(
        "--report-readiness-path",
        type=Path,
        help="Optional background report-readiness JSON path.",
    )
    handoff_parser = subparsers.add_parser(
        "candidate-extraction-handoff-summary",
        help="Summarize local-only candidate extraction handoff readiness.",
    )
    handoff_parser.add_argument(
        "--handoff-path",
        type=Path,
        help="Optional candidate extraction handoff JSON path.",
    )
    background_run_parser = subparsers.add_parser(
        "background-run-once",
        help="Append one explicit local-only background search ledger entry.",
    )
    background_run_parser.add_argument(
        "--ledger-path",
        type=Path,
        required=True,
        help="Background search ledger JSON path to create or append.",
    )
    background_run_parser.add_argument(
        "--reviewed-log-path",
        type=Path,
        help=(
            "Reviewed outcome log path. Defaults to background_reviewed_log.json "
            "next to the ledger."
        ),
    )
    background_run_parser.add_argument(
        "--needs-follow-up-log-path",
        type=Path,
        help=(
            "Needs-follow-up outcome log path. Defaults to "
            "background_needs_follow_up_log.json next to the ledger."
        ),
    )
    background_run_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help=(
            "Optional top-level SQLite log database path. Recommended operational "
            "default: logs/techno_search.sqlite3."
        ),
    )
    background_run_parser.add_argument(
        "--target-path",
        type=Path,
        help="Optional background target-priority JSON path.",
    )
    background_run_parser.add_argument(
        "--config-path",
        type=Path,
        help="Optional background priority config JSON path.",
    )
    background_run_parser.add_argument(
        "--run-id",
        help="Optional stable run ID for reproducibility.",
    )
    background_run_parser.add_argument(
        "--code-commit",
        default="not-recorded",
        help="Optional code commit or workspace identifier to record in the ledger.",
    )
    background_run_parser.add_argument(
        "--acknowledge-local-run",
        action="store_true",
        required=True,
        help="Required opt-in flag acknowledging this local runner does not use network data.",
    )
    init_logs_parser = subparsers.add_parser(
        "init-logs",
        help="Initialize the top-level SQLite operational log database.",
    )
    init_logs_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    init_logs_parser.add_argument(
        "--code-commit",
        default="not-recorded",
        help="Optional code commit or workspace identifier to store in metadata.",
    )
    init_logs_parser.add_argument(
        "--config-version",
        default="not-recorded",
        help="Optional config version to store in metadata.",
    )
    sqlite_summary_parser = subparsers.add_parser(
        "sqlite-log-summary",
        help="Summarize top-level SQLite operational logs.",
    )
    sqlite_summary_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_integrity_parser = subparsers.add_parser(
        "sqlite-log-integrity-summary",
        help="Summarize scheduler-facing SQLite log integrity checks.",
    )
    sqlite_integrity_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_bootstrap_parser = subparsers.add_parser(
        "sqlite-log-bootstrap-summary",
        help=(
            "Initialize local SQLite logs and report integrity, weekly digest, "
            "and operations-readiness SQLite gate visibility."
        ),
    )
    sqlite_bootstrap_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_bootstrap_parser.add_argument(
        "--code-commit",
        default="not-recorded",
        help="Optional code commit or workspace identifier to store in metadata.",
    )
    sqlite_bootstrap_parser.add_argument(
        "--config-version",
        default="not-recorded",
        help="Optional config version to store in metadata.",
    )
    sqlite_bootstrap_parser.add_argument(
        "--window-days",
        type=int,
        default=7,
        help="Weekly digest reporting window in days (default 7).",
    )
    sqlite_export_parser = subparsers.add_parser(
        "sqlite-log-export",
        help="Export a small review-safe JSON summary from SQLite logs.",
    )
    sqlite_export_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_export_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum recent runs and follow-up outcomes to include.",
    )
    sqlite_recent_runs_parser = subparsers.add_parser(
        "sqlite-recent-runs",
        help="List recent background runs from SQLite logs.",
    )
    sqlite_recent_runs_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_recent_runs_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum recent runs to include.",
    )
    sqlite_follow_up_parser = subparsers.add_parser(
        "sqlite-needs-follow-up",
        help="List recent needs-follow-up outcomes from SQLite logs.",
    )
    sqlite_follow_up_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_follow_up_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum needs-follow-up outcomes to include.",
    )
    sqlite_migration_parser = subparsers.add_parser(
        "sqlite-migration-summary",
        help="Report SQLite log schema migration status.",
    )
    sqlite_migration_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_migrate_parser = subparsers.add_parser(
        "sqlite-log-migrate",
        help=(
            "Print a non-destructive SQLite log migration plan. Apply mode is "
            "blocked until a destructive migration is reviewed and added."
        ),
    )
    sqlite_migrate_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_migrate_parser.add_argument(
        "--target-version",
        default=TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
        help="Target schema version. Defaults to the latest supported version.",
    )
    sqlite_migrate_parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Apply mode is currently blocked because no destructive migration is "
            "implemented. Reserved for future explicit migrations."
        ),
    )
    sqlite_pragmas_parser = subparsers.add_parser(
        "sqlite-log-pragmas",
        help="Report SQLite PRAGMA diagnostics for operator checks.",
    )
    sqlite_pragmas_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_retention_parser = subparsers.add_parser(
        "sqlite-log-retention-summary",
        help="Report SQLite log database age, size, and backup coverage.",
    )
    sqlite_retention_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_retention_parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Optional SQLite backup directory. Defaults to logs/backups.",
    )
    sqlite_backup_parser = subparsers.add_parser(
        "sqlite-log-backup",
        help="Create a timestamped local SQLite log backup under ignored logs/backups.",
    )
    sqlite_backup_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_backup_parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Optional SQLite backup directory. Defaults to logs/backups.",
    )
    sqlite_vacuum_parser = subparsers.add_parser(
        "sqlite-log-vacuum",
        help="Compact a local SQLite log database with VACUUM.",
    )
    sqlite_vacuum_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_digest_parser = subparsers.add_parser(
        "sqlite-log-weekly-digest",
        help=(
            "Print a review-safe rolling digest of SQLite operational logs. "
            "Read-only and does not expose payload contents."
        ),
    )
    sqlite_digest_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    sqlite_digest_parser.add_argument(
        "--window-days",
        type=int,
        default=7,
        help="Reporting window in days (default 7).",
    )
    sqlite_commit_guard_parser = subparsers.add_parser(
        "sqlite-log-commit-guard",
        help="Reject generated top-level SQLite log databases in commit paths.",
    )
    sqlite_commit_guard_parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help=(
            "Optional paths to validate. Defaults to Git-tracked paths when omitted."
        ),
    )
    validate_sqlite_parser = subparsers.add_parser(
        "validate-sqlite-logs",
        help="Validate top-level SQLite operational log invariants.",
    )
    validate_sqlite_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    scheduler_dry_run_parser = subparsers.add_parser(
        "scheduler-dry-run",
        help="Run the bounded local scheduler path against a temporary artifact directory.",
    )
    scheduler_dry_run_parser.add_argument(
        "--artifact-dir",
        type=Path,
        required=True,
        help="Temporary artifact directory for dry-run ledger and outcome logs.",
    )
    scheduler_dry_run_parser.add_argument(
        "--run-id",
        default="scheduler-dry-run",
    )
    scheduler_dry_run_parser.add_argument(
        "--code-commit",
        default="dry-run",
    )
    scheduler_dry_run_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help=(
            "Optional SQLite log database path. Defaults to background_logs.sqlite3 "
            "inside the dry-run artifact directory."
        ),
    )
    subparsers.add_parser(
        "validate-all",
        help=(
            "Run local validation summaries for examples, reports, schemas, "
            "calibration, and score snapshots."
        ),
    )
    subparsers.add_parser(
        "validation-summary",
        help="Print a concise local health dashboard without network access.",
    )
    subparsers.add_parser(
        "regenerate-examples",
        help="Regenerate committed example reports from examples/candidates.",
    )
    provenance_parser = subparsers.add_parser(
        "provenance-summary",
        help="Summarize provenance fields across report manifests in a directory.",
    )
    provenance_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing per-candidate report manifests.",
    )
    plot_artifact_parser = subparsers.add_parser(
        "plot-artifact-summary",
        help="Summarize plot artifact entries across report manifests in a directory.",
    )
    plot_artifact_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing per-candidate report manifests.",
    )
    subparsers.add_parser(
        "live-provider-summary",
        help="Print configured live-provider adapter names, URLs, and live-enabled status.",
    )
    live_cache_parser = subparsers.add_parser(
        "live-cache-summary",
        help="Print live-provider cache directory metadata without reading payloads.",
    )
    live_cache_parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Optional live-provider cache directory override.",
    )
    live_fixture_parser = subparsers.add_parser(
        "live-fixture-summary",
        help="Print committed live-metadata fixture coverage without network access.",
    )
    live_fixture_parser.add_argument(
        "--fixture-dir",
        type=Path,
        help="Optional live-metadata fixture directory override.",
    )
    subparsers.add_parser(
        "live-client-summary",
        help="Print configured live-client skeleton status without network access.",
    )
    catalog_cache_parser = subparsers.add_parser(
        "catalog-cache-policy",
        help="Print future catalog cache metadata policy without creating cache files.",
    )
    catalog_cache_parser.add_argument(
        "--cache-root",
        type=Path,
        help="Optional catalog cache metadata root override.",
    )
    catalog_cache_summary_parser = subparsers.add_parser(
        "catalog-cache-summary",
        help="Print catalog cache metadata counts without reading catalog payloads.",
    )
    catalog_cache_summary_parser.add_argument(
        "--cache-root",
        type=Path,
        help="Optional catalog cache metadata root override.",
    )
    catalog_cache_validate_parser = subparsers.add_parser(
        "catalog-cache-validate",
        help="Validate paths for forbidden committed catalog cache locations.",
    )
    catalog_cache_validate_parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Paths to validate before commit or release.",
    )
    baseline_eval_parser = subparsers.add_parser(
        "baseline-eval-summary",
        help=(
            "Evaluate the rule-based interpretable baseline classifier against "
            "synthetic calibration fixtures. Results are local diagnostics only — "
            "not detections, discoveries, or external validation."
        ),
    )
    baseline_eval_parser.add_argument(
        "--calibration-fixture",
        type=Path,
        help="Optional calibration false-positive fixture JSON path.",
    )
    baseline_eval_parser.add_argument(
        "--example-candidates-dir",
        type=Path,
        help="Optional example candidates directory.",
    )
    target_watchlist_parser = subparsers.add_parser(
        "target-watchlist-summary",
        help=(
            "Summarize operator target watchlist fixture coverage. "
            "Watchlist entries are scheduling aids only — they do not modify "
            "candidate scores or pathway routing."
        ),
    )
    target_watchlist_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional target watchlist fixture JSON path.",
    )
    weekly_review_parser = subparsers.add_parser(
        "weekly-review-template",
        help=(
            "Generate an operator weekly review template combining the SQLite log "
            "weekly digest and cross-track summary. Operational summary only — not a "
            "discovery claim."
        ),
    )
    weekly_review_parser.add_argument(
        "--db-path",
        type=Path,
        default=default_sqlite_log_path(default_project_root()),
        help="SQLite log database path. Defaults to logs/techno_search.sqlite3.",
    )
    weekly_review_parser.add_argument(
        "--cross-track-fixture",
        type=Path,
        help="Optional cross-track reference fixture JSON path.",
    )
    weekly_review_parser.add_argument(
        "--window-days",
        type=int,
        default=7,
        help="Rolling window in days for the weekly digest (default: 7).",
    )
    weekly_review_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional output directory for Markdown and JSON template files.",
    )
    weekly_review_parser.add_argument(
        "--operator-notes",
        default="",
        help="Optional free-text operator notes to include in the template.",
    )
    perf_history_parser = subparsers.add_parser(
        "baseline-performance-history-summary",
        help="Summarize the append-only baseline performance history fixture.",
    )
    perf_history_parser.add_argument(
        "--history-path",
        type=Path,
        help="Optional baseline performance history fixture JSON path.",
    )
    drift_parser = subparsers.add_parser(
        "baseline-pathway-drift-summary",
        help=(
            "Compare scoring-model recommended_pathway vs baseline predicted_pathway "
            "for all example candidates. Zero drift is required. "
            "Returns exit 1 if any drift is detected."
        ),
    )
    drift_parser.add_argument(
        "--example-candidates-dir",
        type=Path,
        help="Optional example candidates directory override.",
    )
    subparsers.add_parser(
        "sqlite-log-track-summary",
        help="Show SQLite log run counts broken down by track.",
    )
    subparsers.add_parser(
        "health",
        help=(
            "Concise project health dashboard combining key gate statuses. "
            "Returns exit 1 if any gate fails."
        ),
    )
    ops_ready_parser = subparsers.add_parser(
        "operations-readiness-summary",
        help=(
            "Aggregate local-only readiness blockers across QC, alerts, review "
            "deadlines, route coverage, and top-level SQLite log state."
        ),
    )
    ops_ready_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for readiness snapshot fields.",
    )
    ops_action_parser = subparsers.add_parser(
        "operations-action-plan-summary",
        help=(
            "Translate operations-readiness blockers into prioritized local "
            "operator actions. Scheduling aid only."
        ),
    )
    ops_action_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for readiness snapshot fields.",
    )
    ops_resolution_parser = subparsers.add_parser(
        "operations-action-resolution-summary",
        help=(
            "Summarize local action-plan resolution records. Workflow provenance "
            "only; does not authorize live data or external submission."
        ),
    )
    ops_resolution_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local action-resolution fixture path.",
    )
    ops_resolution_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for action-plan coverage fields.",
    )
    ops_blocker_detail_parser = subparsers.add_parser(
        "operations-blocker-detail-summary",
        help=(
            "Expand operations action-plan blockers into fixture-backed local "
            "source records. Operator review aid only."
        ),
    )
    ops_blocker_detail_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for readiness snapshot fields.",
    )
    ops_blocker_review_parser = subparsers.add_parser(
        "operations-blocker-review-summary",
        help=(
            "Summarize local blocker-detail review records. Workflow provenance "
            "only; does not clear blockers or authorize external workflow."
        ),
    )
    ops_blocker_review_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path.",
    )
    ops_blocker_review_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_followup_parser = subparsers.add_parser(
        "operations-blocker-followup-summary",
        help=(
            "Derive local blocker follow-up actions from blocker-review records. "
            "Planning aid only; does not clear blockers or authorize workflow."
        ),
    )
    ops_blocker_followup_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path.",
    )
    ops_blocker_followup_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_parser = subparsers.add_parser(
        "operations-blocker-followup-progress-summary",
        help=(
            "Summarize local progress notes for blocker follow-up actions. "
            "Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_review_parser = subparsers.add_parser(
        "operations-blocker-progress-review-summary",
        help=(
            "Summarize local second-pass review for unresolved blocker progress. "
            "Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_review_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker progress-review fixture path.",
    )
    ops_blocker_progress_review_parser.add_argument(
        "--progress-fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_review_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_review_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_next_parser = subparsers.add_parser(
        "operations-blocker-progress-next-actions-summary",
        help=(
            "Summarize local next actions for unresolved blocker progress. "
            "Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_next_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker progress next-action fixture path.",
    )
    ops_blocker_progress_next_parser.add_argument(
        "--progress-review-fixture-path",
        type=Path,
        help="Optional local blocker progress-review fixture path.",
    )
    ops_blocker_progress_next_parser.add_argument(
        "--progress-fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_next_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_next_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_execution_parser = subparsers.add_parser(
        "operations-blocker-progress-execution-summary",
        help=(
            "Summarize local execution notes for blocker progress next actions. "
            "Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker progress-execution fixture path.",
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--next-actions-fixture-path",
        type=Path,
        help="Optional local blocker progress next-action fixture path.",
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--progress-review-fixture-path",
        type=Path,
        help="Optional local blocker progress-review fixture path.",
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--progress-fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_execution_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_execution_review_parser = subparsers.add_parser(
        "operations-blocker-progress-execution-review-summary",
        help=(
            "Summarize local reviews for blocker progress-execution notes. "
            "Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker progress execution-review fixture path.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--execution-fixture-path",
        type=Path,
        help="Optional local blocker progress-execution fixture path.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--next-actions-fixture-path",
        type=Path,
        help="Optional local blocker progress next-action fixture path.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--progress-review-fixture-path",
        type=Path,
        help="Optional local blocker progress-review fixture path.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--progress-fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_execution_review_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_blocker_progress_execution_followup_parser = subparsers.add_parser(
        "operations-blocker-progress-execution-followup-summary",
        help=(
            "Summarize local follow-up planning for blocker progress-execution "
            "reviews. Workflow provenance only; does not clear blockers."
        ),
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional local blocker progress execution-followup fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--execution-review-fixture-path",
        type=Path,
        help="Optional local blocker progress execution-review fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--execution-fixture-path",
        type=Path,
        help="Optional local blocker progress-execution fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--next-actions-fixture-path",
        type=Path,
        help="Optional local blocker progress next-action fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--progress-review-fixture-path",
        type=Path,
        help="Optional local blocker progress-review fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--progress-fixture-path",
        type=Path,
        help="Optional local blocker-followup progress fixture path.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--review-fixture-path",
        type=Path,
        help="Optional local blocker-review fixture path for expected actions.",
    )
    ops_blocker_progress_execution_followup_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for blocker-detail coverage fields.",
    )
    ops_digest_parser = subparsers.add_parser(
        "operations-readiness-digest",
        help=(
            "Print a review-safe Markdown operations digest. Local dashboard only; "
            "does not authorize live data or external submission."
        ),
    )
    ops_digest_parser.add_argument(
        "--sqlite-log-path",
        type=Path,
        help="Optional SQLite log database path for readiness snapshot fields.",
    )
    ops_digest_parser.add_argument(
        "--output-path",
        type=Path,
        help="Optional Markdown output path for the digest.",
    )
    subparsers.add_parser(
        "baseline-confusion-matrix-summary",
        help=(
            "Print per-pathway confusion matrix and precision/recall/F1 metrics "
            "from the baseline evaluation harness. Synthetic diagnostics only."
        ),
    )
    det_parser = subparsers.add_parser(
        "score-determinism-check",
        help=(
            "Verify scoring produces identical outputs across repeated runs for "
            "example candidates. Returns exit 1 if any candidate is non-deterministic."
        ),
    )
    det_parser.add_argument(
        "candidate_paths",
        nargs="*",
        type=Path,
        help="Optional candidate JSON paths to check. Defaults to examples/candidates/.",
    )
    det_parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of repeat runs per candidate (default: 3).",
    )
    lifecycle_parser = subparsers.add_parser(
        "candidate-lifecycle-summary",
        help="Summarise candidate lifecycle stage entries. Scheduling aid only.",
    )
    lifecycle_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional candidate lifecycle fixture JSON path.",
    )
    schedule_parser = subparsers.add_parser(
        "observation-schedule-summary",
        help="Summarise planned/completed/cancelled observation windows. Scheduling aid only.",
    )
    schedule_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional observation schedule fixture JSON path.",
    )
    fn_parser = subparsers.add_parser(
        "false-negative-summary",
        help=(
            "Summarise missed injections from the injection-recovery fixture. "
            "Synthetic diagnostic only."
        ),
    )
    fn_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional injection-recovery fixture JSON path.",
    )
    sc_parser = subparsers.add_parser(
        "scoring-config-summary",
        help="Summarise current scoring thresholds. Synthetic v0 parameters only.",
    )
    sc_parser.add_argument(
        "--config-path",
        type=Path,
        help="Optional scoring config JSON path.",
    )
    subparsers.add_parser(
        "route-coverage-summary",
        help=(
            "Check that calibration fixtures cover all Pathway enum values. "
            "Synthetic diagnostic only."
        ),
    )
    lt_parser = subparsers.add_parser(
        "lifecycle-transition-summary",
        help=(
            "Validate that candidate lifecycle stage transitions follow the "
            "allowed ordering. Scheduling/provenance aid only."
        ),
    )
    lt_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional lifecycle entries fixture JSON path.",
    )
    oe_parser = subparsers.add_parser(
        "observation-efficiency-summary",
        help=(
            "Summarise observation window completion and cancellation rates. "
            "Scheduling aid only."
        ),
    )
    oe_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional observation schedule fixture JSON path.",
    )
    sens_parser = subparsers.add_parser(
        "sensitivity-config-summary",
        help=(
            "Summarise per-track sensitivity weights from the scoring config. "
            "Synthetic v0 parameters only — not calibrated detection sensitivities."
        ),
    )
    sens_parser.add_argument(
        "--config-path",
        type=Path,
        help="Optional scoring config JSON path.",
    )
    triage_parser = subparsers.add_parser(
        "triage-summary",
        help=(
            "Summarise operator candidate triage notes. "
            "Triage notes are scheduling aids and provenance records only."
        ),
    )
    triage_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional candidate triage notes fixture JSON path.",
    )
    artifacts_cleanup_parser = subparsers.add_parser(
        "artifacts-cleanup",
        help=(
            "Plan or apply local cleanup of the ignored artifacts/ directory. "
            "Refuses to touch committed project paths."
        ),
    )
    artifacts_cleanup_parser.add_argument(
        "--artifacts-dir",
        type=Path,
        help="Optional artifacts directory override.",
    )
    artifacts_cleanup_parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Apply the plan and delete files under artifacts/. Requires "
            "--acknowledge-local-apply."
        ),
    )
    artifacts_cleanup_parser.add_argument(
        "--acknowledge-local-apply",
        action="store_true",
        help="Required acknowledgement to perform local file deletion.",
    )

    signal_registry_parser = subparsers.add_parser(
        "signal-registry-summary",
        help="Summarize the signal-of-interest registry fixture.",
    )
    signal_registry_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    signal_track_parser = subparsers.add_parser(
        "signal-registry-track-summary",
        help="Per-track breakdown of the signal registry.",
    )
    signal_track_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "schema-drift-check",
        help="Detect structural drift in committed JSON schema files.",
    )

    audit_trail_parser = subparsers.add_parser(
        "audit-trail-summary",
        help="Summarize the candidate audit trail fixture.",
    )
    audit_trail_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    obs_gap_parser = subparsers.add_parser(
        "observation-gap-analysis",
        help="Identify scheduling gaps between planned and completed observation windows.",
    )
    obs_gap_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    multi_epoch_parser = subparsers.add_parser(
        "multi-epoch-summary",
        help="Summarize multi-epoch observation records.",
    )
    multi_epoch_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "classifier-rule-coverage",
        help="Report which baseline classifier rules fire across evaluation cases.",
    )

    recalibration_parser = subparsers.add_parser(
        "target-recalibration-summary",
        help="Compare two most recent target priority snapshots for rank changes.",
    )
    recalibration_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    operator_cov_parser = subparsers.add_parser(
        "operator-coverage-summary",
        help="Summarize operator coverage across triage notes.",
    )
    operator_cov_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    label_completeness_parser = subparsers.add_parser(
        "triage-label-completeness",
        help="Check which triage labels have fixture coverage.",
    )
    label_completeness_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "provenance-chain-validate",
        help="Validate provenance chain fields in committed report manifests.",
    )

    obs_notes_parser = subparsers.add_parser(
        "observation-notes-summary",
        help="Summarize post-observation operator notes by track and outcome.",
    )
    obs_notes_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    epoch_plan_parser = subparsers.add_parser(
        "epoch-plan-summary",
        help="Summarize epoch plan entries for targets needing additional observations.",
    )
    epoch_plan_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "aggregate-blockers-summary",
        help="Collect blocking issues from triage, lifecycle, and observation notes.",
    )

    score_history_parser = subparsers.add_parser(
        "score-history-summary",
        help="Summarize candidate score evolution across observation epochs.",
    )
    score_history_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    op_assignment_parser = subparsers.add_parser(
        "operator-assignment-summary",
        help="Summarize operator assignment records for candidate review.",
    )
    op_assignment_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-health-summary",
        help="Per-track pipeline health dashboard aggregating scheduling state.",
    )

    candidate_flags_parser = subparsers.add_parser(
        "candidate-flags-summary",
        help="Summarize quality flags and operational alerts raised against candidates.",
    )
    candidate_flags_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    review_deadlines_parser = subparsers.add_parser(
        "review-deadlines-summary",
        help="Summarize upcoming operator review deadlines with urgency levels.",
    )
    review_deadlines_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-throughput-summary",
        help="Per-stage pipeline throughput counts and transition rate metrics.",
    )

    candidate_retention_parser = subparsers.add_parser(
        "candidate-retention-summary",
        help="Summarize candidate retention records and pipeline dwell times.",
    )
    candidate_retention_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "operator-performance-summary",
        help="Aggregate operator performance metrics from assignment records.",
    )

    subparsers.add_parser(
        "track-comparison-summary",
        help="Cross-track comparison dashboard for scheduling state and flags.",
    )

    candidate_resolution_parser = subparsers.add_parser(
        "candidate-resolution-summary",
        help="Summarize final disposition records for candidates after review.",
    )
    candidate_resolution_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    escalation_log_parser = subparsers.add_parser(
        "escalation-log-summary",
        help="Summarize workflow escalation events with priority and status breakdown.",
    )
    escalation_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "quality-control-summary",
        help="Aggregate QC dashboard across flags, triage, deadlines, and escalations.",
    )

    observation_campaign_parser = subparsers.add_parser(
        "observation-campaign-summary",
        help="Summarize observation campaigns with session counts and track coverage.",
    )
    observation_campaign_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    data_quality_log_parser = subparsers.add_parser(
        "data-quality-log-summary",
        help="Summarize data quality log entries with grade and issue-type breakdown.",
    )
    data_quality_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-audit-summary",
        help="Aggregate pipeline audit summary from the candidate audit trail.",
    )

    follow_up_request_parser = subparsers.add_parser(
        "follow-up-request-summary",
        help="Summarize follow-up requests with priority and status breakdown.",
    )
    follow_up_request_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-bottleneck-summary",
        help="Identify where candidates are stalling in the pipeline.",
    )

    candidate_annotation_parser = subparsers.add_parser(
        "candidate-annotation-summary",
        help="Summarize operator annotations and tags on candidates.",
    )
    candidate_annotation_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    session_log_parser = subparsers.add_parser(
        "session-log-summary",
        help="Summarize observation session log entries.",
    )
    session_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    priority_queue_parser = subparsers.add_parser(
        "priority-queue-summary",
        help="Summarize candidate priority queue entries.",
    )
    priority_queue_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-capacity-summary",
        help="Summarize current pipeline scheduling capacity and load.",
    )

    feature_vector_parser = subparsers.add_parser(
        "feature-vector-summary",
        help="Summarize ML-ready feature vectors extracted from candidates.",
    )
    feature_vector_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    model_registry_parser = subparsers.add_parser(
        "model-registry-summary",
        help="Summarize ML model registry entries and above-baseline status.",
    )
    model_registry_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "ml-diagnostics-summary",
        help="Summarize ML pipeline status comparing baseline vs registered models.",
    )

    feature_normalization_parser = subparsers.add_parser(
        "feature-normalization-summary",
        help="Summarize per-track feature normalization bounds with drift detection.",
    )
    feature_normalization_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    feature_importance_parser = subparsers.add_parser(
        "feature-importance-summary",
        help="Summarize feature importance scores from baseline rule fire rates.",
    )
    feature_importance_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "ml-training-data-summary",
        help="Summarize ML training data assembled from calibration and injection-recovery cases.",
    )

    model_architecture_parser = subparsers.add_parser(
        "model-architecture-summary",
        help="Summarize ML model architecture scaffold definitions.",
    )
    model_architecture_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    model_evaluation_parser = subparsers.add_parser(
        "model-evaluation-summary",
        help="Summarize ML model evaluation results against the interpretable baseline.",
    )
    model_evaluation_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    model_performance_parser = subparsers.add_parser(
        "model-performance-history-summary",
        help="Summarize ML model training performance snapshots by model and trend.",
    )
    model_performance_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    model_serving_parser = subparsers.add_parser(
        "model-serving-summary",
        help="Summarize model serving scaffold records with inference provenance.",
    )
    model_serving_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    scoring_audit_parser = subparsers.add_parser(
        "scoring-audit-log-summary",
        help="Summarize scoring audit log entries per candidate per model version.",
    )
    scoring_audit_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    curated_intake_parser = subparsers.add_parser(
        "curated-dataset-intake-summary",
        help="Summarize curated dataset intake checklist records.",
    )
    curated_intake_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_rescore_parser = subparsers.add_parser(
        "candidate-rescore-summary",
        help="Summarize candidate re-scoring events with pathway change tracking.",
    )
    candidate_rescore_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    operator_handoff_parser = subparsers.add_parser(
        "operator-handoff-summary",
        help="Summarize operator handoff templates with model version and inference provenance.",
    )
    operator_handoff_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "candidate-methods-summary",
        help="Aggregate candidate methods dashboard combining serving, audit, and handoff state.",
    )

    pipeline_config_parser = subparsers.add_parser(
        "pipeline-config-summary",
        help="Summarize active pipeline configuration records with serving provenance.",
    )
    pipeline_config_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    submission_readiness_parser = subparsers.add_parser(
        "submission-readiness-summary",
        help="Summarize submission readiness provenance checklists per candidate.",
    )
    submission_readiness_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    subparsers.add_parser(
        "pipeline-integration-summary",
        help="Run end-to-end pipeline smoke tests across known fixture candidates.",
    )

    candidate_alert_parser = subparsers.add_parser(
        "candidate-alert-summary",
        help="Summarize candidate alert log entries for threshold crossings and status changes.",
    )
    candidate_alert_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    pipeline_replay_parser = subparsers.add_parser(
        "pipeline-replay-summary",
        help="Summarize pipeline replay log entries for reproducibility verification.",
    )
    pipeline_replay_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    scoring_threshold_audit_parser = subparsers.add_parser(
        "scoring-threshold-audit-summary",
        help="Summarize scoring threshold audit verdicts against pipeline config.",
    )
    scoring_threshold_audit_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    alert_resolution_parser = subparsers.add_parser(
        "alert-resolution-summary",
        help="Summarize alert resolution log entries (provenance records only).",
    )
    alert_resolution_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    config_history_parser = subparsers.add_parser(
        "config-version-history-summary",
        help="Summarize config version history entries (append-only provenance).",
    )
    config_history_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    operator_escalation_parser = subparsers.add_parser(
        "operator-escalation-summary",
        help="Summarize operator escalation log entries (scheduling coordination).",
    )
    operator_escalation_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_dedup_parser = subparsers.add_parser(
        "candidate-deduplication-summary",
        help="Summarize candidate deduplication log entries (provenance records only).",
    )
    candidate_dedup_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    intake_queue_parser = subparsers.add_parser(
        "intake-queue-summary",
        help="Summarize intake queue log entries (planning placeholders only).",
    )
    intake_queue_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    workflow_state_parser = subparsers.add_parser(
        "workflow-state-summary",
        help="Summarize workflow state log entries (scheduling coordination records).",
    )
    workflow_state_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    data_gap_parser = subparsers.add_parser(
        "data-gap-summary",
        help="Summarize data gap log entries (scheduling records only).",
    )
    data_gap_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_match_parser = subparsers.add_parser(
        "candidate-match-summary",
        help="Summarize candidate match log entries (provenance records only).",
    )
    candidate_match_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    pipeline_error_parser = subparsers.add_parser(
        "pipeline-error-summary",
        help="Summarize pipeline error log entries (operational records only).",
    )
    pipeline_error_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    obs_request_parser = subparsers.add_parser(
        "observation-request-summary",
        help="Summarize observation request log entries (scheduling records only).",
    )
    obs_request_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_export_parser = subparsers.add_parser(
        "candidate-export-summary",
        help="Summarize candidate export log entries (provenance records only).",
    )
    candidate_export_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    quality_gate_parser = subparsers.add_parser(
        "quality-gate-summary",
        help="Summarize quality gate log entries (operational provenance records only).",
    )
    quality_gate_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_comparison_parser = subparsers.add_parser(
        "candidate-comparison-summary",
        help="Summarize multi-candidate comparison records (scheduling aid only).",
    )
    candidate_comparison_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    pipeline_telemetry_parser = subparsers.add_parser(
        "pipeline-telemetry-summary",
        help="Summarize per-stage pipeline telemetry latency and throughput records.",
    )
    pipeline_telemetry_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    provenance_audit_parser = subparsers.add_parser(
        "provenance-audit-summary",
        help="Summarize cross-module provenance audit consistency verdicts.",
    )
    provenance_audit_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    instrument_log_parser = subparsers.add_parser(
        "instrument-log-summary",
        help="Summarize instrument/telescope status event log entries (scheduling records only).",
    )
    instrument_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    archival_query_parser = subparsers.add_parser(
        "archival-query-summary",
        help="Summarize archival/catalog query event log entries (provenance records only).",
    )
    archival_query_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_linkage_parser = subparsers.add_parser(
        "candidate-linkage-summary",
        help="Summarize candidate linkage log entries (provenance records only).",
    )
    candidate_linkage_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    signal_classification_parser = subparsers.add_parser(
        "signal-classification-summary",
        help="Summarize signal classification log entries (provenance records only).",
    )
    signal_classification_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    rfi_mitigation_parser = subparsers.add_parser(
        "rfi-mitigation-summary",
        help="Summarize RFI mitigation log entries (processing provenance records only).",
    )
    rfi_mitigation_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_annotation_log_parser = subparsers.add_parser(
        "candidate-annotation-log-summary",
        help="Summarize candidate annotation log entries (operator provenance records only).",
    )
    candidate_annotation_log_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    frequency_channel_parser = subparsers.add_parser(
        "frequency-channel-summary",
        help="Summarize frequency channel log entries (processing provenance records only).",
    )
    frequency_channel_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    pipeline_checkpoint_parser = subparsers.add_parser(
        "pipeline-checkpoint-summary",
        help="Summarize pipeline checkpoint log entries (reproducibility records only).",
    )
    pipeline_checkpoint_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    candidate_status_parser = subparsers.add_parser(
        "candidate-status-summary",
        help="Summarize candidate status log entries (operational provenance records only).",
    )
    candidate_status_parser.add_argument(
        "--fixture-path", type=Path, help="Optional fixture path override."
    )

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
