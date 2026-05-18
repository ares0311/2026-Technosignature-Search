"""Tests for curated dataset intake module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.curated_dataset_intake import (
    ALLOWED_DATA_KINDS,
    ALLOWED_INTAKE_STATUSES,
    CURATED_DATASET_INTAKE_DISCLAIMER,
    CURATED_DATASET_INTAKE_SCHEMA_VERSION,
    CuratedDatasetIntakeRecord,
    curated_dataset_intake_summary,
    load_intake_records,
)


def test_load_records_returns_list():
    result = load_intake_records()
    assert isinstance(result, list)


def test_load_records_returns_dataclass_instances():
    result = load_intake_records()
    assert all(isinstance(r, CuratedDatasetIntakeRecord) for r in result)


def test_fixture_has_four_records():
    result = load_intake_records()
    assert len(result) == 4


def test_intake_statuses_valid():
    result = load_intake_records()
    for r in result:
        assert r.intake_status in ALLOWED_INTAKE_STATUSES


def test_data_kinds_valid():
    result = load_intake_records()
    for r in result:
        assert r.data_kind in ALLOWED_DATA_KINDS


def test_at_least_one_approved():
    result = load_intake_records()
    assert any(r.intake_status == "approved" for r in result)


def test_at_least_one_blocked():
    result = load_intake_records()
    assert any(r.intake_status == "blocked" for r in result)


def test_blocking_issues_is_list():
    result = load_intake_records()
    for r in result:
        assert isinstance(r.blocking_issues, list)


def test_approved_record_has_no_blocking_issues():
    result = load_intake_records()
    for r in result:
        if r.intake_status == "approved":
            assert len(r.blocking_issues) == 0


def test_blocked_record_has_blocking_issues():
    result = load_intake_records()
    for r in result:
        if r.intake_status == "blocked":
            assert len(r.blocking_issues) > 0


def test_as_dict_returns_expected_keys():
    r = load_intake_records()[0]
    d = r.as_dict()
    assert "intake_id" in d
    assert "dataset_label" in d
    assert "intake_status" in d
    assert "has_provenance_documentation" in d
    assert "has_false_positive_baseline" in d
    assert "blocking_issues" in d


def test_summary_returns_dict():
    result = curated_dataset_intake_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = curated_dataset_intake_summary()
    assert result["schema_version"] == CURATED_DATASET_INTAKE_SCHEMA_VERSION


def test_summary_disclaimer():
    result = curated_dataset_intake_summary()
    assert result["disclaimer"] == CURATED_DATASET_INTAKE_DISCLAIMER
    assert "no real observation data" in result["disclaimer"].lower()


def test_summary_record_count():
    result = curated_dataset_intake_summary()
    assert result["record_count"] == 4


def test_summary_approved_count():
    result = curated_dataset_intake_summary()
    assert result["approved_count"] == 1


def test_summary_blocked_count():
    result = curated_dataset_intake_summary()
    assert result["blocked_count"] == 1


def test_summary_by_track_keys():
    result = curated_dataset_intake_summary()
    assert "radio" in result["by_track"]
    assert "infrared" in result["by_track"]
    assert "anomaly" in result["by_track"]


def test_summary_total_blocking_issues():
    result = curated_dataset_intake_summary()
    assert result["total_blocking_issue_count"] >= 1


def test_cli_curated_dataset_intake_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "curated-dataset-intake-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_curated_dataset_intake_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "curated-dataset-intake-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "record_count" in data
    assert "approved_count" in data
    assert "total_blocking_issue_count" in data
