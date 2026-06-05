from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.budget_log import (
    ALLOWED_BUDGET_KINDS,
    ALLOWED_BUDGET_STATUSES,
    BUDGET_LOG_SCHEMA_VERSION,
    BudgetEntry,
    budget_summary,
    load_budget_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "budget_log.json"


def test_schema_version() -> None:
    assert BUDGET_LOG_SCHEMA_VERSION == "budget_log_v1"


def test_allowed_budget_kinds() -> None:
    assert "capital_expenditure" in ALLOWED_BUDGET_KINDS
    assert "contingency" in ALLOWED_BUDGET_KINDS
    assert "operational_expenditure" in ALLOWED_BUDGET_KINDS
    assert "project_budget" in ALLOWED_BUDGET_KINDS
    assert "travel_budget" in ALLOWED_BUDGET_KINDS
    assert len(ALLOWED_BUDGET_KINDS) == 5


def test_allowed_budget_statuses() -> None:
    assert "allocated" in ALLOWED_BUDGET_STATUSES
    assert "approved" in ALLOWED_BUDGET_STATUSES
    assert "closed" in ALLOWED_BUDGET_STATUSES
    assert "overspent" in ALLOWED_BUDGET_STATUSES
    assert len(ALLOWED_BUDGET_STATUSES) == 4


def test_load_fixture_entries() -> None:
    entries = load_budget_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_approved_entries() -> None:
    entries = load_budget_entries(FIXTURE_PATH)
    approved = [e for e in entries if e.status == "approved"]
    assert len(approved) >= 2


def test_fixture_covers_all_statuses() -> None:
    entries = load_budget_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert statuses == ALLOWED_BUDGET_STATUSES


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_budget_entries(FIXTURE_PATH)
    kinds = {e.budget_kind for e in entries}
    assert len(kinds) >= 4


def test_entry_fields_populated() -> None:
    entries = load_budget_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.entry_id
        assert entry.budget_kind
        assert entry.status
        assert entry.cost_center
        assert entry.description


def test_entry_is_frozen() -> None:
    entry = BudgetEntry(
        entry_id="b-x",
        budget_kind="project_budget",
        status="approved",
        cost_center="cc-x",
        description="Test description",
    )
    with pytest.raises(AttributeError):
        entry.status = "closed"  # type: ignore[misc]


def test_invalid_budget_kind_raises() -> None:
    with pytest.raises(ValueError, match="invalid budget_kind"):
        BudgetEntry(
            entry_id="b-bad",
            budget_kind="invalid_kind",
            status="approved",
            cost_center="cc-x",
            description="Description",
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        BudgetEntry(
            entry_id="b-bad",
            budget_kind="project_budget",
            status="invalid_status",
            cost_center="cc-x",
            description="Description",
        )


def test_summary_entry_count() -> None:
    summary = budget_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_approved_count() -> None:
    summary = budget_summary(FIXTURE_PATH)
    assert summary["approved_count"] == 2


def test_summary_schema_version() -> None:
    summary = budget_summary(FIXTURE_PATH)
    assert summary["schema_version"] == BUDGET_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = budget_summary(FIXTURE_PATH)
    assert "disclaimer" in summary
    assert "detection claim" in summary["disclaimer"]


def test_summary_kind_counts() -> None:
    summary = budget_summary(FIXTURE_PATH)
    assert "kind_counts" in summary
    assert set(summary["kind_counts"].keys()) == ALLOWED_BUDGET_KINDS


def test_summary_status_counts() -> None:
    summary = budget_summary(FIXTURE_PATH)
    assert "status_counts" in summary
    assert set(summary["status_counts"].keys()) == ALLOWED_BUDGET_STATUSES


def test_fixture_json_valid() -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "entries" in raw
    assert len(raw["entries"]) == 5


def test_validate_all_budget_gate(tmp_path: Path) -> None:
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
