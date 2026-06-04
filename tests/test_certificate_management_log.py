from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.certificate_management_log import (
    ALLOWED_CERTIFICATE_MANAGEMENT_KINDS,
    ALLOWED_CERTIFICATE_MANAGEMENT_STATUSES,
    CERTIFICATE_MANAGEMENT_LOG_DISCLAIMER,
    CERTIFICATE_MANAGEMENT_LOG_SCHEMA_VERSION,
    CertificateManagementEntry,
    certificate_management_summary,
    load_certificate_management_entries,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "certificate_management_log.json"


def test_allowed_kinds_not_empty() -> None:
    assert len(ALLOWED_CERTIFICATE_MANAGEMENT_KINDS) > 0


def test_allowed_statuses_not_empty() -> None:
    assert len(ALLOWED_CERTIFICATE_MANAGEMENT_STATUSES) > 0


def test_expected_kinds_present() -> None:
    assert "ca_certificate" in ALLOWED_CERTIFICATE_MANAGEMENT_KINDS
    assert "client_certificate" in ALLOWED_CERTIFICATE_MANAGEMENT_KINDS
    assert "code_signing" in ALLOWED_CERTIFICATE_MANAGEMENT_KINDS
    assert "server_certificate" in ALLOWED_CERTIFICATE_MANAGEMENT_KINDS
    assert "tls_renewal" in ALLOWED_CERTIFICATE_MANAGEMENT_KINDS


def test_expected_statuses_present() -> None:
    assert "expired" in ALLOWED_CERTIFICATE_MANAGEMENT_STATUSES
    assert "issued" in ALLOWED_CERTIFICATE_MANAGEMENT_STATUSES
    assert "renewed" in ALLOWED_CERTIFICATE_MANAGEMENT_STATUSES
    assert "revoked" in ALLOWED_CERTIFICATE_MANAGEMENT_STATUSES


def test_schema_version_string() -> None:
    assert isinstance(CERTIFICATE_MANAGEMENT_LOG_SCHEMA_VERSION, str)
    assert len(CERTIFICATE_MANAGEMENT_LOG_SCHEMA_VERSION) > 0


def test_disclaimer_string() -> None:
    assert isinstance(CERTIFICATE_MANAGEMENT_LOG_DISCLAIMER, str)
    assert "does not" in CERTIFICATE_MANAGEMENT_LOG_DISCLAIMER


def test_entry_valid_construction() -> None:
    entry = CertificateManagementEntry(
        entry_id="cm-test-001",
        certificate_kind="server_certificate",
        status="issued",
        actor_id="operator-x",
        resource_id="pipeline-v1",
        timestamp_utc="2026-06-01T00:00:00Z",
        notes=None,
    )
    assert entry.entry_id == "cm-test-001"
    assert entry.certificate_kind == "server_certificate"
    assert entry.status == "issued"


def test_entry_invalid_kind_raises() -> None:
    with pytest.raises(ValueError, match="certificate_kind"):
        CertificateManagementEntry(
            entry_id="cm-bad",
            certificate_kind="unknown_kind",
            status="issued",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_entry_invalid_status_raises() -> None:
    with pytest.raises(ValueError, match="status"):
        CertificateManagementEntry(
            entry_id="cm-bad",
            certificate_kind="tls_renewal",
            status="unknown_status",
            actor_id="op",
            resource_id="res",
            timestamp_utc="2026-06-01T00:00:00Z",
            notes=None,
        )


def test_load_fixture_returns_entries() -> None:
    entries = load_certificate_management_entries(FIXTURE_PATH)
    assert len(entries) >= 1


def test_fixture_has_expected_count() -> None:
    entries = load_certificate_management_entries(FIXTURE_PATH)
    assert len(entries) == 5


def test_fixture_has_issued_entries() -> None:
    entries = load_certificate_management_entries(FIXTURE_PATH)
    issued = [e for e in entries if e.status == "issued"]
    assert len(issued) >= 1


def test_fixture_covers_multiple_kinds() -> None:
    entries = load_certificate_management_entries(FIXTURE_PATH)
    kinds = {e.certificate_kind for e in entries}
    assert len(kinds) >= 3


def test_summary_schema_version() -> None:
    summary = certificate_management_summary(FIXTURE_PATH)
    assert summary["schema_version"] == CERTIFICATE_MANAGEMENT_LOG_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    summary = certificate_management_summary(FIXTURE_PATH)
    assert "does not" in summary["disclaimer"]


def test_summary_entry_count() -> None:
    summary = certificate_management_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 5


def test_summary_issued_count() -> None:
    summary = certificate_management_summary(FIXTURE_PATH)
    assert summary["issued_count"] >= 1


def test_summary_by_kind() -> None:
    summary = certificate_management_summary(FIXTURE_PATH)
    assert isinstance(summary["by_kind"], dict)
    assert len(summary["by_kind"]) >= 1


def test_summary_by_status() -> None:
    summary = certificate_management_summary(FIXTURE_PATH)
    assert isinstance(summary["by_status"], dict)
    assert "issued" in summary["by_status"]


def test_fixture_json_parseable() -> None:
    raw = json.loads(FIXTURE_PATH.read_text())
    assert "entries" in raw
    assert raw["schema_version"] == CERTIFICATE_MANAGEMENT_LOG_SCHEMA_VERSION


def test_entry_has_resource_id() -> None:
    entries = load_certificate_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry.resource_id, str)
        assert len(entry.resource_id) > 0


def test_load_returns_certificate_management_entry_instances() -> None:
    entries = load_certificate_management_entries(FIXTURE_PATH)
    for entry in entries:
        assert isinstance(entry, CertificateManagementEntry)
