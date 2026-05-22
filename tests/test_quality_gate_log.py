from __future__ import annotations

from techno_search.quality_gate_log import (
    ALLOWED_GATE_KINDS,
    ALLOWED_GATE_RESULTS,
    QUALITY_GATE_DISCLAIMER,
    QUALITY_GATE_SCHEMA_VERSION,
    QualityGateEntry,
    load_quality_gate_entries,
    quality_gate_summary,
)


def test_schema_version() -> None:
    assert QUALITY_GATE_SCHEMA_VERSION == "quality_gate_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in QUALITY_GATE_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in QUALITY_GATE_DISCLAIMER


def test_disclaimer_no_pathway_modification() -> None:
    assert "pathway routing" in QUALITY_GATE_DISCLAIMER


def test_disclaimer_scheduling_aids() -> None:
    assert "scheduling" in QUALITY_GATE_DISCLAIMER


def test_allowed_gate_kinds() -> None:
    assert "score_threshold" in ALLOWED_GATE_KINDS
    assert "provenance_completeness" in ALLOWED_GATE_KINDS
    assert "rfi_screen" in ALLOWED_GATE_KINDS
    assert "catalog_check" in ALLOWED_GATE_KINDS
    assert "review_coverage" in ALLOWED_GATE_KINDS


def test_allowed_gate_results() -> None:
    assert "pass" in ALLOWED_GATE_RESULTS
    assert "fail" in ALLOWED_GATE_RESULTS
    assert "warn" in ALLOWED_GATE_RESULTS
    assert "not_applicable" in ALLOWED_GATE_RESULTS


def test_load_entries_count() -> None:
    entries = load_quality_gate_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_quality_gate_entries()
    assert all(isinstance(e, QualityGateEntry) for e in entries)


def test_first_entry_fields() -> None:
    entries = load_quality_gate_entries()
    e = entries[0]
    assert e.gate_id == "gate-001"
    assert e.candidate_id == "radio-clean-candidate"
    assert e.gate_kind == "score_threshold"
    assert e.result == "pass"
    assert e.score_at_check == 0.72


def test_pass_entries_count() -> None:
    entries = load_quality_gate_entries()
    passed = [e for e in entries if e.result == "pass"]
    assert len(passed) == 2


def test_fail_entry() -> None:
    entries = load_quality_gate_entries()
    failed = [e for e in entries if e.result == "fail"]
    assert len(failed) == 1
    assert failed[0].gate_kind == "rfi_screen"


def test_warn_entry() -> None:
    entries = load_quality_gate_entries()
    warn = [e for e in entries if e.result == "warn"]
    assert len(warn) == 1
    assert warn[0].gate_kind == "catalog_check"


def test_not_applicable_entry() -> None:
    entries = load_quality_gate_entries()
    na = [e for e in entries if e.result == "not_applicable"]
    assert len(na) == 1
    assert na[0].score_at_check is None


def test_score_at_check_nullable() -> None:
    entries = load_quality_gate_entries()
    null_score = [e for e in entries if e.score_at_check is None]
    assert len(null_score) == 2


def test_as_dict_keys() -> None:
    entries = load_quality_gate_entries()
    d = entries[0].as_dict()
    expected_keys = {
        "gate_id", "candidate_id", "gate_kind", "result",
        "checked_by", "checked_utc", "score_at_check", "notes",
    }
    assert set(d.keys()) == expected_keys


def test_as_dict_values_match() -> None:
    entries = load_quality_gate_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["gate_id"] == e.gate_id
    assert d["result"] == e.result
    assert d["score_at_check"] == e.score_at_check


def test_summary_entry_count() -> None:
    s = quality_gate_summary()
    assert s["entry_count"] == 5


def test_summary_pass_count() -> None:
    s = quality_gate_summary()
    assert s["pass_count"] == 2


def test_summary_fail_count() -> None:
    s = quality_gate_summary()
    assert s["fail_count"] == 1


def test_summary_warn_count() -> None:
    s = quality_gate_summary()
    assert s["warn_count"] == 1


def test_summary_not_applicable_count() -> None:
    s = quality_gate_summary()
    assert s["not_applicable_count"] == 1


def test_summary_schema_version() -> None:
    s = quality_gate_summary()
    assert s["schema_version"] == QUALITY_GATE_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = quality_gate_summary()
    assert "detection claim" in s["disclaimer"]
