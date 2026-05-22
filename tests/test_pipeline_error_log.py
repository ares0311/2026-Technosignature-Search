from __future__ import annotations

from techno_search.pipeline_error_log import (
    ALLOWED_ERROR_KINDS,
    ALLOWED_ERROR_SEVERITIES,
    PIPELINE_ERROR_DISCLAIMER,
    PIPELINE_ERROR_SCHEMA_VERSION,
    PipelineErrorEntry,
    load_error_entries,
    pipeline_error_summary,
)


def test_schema_version() -> None:
    assert PIPELINE_ERROR_SCHEMA_VERSION == "pipeline_error_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in PIPELINE_ERROR_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in PIPELINE_ERROR_DISCLAIMER


def test_disclaimer_no_pathway_modification() -> None:
    assert "pathway routing" in PIPELINE_ERROR_DISCLAIMER


def test_disclaimer_scheduling_aids() -> None:
    assert "scheduling" in PIPELINE_ERROR_DISCLAIMER


def test_allowed_error_kinds() -> None:
    assert "scoring_failure" in ALLOWED_ERROR_KINDS
    assert "data_missing" in ALLOWED_ERROR_KINDS
    assert "config_mismatch" in ALLOWED_ERROR_KINDS
    assert "timeout" in ALLOWED_ERROR_KINDS
    assert "validation_error" in ALLOWED_ERROR_KINDS
    assert len(ALLOWED_ERROR_KINDS) == 5


def test_allowed_error_severities() -> None:
    assert "warning" in ALLOWED_ERROR_SEVERITIES
    assert "error" in ALLOWED_ERROR_SEVERITIES
    assert "critical" in ALLOWED_ERROR_SEVERITIES
    assert len(ALLOWED_ERROR_SEVERITIES) == 3


def test_load_entries_count() -> None:
    entries = load_error_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_error_entries()
    assert all(isinstance(e, PipelineErrorEntry) for e in entries)


def test_first_entry_fields() -> None:
    entries = load_error_entries()
    first = entries[0]
    assert first.error_id == "err-001"
    assert first.error_kind == "scoring_failure"
    assert first.severity == "critical"
    assert first.resolved is False
    assert first.resolved_utc is None


def test_unresolved_entries_count() -> None:
    entries = load_error_entries()
    unresolved = [e for e in entries if not e.resolved]
    assert len(unresolved) == 2


def test_resolved_entries_have_resolved_utc() -> None:
    entries = load_error_entries()
    for e in entries:
        if e.resolved:
            assert e.resolved_utc is not None


def test_unresolved_entries_have_null_resolved_utc() -> None:
    entries = load_error_entries()
    for e in entries:
        if not e.resolved:
            assert e.resolved_utc is None


def test_critical_entry_present() -> None:
    entries = load_error_entries()
    critical = [e for e in entries if e.severity == "critical"]
    assert len(critical) == 1


def test_as_dict_keys() -> None:
    entries = load_error_entries()
    d = entries[0].as_dict()
    expected_keys = {
        "error_id", "error_kind", "severity", "resolved",
        "reported_by", "reported_utc", "pipeline_stage",
        "resolved_utc", "notes",
    }
    assert set(d.keys()) == expected_keys


def test_as_dict_values_match() -> None:
    entries = load_error_entries()
    first = entries[0]
    d = first.as_dict()
    assert d["error_id"] == first.error_id
    assert d["error_kind"] == first.error_kind
    assert d["severity"] == first.severity
    assert d["resolved"] == first.resolved
    assert d["resolved_utc"] == first.resolved_utc


def test_summary_entry_count() -> None:
    summary = pipeline_error_summary()
    assert summary["entry_count"] == 5


def test_summary_unresolved_count() -> None:
    summary = pipeline_error_summary()
    assert summary["unresolved_count"] == 2


def test_summary_resolved_count() -> None:
    summary = pipeline_error_summary()
    assert summary["resolved_count"] == 3


def test_summary_critical_count() -> None:
    summary = pipeline_error_summary()
    assert summary["critical_count"] == 1


def test_summary_schema_version() -> None:
    summary = pipeline_error_summary()
    assert summary["schema_version"] == PIPELINE_ERROR_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = pipeline_error_summary()
    assert "detection claim" in summary["disclaimer"]
