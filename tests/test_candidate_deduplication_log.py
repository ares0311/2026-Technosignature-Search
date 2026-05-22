from __future__ import annotations

from techno_search.candidate_deduplication_log import (
    ALLOWED_DEDUPLICATION_STATUSES,
    ALLOWED_MATCH_KINDS,
    CANDIDATE_DEDUPLICATION_DISCLAIMER,
    CANDIDATE_DEDUPLICATION_SCHEMA_VERSION,
    CandidateDeduplicationEntry,
    candidate_deduplication_summary,
    load_deduplication_entries,
)


def test_schema_version() -> None:
    assert CANDIDATE_DEDUPLICATION_SCHEMA_VERSION == "candidate_deduplication_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in CANDIDATE_DEDUPLICATION_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in CANDIDATE_DEDUPLICATION_DISCLAIMER


def test_disclaimer_does_not_remove_candidates() -> None:
    assert "does not remove candidates" in CANDIDATE_DEDUPLICATION_DISCLAIMER


def test_disclaimer_no_pathway_modification() -> None:
    assert "pathway routing" in CANDIDATE_DEDUPLICATION_DISCLAIMER


def test_allowed_statuses() -> None:
    assert "pending" in ALLOWED_DEDUPLICATION_STATUSES
    assert "confirmed_duplicate" in ALLOWED_DEDUPLICATION_STATUSES
    assert "confirmed_distinct" in ALLOWED_DEDUPLICATION_STATUSES
    assert "inconclusive" in ALLOWED_DEDUPLICATION_STATUSES


def test_allowed_match_kinds() -> None:
    assert "cross_candidate" in ALLOWED_MATCH_KINDS
    assert "known_object" in ALLOWED_MATCH_KINDS
    assert "prior_epoch" in ALLOWED_MATCH_KINDS
    assert "catalog_match" in ALLOWED_MATCH_KINDS


def test_load_entries_count() -> None:
    entries = load_deduplication_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_deduplication_entries()
    for e in entries:
        assert isinstance(e, CandidateDeduplicationEntry)


def test_first_entry_fields() -> None:
    entries = load_deduplication_entries()
    e = entries[0]
    assert e.dedup_id == "dedup-001"
    assert e.candidate_id == "radio-clean-candidate"
    assert e.match_kind == "prior_epoch"
    assert e.status == "confirmed_distinct"
    assert e.compared_to_id == "radio-epoch-2025-candidate"
    assert e.compared_by == "operator-alpha"
    assert e.match_score == 0.12
    assert e.resolved_utc is not None


def test_pending_entry_present() -> None:
    entries = load_deduplication_entries()
    pending = [e for e in entries if e.status == "pending"]
    assert len(pending) == 1
    assert pending[0].dedup_id == "dedup-005"


def test_confirmed_duplicate_entry() -> None:
    entries = load_deduplication_entries()
    dups = [e for e in entries if e.status == "confirmed_duplicate"]
    assert len(dups) == 1
    assert dups[0].dedup_id == "dedup-002"


def test_inconclusive_entry_no_resolved_utc() -> None:
    entries = load_deduplication_entries()
    inc = [e for e in entries if e.status == "inconclusive"]
    assert len(inc) == 1
    assert inc[0].resolved_utc is None


def test_pending_entry_null_match_score() -> None:
    entries = load_deduplication_entries()
    pending = [e for e in entries if e.status == "pending"]
    assert pending[0].match_score is None


def test_as_dict_keys() -> None:
    entries = load_deduplication_entries()
    d = entries[0].as_dict()
    expected = {
        "dedup_id", "candidate_id", "match_kind", "status",
        "compared_to_id", "compared_by", "compared_utc",
        "match_score", "resolved_utc", "notes",
    }
    assert set(d.keys()) == expected


def test_as_dict_values_match() -> None:
    entries = load_deduplication_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["dedup_id"] == e.dedup_id
    assert d["status"] == e.status
    assert d["match_kind"] == e.match_kind


def test_summary_entry_count() -> None:
    s = candidate_deduplication_summary()
    assert s["entry_count"] == 5


def test_summary_pending_count() -> None:
    s = candidate_deduplication_summary()
    assert s["pending_count"] == 1


def test_summary_confirmed_duplicate_count() -> None:
    s = candidate_deduplication_summary()
    assert s["confirmed_duplicate_count"] == 1


def test_summary_confirmed_distinct_count() -> None:
    s = candidate_deduplication_summary()
    assert s["confirmed_distinct_count"] == 2


def test_summary_by_status() -> None:
    s = candidate_deduplication_summary()
    bs = s["by_status"]
    assert bs.get("confirmed_distinct", 0) == 2
    assert bs.get("confirmed_duplicate", 0) == 1
    assert bs.get("inconclusive", 0) == 1
    assert bs.get("pending", 0) == 1


def test_summary_by_kind() -> None:
    s = candidate_deduplication_summary()
    bk = s["by_kind"]
    assert bk.get("prior_epoch", 0) == 2
    assert bk.get("catalog_match", 0) == 1
    assert bk.get("known_object", 0) == 1
    assert bk.get("cross_candidate", 0) == 1


def test_summary_schema_version() -> None:
    s = candidate_deduplication_summary()
    assert s["schema_version"] == CANDIDATE_DEDUPLICATION_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = candidate_deduplication_summary()
    assert "disclaimer" in s
    assert "detection claim" in s["disclaimer"]
