"""Operational provenance records for certificate management events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CERTIFICATE_MANAGEMENT_LOG_SCHEMA_VERSION = "certificate_management_log_v1"
CERTIFICATE_MANAGEMENT_LOG_DISCLAIMER = (
    "Certificate management log entries are operational provenance records — "
    "a certificate management event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)
ALLOWED_CERTIFICATE_MANAGEMENT_KINDS = frozenset(
    {
        "ca_certificate",
        "client_certificate",
        "code_signing",
        "server_certificate",
        "tls_renewal",
    }
)
ALLOWED_CERTIFICATE_MANAGEMENT_STATUSES = frozenset(
    {
        "expired",
        "issued",
        "renewed",
        "revoked",
    }
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "certificate_management_log.json"
)


@dataclass(frozen=True)
class CertificateManagementEntry:
    entry_id: str
    certificate_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.certificate_kind not in ALLOWED_CERTIFICATE_MANAGEMENT_KINDS:
            raise ValueError(f"Invalid certificate_kind: {self.certificate_kind!r}")
        if self.status not in ALLOWED_CERTIFICATE_MANAGEMENT_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_certificate_management_entries(
    path: Path | None = None,
) -> list[CertificateManagementEntry]:
    fixture_path = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(Path(fixture_path).read_text())
    return [
        CertificateManagementEntry(
            entry_id=e["entry_id"],
            certificate_kind=e["certificate_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def certificate_management_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_certificate_management_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    issued_count = 0
    for e in entries:
        by_kind[e.certificate_kind] = by_kind.get(e.certificate_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "issued":
            issued_count += 1
    return {
        "schema_version": CERTIFICATE_MANAGEMENT_LOG_SCHEMA_VERSION,
        "disclaimer": CERTIFICATE_MANAGEMENT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "issued_count": issued_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
