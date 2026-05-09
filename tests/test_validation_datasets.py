from techno_search.validation_datasets import (
    VALIDATION_DATASET_DISCLAIMER,
    VALIDATION_PROMOTION_DISCLAIMER,
    VALIDATION_READINESS_DISCLAIMER,
    load_validation_dataset_entries,
    load_validation_promotion_rules,
    load_validation_readiness_records,
    validation_dataset_summary,
    validation_promotion_summary,
    validation_readiness_summary,
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


def test_validation_promotion_rules_load_evidence_and_blockers() -> None:
    rules = load_validation_promotion_rules()

    assert len(rules) == 3
    assert {rule.from_readiness for rule in rules} == {"synthetic_scaffold"}
    assert {rule.to_readiness for rule in rules} == {"curated_non_synthetic_candidate"}
    assert all(rule.requires_external_review for rule in rules)
    assert all(rule.minimum_case_count == 10 for rule in rules)
    assert "negative_evidence_reviewed" in rules[0].required_evidence
    assert "unsupported_discovery_language" in rules[2].blocking_conditions
    assert "do not certify discoveries" in VALIDATION_PROMOTION_DISCLAIMER


def test_validation_promotion_summary_counts_rules_and_requirements() -> None:
    summary = validation_promotion_summary()

    assert summary["schema_version"] == "validation_dataset_promotion_rules_v1"
    assert summary["rule_count"] == 3
    assert summary["required_evidence_count"] == 12
    assert summary["blocking_condition_count"] == 9
    assert summary["minimum_case_count_floor"] == 10
    assert summary["rules_requiring_external_review"] == 3
    assert summary["by_from_readiness"] == {"synthetic_scaffold": 3}
    assert summary["by_to_readiness"] == {"curated_non_synthetic_candidate": 3}


def test_validation_readiness_records_load_statuses_and_blockers() -> None:
    records = load_validation_readiness_records()

    assert len(records) == 3
    assert {record.track.value for record in records} == {
        "anomaly",
        "infrared",
        "radio",
    }
    assert {record.readiness_status for record in records} == {
        "blocked",
        "not_yet_admissible",
        "ready",
    }
    assert all(record.requires_external_review for record in records)
    assert records[0].readiness_status == "ready"
    assert records[1].blocking_issues == (
        "source_license_not_documented",
        "unreviewed_confusion_flags",
    )
    assert "do not certify discoveries" in VALIDATION_READINESS_DISCLAIMER


def test_validation_readiness_summary_counts_statuses_and_requirements() -> None:
    summary = validation_readiness_summary()

    assert summary["schema_version"] == "validation_readiness_v1"
    assert summary["record_count"] == 3
    assert summary["ready_count"] == 1
    assert summary["blocked_count"] == 1
    assert summary["not_yet_admissible_count"] == 1
    assert summary["evidence_requirement_count"] == 12
    assert summary["satisfied_evidence_count"] == 9
    assert summary["blocking_issue_count"] == 4
    assert summary["records_requiring_external_review"] == 3
    assert summary["minimum_case_count_floor"] == 10
    assert summary["total_current_case_count"] == 29
    assert summary["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert summary["by_status"] == {
        "blocked": 1,
        "not_yet_admissible": 1,
        "ready": 1,
    }
    assert summary["ready_dataset_ids"] == ["future-radio-rfi-curated-v0"]
