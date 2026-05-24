"""Tests for spectral_feature_log module."""
from __future__ import annotations

from pathlib import Path

from techno_search.spectral_feature_log import (
    ALLOWED_FEATURE_KINDS,
    ALLOWED_FEATURE_STATUSES,
    SPECTRAL_FEATURE_LOG_DISCLAIMER,
    SPECTRAL_FEATURE_LOG_SCHEMA_VERSION,
    load_spectral_feature_entries,
    spectral_feature_log_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "spectral_feature_log.json"


def test_load_entries_returns_five() -> None:
    entries = load_spectral_feature_entries()
    assert len(entries) == 5


def test_all_feature_kinds_present() -> None:
    entries = load_spectral_feature_entries()
    kinds = {e.feature_kind for e in entries}
    assert "emission_line" in kinds
    assert "spectral_index" in kinds
    assert "continuum_fit" in kinds
    assert "absorption_line" in kinds
    assert "line_complex" in kinds


def test_all_statuses_present() -> None:
    entries = load_spectral_feature_entries()
    statuses = {e.status for e in entries}
    assert "detected" in statuses
    assert "tentative" in statuses
    assert "not_detected" in statuses
    assert "artifact" in statuses


def test_summary_entry_count_five() -> None:
    summary = spectral_feature_log_summary()
    assert summary["entry_count"] == 5


def test_detected_count_is_two() -> None:
    summary = spectral_feature_log_summary()
    assert summary["detected_count"] == 2


def test_artifact_count_is_one() -> None:
    summary = spectral_feature_log_summary()
    assert summary["artifact_count"] == 1


def test_counts_by_status_covers_all_four() -> None:
    summary = spectral_feature_log_summary()
    by_status = summary["counts_by_status"]
    assert set(by_status.keys()) == {"detected", "tentative", "not_detected", "artifact"}


def test_counts_by_kind_covers_all_five() -> None:
    summary = spectral_feature_log_summary()
    by_kind = summary["counts_by_kind"]
    for kind in ALLOWED_FEATURE_KINDS:
        assert kind in by_kind


def test_schema_version() -> None:
    summary = spectral_feature_log_summary()
    assert summary["schema_version"] == SPECTRAL_FEATURE_LOG_SCHEMA_VERSION


def test_disclaimer_present_and_provenance() -> None:
    summary = spectral_feature_log_summary()
    assert "provenance records" in summary["disclaimer"]
    assert summary["disclaimer"] == SPECTRAL_FEATURE_LOG_DISCLAIMER


def test_disclaimer_no_detection_language() -> None:
    summary = spectral_feature_log_summary()
    assert "detection claim" in summary["disclaimer"]
    assert "discovery" not in summary["disclaimer"].lower()


def test_allowed_feature_kinds_has_five_members() -> None:
    assert len(ALLOWED_FEATURE_KINDS) == 5


def test_allowed_feature_statuses_has_four_members() -> None:
    assert len(ALLOWED_FEATURE_STATUSES) == 4


def test_fixture_feature_kinds_in_allowed() -> None:
    entries = load_spectral_feature_entries()
    for e in entries:
        assert e.feature_kind in ALLOWED_FEATURE_KINDS


def test_fixture_status_values_in_allowed() -> None:
    entries = load_spectral_feature_entries()
    for e in entries:
        assert e.status in ALLOWED_FEATURE_STATUSES


def test_frequency_mhz_nullable() -> None:
    entries = load_spectral_feature_entries()
    sfl001 = next(e for e in entries if e.entry_id == "sfl-001")
    assert sfl001.frequency_mhz == 1420.4
    sfl004 = next(e for e in entries if e.entry_id == "sfl-004")
    assert sfl004.frequency_mhz is None


def test_significance_nullable() -> None:
    entries = load_spectral_feature_entries()
    sfl001 = next(e for e in entries if e.entry_id == "sfl-001")
    assert sfl001.significance == 5.2
    sfl004 = next(e for e in entries if e.entry_id == "sfl-004")
    assert sfl004.significance is None


def test_as_dict_returns_required_keys() -> None:
    entries = load_spectral_feature_entries()
    d = entries[0].as_dict()
    for key in ("entry_id", "candidate_id", "feature_kind", "status",
                "detected_by", "detected_at", "track",
                "frequency_mhz", "significance", "notes"):
        assert key in d


def test_custom_path_argument() -> None:
    entries = load_spectral_feature_entries(FIXTURE_PATH)
    assert len(entries) == 5
    summary = spectral_feature_log_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_tracks_cover_radio_infrared_anomaly() -> None:
    entries = load_spectral_feature_entries()
    tracks = {e.track for e in entries}
    assert "radio" in tracks
    assert "infrared" in tracks
    assert "anomaly" in tracks


def test_emission_line_count_is_one() -> None:
    summary = spectral_feature_log_summary()
    assert summary["counts_by_kind"].get("emission_line", 0) == 1
