"""Operational provenance records for facility software deployment events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SOFTWARE_DEPLOYMENT_LOG_SCHEMA_VERSION = "software_deployment_log_v1"

ALLOWED_DEPLOYMENT_KINDS = frozenset(
    {
        "hotfix",
        "major_release",
        "minor_release",
        "patch",
        "rollback",
    }
)

ALLOWED_DEPLOYMENT_STATUSES = frozenset(
    {
        "completed",
        "failed",
        "in_progress",
        "rolled_back",
    }
)

_DISCLAIMER = (
    "Software deployment log entries are operational provenance records — "
    "a software deployment event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "software_deployment_log.json"
)


@dataclass(frozen=True)
class SoftwareDeploymentEntry:
    entry_id: str
    deployment_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.deployment_kind not in ALLOWED_DEPLOYMENT_KINDS:
            raise ValueError(f"Invalid deployment_kind: {self.deployment_kind!r}")
        if self.status not in ALLOWED_DEPLOYMENT_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_software_deployment_entries(
    path: Path | None = None,
) -> list[SoftwareDeploymentEntry]:
    if path is None:
        path = _DEFAULT_FIXTURE
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return [
        SoftwareDeploymentEntry(
            entry_id=e["entry_id"],
            deployment_kind=e["deployment_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def software_deployment_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_software_deployment_entries(path)
    completed = sum(1 for e in entries if e.status == "completed")
    return {
        "schema_version": SOFTWARE_DEPLOYMENT_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "completed_count": completed,
        "by_kind": {
            kind: sum(1 for e in entries if e.deployment_kind == kind)
            for kind in sorted(ALLOWED_DEPLOYMENT_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_DEPLOYMENT_STATUSES)
        },
    }
