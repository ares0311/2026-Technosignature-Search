from __future__ import annotations

from techno_search.scoring_threshold_audit import (
    ALLOWED_THRESHOLD_AUDIT_VERDICTS,
    SCORING_THRESHOLD_AUDIT_DISCLAIMER,
    SCORING_THRESHOLD_AUDIT_SCHEMA_VERSION,
    ScoringThresholdAuditEntry,
    load_threshold_audit_entries,
    scoring_threshold_audit_summary,
)


def test_schema_version() -> None:
    assert SCORING_THRESHOLD_AUDIT_SCHEMA_VERSION == "scoring_threshold_audit_v1"


def test_disclaimer_local_provenance_only() -> None:
    assert "local provenance consistency checks only" in SCORING_THRESHOLD_AUDIT_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "does not authorize external submission" in SCORING_THRESHOLD_AUDIT_DISCLAIMER


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in SCORING_THRESHOLD_AUDIT_DISCLAIMER


def test_disclaimer_not_scientifically_calibrated() -> None:
    assert "scientifically" in SCORING_THRESHOLD_AUDIT_DISCLAIMER


def test_allowed_verdicts() -> None:
    assert "pass" in ALLOWED_THRESHOLD_AUDIT_VERDICTS
    assert "fail" in ALLOWED_THRESHOLD_AUDIT_VERDICTS
    assert "warning" in ALLOWED_THRESHOLD_AUDIT_VERDICTS
    assert "not_checked" in ALLOWED_THRESHOLD_AUDIT_VERDICTS


def test_load_entries_count() -> None:
    entries = load_threshold_audit_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_threshold_audit_entries()
    for e in entries:
        assert isinstance(e, ScoringThresholdAuditEntry)


def test_first_entry_fields() -> None:
    entries = load_threshold_audit_entries()
    e = entries[0]
    assert e.audit_id == "thr-001"
    assert e.config_id == "pcfg-001"
    assert e.scoring_config_version == "scoring_v0"
    assert e.track == "radio"
    assert e.threshold_name == "candidate_review_packet_min_score"
    assert e.expected_value == 0.75
    assert e.observed_value == 0.75
    assert e.verdict == "pass"


def test_pass_entries_count() -> None:
    entries = load_threshold_audit_entries()
    passed = [e for e in entries if e.verdict == "pass"]
    assert len(passed) == 3


def test_warning_entry_present() -> None:
    entries = load_threshold_audit_entries()
    warnings = [e for e in entries if e.verdict == "warning"]
    assert len(warnings) == 1
    assert warnings[0].audit_id == "thr-004"


def test_not_checked_entry_present() -> None:
    entries = load_threshold_audit_entries()
    not_checked = [e for e in entries if e.verdict == "not_checked"]
    assert len(not_checked) == 1
    assert not_checked[0].audit_id == "thr-005"


def test_as_dict_keys() -> None:
    entries = load_threshold_audit_entries()
    d = entries[0].as_dict()
    expected = {
        "audit_id", "config_id", "scoring_config_version", "track",
        "threshold_name", "expected_value", "observed_value",
        "verdict", "audit_utc", "notes",
    }
    assert set(d.keys()) == expected


def test_as_dict_values_match() -> None:
    entries = load_threshold_audit_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["audit_id"] == e.audit_id
    assert d["expected_value"] == e.expected_value
    assert d["verdict"] == e.verdict


def test_summary_entry_count() -> None:
    s = scoring_threshold_audit_summary()
    assert s["entry_count"] == 5


def test_summary_pass_count() -> None:
    s = scoring_threshold_audit_summary()
    assert s["pass_count"] == 3


def test_summary_fail_count() -> None:
    s = scoring_threshold_audit_summary()
    assert s["fail_count"] == 0


def test_summary_warning_count() -> None:
    s = scoring_threshold_audit_summary()
    assert s["warning_count"] == 1


def test_summary_not_checked_count() -> None:
    s = scoring_threshold_audit_summary()
    assert s["not_checked_count"] == 1


def test_summary_tracks_covered() -> None:
    s = scoring_threshold_audit_summary()
    tracks = s["tracks_covered"]
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_summary_all_passed_true_when_no_fails() -> None:
    s = scoring_threshold_audit_summary()
    assert s["all_passed"] is True


def test_summary_by_verdict() -> None:
    s = scoring_threshold_audit_summary()
    bv = s["by_verdict"]
    assert bv.get("pass", 0) == 3
    assert bv.get("warning", 0) == 1
    assert bv.get("not_checked", 0) == 1


def test_summary_schema_version() -> None:
    s = scoring_threshold_audit_summary()
    assert s["schema_version"] == SCORING_THRESHOLD_AUDIT_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = scoring_threshold_audit_summary()
    assert "disclaimer" in s
    assert "detection claim" in s["disclaimer"]
