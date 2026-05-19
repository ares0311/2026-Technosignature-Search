from __future__ import annotations

from techno_search.candidate_alert_log import (
    ALLOWED_ALERT_KINDS,
    ALLOWED_ALERT_SEVERITIES,
    CANDIDATE_ALERT_DISCLAIMER,
    CANDIDATE_ALERT_SCHEMA_VERSION,
    CandidateAlertEntry,
    candidate_alert_summary,
    load_alert_entries,
)


def test_schema_version() -> None:
    assert CANDIDATE_ALERT_SCHEMA_VERSION == "candidate_alert_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in CANDIDATE_ALERT_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "does not" in CANDIDATE_ALERT_DISCLAIMER
    assert "authorize external submission" in CANDIDATE_ALERT_DISCLAIMER


def test_disclaimer_no_pathway_modification() -> None:
    assert "pathway routing" in CANDIDATE_ALERT_DISCLAIMER


def test_allowed_severities() -> None:
    assert "info" in ALLOWED_ALERT_SEVERITIES
    assert "warning" in ALLOWED_ALERT_SEVERITIES
    assert "critical" in ALLOWED_ALERT_SEVERITIES


def test_allowed_kinds_contains_expected() -> None:
    assert "score_threshold_crossed" in ALLOWED_ALERT_KINDS
    assert "pathway_changed" in ALLOWED_ALERT_KINDS
    assert "flag_raised" in ALLOWED_ALERT_KINDS
    assert "rescore_triggered" in ALLOWED_ALERT_KINDS
    assert "provenance_inconsistency" in ALLOWED_ALERT_KINDS
    assert "deadline_approaching" in ALLOWED_ALERT_KINDS
    assert "operator_action_required" in ALLOWED_ALERT_KINDS


def test_load_entries_count() -> None:
    entries = load_alert_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_alert_entries()
    for e in entries:
        assert isinstance(e, CandidateAlertEntry)


def test_entry_fields() -> None:
    entries = load_alert_entries()
    e = entries[0]
    assert e.alert_id == "alrt-001"
    assert e.candidate_id == "radio-clean-candidate"
    assert e.alert_kind == "score_threshold_crossed"
    assert e.severity == "info"
    assert e.resolved is True
    assert e.resolved_utc is not None


def test_unresolved_entry_has_no_resolved_utc() -> None:
    entries = load_alert_entries()
    open_entries = [e for e in entries if not e.resolved]
    for e in open_entries:
        assert e.resolved_utc is None


def test_critical_entry_present() -> None:
    entries = load_alert_entries()
    critical = [e for e in entries if e.severity == "critical"]
    assert len(critical) >= 1
    assert critical[0].alert_id == "alrt-003"


def test_as_dict_keys() -> None:
    entries = load_alert_entries()
    d = entries[0].as_dict()
    expected = {
        "alert_id", "candidate_id", "alert_kind", "severity",
        "message", "resolved", "alert_utc", "resolved_utc", "notes",
    }
    assert set(d.keys()) == expected


def test_as_dict_values_match() -> None:
    entries = load_alert_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["alert_id"] == e.alert_id
    assert d["severity"] == e.severity
    assert d["resolved"] == e.resolved


def test_summary_entry_count() -> None:
    s = candidate_alert_summary()
    assert s["entry_count"] == 5


def test_summary_open_count() -> None:
    s = candidate_alert_summary()
    assert s["open_count"] == 3


def test_summary_resolved_count() -> None:
    s = candidate_alert_summary()
    assert s["resolved_count"] == 2


def test_summary_critical_open_count() -> None:
    s = candidate_alert_summary()
    assert s["critical_open_count"] == 1


def test_summary_by_severity() -> None:
    s = candidate_alert_summary()
    bv = s["by_severity"]
    assert bv.get("info", 0) == 2
    assert bv.get("warning", 0) == 2
    assert bv.get("critical", 0) == 1


def test_summary_by_kind() -> None:
    s = candidate_alert_summary()
    bk = s["by_kind"]
    assert "score_threshold_crossed" in bk
    assert "pathway_changed" in bk
    assert "provenance_inconsistency" in bk


def test_summary_schema_version() -> None:
    s = candidate_alert_summary()
    assert s["schema_version"] == CANDIDATE_ALERT_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = candidate_alert_summary()
    assert "disclaimer" in s
    assert "detection claim" in s["disclaimer"]
