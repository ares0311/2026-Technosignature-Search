"""Tests for telescope_status_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.telescope_status_log import (
    ALLOWED_TELESCOPE_STATUS_KINDS,
    ALLOWED_TELESCOPE_STATUS_STATUSES,
    TELESCOPE_STATUS_LOG_DISCLAIMER,
    TELESCOPE_STATUS_LOG_SCHEMA_VERSION,
    load_telescope_status_entries,
    telescope_status_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "telescope_status_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_telescope_status_entries()
    assert len(entries) == 5


def test_all_status_kinds_present() -> None:
    entries = load_telescope_status_entries()
    kinds = {e.status_kind for e in entries}
    assert "operational" in kinds
    assert "maintenance" in kinds
    assert "degraded" in kinds
    assert "offline" in kinds
    assert "commissioning" in kinds


def test_all_statuses_present() -> None:
    entries = load_telescope_status_entries()
    statuses = {e.status for e in entries}
    assert "recorded" in statuses
    assert "updated" in statuses
    assert "superseded" in statuses
    assert "error" in statuses


def test_summary_entry_count_five() -> None:
    summary = telescope_status_log_summary()
    assert summary["entry_count"] == 5


def test_recorded_count_is_two() -> None:
    summary = telescope_status_log_summary()
    assert summary["recorded_count"] == 2


def test_operational_count_is_one() -> None:
    summary = telescope_status_log_summary()
    assert summary["operational_count"] == 1


def test_counts_by_status_covers_all_four() -> None:
    summary = telescope_status_log_summary()
    by_status = summary["counts_by_status"]
    assert set(by_status.keys()) == {"recorded", "updated", "superseded", "error"}


def test_counts_by_kind_covers_all_five() -> None:
    summary = telescope_status_log_summary()
    by_kind = summary["counts_by_kind"]
    for kind in ALLOWED_TELESCOPE_STATUS_KINDS:
        assert kind in by_kind


def test_schema_version() -> None:
    summary = telescope_status_log_summary()
    assert summary["schema_version"] == TELESCOPE_STATUS_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = telescope_status_log_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == TELESCOPE_STATUS_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = telescope_status_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_status_kinds_has_five_members() -> None:
    assert len(ALLOWED_TELESCOPE_STATUS_KINDS) == 5


def test_allowed_statuses_has_four_members() -> None:
    assert len(ALLOWED_TELESCOPE_STATUS_STATUSES) == 4


def test_fixture_status_kinds_in_allowed() -> None:
    entries = load_telescope_status_entries()
    for e in entries:
        assert e.status_kind in ALLOWED_TELESCOPE_STATUS_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_telescope_status_entries()
    for e in entries:
        assert e.status in ALLOWED_TELESCOPE_STATUS_STATUSES


def test_telescope_id_nullable() -> None:
    entries = load_telescope_status_entries()
    tsl001 = next(e for e in entries if e.entry_id == "tsl-001")
    assert tsl001.telescope_id == "GBT"
    tsl004 = next(e for e in entries if e.entry_id == "tsl-004")
    assert tsl004.telescope_id is None


def test_affected_tracks_list() -> None:
    entries = load_telescope_status_entries()
    tsl001 = next(e for e in entries if e.entry_id == "tsl-001")
    assert "radio" in tsl001.affected_tracks
    tsl004 = next(e for e in entries if e.entry_id == "tsl-004")
    assert tsl004.affected_tracks == []


def test_as_dict_returns_required_keys() -> None:
    entries = load_telescope_status_entries()
    d = entries[0].as_dict()
    for key in ("entry_id", "run_id", "status_kind", "status",
                "recorded_by", "recorded_at",
                "telescope_id", "affected_tracks", "notes"):
        assert key in d


def test_custom_path_argument() -> None:
    entries = load_telescope_status_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = telescope_status_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_run_ids_cover_two_runs() -> None:
    entries = load_telescope_status_entries()
    run_ids = {e.run_id for e in entries}
    assert len(run_ids) == 2


def test_operational_kind_count_is_one() -> None:
    summary = telescope_status_log_summary()
    assert summary["counts_by_kind"].get("operational", 0) == 1
