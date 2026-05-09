import json
from io import StringIO

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
    assert result["by_track_and_class"]["radio"]["satellite_like_recurrence"] == 1
    assert "not calibrated survey contamination analysis" in result["disclaimer"]


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
        "background_search_ledger",
        "background_targets",
        "batch_manifest",
        "benchmark_metadata",
        "benchmark_run_results",
        "candidate_packet",
        "consensus_export",
        "consensus_labels",
        "report_manifest",
        "review_queue",
        "validation_dataset_manifest",
        "validation_promotion_rules",
    }
    assert result["background_search_ledger"].endswith(
        "schemas/background_search_ledger.schema.json"
    )
    assert result["background_targets"].endswith("schemas/background_targets.schema.json")
    assert result["benchmark_metadata"].endswith("schemas/benchmark_metadata.schema.json")
    assert result["benchmark_run_results"].endswith(
        "schemas/benchmark_run_results.schema.json"
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
    assert "not scientific performance claims" in result["disclaimer"]


def test_cli_target_priority_summary_outputs_selected_target() -> None:
    stdout = StringIO()

    exit_code = main(["target-priority-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_target_priority_v1"
    assert result["target_count"] == 3
    assert result["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert result["selected_target_id"] == "target-radio-clean-drift"
    assert result["selected_priority_score"] == 0.7515
    assert result["weights"]["false_positive_probability"] < 0
    assert "not evidence" in result["disclaimer"]


def test_cli_background_ledger_summary_outputs_logged_searches() -> None:
    stdout = StringIO()

    exit_code = main(["background-ledger-summary"], stdout=stdout)
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["schema_version"] == "background_search_ledger_v1"
    assert result["entry_count"] == 3
    assert result["searched_target_count"] == 3
    assert result["candidate_count"] == 2
    assert result["blocking_issue_count"] == 3
    assert result["by_status"] == {
        "completed": 1,
        "completed_with_blockers": 1,
        "searched_no_candidate": 1,
    }
    assert "not discovery claims" in result["disclaimer"]


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
    assert result["benchmark_metadata_summary"]["command_count"] == 4
    assert result["benchmark_metadata_summary"]["default_cpu_worker_limit"] == 12
    assert result["benchmark_metadata_summary"]["memory_budget_gb"] == 48
    assert result["benchmark_run_summary"]["run_count"] == 3
    assert result["benchmark_run_summary"]["input_case_total"] == 171
    assert result["benchmark_run_summary"]["max_worker_count"] == 12
    assert result["target_priority_summary"]["target_count"] == 3
    assert result["target_priority_summary"]["selected_target_id"] == (
        "target-radio-clean-drift"
    )
    assert result["background_ledger_summary"]["entry_count"] == 3
    assert result["background_ledger_summary"]["candidate_count"] == 2
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
    assert result["schema_count"] == 12
    assert result["schemas_ok"] is True
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
    assert result["benchmark_command_count"] == 4
    assert result["benchmark_default_cpu_worker_limit"] == 12
    assert result["benchmark_memory_budget_gb"] == 48
    assert result["benchmark_run_count"] == 3
    assert result["benchmark_run_input_case_total"] == 171
    assert result["benchmark_run_max_worker_count"] == 12
    assert result["target_priority_count"] == 3
    assert result["selected_background_target_id"] == "target-radio-clean-drift"
    assert result["background_ledger_entry_count"] == 3
    assert result["background_ledger_candidate_count"] == 2
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
