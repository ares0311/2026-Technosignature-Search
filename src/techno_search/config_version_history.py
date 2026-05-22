from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIG_VERSION_HISTORY_SCHEMA_VERSION = "config_version_history_v1"

CONFIG_VERSION_HISTORY_DISCLAIMER = (
    "Config version history entries are append-only local provenance records only. "
    "They record pipeline config changes — when a config was created, promoted, "
    "updated, or deprecated — for scheduling auditability. History entries do not "
    "re-run or re-route any candidate, authorize external submission, or constitute "
    "a detection claim."
)

ALLOWED_CHANGE_KINDS = frozenset({"created", "promoted", "updated", "deprecated"})


def _default_config_history_fixture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "config_version_history.json"
    )


@dataclass
class ConfigVersionHistoryEntry:
    history_id: str
    config_id: str
    change_kind: str
    effective_utc: str
    changed_by: str
    prior_config_id: str | None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "history_id": self.history_id,
            "config_id": self.config_id,
            "change_kind": self.change_kind,
            "effective_utc": self.effective_utc,
            "changed_by": self.changed_by,
            "prior_config_id": self.prior_config_id,
            "notes": self.notes,
        }


def load_config_history_entries(
    fixture_path: Path | str | None = None,
) -> list[ConfigVersionHistoryEntry]:
    path = (
        Path(fixture_path)
        if fixture_path is not None
        else _default_config_history_fixture_path()
    )
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = []
    for entry in data.get("config_version_history_entries", []):
        entries.append(
            ConfigVersionHistoryEntry(
                history_id=entry["history_id"],
                config_id=entry["config_id"],
                change_kind=entry["change_kind"],
                effective_utc=entry["effective_utc"],
                changed_by=entry["changed_by"],
                prior_config_id=entry.get("prior_config_id"),
                notes=entry.get("notes", ""),
            )
        )
    return entries


def config_version_history_summary(
    fixture_path: Path | str | None = None,
) -> dict[str, Any]:
    entries = load_config_history_entries(fixture_path)
    by_kind: dict[str, int] = {}
    by_config: dict[str, int] = {}
    deprecated_count = 0
    promoted_count = 0
    for e in entries:
        by_kind[e.change_kind] = by_kind.get(e.change_kind, 0) + 1
        by_config[e.config_id] = by_config.get(e.config_id, 0) + 1
        if e.change_kind == "deprecated":
            deprecated_count += 1
        elif e.change_kind == "promoted":
            promoted_count += 1
    configs_tracked = sorted(by_config.keys())
    return {
        "disclaimer": CONFIG_VERSION_HISTORY_DISCLAIMER,
        "schema_version": CONFIG_VERSION_HISTORY_SCHEMA_VERSION,
        "entry_count": len(entries),
        "deprecated_count": deprecated_count,
        "promoted_count": promoted_count,
        "by_kind": by_kind,
        "by_config": by_config,
        "configs_tracked": configs_tracked,
    }
