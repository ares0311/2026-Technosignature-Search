from __future__ import annotations

from techno_search.candidate_export_log import (
    ALLOWED_EXPORT_FORMATS,
    ALLOWED_EXPORT_STATUSES,
    CANDIDATE_EXPORT_DISCLAIMER,
    CANDIDATE_EXPORT_SCHEMA_VERSION,
    CandidateExportEntry,
    candidate_export_summary,
    load_export_entries,
)


def test_schema_version() -> None:
    assert CANDIDATE_EXPORT_SCHEMA_VERSION == "candidate_export_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in CANDIDATE_EXPORT_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in CANDIDATE_EXPORT_DISCLAIMER


def test_disclaimer_no_pathway_modification() -> None:
    assert "pathway routing" in CANDIDATE_EXPORT_DISCLAIMER


def test_disclaimer_provenance_records() -> None:
    assert "provenance records" in CANDIDATE_EXPORT_DISCLAIMER


def test_allowed_export_formats() -> None:
    assert "json" in ALLOWED_EXPORT_FORMATS
    assert "csv" in ALLOWED_EXPORT_FORMATS
    assert "markdown" in ALLOWED_EXPORT_FORMATS
    assert "fits_stub" in ALLOWED_EXPORT_FORMATS
    assert "parquet_stub" in ALLOWED_EXPORT_FORMATS


def test_allowed_export_statuses() -> None:
    assert "prepared" in ALLOWED_EXPORT_STATUSES
    assert "exported" in ALLOWED_EXPORT_STATUSES
    assert "delivered" in ALLOWED_EXPORT_STATUSES
    assert "failed" in ALLOWED_EXPORT_STATUSES
    assert "cancelled" in ALLOWED_EXPORT_STATUSES


def test_load_entries_count() -> None:
    entries = load_export_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_export_entries()
    assert all(isinstance(e, CandidateExportEntry) for e in entries)


def test_first_entry_fields() -> None:
    entries = load_export_entries()
    e = entries[0]
    assert e.export_id == "exp-001"
    assert e.candidate_id == "radio-clean-candidate"
    assert e.export_format == "json"
    assert e.status == "exported"
    assert e.destination == "internal-review-bucket"


def test_exported_entries() -> None:
    entries = load_export_entries()
    exported = [e for e in entries if e.status == "exported"]
    assert len(exported) == 2


def test_delivered_entry() -> None:
    entries = load_export_entries()
    delivered = [e for e in entries if e.status == "delivered"]
    assert len(delivered) == 1
    assert delivered[0].export_id == "exp-002"


def test_failed_entry() -> None:
    entries = load_export_entries()
    failed = [e for e in entries if e.status == "failed"]
    assert len(failed) == 1
    assert failed[0].export_id == "exp-004"


def test_prepared_entry_null_destination() -> None:
    entries = load_export_entries()
    prepared = [e for e in entries if e.status == "prepared"]
    assert len(prepared) == 1
    assert prepared[0].destination is None


def test_as_dict_keys() -> None:
    entries = load_export_entries()
    d = entries[0].as_dict()
    expected_keys = {
        "export_id", "candidate_id", "export_format", "status",
        "exported_by", "exported_utc", "destination", "notes",
    }
    assert set(d.keys()) == expected_keys


def test_as_dict_values_match() -> None:
    entries = load_export_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["export_id"] == e.export_id
    assert d["status"] == e.status


def test_summary_entry_count() -> None:
    s = candidate_export_summary()
    assert s["entry_count"] == 5


def test_summary_delivered_count() -> None:
    s = candidate_export_summary()
    assert s["delivered_count"] == 1


def test_summary_exported_count() -> None:
    s = candidate_export_summary()
    assert s["exported_count"] == 2


def test_summary_failed_count() -> None:
    s = candidate_export_summary()
    assert s["failed_count"] == 1


def test_summary_by_status() -> None:
    s = candidate_export_summary()
    assert s["by_status"]["exported"] == 2
    assert s["by_status"]["delivered"] == 1


def test_summary_schema_version() -> None:
    s = candidate_export_summary()
    assert s["schema_version"] == CANDIDATE_EXPORT_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = candidate_export_summary()
    assert "detection claim" in s["disclaimer"]
