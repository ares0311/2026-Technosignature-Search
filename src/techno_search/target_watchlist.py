"""Operator target watchlist for scheduling aid."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TARGET_WATCHLIST_SCHEMA_VERSION = "target_watchlist_v1"

TARGET_WATCHLIST_DISCLAIMER = (
    "This target watchlist is a scheduling aid only. "
    "Watchlist entries do not modify candidate posteriors, false-positive probability, "
    "or pathway routing. No entry constitutes a technosignature claim or detection."
)

ALLOWED_WATCHLIST_KINDS = frozenset({"elevated", "deprioritized", "blocked", "completed"})


def _default_watchlist_fixture_path() -> Path:
    return (
        Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "target_watchlist.json"
    )


@dataclass
class WatchlistEntry:
    target_id: str
    watchlist_kind: str
    added_at_utc: str
    operator_notes: str = ""
    priority_override_score: float | None = None
    blocking_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "watchlist_kind": self.watchlist_kind,
            "operator_notes": self.operator_notes,
            "priority_override_score": self.priority_override_score,
            "added_at_utc": self.added_at_utc,
            "blocking_reasons": list(self.blocking_reasons),
        }


def load_watchlist_entries(fixture_path: Path | None = None) -> list[WatchlistEntry]:
    path = fixture_path or _default_watchlist_fixture_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    entries = []
    for raw in data.get("entries", []):
        entries.append(
            WatchlistEntry(
                target_id=str(raw["target_id"]),
                watchlist_kind=str(raw["watchlist_kind"]),
                added_at_utc=str(raw["added_at_utc"]),
                operator_notes=str(raw.get("operator_notes", "")),
                priority_override_score=raw.get("priority_override_score"),
                blocking_reasons=list(raw.get("blocking_reasons", [])),
            )
        )
    return entries


def target_watchlist_summary(fixture_path: Path | None = None) -> dict[str, Any]:
    entries = load_watchlist_entries(fixture_path)
    by_kind: dict[str, int] = {}
    blocked_entries: list[str] = []
    elevated_entries: list[str] = []
    conflict_targets: list[str] = []
    elevated_ids = {e.target_id for e in entries if e.watchlist_kind == "elevated"}
    blocked_ids = {e.target_id for e in entries if e.watchlist_kind == "blocked"}

    for entry in entries:
        kind = entry.watchlist_kind
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if kind == "blocked":
            blocked_entries.append(entry.target_id)
        if kind == "elevated":
            elevated_entries.append(entry.target_id)

    conflict_targets = sorted(elevated_ids & blocked_ids)
    total_blocking_reasons = sum(len(e.blocking_reasons) for e in entries)

    return {
        "schema_version": TARGET_WATCHLIST_SCHEMA_VERSION,
        "disclaimer": TARGET_WATCHLIST_DISCLAIMER,
        "entry_count": len(entries),
        "by_kind": dict(sorted(by_kind.items())),
        "elevated_count": by_kind.get("elevated", 0),
        "deprioritized_count": by_kind.get("deprioritized", 0),
        "blocked_count": by_kind.get("blocked", 0),
        "completed_count": by_kind.get("completed", 0),
        "elevated_target_ids": sorted(elevated_entries),
        "blocked_target_ids": sorted(blocked_entries),
        "conflict_elevated_and_blocked": conflict_targets,
        "conflict_count": len(conflict_targets),
        "total_blocking_reasons": total_blocking_reasons,
        "operator_note_count": sum(1 for e in entries if e.operator_notes),
    }
