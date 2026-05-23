"""Operational processing provenance records for RFI mitigation actions."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RFI_MITIGATION_SCHEMA_VERSION = "rfi_mitigation_log_v1"

RFI_MITIGATION_DISCLAIMER = (
    "RFI mitigation entries are operational processing provenance records. "
    "A passed action does not confirm a signal is not RFI, "
    "does not modify candidate scores or pathway routing, "
    "and does not authorize external submission or constitute a detection claim."
)

ALLOWED_MITIGATION_KINDS = frozenset({
    "known_rfi_source", "statistical_outlier", "satellite_track",
    "terrestrial_interference", "other",
})

ALLOWED_MITIGATION_ACTIONS = frozenset({
    "flagged", "excised", "masked", "passed", "deferred",
})


def _default_rfi_mitigation_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "rfi_mitigation_log.json"
    )


@dataclass
class RfiMitigationEntry:
    entry_id: str
    candidate_id: str
    mitigation_kind: str
    action: str
    mitigated_by: str
    mitigated_at: str
    track: str
    frequency_mhz: float | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "mitigation_kind": self.mitigation_kind,
            "action": self.action,
            "mitigated_by": self.mitigated_by,
            "mitigated_at": self.mitigated_at,
            "track": self.track,
            "frequency_mhz": self.frequency_mhz,
            "notes": self.notes,
        }


def load_rfi_mitigation_entries(
    path: Path | None = None,
) -> list[RfiMitigationEntry]:
    fpath = path or _default_rfi_mitigation_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("rfi_mitigation_entries", []):
        entries.append(RfiMitigationEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            mitigation_kind=item["mitigation_kind"],
            action=item["action"],
            mitigated_by=item["mitigated_by"],
            mitigated_at=item["mitigated_at"],
            track=item["track"],
            frequency_mhz=item.get("frequency_mhz"),
            notes=item.get("notes", ""),
        ))
    return entries


def rfi_mitigation_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_rfi_mitigation_entries(path)
    by_action: dict[str, int] = {}
    by_mitigation_kind: dict[str, int] = {}
    by_track: dict[str, int] = {}
    for e in entries:
        by_action[e.action] = by_action.get(e.action, 0) + 1
        by_mitigation_kind[e.mitigation_kind] = (
            by_mitigation_kind.get(e.mitigation_kind, 0) + 1
        )
        by_track[e.track] = by_track.get(e.track, 0) + 1
    return {
        "schema_version": RFI_MITIGATION_SCHEMA_VERSION,
        "disclaimer": RFI_MITIGATION_DISCLAIMER,
        "entry_count": len(entries),
        "flagged_count": by_action.get("flagged", 0),
        "excised_count": by_action.get("excised", 0),
        "masked_count": by_action.get("masked", 0),
        "passed_count": by_action.get("passed", 0),
        "deferred_count": by_action.get("deferred", 0),
        "by_action": by_action,
        "by_mitigation_kind": by_mitigation_kind,
        "by_track": by_track,
    }
