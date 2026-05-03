import json
from pathlib import Path


def test_json_schema_files_are_parseable_and_named() -> None:
    schema_dir = Path("schemas")
    schema_paths = sorted(schema_dir.glob("*.schema.json"))

    assert {path.name for path in schema_paths} == {
        "batch_manifest.schema.json",
        "candidate_packet.schema.json",
        "consensus_labels.schema.json",
        "report_manifest.schema.json",
        "review_queue.schema.json",
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
    review_queue_schema = json.loads(
        Path("schemas/review_queue.schema.json").read_text(encoding="utf-8")
    )
    consensus_schema = json.loads(
        Path("schemas/consensus_labels.schema.json").read_text(encoding="utf-8")
    )
    packet = json.loads(Path("examples/reports/example-radio-clean.json").read_text())
    manifest = json.loads(
        Path("examples/reports/example-radio-clean.manifest.json").read_text()
    )
    batch = json.loads(Path("examples/batch_reports/batch_manifest.json").read_text())
    review_queue = json.loads(Path("tests/fixtures/review_queue.json").read_text())
    consensus = json.loads(Path("tests/fixtures/consensus_labels.json").read_text())

    assert set(packet_schema["required"]) <= set(packet)
    assert set(manifest_schema["required"]) <= set(manifest)
    assert set(batch_schema["required"]) <= set(batch)
    assert set(review_queue_schema["required"]) <= set(review_queue)
    assert set(consensus_schema["required"]) <= set(consensus)
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
