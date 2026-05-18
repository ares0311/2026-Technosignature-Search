from __future__ import annotations

import json
from pathlib import Path

from techno_search.provenance_audit import (
    ALLOWED_AUDIT_VERDICTS,
    PROVENANCE_AUDIT_DISCLAIMER,
    PROVENANCE_AUDIT_SCHEMA_VERSION,
    ProvenanceAuditEntry,
    load_provenance_audit_entries,
    provenance_audit_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "provenance_audit.json"


def test_schema_version():
    assert PROVENANCE_AUDIT_SCHEMA_VERSION == "provenance_audit_v1"


def test_disclaimer_present():
    assert len(PROVENANCE_AUDIT_DISCLAIMER) > 20
    assert "provenance" in PROVENANCE_AUDIT_DISCLAIMER.lower()


def test_disclaimer_no_authorization():
    lower = PROVENANCE_AUDIT_DISCLAIMER.lower()
    assert "does not authorize external submission" in lower


def test_allowed_verdicts():
    assert "consistent" in ALLOWED_AUDIT_VERDICTS
    assert "inconsistent" in ALLOWED_AUDIT_VERDICTS
    assert "partial" in ALLOWED_AUDIT_VERDICTS
    assert "not_applicable" in ALLOWED_AUDIT_VERDICTS


def test_load_returns_list():
    entries = load_provenance_audit_entries(FIXTURE_PATH)
    assert isinstance(entries, list)


def test_load_count():
    entries = load_provenance_audit_entries(FIXTURE_PATH)
    assert len(entries) == 4


def test_entry_fields():
    entries = load_provenance_audit_entries(FIXTURE_PATH)
    e = entries[0]
    assert isinstance(e, ProvenanceAuditEntry)
    assert e.audit_id == "aud-001"
    assert e.verdict == "consistent"
    assert isinstance(e.checked_modules, list)
    assert isinstance(e.inconsistencies, list)


def test_entry_as_dict():
    entries = load_provenance_audit_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "audit_id" in d
    assert "candidate_id" in d
    assert "verdict" in d
    assert "checked_modules" in d
    assert "inconsistencies" in d


def test_consistent_entry_no_inconsistencies():
    entries = load_provenance_audit_entries(FIXTURE_PATH)
    consistent = [e for e in entries if e.verdict == "consistent"]
    assert len(consistent) >= 1
    for e in consistent:
        assert len(e.inconsistencies) == 0


def test_inconsistent_entry_has_issues():
    entries = load_provenance_audit_entries(FIXTURE_PATH)
    inconsistent = [e for e in entries if e.verdict == "inconsistent"]
    assert len(inconsistent) >= 1
    assert len(inconsistent[0].inconsistencies) > 0


def test_partial_entry_has_checked_modules():
    entries = load_provenance_audit_entries(FIXTURE_PATH)
    partial = [e for e in entries if e.verdict == "partial"]
    assert len(partial) >= 1
    assert len(partial[0].checked_modules) > 0


def test_not_applicable_entry_empty_modules():
    entries = load_provenance_audit_entries(FIXTURE_PATH)
    na = [e for e in entries if e.verdict == "not_applicable"]
    assert len(na) >= 1
    assert len(na[0].checked_modules) == 0


def test_all_verdicts_valid():
    entries = load_provenance_audit_entries(FIXTURE_PATH)
    for e in entries:
        assert e.verdict in ALLOWED_AUDIT_VERDICTS


def test_summary_entry_count():
    summary = provenance_audit_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 4


def test_summary_consistent_count():
    summary = provenance_audit_summary(FIXTURE_PATH)
    assert summary["consistent_count"] == 1


def test_summary_inconsistent_count():
    summary = provenance_audit_summary(FIXTURE_PATH)
    assert summary["inconsistent_count"] == 1


def test_summary_by_verdict():
    summary = provenance_audit_summary(FIXTURE_PATH)
    bv = summary["by_verdict"]
    assert bv["consistent"] == 1
    assert bv["inconsistent"] == 1
    assert bv["partial"] == 1
    assert bv["not_applicable"] == 1


def test_summary_total_inconsistencies():
    summary = provenance_audit_summary(FIXTURE_PATH)
    assert summary["total_inconsistency_count"] >= 1


def test_summary_modules_covered():
    summary = provenance_audit_summary(FIXTURE_PATH)
    modules = summary["modules_covered"]
    assert "pipeline_config" in modules
    assert "model_serving" in modules


def test_summary_disclaimer():
    summary = provenance_audit_summary(FIXTURE_PATH)
    assert len(summary["disclaimer"]) > 20


def test_fixture_json_valid():
    data = json.loads(FIXTURE_PATH.read_text())
    assert "provenance_audit_entries" in data
    assert len(data["provenance_audit_entries"]) >= 4


def test_fixture_required_fields():
    data = json.loads(FIXTURE_PATH.read_text())
    required = {
        "audit_id", "candidate_id", "verdict",
        "checked_modules", "inconsistencies", "audit_utc",
    }
    for entry in data["provenance_audit_entries"]:
        for f in required:
            assert f in entry, f"Missing {f} in {entry.get('audit_id')}"
