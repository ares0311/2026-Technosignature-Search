"""Operational provenance records for identity management events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

IDENTITY_MANAGEMENT_LOG_SCHEMA_VERSION = "identity_management_log_v1"
IDENTITY_MANAGEMENT_LOG_DISCLAIMER = (
    "Identity management log entries are operational provenance records — "
    "an identity management event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)
ALLOWED_IDENTITY_MANAGEMENT_KINDS = frozenset(
    {
        "account_creation",
        "account_deletion",
        "password_reset",
        "privilege_change",
        "role_assignment",
    }
)
ALLOWED_IDENTITY_MANAGEMENT_STATUSES = frozenset(
    {
        "active",
        "expired",
        "pending",
        "revoked",
    }
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "identity_management_log.json"
)


@dataclass(frozen=True)
class IdentityManagementEntry:
    entry_id: str
    identity_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.identity_kind not in ALLOWED_IDENTITY_MANAGEMENT_KINDS:
            raise ValueError(f"Invalid identity_kind: {self.identity_kind!r}")
        if self.status not in ALLOWED_IDENTITY_MANAGEMENT_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_identity_management_entries(
    path: Path | None = None,
) -> list[IdentityManagementEntry]:
    fixture_path = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(Path(fixture_path).read_text())
    return [
        IdentityManagementEntry(
            entry_id=e["entry_id"],
            identity_kind=e["identity_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def identity_management_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_identity_management_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    active_count = 0
    for e in entries:
        by_kind[e.identity_kind] = by_kind.get(e.identity_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "active":
            active_count += 1
    return {
        "schema_version": IDENTITY_MANAGEMENT_LOG_SCHEMA_VERSION,
        "disclaimer": IDENTITY_MANAGEMENT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "active_count": active_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
