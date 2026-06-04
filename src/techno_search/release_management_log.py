from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RELEASE_MANAGEMENT_LOG_SCHEMA_VERSION = "release_management_log_v1"

ALLOWED_RELEASE_MANAGEMENT_KINDS = frozenset({
    "hotfix",
    "major_release",
    "minor_release",
    "patch_release",
    "rollback",
})

ALLOWED_RELEASE_MANAGEMENT_STATUSES = frozenset({
    "approved",
    "deployed",
    "planned",
    "rolled_back",
})

_DISCLAIMER = (
    "Release management entries are operational provenance records — a release"
    " management event does not modify candidate scores or pathway routing, does not"
    " authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "release_management_log.json"
)


@dataclass(frozen=True)
class ReleaseManagementEntry:
    entry_id: str
    release_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str

    def __post_init__(self) -> None:
        if self.release_kind not in ALLOWED_RELEASE_MANAGEMENT_KINDS:
            raise ValueError(
                f"release_kind {self.release_kind!r} not in"
                f" {sorted(ALLOWED_RELEASE_MANAGEMENT_KINDS)}"
            )
        if self.status not in ALLOWED_RELEASE_MANAGEMENT_STATUSES:
            raise ValueError(
                f"status {self.status!r} not in"
                f" {sorted(ALLOWED_RELEASE_MANAGEMENT_STATUSES)}"
            )


def load_release_management_entries(
    fixture_path: Path | None = None,
) -> list[ReleaseManagementEntry]:
    path = fixture_path or _DEFAULT_FIXTURE
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        ReleaseManagementEntry(
            entry_id=e["entry_id"],
            release_kind=e["release_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes", ""),
        )
        for e in data["entries"]
    ]


def release_management_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_release_management_entries(fixture_path)
    deployed_count = sum(1 for e in entries if e.status == "deployed")
    return {
        "schema_version": RELEASE_MANAGEMENT_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "deployed_count": deployed_count,
        "disclaimer": _DISCLAIMER,
    }
