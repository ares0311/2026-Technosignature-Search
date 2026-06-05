from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.document_management_log import (
    ALLOWED_DOCUMENT_MANAGEMENT_KINDS,
    ALLOWED_DOCUMENT_MANAGEMENT_STATUSES,
    DOCUMENT_MANAGEMENT_LOG_SCHEMA_VERSION,
    DocumentManagementEntry,
    document_management_summary,
    load_document_management_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "document_management_log.json"


def test_schema_version() -> None:
    assert DOCUMENT_MANAGEMENT_LOG_SCHEMA_VERSION == "document_management_log_v1"


def test_allowed_document_management_kinds() -> None:
    assert "approval" in ALLOWED_DOCUMENT_MANAGEMENT_KINDS
    assert "archival" in ALLOWED_DOCUMENT_MANAGEMENT_KINDS
    assert "creation" in ALLOWED_DOCUMENT_MANAGEMENT_KINDS
    assert "review" in ALLOWED_DOCUMENT_MANAGEMENT_KINDS
    assert "revision" in ALLOWED_DOCUMENT_MANAGEMENT_KINDS
    assert len(ALLOWED_DOCUMENT_MANAGEMENT_KINDS) == 5


def test_allowed_document_management_statuses() -> None:
    assert "active" in ALLOWED_DOCUMENT_MANAGEMENT_STATUSES
    assert "archived" in ALLOWED_DOCUMENT_MANAGEMENT_STATUSES
    assert "draft" in ALLOWED_DOCUMENT_MANAGEMENT_STATUSES
    assert "superseded" in ALLOWED_DOCUMENT_MANAGEMENT_STATUSES
    assert len(ALLOWED_DOCUMENT_MANAGEMENT_STATUSES) == 4


def test_load_fixture_entries() -> None:
    entries = load_document_management_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_active_entries() -> None:
    entries = load_document_management_entries(FIXTURE_PATH)
    active = [e for e in entries if e.status == "active"]
    assert len(active) >= 2


def test_fixture_covers_all_statuses() -> None:
    entries = load_document_management_entries(FIXTURE_PATH)
    statuses = {e.status for e in entries}
    assert statuses == ALLOWED_DOCUMENT_MANAGEMENT_STATUSES


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_document_management_entries(FIXTURE_PATH)
    kinds = {e.document_kind for e in entries}
    assert len(kinds) >= 4


def test_entry_fields_populated() -> None:
    entries = load_document_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.entry_id
        assert entry.document_kind
        assert entry.status
        assert entry.document_id
        assert entry.description


def test_entry_is_frozen() -> None:
    entry = DocumentManagementEntry(
        entry_id="dm-x",
        document_kind="creation",
        status="active",
        document_id="doc-x",
        description="Test description",
    )
    with pytest.raises(AttributeError):
        entry.status = "archived"  # type: ignore[misc]


def test_invalid_document_kind_raises() -> None:
    with pytest.raises(ValueError, match="invalid document_kind"):
        DocumentManagementEntry(
            entry_id="dm-bad",
            document_kind="invalid_kind",
            status="active",
            document_id="doc-x",
            description="Description",
        )


def test_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="invalid status"):
        DocumentManagementEntry(
            entry_id="dm-bad",
            document_kind="creation",
            status="invalid_status",
            document_id="doc-x",
            description="Description",
        )


def test_summary_entry_count() -> None:
    summary = document_management_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_active_count() -> None:
    summary = document_management_summary(FIXTURE_PATH)
    assert summary["active_count"] == 2


def test_summary_schema_version() -> None:
    summary = document_management_summary(FIXTURE_PATH)
    assert summary["schema_version"] == DOCUMENT_MANAGEMENT_LOG_SCHEMA_VERSION


def test_summary_has_disclaimer() -> None:
    summary = document_management_summary(FIXTURE_PATH)
    assert "disclaimer" in summary
    assert "detection claim" in summary["disclaimer"]


def test_summary_kind_counts() -> None:
    summary = document_management_summary(FIXTURE_PATH)
    assert "kind_counts" in summary
    assert set(summary["kind_counts"].keys()) == ALLOWED_DOCUMENT_MANAGEMENT_KINDS


def test_summary_status_counts() -> None:
    summary = document_management_summary(FIXTURE_PATH)
    assert "status_counts" in summary
    assert set(summary["status_counts"].keys()) == ALLOWED_DOCUMENT_MANAGEMENT_STATUSES


def test_fixture_json_valid() -> None:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "entries" in raw
    assert len(raw["entries"]) == 5


def test_validate_all_document_management_gate(tmp_path: Path) -> None:
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
