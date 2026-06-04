"""Operational provenance records for asset management events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ASSET_MANAGEMENT_LOG_SCHEMA_VERSION = "asset_management_log_v1"
ASSET_MANAGEMENT_LOG_DISCLAIMER = (
    "Asset management log entries are operational provenance records — "
    "an asset management event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)
ALLOWED_ASSET_MANAGEMENT_KINDS = frozenset(
    {
        "asset_acquisition",
        "asset_audit",
        "asset_decommission",
        "asset_maintenance",
        "asset_transfer",
    }
)
ALLOWED_ASSET_MANAGEMENT_STATUSES = frozenset(
    {
        "active",
        "decommissioned",
        "pending",
        "under_maintenance",
    }
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "asset_management_log.json"
)


@dataclass(frozen=True)
class AssetManagementEntry:
    entry_id: str
    asset_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.asset_kind not in ALLOWED_ASSET_MANAGEMENT_KINDS:
            raise ValueError(f"Invalid asset_kind: {self.asset_kind!r}")
        if self.status not in ALLOWED_ASSET_MANAGEMENT_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_asset_management_entries(
    path: Path | None = None,
) -> list[AssetManagementEntry]:
    fixture_path = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(Path(fixture_path).read_text())
    return [
        AssetManagementEntry(
            entry_id=e["entry_id"],
            asset_kind=e["asset_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def asset_management_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_asset_management_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    active_count = 0
    for e in entries:
        by_kind[e.asset_kind] = by_kind.get(e.asset_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "active":
            active_count += 1
    return {
        "schema_version": ASSET_MANAGEMENT_LOG_SCHEMA_VERSION,
        "disclaimer": ASSET_MANAGEMENT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "active_count": active_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
