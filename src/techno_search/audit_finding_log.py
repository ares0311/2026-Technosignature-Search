"""Operational provenance records for formal audit finding events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

AUDIT_FINDING_LOG_SCHEMA_VERSION = "audit_finding_log_v1"

ALLOWED_AUDIT_FINDING_KINDS = frozenset(
    {
        "compliance_gap",
        "configuration_issue",
        "documentation_gap",
        "process_gap",
        "security_finding",
    }
)

ALLOWED_AUDIT_FINDING_STATUSES = frozenset(
    {
        "accepted",
        "closed",
        "open",
        "remediated",
    }
)

_DISCLAIMER = (
    "Audit finding log entries are operational provenance records only. "
    "An audit finding event does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a "
    "detection claim."
)


def _default_fixture_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "audit_finding_log.json"
    )


@dataclass(frozen=True)
class AuditFindingEntry:
    entry_id: str
    finding_kind: str
    status: str
    audit_ref: str
    description: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.finding_kind not in ALLOWED_AUDIT_FINDING_KINDS:
            raise ValueError(f"invalid finding_kind: {self.finding_kind!r}")
        if self.status not in ALLOWED_AUDIT_FINDING_STATUSES:
            raise ValueError(f"invalid status: {self.status!r}")


def load_audit_finding_entries(path: Path | None = None) -> list[AuditFindingEntry]:
    fixture_path = path if path is not None else _default_fixture_path()
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    return [
        AuditFindingEntry(
            entry_id=str(entry["entry_id"]),
            finding_kind=str(entry["finding_kind"]),
            status=str(entry["status"]),
            audit_ref=str(entry["audit_ref"]),
            description=str(entry["description"]),
            notes=str(entry.get("notes", "")),
        )
        for entry in raw["entries"]
    ]


def audit_finding_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_audit_finding_entries(path)
    remediated_count = sum(1 for e in entries if e.status == "remediated")
    return {
        "schema_version": AUDIT_FINDING_LOG_SCHEMA_VERSION,
        "disclaimer": _DISCLAIMER,
        "entry_count": len(entries),
        "remediated_count": remediated_count,
        "kind_counts": {
            kind: sum(1 for e in entries if e.finding_kind == kind)
            for kind in sorted(ALLOWED_AUDIT_FINDING_KINDS)
        },
        "status_counts": {
            status: sum(1 for e in entries if e.status == status)
            for status in sorted(ALLOWED_AUDIT_FINDING_STATUSES)
        },
    }
