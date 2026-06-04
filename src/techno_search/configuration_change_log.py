"""Operational provenance records for configuration change events."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIGURATION_CHANGE_LOG_SCHEMA_VERSION = "configuration_change_log_v1"

ALLOWED_CONFIGURATION_CHANGE_KINDS = frozenset(
    {
        "parameter_update",
        "profile_switch",
        "rollback",
        "template_apply",
        "version_pin",
    }
)

ALLOWED_CONFIGURATION_CHANGE_STATUSES = frozenset(
    {
        "applied",
        "failed",
        "pending",
        "reverted",
    }
)

_FIXTURE_PATH = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "configuration_change_log.json"
)


@dataclass(frozen=True)
class ConfigurationChangeEntry:
    entry_id: str
    change_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str

    def __post_init__(self) -> None:
        if self.change_kind not in ALLOWED_CONFIGURATION_CHANGE_KINDS:
            raise ValueError(f"Invalid change_kind: {self.change_kind!r}")
        if self.status not in ALLOWED_CONFIGURATION_CHANGE_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_configuration_change_entries(
    fixture_path: Path | None = None,
) -> list[ConfigurationChangeEntry]:
    import json

    path = fixture_path or _FIXTURE_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        ConfigurationChangeEntry(
            entry_id=str(entry["entry_id"]),
            change_kind=str(entry["change_kind"]),
            status=str(entry["status"]),
            actor_id=str(entry["actor_id"]),
            resource_id=str(entry["resource_id"]),
            timestamp_utc=str(entry["timestamp_utc"]),
            notes=str(entry["notes"]),
        )
        for entry in data["entries"]
    ]


def configuration_change_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_configuration_change_entries(fixture_path)
    applied_count = sum(1 for e in entries if e.status == "applied")
    return {
        "schema_version": CONFIGURATION_CHANGE_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "applied_count": applied_count,
        "disclaimer": (
            "Configuration change entries are operational provenance records — "
            "a configuration change event does not modify candidate scores or "
            "pathway routing, does not authorize external submission, and does "
            "not constitute a detection claim."
        ),
    }
