from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.project_milestone_log import (
    ALLOWED_PROJECT_MILESTONE_KINDS,
    ALLOWED_PROJECT_MILESTONE_STATUSES,
    PROJECT_MILESTONE_LOG_SCHEMA_VERSION,
    ProjectMilestoneEntry,
    load_project_milestone_entries,
    project_milestone_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "project_milestone_log.json"


def test_schema_version() -> None:
    assert PROJECT_MILESTONE_LOG_SCHEMA_VERSION == "project_milestone_log_v1"


def test_allowed_project_milestone_kinds() -> None:
    assert "checkpoint" in ALLOWED_PROJECT_MILESTONE_KINDS
    assert "deliverable" in ALLOWED_PROJECT_MILESTONE_KINDS
    assert "go_live" in ALLOWED_PROJECT_MILESTONE_KINDS
    assert "phase_completion" in ALLOWED_PROJECT_MILESTONE_KINDS
    assert "review_gate" in ALLOWED_PROJECT_MILESTONE_KINDS
    assert len(ALLOWED_PROJECT_MILESTONE_KINDS) == 5


def test_allowed_project_milestone_statuses() -> None:
    assert "achieved" in ALLOWED_PROJECT_MILESTONE_STATUSES
    assert "at_risk" in ALLOWED_PROJECT_MILESTONE_STATUSES
    assert "deferred" in ALLOWED_PROJECT_MILESTONE_STATUSES
    assert "missed" in ALLOWED_PROJECT_MILESTONE_STATUSES
    assert len(ALLOWED_PROJECT_MILESTONE_STATUSES) == 4


def test_load_fixture_entries() -> None:
    entries = load_project_milestone_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_achieved_entries() -> None:
    entries = load_project_milestone_entries(FIXTURE_PATH)
    achieved = [e for e in entries if e.status == "achieved"]
    assert len(achieved) >= 2


def test_fixture_covers_all_statuses() -> None:
    entries = load_project_milestone_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert statuses == ALLOWED_PROJECT_MILESTONE_STATUSES


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_project_milestone_entries(FIXTURE_PATH)
    kinds = {e.milestone_kind for e in entries}
    assert len(kinds) >= 4


def test_entry_fields_populated() -> None:
    entries = load_project_milestone_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.entry_id
        assert entry.milestone_kind
        assert entry.status
        assert entry.project_id
        assert entry.description


def test_entry_is_frozen() -> None:
    entry = ProjectMilestoneEntry(
        entry_id="pm-x",
        milestone_kind="checkpoint",
        status="achieved",
        project_id="proj-x",
        description="Test description",
    )
    with pytest.raises(AttributeError):
        entry.status = "missed"  # type: ignore[misc]


def test_invalid_milestone_kind_raises() -> None:
    with pytest.raises(ValueError, match="invalid milestone_kind"):
        ProjectMilestoneEntry(
            entry_id="pm-bad",
            milestone_kind="invalid_kind",
            status="achieved",
            project_id="proj-x",
            description="Description",
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        ProjectMilestoneEntry(
            entry_id="pm-bad",
            milestone_kind="checkpoint",
            status="invalid_status",
            project_id="proj-x",
            description="Description",
        )


def test_summary_entry_count() -> None:
    summary = project_milestone_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_achieved_count() -> None:
    summary = project_milestone_summary(FIXTURE_PATH)
    assert summary["achieved_count"] == 2


def test_summary_schema_version() -> None:
    summary = project_milestone_summary(FIXTURE_PATH)
    assert summary["schema_version"] == PROJECT_MILESTONE_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = project_milestone_summary(FIXTURE_PATH)
    assert "disclaimer" in summary
    assert "detection claim" in summary["disclaimer"]


def test_summary_kind_counts() -> None:
    summary = project_milestone_summary(FIXTURE_PATH)
    assert "kind_counts" in summary
    assert set(summary["kind_counts"].keys()) == ALLOWED_PROJECT_MILESTONE_KINDS


def test_summary_status_counts() -> None:
    summary = project_milestone_summary(FIXTURE_PATH)
    assert "status_counts" in summary
    assert set(summary["status_counts"].keys()) == ALLOWED_PROJECT_MILESTONE_STATUSES


def test_fixture_json_valid() -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "entries" in raw
    assert len(raw["entries"]) == 5


def test_validate_all_project_milestone_gate(tmp_path: Path) -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "validate-all"],
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert result.returncode == 0
