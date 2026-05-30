"""Tests for risk_assessment_log operational provenance records."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.risk_assessment_log import (
    ALLOWED_RISK_KINDS,
    ALLOWED_RISK_STATUSES,
    RISK_ASSESSMENT_LOG_SCHEMA_VERSION,
    RiskAssessmentEntry,
    load_risk_assessment_entries,
    risk_assessment_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "risk_assessment_log.json"


def test_fixture_file_exists() -> None:
    assert FIXTURE_PATH.exists()


def test_fixture_loads_as_json() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert isinstance(obj, dict)
    assert "entries" in obj
    assert len(obj["entries"]) == 5


def test_fixture_top_level_schema_version() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    assert obj["schema_version"] == RISK_ASSESSMENT_LOG_SCHEMA_VERSION


def test_fixture_risk_kinds_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["risk_kind"] in ALLOWED_RISK_KINDS


def test_fixture_statuses_valid() -> None:
    obj = json.loads(FIXTURE_PATH.read_text())
    for row in obj["entries"]:
        assert row["status"] in ALLOWED_RISK_STATUSES


def test_load_entries_returns_list() -> None:
    entries = load_risk_assessment_entries(FIXTURE_PATH)
    assert isinstance(entries, list)
    assert len(entries) == 5


def test_load_entries_are_dataclasses() -> None:
    entries = load_risk_assessment_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, RiskAssessmentEntry)


def test_entry_ids_unique() -> None:
    entries = load_risk_assessment_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_identified_entries_present() -> None:
    entries = load_risk_assessment_entries(FIXTURE_PATH)
    assert any(e.status == "identified" for e in entries)


def test_assessed_entries_present() -> None:
    entries = load_risk_assessment_entries(FIXTURE_PATH)
    assert any(e.status == "assessed" for e in entries)


def test_mitigated_entries_present() -> None:
    entries = load_risk_assessment_entries(FIXTURE_PATH)
    assert any(e.status == "mitigated" for e in entries)


def test_accepted_entries_present() -> None:
    entries = load_risk_assessment_entries(FIXTURE_PATH)
    assert any(e.status == "accepted" for e in entries)


def test_summary_entry_count() -> None:
    summary = risk_assessment_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_mitigated_count() -> None:
    summary = risk_assessment_summary(FIXTURE_PATH)
    assert summary["mitigated_count"] >= 1


def test_summary_has_disclaimer() -> None:
    summary = risk_assessment_summary(FIXTURE_PATH)
    assert "does not constitute a detection claim" in summary["disclaimer"]


def test_summary_by_kind_keys() -> None:
    summary = risk_assessment_summary(FIXTURE_PATH)
    assert set(summary["by_kind"].keys()) == ALLOWED_RISK_KINDS


def test_summary_by_status_keys() -> None:
    summary = risk_assessment_summary(FIXTURE_PATH)
    assert set(summary["by_status"].keys()) == ALLOWED_RISK_STATUSES


def test_summary_by_kind_total_matches_entry_count() -> None:
    summary = risk_assessment_summary(FIXTURE_PATH)
    assert sum(summary["by_kind"].values()) == summary["entry_count"]


def test_summary_by_status_total_matches_entry_count() -> None:
    summary = risk_assessment_summary(FIXTURE_PATH)
    assert sum(summary["by_status"].values()) == summary["entry_count"]


def test_invalid_risk_kind_raises() -> None:
    with pytest.raises(ValueError, match="risk_kind"):
        RiskAssessmentEntry(
            entry_id="x",
            risk_kind="invalid_kind",
            status="identified",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        RiskAssessmentEntry(
            entry_id="x",
            risk_kind="cyber_risk",
            status="invalid_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-01-01T00:00:00Z",
            notes=None,
        )
