from __future__ import annotations

from techno_search.data_gap_log import (
    ALLOWED_GAP_STATUSES,
    ALLOWED_MISSING_REASONS,
    DATA_GAP_DISCLAIMER,
    DATA_GAP_SCHEMA_VERSION,
    DataGapEntry,
    data_gap_summary,
    load_data_gap_entries,
)


def test_schema_version() -> None:
    assert DATA_GAP_SCHEMA_VERSION == "data_gap_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in DATA_GAP_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in DATA_GAP_DISCLAIMER


def test_disclaimer_no_pathway_modification() -> None:
    assert "pathway routing" in DATA_GAP_DISCLAIMER


def test_disclaimer_scheduling_aids() -> None:
    assert "scheduling" in DATA_GAP_DISCLAIMER


def test_allowed_missing_reasons() -> None:
    assert "instrument_downtime" in ALLOWED_MISSING_REASONS
    assert "weather" in ALLOWED_MISSING_REASONS
    assert "scheduling_conflict" in ALLOWED_MISSING_REASONS
    assert "data_quality_failure" in ALLOWED_MISSING_REASONS
    assert "unknown" in ALLOWED_MISSING_REASONS
    assert len(ALLOWED_MISSING_REASONS) == 5


def test_allowed_gap_statuses() -> None:
    assert "identified" in ALLOWED_GAP_STATUSES
    assert "under_investigation" in ALLOWED_GAP_STATUSES
    assert "resolved" in ALLOWED_GAP_STATUSES
    assert "accepted" in ALLOWED_GAP_STATUSES
    assert len(ALLOWED_GAP_STATUSES) == 4


def test_load_entries_count() -> None:
    entries = load_data_gap_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_data_gap_entries()
    assert all(isinstance(e, DataGapEntry) for e in entries)


def test_first_entry_fields() -> None:
    entries = load_data_gap_entries()
    first = entries[0]
    assert first.gap_id == "gap-001"
    assert first.track == "radio"
    assert first.missing_reason == "instrument_downtime"
    assert first.status == "identified"
    assert first.resolved_utc is None


def test_under_investigation_entry() -> None:
    entries = load_data_gap_entries()
    under_inv = [e for e in entries if e.status == "under_investigation"]
    assert len(under_inv) == 1


def test_resolved_entries_have_resolved_utc() -> None:
    entries = load_data_gap_entries()
    for e in entries:
        if e.status == "resolved":
            assert e.resolved_utc is not None


def test_identified_entries_have_null_resolved_utc() -> None:
    entries = load_data_gap_entries()
    for e in entries:
        if e.status == "identified":
            assert e.resolved_utc is None


def test_as_dict_keys() -> None:
    entries = load_data_gap_entries()
    d = entries[0].as_dict()
    expected_keys = {
        "gap_id", "track", "missing_reason", "status",
        "expected_utc", "reported_by", "reported_utc",
        "resolved_utc", "notes",
    }
    assert set(d.keys()) == expected_keys


def test_as_dict_values_match() -> None:
    entries = load_data_gap_entries()
    first = entries[0]
    d = first.as_dict()
    assert d["gap_id"] == first.gap_id
    assert d["track"] == first.track
    assert d["missing_reason"] == first.missing_reason
    assert d["status"] == first.status
    assert d["resolved_utc"] == first.resolved_utc


def test_summary_entry_count() -> None:
    summary = data_gap_summary()
    assert summary["entry_count"] == 5


def test_summary_unresolved_count() -> None:
    # identified×2 (gap-001, gap-005) + under_investigation×1 (gap-002) = 3
    summary = data_gap_summary()
    assert summary["unresolved_count"] == 3


def test_summary_resolved_count() -> None:
    summary = data_gap_summary()
    assert summary["resolved_count"] == 1


def test_summary_accepted_count() -> None:
    summary = data_gap_summary()
    assert summary["accepted_count"] == 1


def test_summary_by_status() -> None:
    summary = data_gap_summary()
    by_status = summary["by_status"]
    assert by_status.get("identified", 0) == 2
    assert by_status.get("under_investigation", 0) == 1
    assert by_status.get("resolved", 0) == 1
    assert by_status.get("accepted", 0) == 1


def test_summary_schema_version() -> None:
    summary = data_gap_summary()
    assert summary["schema_version"] == DATA_GAP_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = data_gap_summary()
    assert "detection claim" in summary["disclaimer"]
