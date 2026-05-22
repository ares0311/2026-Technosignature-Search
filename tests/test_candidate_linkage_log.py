"""Tests for candidate_linkage_log module."""
from __future__ import annotations

from pathlib import Path

import pytest

from techno_search.candidate_linkage_log import (
    ALLOWED_LINKAGE_KINDS,
    ALLOWED_LINKAGE_STATUSES,
    CANDIDATE_LINKAGE_DISCLAIMER,
    CANDIDATE_LINKAGE_SCHEMA_VERSION,
    candidate_linkage_summary,
    load_linkage_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "candidate_linkage_log.json"


def test_load_linkage_entries_returns_five() -> None:
    entries = load_linkage_entries()
    assert len(entries) == 5


def test_all_linkage_kinds_present() -> None:
    entries = load_linkage_entries()
    kinds = {e.linkage_kind for e in entries}
    assert "same_source" in kinds
    assert "temporal_followup" in kinds
    assert "spatial_neighbor" in kinds
    assert "frequency_related" in kinds
    assert "cross_track" in kinds


def test_all_linkage_statuses_present() -> None:
    entries = load_linkage_entries()
    statuses = {e.status for e in entries}
    assert "proposed" in statuses
    assert "confirmed" in statuses
    assert "rejected" in statuses
    assert "under_review" in statuses


def test_summary_entry_count_five() -> None:
    summary = candidate_linkage_summary()
    assert summary["entry_count"] == 5


def test_confirmed_count_is_two() -> None:
    summary = candidate_linkage_summary()
    assert summary["confirmed_count"] == 2


def test_proposed_count_is_one() -> None:
    summary = candidate_linkage_summary()
    assert summary["proposed_count"] == 1


def test_rejected_count_is_one() -> None:
    summary = candidate_linkage_summary()
    assert summary["rejected_count"] == 1


def test_under_review_count_is_one() -> None:
    summary = candidate_linkage_summary()
    assert summary["under_review_count"] == 1


def test_by_status_covers_all_four() -> None:
    summary = candidate_linkage_summary()
    by_status = summary["by_status"]
    assert set(by_status.keys()) == {"proposed", "confirmed", "rejected", "under_review"}


def test_by_linkage_kind_covers_all_five() -> None:
    summary = candidate_linkage_summary()
    by_kind = summary["by_linkage_kind"]
    assert len(by_kind) >= 5


def test_schema_version() -> None:
    summary = candidate_linkage_summary()
    assert summary["schema_version"] == CANDIDATE_LINKAGE_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = candidate_linkage_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == CANDIDATE_LINKAGE_DISCLAIMER


def test_separation_arcsec_nullable_link001() -> None:
    entries = load_linkage_entries()
    link001 = next(e for e in entries if e.linkage_id == "link-001")
    assert link001.separation_arcsec is None


def test_separation_arcsec_link002_is_4_2() -> None:
    entries = load_linkage_entries()
    link002 = next(e for e in entries if e.linkage_id == "link-002")
    assert link002.separation_arcsec == pytest.approx(4.2)


def test_as_dict_returns_required_keys() -> None:
    entries = load_linkage_entries()
    d = entries[0].as_dict()
    assert "linkage_id" in d
    assert "candidate_id_a" in d
    assert "candidate_id_b" in d
    assert "linkage_kind" in d
    assert "status" in d
    assert "linked_by" in d
    assert "linked_utc" in d
    assert "separation_arcsec" in d
    assert "notes" in d


def test_allowed_linkage_kinds_has_five_members() -> None:
    assert len(ALLOWED_LINKAGE_KINDS) == 5


def test_allowed_linkage_statuses_has_four_members() -> None:
    assert len(ALLOWED_LINKAGE_STATUSES) == 4


def test_fixture_linkage_kinds_in_allowed() -> None:
    entries = load_linkage_entries()
    for e in entries:
        assert e.linkage_kind in ALLOWED_LINKAGE_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_linkage_entries()
    for e in entries:
        assert e.status in ALLOWED_LINKAGE_STATUSES


def test_summary_no_detection_language() -> None:
    summary = candidate_linkage_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_custom_path_argument() -> None:
    entries = load_linkage_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = candidate_linkage_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5
