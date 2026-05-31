"""Operational provenance records for software license lifecycle events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LICENSE_MANAGEMENT_LOG_SCHEMA_VERSION = "license_management_log_v1"

ALLOWED_LICENSE_KINDS = frozenset(
    {
        "activation",
        "deactivation",
        "expiry_warning",
        "renewal",
        "transfer",
    }
)

ALLOWED_LICENSE_STATUSES = frozenset(
    {
        "active",
        "expired",
        "failed",
        "renewed",
    }
)

_DISCLAIMER = (
    "License management log entries are operational provenance records — "
    "a license management event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "license_management_log.json"
)


@dataclass(frozen=True)
class LicenseManagementEntry:
    entry_id: str
    license_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.license_kind not in ALLOWED_LICENSE_KINDS:
            raise ValueError(f"Invalid license_kind: {self.license_kind!r}")
        if self.status not in ALLOWED_LICENSE_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_license_management_entries(
    path: Path | None = None,
) -> list[LicenseManagementEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        LicenseManagementEntry(
            entry_id=e["entry_id"],
            license_kind=e["license_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def license_management_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_license_management_entries(path)
    active = sum(1 for e in entries if e.status == "active")
    return {
        "schema_version": LICENSE_MANAGEMENT_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "active_count": active,
        "by_kind": {
            kind: sum(1 for e in entries if e.license_kind == kind)
            for kind in sorted(ALLOWED_LICENSE_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_LICENSE_STATUSES)
        },
    }
