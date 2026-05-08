from techno_search.validation_datasets import (
    VALIDATION_DATASET_DISCLAIMER,
    load_validation_dataset_entries,
    validation_dataset_summary,
)


def test_validation_dataset_manifest_loads_synthetic_track_entries() -> None:
    entries = load_validation_dataset_entries()

    assert len(entries) == 3
    assert {entry.track.value for entry in entries} == {"anomaly", "infrared", "radio"}
    assert {entry.readiness for entry in entries} == {"synthetic_scaffold"}
    assert entries[0].source_fixture_path == "tests/fixtures/calibration_false_positives.json"
    assert "not calibrated survey performance claims" in VALIDATION_DATASET_DISCLAIMER


def test_validation_dataset_summary_counts_manifest_coverage() -> None:
    summary = validation_dataset_summary()

    assert summary["schema_version"] == "validation_dataset_manifest_v1"
    assert summary["dataset_count"] == 3
    assert summary["total_case_count"] == 15
    assert summary["false_positive_class_count"] == 15
    assert summary["expected_pathway_count"] == 1
    assert summary["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert summary["by_dataset_kind"] == {"synthetic_false_positive_suite": 3}
    assert summary["by_readiness"] == {"synthetic_scaffold": 3}
    assert summary["dataset_ids"] == [
        "synthetic-anomaly-false-positive-v0",
        "synthetic-infrared-false-positive-v0",
        "synthetic-radio-false-positive-v0",
    ]
