from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.supplier_management_log import (
    ALLOWED_SUPPLIER_MANAGEMENT_KINDS,
    ALLOWED_SUPPLIER_MANAGEMENT_STATUSES,
    SUPPLIER_MANAGEMENT_LOG_SCHEMA_VERSION,
    SupplierManagementEntry,
    load_supplier_management_entries,
    supplier_management_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "supplier_management_log.json"


def test_fixture_loads() -> None:
    entries = load_supplier_management_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_schema_version() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == SUPPLIER_MANAGEMENT_LOG_SCHEMA_VERSION


def test_entry_ids_unique() -> None:
    entries = load_supplier_management_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_all_supplier_kinds_valid() -> None:
    entries = load_supplier_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.supplier_kind in ALLOWED_SUPPLIER_MANAGEMENT_KINDS


def test_all_statuses_valid() -> None:
    entries = load_supplier_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.status in ALLOWED_SUPPLIER_MANAGEMENT_STATUSES


def test_active_count() -> None:
    entries = load_supplier_management_entries(FIXTURE_PATH)
    assert len([e for e in entries if e.status == "active"]) == 2


def test_inactive_present() -> None:
    entries = load_supplier_management_entries(FIXTURE_PATH)
    assert any(e.status == "inactive" for e in entries)


def test_on_probation_present() -> None:
    entries = load_supplier_management_entries(FIXTURE_PATH)
    assert any(e.status == "on_probation" for e in entries)


def test_terminated_present() -> None:
    entries = load_supplier_management_entries(FIXTURE_PATH)
    assert any(e.status == "terminated" for e in entries)


def test_hardware_vendor_kind_present() -> None:
    entries = load_supplier_management_entries(FIXTURE_PATH)
    assert any(e.supplier_kind == "hardware_vendor" for e in entries)


def test_consultant_kind_present() -> None:
    entries = load_supplier_management_entries(FIXTURE_PATH)
    assert any(e.supplier_kind == "consultant" for e in entries)


def test_summary_entry_count() -> None:
    summary = supplier_management_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_active_count() -> None:
    summary = supplier_management_summary(FIXTURE_PATH)
    assert summary["active_count"] == 2


def test_summary_schema_version() -> None:
    summary = supplier_management_summary(FIXTURE_PATH)
    assert summary["schema_version"] == SUPPLIER_MANAGEMENT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = supplier_management_summary(FIXTURE_PATH)
    assert "operational provenance records" in summary["disclaimer"]


def test_summary_disclaimer_no_detection_claim() -> None:
    summary = supplier_management_summary(FIXTURE_PATH)
    assert "detection claim" in summary["disclaimer"]


def test_dataclass_invalid_supplier_kind() -> None:
    with pytest.raises(ValueError, match="supplier_kind"):
        SupplierManagementEntry(
            entry_id="x", supplier_kind="invalid_kind", status="active",
            actor_id="op", resource_id="res", timestamp_utc="2026-01-01T00:00:00Z", notes="",
        )


def test_dataclass_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        SupplierManagementEntry(
            entry_id="x", supplier_kind="contractor", status="invalid_status",
            actor_id="op", resource_id="res", timestamp_utc="2026-01-01T00:00:00Z", notes="",
        )


def test_dataclass_frozen() -> None:
    entry = SupplierManagementEntry(
        entry_id="x", supplier_kind="software_vendor", status="active",
        actor_id="op", resource_id="res", timestamp_utc="2026-01-01T00:00:00Z", notes="",
    )
    with pytest.raises(AttributeError):
        entry.status = "inactive"  # type: ignore[misc]


def test_allowed_kinds_completeness() -> None:
    assert "contractor" in ALLOWED_SUPPLIER_MANAGEMENT_KINDS
    assert "consultant" in ALLOWED_SUPPLIER_MANAGEMENT_KINDS
    assert "hardware_vendor" in ALLOWED_SUPPLIER_MANAGEMENT_KINDS
    assert "service_provider" in ALLOWED_SUPPLIER_MANAGEMENT_KINDS
    assert "software_vendor" in ALLOWED_SUPPLIER_MANAGEMENT_KINDS


def test_allowed_statuses_completeness() -> None:
    assert "active" in ALLOWED_SUPPLIER_MANAGEMENT_STATUSES
    assert "inactive" in ALLOWED_SUPPLIER_MANAGEMENT_STATUSES
    assert "on_probation" in ALLOWED_SUPPLIER_MANAGEMENT_STATUSES
    assert "terminated" in ALLOWED_SUPPLIER_MANAGEMENT_STATUSES


def test_no_external_submission_in_disclaimer() -> None:
    summary = supplier_management_summary(FIXTURE_PATH)
    assert "external submission" in summary["disclaimer"]
