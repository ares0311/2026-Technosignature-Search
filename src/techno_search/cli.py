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

from techno_search.background_search import (
    background_review_workflow_summary,
    background_search_ledger_summary,
    run_local_background_search_once,
    target_priority_summary,
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
from techno_search.plotting import plot_artifact_summary
from techno_search.reporting import (
    candidate_packet_json,
    write_candidate_reports,
)
from techno_search.review_queue import (
    consensus_export_summary,
    consensus_summary,
    review_queue_summary,
)
from techno_search.schemas import Candidate, candidate_from_mapping
from techno_search.scoring import score_candidate
from techno_search.validation import validate_candidate_file, validate_report_directory
from techno_search.validation_datasets import (
    validation_dataset_summary,
    validation_promotion_summary,
    validation_readiness_summary,
)

SCHEMA_FILENAMES = {
    "background_search_ledger": "background_search_ledger.schema.json",
    "background_targets": "background_targets.schema.json",
    "batch_manifest": "batch_manifest.schema.json",
    "benchmark_metadata": "benchmark_metadata.schema.json",
    "benchmark_run_results": "benchmark_run_results.schema.json",
    "candidate_packet": "candidate_packet.schema.json",
    "consensus_export": "consensus_export.schema.json",
    "consensus_labels": "consensus_labels.schema.json",
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
                target_priority_summary(args.target_path, args.config_path),
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

    if args.command == "background-run-once":
        print(
            json.dumps(
                run_local_background_search_once(
                    args.ledger_path,
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
    catalog_cache = catalog_cache_validation_summary(git_tracked_paths(root), project_root=root)
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

    ok = (
        all(result["ok"] for result in candidate_results.values())
        and bool(report_result["ok"])
        and all(schema_results.values())
        and bool(catalog_cache["ok"])
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
        "validation_dataset_summary": validation_datasets,
        "validation_promotion_summary": validation_promotions,
        "validation_readiness_summary": validation_readiness,
        "benchmark_metadata_summary": benchmark_metadata,
        "benchmark_run_summary": benchmark_runs,
        "target_priority_summary": target_priorities,
        "background_ledger_summary": background_ledger,
        "background_review_workflow_summary": background_review_workflow,
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
    validation_datasets = validation["validation_dataset_summary"]
    validation_promotions = validation["validation_promotion_summary"]
    validation_readiness = validation["validation_readiness_summary"]
    benchmark_metadata = validation["benchmark_metadata_summary"]
    benchmark_runs = validation["benchmark_run_summary"]
    target_priorities = validation["target_priority_summary"]
    background_ledger = validation["background_ledger_summary"]
    background_review_workflow = validation["background_review_workflow_summary"]
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
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
