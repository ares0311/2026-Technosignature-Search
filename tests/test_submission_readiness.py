from __future__ import annotations

import json
from pathlib import Path

from techno_search.submission_readiness import (
    ALLOWED_READINESS_STATUSES,
    REQUIRED_PROVENANCE_FIELDS,
    SUBMISSION_READINESS_DISCLAIMER,
    SUBMISSION_READINESS_SCHEMA_VERSION,
    SubmissionReadinessRecord,
    load_submission_readiness_records,
    submission_readiness_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "submission_readiness.json"


def test_schema_version():
    assert SUBMISSION_READINESS_SCHEMA_VERSION == "submission_readiness_v1"


def test_disclaimer_present():
    assert len(SUBMISSION_READINESS_DISCLAIMER) > 20
    assert "provenance" in SUBMISSION_READINESS_DISCLAIMER.lower()


def test_disclaimer_no_authorization():
    lower = SUBMISSION_READINESS_DISCLAIMER.lower()
    assert "does not authorize external submission" in lower


def test_allowed_statuses():
    assert "ready" in ALLOWED_READINESS_STATUSES
    assert "blocked" in ALLOWED_READINESS_STATUSES
    assert "pending_review" in ALLOWED_READINESS_STATUSES
    assert "not_applicable" in ALLOWED_READINESS_STATUSES


def test_required_provenance_fields_present():
    assert "candidate_id" in REQUIRED_PROVENANCE_FIELDS
    assert "model_id" in REQUIRED_PROVENANCE_FIELDS
    assert "serving_id" in REQUIRED_PROVENANCE_FIELDS
    assert "pathway" in REQUIRED_PROVENANCE_FIELDS
    assert "operator_handoff_id" in REQUIRED_PROVENANCE_FIELDS


def test_load_returns_list():
    records = load_submission_readiness_records(FIXTURE_PATH)
    assert isinstance(records, list)


def test_load_count():
    records = load_submission_readiness_records(FIXTURE_PATH)
    assert len(records) == 4


def test_record_fields():
    records = load_submission_readiness_records(FIXTURE_PATH)
    r = records[0]
    assert isinstance(r, SubmissionReadinessRecord)
    assert r.readiness_id == "sr-001"
    assert r.readiness_status == "ready"
    assert isinstance(r.present_provenance_fields, list)
    assert isinstance(r.missing_provenance_fields, list)
    assert isinstance(r.blocking_issues, list)


def test_record_as_dict():
    records = load_submission_readiness_records(FIXTURE_PATH)
    d = records[0].as_dict()
    assert "readiness_id" in d
    assert "present_provenance_fields" in d
    assert "missing_provenance_fields" in d
    assert "blocking_issues" in d


def test_ready_record_has_no_missing_fields():
    records = load_submission_readiness_records(FIXTURE_PATH)
    ready = [r for r in records if r.readiness_status == "ready"]
    for r in ready:
        assert len(r.missing_provenance_fields) == 0


def test_blocked_record_has_blocking_issues():
    records = load_submission_readiness_records(FIXTURE_PATH)
    blocked = [r for r in records if r.readiness_status == "blocked"]
    assert len(blocked) >= 1
    assert len(blocked[0].blocking_issues) > 0


def test_all_statuses_valid():
    records = load_submission_readiness_records(FIXTURE_PATH)
    for r in records:
        assert r.readiness_status in ALLOWED_READINESS_STATUSES


def test_summary_record_count():
    summary = submission_readiness_summary(FIXTURE_PATH)
    assert summary["record_count"] == 4


def test_summary_ready_count():
    summary = submission_readiness_summary(FIXTURE_PATH)
    assert summary["ready_count"] == 1


def test_summary_blocked_count():
    summary = submission_readiness_summary(FIXTURE_PATH)
    assert summary["blocked_count"] == 1


def test_summary_blocking_issue_count():
    summary = submission_readiness_summary(FIXTURE_PATH)
    assert summary["total_blocking_issue_count"] >= 1


def test_summary_by_status():
    summary = submission_readiness_summary(FIXTURE_PATH)
    bs = summary["by_status"]
    assert bs["ready"] == 1
    assert bs["blocked"] == 1
    assert bs["not_applicable"] == 2


def test_summary_required_fields_list():
    summary = submission_readiness_summary(FIXTURE_PATH)
    assert "candidate_id" in summary["required_provenance_fields"]
    assert "operator_handoff_id" in summary["required_provenance_fields"]


def test_summary_schema_version():
    summary = submission_readiness_summary(FIXTURE_PATH)
    assert summary["schema_version"] == "submission_readiness_v1"


def test_summary_disclaimer():
    summary = submission_readiness_summary(FIXTURE_PATH)
    assert len(summary["disclaimer"]) > 20


def test_fixture_json_valid():
    data = json.loads(FIXTURE_PATH.read_text())
    assert "submission_readiness_records" in data
    assert len(data["submission_readiness_records"]) >= 4


def test_fixture_required_fields():
    data = json.loads(FIXTURE_PATH.read_text())
    required = {
        "readiness_id", "candidate_id", "pathway", "readiness_status",
        "present_provenance_fields", "missing_provenance_fields",
        "blocking_issues", "assessed_utc",
    }
    for entry in data["submission_readiness_records"]:
        for field in required:
            assert field in entry, f"Missing {field} in {entry.get('readiness_id')}"
