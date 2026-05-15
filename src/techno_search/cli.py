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
from techno_search.constants import DEFAULT_SCHEMA_VERSION, DEFAULT_SCORING_CONFIG_VERSION
from techno_search.cross_track import cross_track_summary
from techno_search.injection_recovery import injection_recovery_summary
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
from techno_search.plotting import plot_artifact_summary
from techno_search.reporting import (
    candidate_packet_json,
    write_candidate_reports,
)
from techno_search.reproducibility import verify_report_directory
from techno_search.review_queue import (
    consensus_export_summary,
    consensus_summary,
    review_queue_summary,
)
from techno_search.schemas import Candidate, Track, candidate_from_mapping
from techno_search.scoring import score_candidate
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
            plan = {
                **plan,
                "dry_run": False,
                "apply_blocked": True,
                "apply_blocked_reason": (
                    "No automatic migration is implemented. Apply mode is "
                    "blocked until a destructive migration is reviewed and "
                    "added explicitly."
                ),
            }
            print(json.dumps(plan, indent=2, sort_keys=True), file=out)
            return 1
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
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
