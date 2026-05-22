from __future__ import annotations

from techno_search.candidate_match_log import (
    ALLOWED_MATCH_SOURCES,
    ALLOWED_MATCH_STATUSES,
    CANDIDATE_MATCH_DISCLAIMER,
    CANDIDATE_MATCH_SCHEMA_VERSION,
    CandidateMatchEntry,
    candidate_match_summary,
    load_match_entries,
)


def test_schema_version() -> None:
    assert CANDIDATE_MATCH_SCHEMA_VERSION == "candidate_match_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in CANDIDATE_MATCH_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in CANDIDATE_MATCH_DISCLAIMER


def test_disclaimer_no_pathway_modification() -> None:
    assert "pathway routing" in CANDIDATE_MATCH_DISCLAIMER


def test_disclaimer_catalog_match_does_not_confirm() -> None:
    assert "does not confirm" in CANDIDATE_MATCH_DISCLAIMER


def test_allowed_match_sources() -> None:
    assert "simbad" in ALLOWED_MATCH_SOURCES
    assert "gaia" in ALLOWED_MATCH_SOURCES
    assert "vizier" in ALLOWED_MATCH_SOURCES
    assert "irsa" in ALLOWED_MATCH_SOURCES
    assert "internal_catalog" in ALLOWED_MATCH_SOURCES
    assert len(ALLOWED_MATCH_SOURCES) == 5


def test_allowed_match_statuses() -> None:
    assert "matched" in ALLOWED_MATCH_STATUSES
    assert "no_match" in ALLOWED_MATCH_STATUSES
    assert "ambiguous" in ALLOWED_MATCH_STATUSES
    assert "pending" in ALLOWED_MATCH_STATUSES
    assert len(ALLOWED_MATCH_STATUSES) == 4


def test_load_entries_count() -> None:
    entries = load_match_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_match_entries()
    assert all(isinstance(e, CandidateMatchEntry) for e in entries)


def test_first_entry_fields() -> None:
    entries = load_match_entries()
    first = entries[0]
    assert first.match_id == "match-001"
    assert first.candidate_id == "radio-clean-candidate"
    assert first.match_source == "simbad"
    assert first.status == "matched"
    assert first.angular_separation_arcsec == 1.2


def test_matched_entries() -> None:
    entries = load_match_entries()
    matched = [e for e in entries if e.status == "matched"]
    assert len(matched) == 2


def test_no_match_entry() -> None:
    entries = load_match_entries()
    no_match = [e for e in entries if e.status == "no_match"]
    assert len(no_match) == 1


def test_ambiguous_entry() -> None:
    entries = load_match_entries()
    ambiguous = [e for e in entries if e.status == "ambiguous"]
    assert len(ambiguous) == 1


def test_pending_entry_null_angular_separation() -> None:
    entries = load_match_entries()
    pending = [e for e in entries if e.status == "pending"]
    assert len(pending) == 1
    assert pending[0].angular_separation_arcsec is None


def test_matched_entries_have_angular_separation() -> None:
    entries = load_match_entries()
    for e in entries:
        if e.status == "matched":
            assert e.angular_separation_arcsec is not None


def test_as_dict_keys() -> None:
    entries = load_match_entries()
    d = entries[0].as_dict()
    expected_keys = {
        "match_id", "candidate_id", "match_source", "status",
        "matched_by", "matched_utc", "angular_separation_arcsec",
        "matched_object_id", "matched_object_type", "notes",
    }
    assert set(d.keys()) == expected_keys


def test_as_dict_values_match() -> None:
    entries = load_match_entries()
    first = entries[0]
    d = first.as_dict()
    assert d["match_id"] == first.match_id
    assert d["candidate_id"] == first.candidate_id
    assert d["match_source"] == first.match_source
    assert d["status"] == first.status
    assert d["angular_separation_arcsec"] == first.angular_separation_arcsec


def test_summary_entry_count() -> None:
    summary = candidate_match_summary()
    assert summary["entry_count"] == 5


def test_summary_matched_count() -> None:
    summary = candidate_match_summary()
    assert summary["matched_count"] == 2


def test_summary_by_status() -> None:
    summary = candidate_match_summary()
    by_status = summary["by_status"]
    assert by_status.get("matched", 0) == 2
    assert by_status.get("no_match", 0) == 1
    assert by_status.get("ambiguous", 0) == 1
    assert by_status.get("pending", 0) == 1


def test_summary_schema_version() -> None:
    summary = candidate_match_summary()
    assert summary["schema_version"] == CANDIDATE_MATCH_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = candidate_match_summary()
    assert "detection claim" in summary["disclaimer"]
