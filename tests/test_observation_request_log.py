from __future__ import annotations

from techno_search.observation_request_log import (
    ALLOWED_REQUEST_KINDS,
    ALLOWED_REQUEST_STATUSES,
    OBSERVATION_REQUEST_DISCLAIMER,
    OBSERVATION_REQUEST_SCHEMA_VERSION,
    ObservationRequestEntry,
    load_observation_request_entries,
    observation_request_summary,
)


def test_schema_version() -> None:
    assert OBSERVATION_REQUEST_SCHEMA_VERSION == "observation_request_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in OBSERVATION_REQUEST_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in OBSERVATION_REQUEST_DISCLAIMER


def test_disclaimer_no_pathway_modification() -> None:
    assert "pathway routing" in OBSERVATION_REQUEST_DISCLAIMER


def test_disclaimer_scheduling_records() -> None:
    assert "scheduling" in OBSERVATION_REQUEST_DISCLAIMER


def test_allowed_request_kinds() -> None:
    assert "target_followup" in ALLOWED_REQUEST_KINDS
    assert "reobservation" in ALLOWED_REQUEST_KINDS
    assert "calibration_check" in ALLOWED_REQUEST_KINDS
    assert "verification" in ALLOWED_REQUEST_KINDS
    assert "archival_search" in ALLOWED_REQUEST_KINDS


def test_allowed_request_statuses() -> None:
    assert "submitted" in ALLOWED_REQUEST_STATUSES
    assert "acknowledged" in ALLOWED_REQUEST_STATUSES
    assert "scheduled" in ALLOWED_REQUEST_STATUSES
    assert "completed" in ALLOWED_REQUEST_STATUSES
    assert "rejected" in ALLOWED_REQUEST_STATUSES
    assert "withdrawn" in ALLOWED_REQUEST_STATUSES


def test_load_entries_count() -> None:
    entries = load_observation_request_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_observation_request_entries()
    assert all(isinstance(e, ObservationRequestEntry) for e in entries)


def test_first_entry_fields() -> None:
    entries = load_observation_request_entries()
    e = entries[0]
    assert e.request_id == "req-001"
    assert e.candidate_id == "radio-clean-candidate"
    assert e.request_kind == "target_followup"
    assert e.status == "submitted"
    assert e.target_utc is None
    assert e.instrument is None


def test_acknowledged_entry() -> None:
    entries = load_observation_request_entries()
    ack = [e for e in entries if e.status == "acknowledged"]
    assert len(ack) == 1
    assert ack[0].request_id == "req-002"


def test_completed_entry_has_target_utc() -> None:
    entries = load_observation_request_entries()
    completed = [e for e in entries if e.status == "completed"]
    assert len(completed) == 1
    assert completed[0].target_utc is not None


def test_rejected_entry() -> None:
    entries = load_observation_request_entries()
    rejected = [e for e in entries if e.status == "rejected"]
    assert len(rejected) == 1
    assert rejected[0].request_id == "req-004"


def test_scheduled_entry() -> None:
    entries = load_observation_request_entries()
    scheduled = [e for e in entries if e.status == "scheduled"]
    assert len(scheduled) == 1


def test_as_dict_keys() -> None:
    entries = load_observation_request_entries()
    d = entries[0].as_dict()
    expected_keys = {
        "request_id", "candidate_id", "request_kind", "status",
        "requested_by", "requested_utc", "target_utc", "instrument", "notes",
    }
    assert set(d.keys()) == expected_keys


def test_as_dict_values_match() -> None:
    entries = load_observation_request_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["request_id"] == e.request_id
    assert d["status"] == e.status


def test_summary_entry_count() -> None:
    s = observation_request_summary()
    assert s["entry_count"] == 5


def test_summary_pending_count() -> None:
    s = observation_request_summary()
    # submitted(1) + acknowledged(1) + scheduled(1) = 3
    assert s["pending_count"] == 3


def test_summary_completed_count() -> None:
    s = observation_request_summary()
    assert s["completed_count"] == 1


def test_summary_rejected_count() -> None:
    s = observation_request_summary()
    assert s["rejected_count"] == 1


def test_summary_by_status() -> None:
    s = observation_request_summary()
    assert s["by_status"]["submitted"] == 1
    assert s["by_status"]["completed"] == 1


def test_summary_schema_version() -> None:
    s = observation_request_summary()
    assert s["schema_version"] == OBSERVATION_REQUEST_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = observation_request_summary()
    assert "detection claim" in s["disclaimer"]
