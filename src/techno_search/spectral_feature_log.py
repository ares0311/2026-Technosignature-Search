"""Operational provenance records for spectral feature extraction events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SPECTRAL_FEATURE_LOG_SCHEMA_VERSION = "spectral_feature_log_v1"

SPECTRAL_FEATURE_LOG_DISCLAIMER = (
    "Spectral feature entries are operational provenance records — a detected "
    "feature does not confirm technosignature interest, does not modify candidate "
    "scores or pathway routing, and does not authorize external submission or "
    "constitute a detection claim."
)

ALLOWED_FEATURE_KINDS = frozenset({
    "emission_line", "absorption_line", "continuum_fit", "spectral_index", "line_complex",
})

ALLOWED_FEATURE_STATUSES = frozenset({
    "detected", "tentative", "not_detected", "artifact",
})


def _default_spectral_feature_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "spectral_feature_log.json"
    )


@dataclass
class SpectralFeatureEntry:
    entry_id: str
    candidate_id: str
    feature_kind: str
    status: str
    detected_by: str
    detected_at: str
    track: str
    frequency_mhz: float | None = None
    significance: float | None = None
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "feature_kind": self.feature_kind,
            "status": self.status,
            "detected_by": self.detected_by,
            "detected_at": self.detected_at,
            "track": self.track,
            "frequency_mhz": self.frequency_mhz,
            "significance": self.significance,
            "notes": self.notes,
        }


def load_spectral_feature_entries(
    path: Path | None = None,
) -> list[SpectralFeatureEntry]:
    fpath = path or _default_spectral_feature_log_path()
    with open(fpath) as f:
        data = json.load(f)
    entries = []
    for item in data.get("spectral_feature_entries", []):
        entries.append(SpectralFeatureEntry(
            entry_id=item["entry_id"],
            candidate_id=item["candidate_id"],
            feature_kind=item["feature_kind"],
            status=item["status"],
            detected_by=item["detected_by"],
            detected_at=item["detected_at"],
            track=item["track"],
            frequency_mhz=item.get("frequency_mhz"),
            significance=item.get("significance"),
            notes=item.get("notes"),
        ))
    return entries


def spectral_feature_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_spectral_feature_entries(path)
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for e in entries:
        by_kind[e.feature_kind] = by_kind.get(e.feature_kind, 0) + 1
        by_status[e.status] = by_status.get(e.status, 0) + 1
    return {
        "schema_version": SPECTRAL_FEATURE_LOG_SCHEMA_VERSION,
        "disclaimer": SPECTRAL_FEATURE_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "detected_count": by_status.get("detected", 0),
        "artifact_count": by_status.get("artifact", 0),
        "counts_by_kind": by_kind,
        "counts_by_status": by_status,
    }
