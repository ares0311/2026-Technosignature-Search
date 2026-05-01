import json
from pathlib import Path


def test_json_schema_files_are_parseable_and_named() -> None:
    schema_dir = Path("schemas")
    schema_paths = sorted(schema_dir.glob("*.schema.json"))

    assert {path.name for path in schema_paths} == {
        "batch_manifest.schema.json",
        "candidate_packet.schema.json",
        "report_manifest.schema.json",
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
    packet = json.loads(Path("examples/reports/example-radio-clean.json").read_text())
    manifest = json.loads(
        Path("examples/reports/example-radio-clean.manifest.json").read_text()
    )
    batch = json.loads(Path("examples/batch_reports/batch_manifest.json").read_text())

    assert set(packet_schema["required"]) <= set(packet)
    assert set(manifest_schema["required"]) <= set(manifest)
    assert set(batch_schema["required"]) <= set(batch)
    assert "schema_version" in packet_schema["required"]
    assert "schema_version" in manifest_schema["required"]
    assert "schema_version" in batch_schema["required"]
    assert "provenance_summary" in manifest_schema["required"]
    assert packet["schema_version"] == "techno_search_packet_v1"
    assert manifest["schema_version"] == "techno_search_packet_v1"
    assert manifest["provenance_summary"]["source_dataset"] == "synthetic-example"
    assert batch["schema_version"] == "techno_search_packet_v1"
    assert packet["config_version"] == "scoring_v0"
    assert batch["config_version"] == "scoring_v0"
