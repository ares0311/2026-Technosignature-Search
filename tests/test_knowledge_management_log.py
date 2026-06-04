from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.knowledge_management_log import (
    ALLOWED_KNOWLEDGE_MANAGEMENT_KINDS,
    ALLOWED_KNOWLEDGE_MANAGEMENT_STATUSES,
    KNOWLEDGE_MANAGEMENT_LOG_SCHEMA_VERSION,
    KnowledgeManagementEntry,
    knowledge_management_summary,
    load_knowledge_management_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "knowledge_management_log.json"


def test_fixture_loads() -> None:
    entries = load_knowledge_management_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_schema_version() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == KNOWLEDGE_MANAGEMENT_LOG_SCHEMA_VERSION


def test_entry_ids_unique() -> None:
    entries = load_knowledge_management_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_all_knowledge_kinds_valid() -> None:
    entries = load_knowledge_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.knowledge_kind in ALLOWED_KNOWLEDGE_MANAGEMENT_KINDS


def test_all_statuses_valid() -> None:
    entries = load_knowledge_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.status in ALLOWED_KNOWLEDGE_MANAGEMENT_STATUSES


def test_published_count() -> None:
    entries = load_knowledge_management_entries(FIXTURE_PATH)
    assert len([e for e in entries if e.status == "published"]) == 2


def test_approved_present() -> None:
    entries = load_knowledge_management_entries(FIXTURE_PATH)
    assert any(e.status == "approved" for e in entries)


def test_draft_present() -> None:
    entries = load_knowledge_management_entries(FIXTURE_PATH)
    assert any(e.status == "draft" for e in entries)


def test_retired_present() -> None:
    entries = load_knowledge_management_entries(FIXTURE_PATH)
    assert any(e.status == "retired" for e in entries)


def test_how_to_kind_present() -> None:
    entries = load_knowledge_management_entries(FIXTURE_PATH)
    assert any(e.knowledge_kind == "how_to" for e in entries)


def test_known_error_kind_present() -> None:
    entries = load_knowledge_management_entries(FIXTURE_PATH)
    assert any(e.knowledge_kind == "known_error" for e in entries)


def test_summary_entry_count() -> None:
    summary = knowledge_management_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_published_count() -> None:
    summary = knowledge_management_summary(FIXTURE_PATH)
    assert summary["published_count"] == 2


def test_summary_schema_version() -> None:
    summary = knowledge_management_summary(FIXTURE_PATH)
    assert summary["schema_version"] == KNOWLEDGE_MANAGEMENT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = knowledge_management_summary(FIXTURE_PATH)
    assert "operational provenance records" in summary["disclaimer"]


def test_summary_disclaimer_no_detection_claim() -> None:
    summary = knowledge_management_summary(FIXTURE_PATH)
    assert "detection claim" in summary["disclaimer"]


def test_dataclass_invalid_knowledge_kind() -> None:
    with pytest.raises(ValueError, match="knowledge_kind"):
        KnowledgeManagementEntry(
            entry_id="x", knowledge_kind="invalid_kind", status="published",
            actor_id="op", resource_id="res", timestamp_utc="2026-01-01T00:00:00Z", notes="",
        )


def test_dataclass_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        KnowledgeManagementEntry(
            entry_id="x", knowledge_kind="how_to", status="invalid_status",
            actor_id="op", resource_id="res", timestamp_utc="2026-01-01T00:00:00Z", notes="",
        )


def test_dataclass_frozen() -> None:
    entry = KnowledgeManagementEntry(
        entry_id="x", knowledge_kind="faq", status="draft",
        actor_id="op", resource_id="res", timestamp_utc="2026-01-01T00:00:00Z", notes="",
    )
    with pytest.raises(AttributeError):
        entry.status = "published"  # type: ignore[misc]


def test_allowed_kinds_completeness() -> None:
    assert "faq" in ALLOWED_KNOWLEDGE_MANAGEMENT_KINDS
    assert "how_to" in ALLOWED_KNOWLEDGE_MANAGEMENT_KINDS
    assert "known_error" in ALLOWED_KNOWLEDGE_MANAGEMENT_KINDS
    assert "reference_document" in ALLOWED_KNOWLEDGE_MANAGEMENT_KINDS
    assert "troubleshooting_guide" in ALLOWED_KNOWLEDGE_MANAGEMENT_KINDS


def test_allowed_statuses_completeness() -> None:
    assert "approved" in ALLOWED_KNOWLEDGE_MANAGEMENT_STATUSES
    assert "draft" in ALLOWED_KNOWLEDGE_MANAGEMENT_STATUSES
    assert "published" in ALLOWED_KNOWLEDGE_MANAGEMENT_STATUSES
    assert "retired" in ALLOWED_KNOWLEDGE_MANAGEMENT_STATUSES


def test_no_external_submission_in_disclaimer() -> None:
    summary = knowledge_management_summary(FIXTURE_PATH)
    assert "external submission" in summary["disclaimer"]
