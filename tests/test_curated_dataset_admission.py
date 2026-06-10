from __future__ import annotations

import json
from pathlib import Path

from techno_search.curated_dataset_admission import (
    ALLOWED_CURATED_DATASET_ADMISSION_STATUSES,
    CuratedDatasetAdmissionRecord,
    curated_dataset_admission_summary,
    load_curated_dataset_admission_records,
    validate_curated_dataset_admission_records,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "curated_dataset_admission.json"


def test_load_curated_dataset_admission_records_default_fixture() -> None:
    records = load_curated_dataset_admission_records()

    assert len(records) == 5
    assert records[0].dataset_id == "curated-admit-synthetic-v0"
    assert records[0].synthetic_fixture_only is True


def test_curated_dataset_admission_summary_counts_gate_states() -> None:
    summary = curated_dataset_admission_summary()

    assert summary["schema_version"] == "curated_dataset_admission_v1"
    assert summary["record_count"] == 5
    assert summary["blocked_count"] == 3
    assert summary["ready_for_local_fixture_count"] == 1
    assert summary["synthetic_only_count"] == 1
    assert summary["real_data_authorized_count"] == 1
    assert summary["external_review_required_count"] == 3
    assert summary["citizen_science_review_completed_count"] == 1
    assert summary["total_blocker_count"] == 9
    assert summary["validation_ok"] is True
    assert summary["by_track"] == {
        "anomaly": 1,
        "infrared": 1,
        "multi": 1,
        "radio": 2,
    }


def test_curated_dataset_admission_summary_has_conservative_disclaimer() -> None:
    summary = curated_dataset_admission_summary()

    assert "does not authorize unreviewed real observation data" in summary["disclaimer"]
    assert "calibrate scoring thresholds" in summary["disclaimer"]


def test_curated_dataset_admission_statuses_are_allowed() -> None:
    for record in load_curated_dataset_admission_records():
        assert record.admission_status in ALLOWED_CURATED_DATASET_ADMISSION_STATUSES


def test_curated_dataset_admission_fixture_validation_passes() -> None:
    validation = validate_curated_dataset_admission_records(
        load_curated_dataset_admission_records()
    )

    assert validation == {"ok": True, "issue_count": 0, "issues": []}


def test_curated_dataset_admission_rejects_real_authorization_without_reviews(
    tmp_path: Path,
) -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    data["curated_dataset_admission_records"][1]["real_data_authorized"] = True
    path = tmp_path / "curated_dataset_admission.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    summary = curated_dataset_admission_summary(path)

    assert summary["validation_ok"] is False
    assert summary["real_data_authorized_count"] == 2
    assert any(
        "requires ready_for_local_fixture" in issue
        for issue in summary["validation_issues"]
    )
    assert any(
        "requires all reviews and zero blockers" in issue
        for issue in summary["validation_issues"]
    )


def test_curated_dataset_admission_rejects_synthetic_real_authorization(
    tmp_path: Path,
) -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    data["curated_dataset_admission_records"][0]["real_data_authorized"] = True
    path = tmp_path / "curated_dataset_admission.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    summary = curated_dataset_admission_summary(path)

    assert summary["validation_ok"] is False
    assert any("synthetic-only" in issue for issue in summary["validation_issues"])


def test_curated_dataset_admission_rejects_ready_fixture_with_blockers() -> None:
    record = CuratedDatasetAdmissionRecord(
        dataset_id="curated-admit-ready-but-blocked",
        dataset_label="Blocked Ready Dataset",
        track="radio",
        dataset_kind="curated_non_synthetic_false_positive_suite",
        admission_status="ready_for_local_fixture",
        provenance_reviewed=True,
        license_reviewed=True,
        labeling_method_reviewed=True,
        false_positive_baseline_reviewed=True,
        external_review_required=True,
        external_review_completed=True,
        real_data_authorized=False,
        synthetic_fixture_only=False,
        blocker_count=1,
        notes="Deliberately invalid ready record.",
    )

    validation = validate_curated_dataset_admission_records([record])

    assert validation["ok"] is False
    assert validation["issue_count"] == 1
    assert (
        "ready_for_local_fixture requires all reviews and zero blockers"
        in validation["issues"][0]
    )


def test_curated_dataset_admission_custom_path_matches_default() -> None:
    records = load_curated_dataset_admission_records(FIXTURE_PATH)
    summary = curated_dataset_admission_summary(FIXTURE_PATH)

    assert len(records) == summary["record_count"] == 5
