from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.contract_management_log import (
    ALLOWED_CONTRACT_MANAGEMENT_KINDS,
    ALLOWED_CONTRACT_MANAGEMENT_STATUSES,
    CONTRACT_MANAGEMENT_LOG_SCHEMA_VERSION,
    ContractManagementEntry,
    contract_management_summary,
    load_contract_management_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "contract_management_log.json"


def test_fixture_loads() -> None:
    entries = load_contract_management_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_schema_version() -> None:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert data["schema_version"] == CONTRACT_MANAGEMENT_LOG_SCHEMA_VERSION


def test_entry_ids_unique() -> None:
    entries = load_contract_management_entries(FIXTURE_PATH)
    ids = [e.entry_id for e in entries]
    assert len(ids) == len(set(ids))


def test_all_contract_kinds_valid() -> None:
    entries = load_contract_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.contract_kind in ALLOWED_CONTRACT_MANAGEMENT_KINDS


def test_all_statuses_valid() -> None:
    entries = load_contract_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert entry.status in ALLOWED_CONTRACT_MANAGEMENT_STATUSES


def test_active_count() -> None:
    entries = load_contract_management_entries(FIXTURE_PATH)
    assert len([e for e in entries if e.status == "active"]) == 2


def test_pending_renewal_present() -> None:
    entries = load_contract_management_entries(FIXTURE_PATH)
    assert any(e.status == "pending_renewal" for e in entries)


def test_expired_present() -> None:
    entries = load_contract_management_entries(FIXTURE_PATH)
    assert any(e.status == "expired" for e in entries)


def test_terminated_present() -> None:
    entries = load_contract_management_entries(FIXTURE_PATH)
    assert any(e.status == "terminated" for e in entries)


def test_software_license_kind_present() -> None:
    entries = load_contract_management_entries(FIXTURE_PATH)
    assert any(e.contract_kind == "software_license" for e in entries)


def test_service_contract_kind_present() -> None:
    entries = load_contract_management_entries(FIXTURE_PATH)
    assert any(e.contract_kind == "service_contract" for e in entries)


def test_summary_entry_count() -> None:
    summary = contract_management_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_active_count() -> None:
    summary = contract_management_summary(FIXTURE_PATH)
    assert summary["active_count"] == 2


def test_summary_schema_version() -> None:
    summary = contract_management_summary(FIXTURE_PATH)
    assert summary["schema_version"] == CONTRACT_MANAGEMENT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = contract_management_summary(FIXTURE_PATH)
    assert "operational provenance records" in summary["disclaimer"]


def test_summary_disclaimer_no_detection_claim() -> None:
    summary = contract_management_summary(FIXTURE_PATH)
    assert "detection claim" in summary["disclaimer"]


def test_dataclass_invalid_contract_kind() -> None:
    with pytest.raises(ValueError, match="contract_kind"):
        ContractManagementEntry(
            entry_id="x", contract_kind="invalid_kind", status="active",
            actor_id="op", resource_id="res", timestamp_utc="2026-01-01T00:00:00Z", notes="",
        )


def test_dataclass_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        ContractManagementEntry(
            entry_id="x", contract_kind="software_license", status="invalid_status",
            actor_id="op", resource_id="res", timestamp_utc="2026-01-01T00:00:00Z", notes="",
        )


def test_dataclass_frozen() -> None:
    entry = ContractManagementEntry(
        entry_id="x", contract_kind="support_agreement", status="active",
        actor_id="op", resource_id="res", timestamp_utc="2026-01-01T00:00:00Z", notes="",
    )
    with pytest.raises(AttributeError):
        entry.status = "expired"  # type: ignore[misc]


def test_allowed_kinds_completeness() -> None:
    assert "hardware_contract" in ALLOWED_CONTRACT_MANAGEMENT_KINDS
    assert "service_contract" in ALLOWED_CONTRACT_MANAGEMENT_KINDS
    assert "software_license" in ALLOWED_CONTRACT_MANAGEMENT_KINDS
    assert "support_agreement" in ALLOWED_CONTRACT_MANAGEMENT_KINDS
    assert "vendor_agreement" in ALLOWED_CONTRACT_MANAGEMENT_KINDS


def test_allowed_statuses_completeness() -> None:
    assert "active" in ALLOWED_CONTRACT_MANAGEMENT_STATUSES
    assert "expired" in ALLOWED_CONTRACT_MANAGEMENT_STATUSES
    assert "pending_renewal" in ALLOWED_CONTRACT_MANAGEMENT_STATUSES
    assert "terminated" in ALLOWED_CONTRACT_MANAGEMENT_STATUSES


def test_no_external_submission_in_disclaimer() -> None:
    summary = contract_management_summary(FIXTURE_PATH)
    assert "external submission" in summary["disclaimer"]
