from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROVENANCE_AUDIT_SCHEMA_VERSION = "provenance_audit_v1"

PROVENANCE_AUDIT_DISCLAIMER = (
    "Provenance audit entries are local cross-module consistency checks only. "
    "A consistent verdict means all checked modules agree on provenance fields "
    "for this candidate — it does not authorize external submission, "
    "confirm a detection, or constitute external validation."
)

ALLOWED_AUDIT_VERDICTS = frozenset(
    {"consistent", "inconsistent", "partial", "not_applicable"}
)


def _default_provenance_audit_fixture_path() -> Path:
    return Path(__file__).parent.parent.parent / "tests" / "fixtures" / "provenance_audit.json"


@dataclass
class ProvenanceAuditEntry:
    audit_id: str
    candidate_id: str
    verdict: str
    checked_modules: list[str] = field(default_factory=list)
    inconsistencies: list[str] = field(default_factory=list)
    audit_utc: str = ""
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "candidate_id": self.candidate_id,
            "verdict": self.verdict,
            "checked_modules": self.checked_modules,
            "inconsistencies": self.inconsistencies,
            "audit_utc": self.audit_utc,
            "notes": self.notes,
        }


def load_provenance_audit_entries(
    fixture_path: Path | str | None = None,
) -> list[ProvenanceAuditEntry]:
    path = (
        Path(fixture_path) if fixture_path is not None else _default_provenance_audit_fixture_path()
    )
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = []
    for entry in data.get("provenance_audit_entries", []):
        entries.append(
            ProvenanceAuditEntry(
                audit_id=entry["audit_id"],
                candidate_id=entry["candidate_id"],
                verdict=entry["verdict"],
                checked_modules=list(entry.get("checked_modules", [])),
                inconsistencies=list(entry.get("inconsistencies", [])),
                audit_utc=entry.get("audit_utc", ""),
                notes=entry.get("notes", ""),
            )
        )
    return entries


def provenance_audit_summary(
    fixture_path: Path | str | None = None,
) -> dict[str, Any]:
    entries = load_provenance_audit_entries(fixture_path)
    by_verdict: dict[str, int] = {}
    total_inconsistencies = 0
    all_modules: set[str] = set()
    for e in entries:
        by_verdict[e.verdict] = by_verdict.get(e.verdict, 0) + 1
        total_inconsistencies += len(e.inconsistencies)
        all_modules.update(e.checked_modules)
    return {
        "disclaimer": PROVENANCE_AUDIT_DISCLAIMER,
        "schema_version": PROVENANCE_AUDIT_SCHEMA_VERSION,
        "entry_count": len(entries),
        "consistent_count": by_verdict.get("consistent", 0),
        "inconsistent_count": by_verdict.get("inconsistent", 0),
        "partial_count": by_verdict.get("partial", 0),
        "not_applicable_count": by_verdict.get("not_applicable", 0),
        "by_verdict": by_verdict,
        "total_inconsistency_count": total_inconsistencies,
        "modules_covered": sorted(all_modules),
    }
