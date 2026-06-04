"""Operational provenance records for patch management events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PATCH_MANAGEMENT_LOG_SCHEMA_VERSION = "patch_management_log_v1"
PATCH_MANAGEMENT_LOG_DISCLAIMER = (
    "Patch management log entries are operational provenance records — "
    "a patch management event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)
ALLOWED_PATCH_MANAGEMENT_KINDS = frozenset(
    {
        "critical_patch",
        "feature_update",
        "hotfix",
        "rollback",
        "security_patch",
    }
)
ALLOWED_PATCH_MANAGEMENT_STATUSES = frozenset(
    {
        "applied",
        "failed",
        "pending",
        "skipped",
    }
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent / "tests" / "fixtures" / "patch_management_log.json"
)


@dataclass(frozen=True)
class PatchManagementEntry:
    entry_id: str
    patch_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.patch_kind not in ALLOWED_PATCH_MANAGEMENT_KINDS:
            raise ValueError(f"Invalid patch_kind: {self.patch_kind!r}")
        if self.status not in ALLOWED_PATCH_MANAGEMENT_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_patch_management_entries(path: Path | None = None) -> list[PatchManagementEntry]:
    fixture_path = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(Path(fixture_path).read_text())
    return [
        PatchManagementEntry(
            entry_id=e["entry_id"],
            patch_kind=e["patch_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def patch_management_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_patch_management_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    applied_count = 0
    for e in entries:
        by_kind[e.patch_kind] = by_kind.get(e.patch_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
        if e.status == "applied":
            applied_count += 1
    return {
        "schema_version": PATCH_MANAGEMENT_LOG_SCHEMA_VERSION,
        "disclaimer": PATCH_MANAGEMENT_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "applied_count": applied_count,
        "by_kind": by_kind,
        "by_status": by_status,
    }
