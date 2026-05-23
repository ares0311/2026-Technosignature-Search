"""Tests for rfi_mitigation_log module."""
from __future__ import annotations

from pathlib import Path

import pytest

from techno_search.rfi_mitigation_log import (
    ALLOWED_MITIGATION_ACTIONS,
    ALLOWED_MITIGATION_KINDS,
    RFI_MITIGATION_DISCLAIMER,
    RFI_MITIGATION_SCHEMA_VERSION,
    load_rfi_mitigation_entries,
    rfi_mitigation_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "rfi_mitigation_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_rfi_mitigation_entries()
    assert len(entries) == 5


def test_all_mitigation_kinds_present() -> None:
    entries = load_rfi_mitigation_entries()
    kinds = {e.mitigation_kind for e in entries}
    assert "known_rfi_source" in kinds
    assert "satellite_track" in kinds
    assert "statistical_outlier" in kinds
    assert "terrestrial_interference" in kinds
    assert "other" in kinds


def test_all_actions_present() -> None:
    entries = load_rfi_mitigation_entries()
    actions = {e.action for e in entries}
    assert "flagged" in actions
    assert "excised" in actions
    assert "masked" in actions
    assert "passed" in actions


def test_summary_entry_count_five() -> None:
    summary = rfi_mitigation_summary()
    assert summary["entry_count"] == 5


def test_flagged_count_is_two() -> None:
    summary = rfi_mitigation_summary()
    assert summary["flagged_count"] == 2


def test_excised_count_is_one() -> None:
    summary = rfi_mitigation_summary()
    assert summary["excised_count"] == 1


def test_masked_count_is_one() -> None:
    summary = rfi_mitigation_summary()
    assert summary["masked_count"] == 1


def test_passed_count_is_one() -> None:
    summary = rfi_mitigation_summary()
    assert summary["passed_count"] == 1


def test_by_action_covers_all_present_actions() -> None:
    summary = rfi_mitigation_summary()
    by_action = summary["by_action"]
    assert "flagged" in by_action
    assert "excised" in by_action
    assert "masked" in by_action
    assert "passed" in by_action


def test_by_mitigation_kind_covers_all_five() -> None:
    summary = rfi_mitigation_summary()
    by_kind = summary["by_mitigation_kind"]
    assert len(by_kind) >= 5


def test_by_track_is_radio_only() -> None:
    summary = rfi_mitigation_summary()
    by_track = summary["by_track"]
    assert "radio" in by_track
    assert by_track["radio"] == 5


def test_schema_version() -> None:
    summary = rfi_mitigation_summary()
    assert summary["schema_version"] == RFI_MITIGATION_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = rfi_mitigation_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == RFI_MITIGATION_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = rfi_mitigation_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_mitigation_kinds_has_five_members() -> None:
    assert len(ALLOWED_MITIGATION_KINDS) == 5


def test_allowed_mitigation_actions_has_five_members() -> None:
    assert len(ALLOWED_MITIGATION_ACTIONS) == 5


def test_fixture_mitigation_kinds_in_allowed() -> None:
    entries = load_rfi_mitigation_entries()
    for e in entries:
        assert e.mitigation_kind in ALLOWED_MITIGATION_KINDS


def test_fixture_action_values_in_allowed() -> None:
    entries = load_rfi_mitigation_entries()
    for e in entries:
        assert e.action in ALLOWED_MITIGATION_ACTIONS


def test_frequency_mhz_nullable() -> None:
    entries = load_rfi_mitigation_entries()
    rfimit003 = next(e for e in entries if e.entry_id == "rfimit-003")
    assert rfimit003.frequency_mhz is None


def test_frequency_mhz_rfimit001_is_gps() -> None:
    entries = load_rfi_mitigation_entries()
    rfimit001 = next(e for e in entries if e.entry_id == "rfimit-001")
    assert rfimit001.frequency_mhz == pytest.approx(1575.42)


def test_as_dict_returns_required_keys() -> None:
    entries = load_rfi_mitigation_entries()
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "candidate_id" in d
    assert "mitigation_kind" in d
    assert "action" in d
    assert "mitigated_by" in d
    assert "mitigated_at" in d
    assert "track" in d
    assert "frequency_mhz" in d
    assert "notes" in d


def test_custom_path_argument() -> None:
    entries = load_rfi_mitigation_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = rfi_mitigation_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5
