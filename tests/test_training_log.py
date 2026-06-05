from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.training_log import (
    ALLOWED_TRAINING_KINDS,
    ALLOWED_TRAINING_STATUSES,
    TRAINING_LOG_SCHEMA_VERSION,
    TrainingEntry,
    load_training_entries,
    training_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "training_log.json"


def test_schema_version() -> None:
    assert TRAINING_LOG_SCHEMA_VERSION == "training_log_v1"


def test_allowed_training_kinds() -> None:
    assert "certification" in ALLOWED_TRAINING_KINDS
    assert "compliance_training" in ALLOWED_TRAINING_KINDS
    assert "onboarding" in ALLOWED_TRAINING_KINDS
    assert "skills_development" in ALLOWED_TRAINING_KINDS
    assert "vendor_training" in ALLOWED_TRAINING_KINDS
    assert len(ALLOWED_TRAINING_KINDS) == 5


def test_allowed_training_statuses() -> None:
    assert "completed" in ALLOWED_TRAINING_STATUSES
    assert "expired" in ALLOWED_TRAINING_STATUSES
    assert "in_progress" in ALLOWED_TRAINING_STATUSES
    assert "scheduled" in ALLOWED_TRAINING_STATUSES
    assert len(ALLOWED_TRAINING_STATUSES) == 4


def test_load_fixture_entries() -> None:
    entries = load_training_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_completed_entries() -> None:
    entries = load_training_entries(FIXTURE_PATH)
    completed = [e for e in entries if e.status == "completed"]
    assert len(completed) >= 2


def test_fixture_covers_all_statuses() -> None:
    entries = load_training_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert statuses == ALLOWED_TRAINING_STATUSES


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_training_entries(FIXTURE_PATH)
    kinds = {e.training_kind for e in entries}
    assert len(kinds) >= 4


def test_entry_fields_populated() -> None:
    entries = load_training_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.entry_id
        assert entry.training_kind
        assert entry.status
        assert entry.personnel_id
        assert entry.training_topic


def test_entry_is_frozen() -> None:
    entry = TrainingEntry(
        entry_id="t-x",
        training_kind="onboarding",
        status="completed",
        personnel_id="pers-x",
        training_topic="Test topic",
    )
    with pytest.raises(AttributeError):
        entry.status = "expired"  # type: ignore[misc]


def test_invalid_training_kind_raises() -> None:
    with pytest.raises(ValueError, match="invalid training_kind"):
        TrainingEntry(
            entry_id="t-bad",
            training_kind="invalid_kind",
            status="completed",
            personnel_id="pers-x",
            training_topic="Topic",
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        TrainingEntry(
            entry_id="t-bad",
            training_kind="onboarding",
            status="invalid_status",
            personnel_id="pers-x",
            training_topic="Topic",
        )


def test_summary_entry_count() -> None:
    summary = training_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_completed_count() -> None:
    summary = training_summary(FIXTURE_PATH)
    assert summary["completed_count"] == 2


def test_summary_schema_version() -> None:
    summary = training_summary(FIXTURE_PATH)
    assert summary["schema_version"] == TRAINING_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = training_summary(FIXTURE_PATH)
    assert "disclaimer" in summary
    assert "detection claim" in summary["disclaimer"]


def test_summary_kind_counts() -> None:
    summary = training_summary(FIXTURE_PATH)
    assert "kind_counts" in summary
    assert set(summary["kind_counts"].keys()) == ALLOWED_TRAINING_KINDS


def test_summary_status_counts() -> None:
    summary = training_summary(FIXTURE_PATH)
    assert "status_counts" in summary
    assert set(summary["status_counts"].keys()) == ALLOWED_TRAINING_STATUSES


def test_fixture_json_valid() -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "entries" in raw
    assert len(raw["entries"]) == 5


def test_validate_all_training_gate(tmp_path: Path) -> None:
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
