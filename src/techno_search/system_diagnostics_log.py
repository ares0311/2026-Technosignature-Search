"""Operational provenance records for system diagnostic check events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SYSTEM_DIAGNOSTICS_LOG_SCHEMA_VERSION = "system_diagnostics_log_v1"

SYSTEM_DIAGNOSTICS_LOG_DISCLAIMER = (
    "System diagnostics log entries are operational provenance records — "
    "a system diagnostic event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_SYSTEM_DIAGNOSTICS_KINDS = frozenset(
    {
        "hardware_check",
        "network_check",
        "performance_check",
        "software_check",
        "storage_check",
    }
)

ALLOWED_SYSTEM_DIAGNOSTICS_STATUSES = frozenset(
    {
        "failed",
        "not_run",
        "passed",
        "warning",
    }
)


def _default_system_diagnostics_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "system_diagnostics_log.json"
    )


@dataclass(frozen=True)
class SystemDiagnosticsEntry:
    entry_id: str
    diagnostics_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str | None

    def __post_init__(self) -> None:
        if self.diagnostics_kind not in ALLOWED_SYSTEM_DIAGNOSTICS_KINDS:
            raise ValueError(f"Invalid diagnostics_kind: {self.diagnostics_kind!r}")
        if self.status not in ALLOWED_SYSTEM_DIAGNOSTICS_STATUSES:
            raise ValueError(f"Invalid status: {self.status!r}")


def load_system_diagnostics_entries(
    path: Path | None = None,
) -> list[SystemDiagnosticsEntry]:
    fpath = path or _default_system_diagnostics_log_path()
    raw: dict[str, Any] = json.loads(fpath.read_text(encoding="utf-8"))
    return [
        SystemDiagnosticsEntry(
            entry_id=e["entry_id"],
            diagnostics_kind=e["diagnostics_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def system_diagnostics_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_system_diagnostics_entries(path)
    passed = sum(1 for e in entries if e.status == "passed")
    return {
        "schema_version": SYSTEM_DIAGNOSTICS_LOG_SCHEMA_VERSION,
        "disclaimer": SYSTEM_DIAGNOSTICS_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "passed_count": passed,
        "by_kind": {
            kind: sum(1 for e in entries if e.diagnostics_kind == kind)
            for kind in sorted(ALLOWED_SYSTEM_DIAGNOSTICS_KINDS)
        },
        "by_status": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_SYSTEM_DIAGNOSTICS_STATUSES)
        },
    }
