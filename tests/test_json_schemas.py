import json
from pathlib import Path


def test_json_schema_files_are_parseable_and_named() -> None:
    schema_dir = Path("schemas")
    schema_paths = sorted(schema_dir.glob("*.schema.json"))

    assert {path.name for path in schema_paths} == {
        "background_search_ledger.schema.json",
        "background_targets.schema.json",
        "batch_manifest.schema.json",
        "benchmark_metadata.schema.json",
        "benchmark_run_results.schema.json",
        "candidate_packet.schema.json",
        "consensus_export.schema.json",
        "consensus_labels.schema.json",
        "report_manifest.schema.json",
        "review_queue.schema.json",
        "validation_dataset_manifest.schema.json",
        "validation_promotion_rules.schema.json",
        "validation_readiness.schema.json",
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
    assert len(background_targets["targets"]) == 3
    assert background_ledger["schema_version"] == "background_search_ledger_v1"
    assert len(background_ledger["ledger_entries"]) == 3
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
