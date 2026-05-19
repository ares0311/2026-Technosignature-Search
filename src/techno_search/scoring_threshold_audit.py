from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCORING_THRESHOLD_AUDIT_SCHEMA_VERSION = "scoring_threshold_audit_v1"

SCORING_THRESHOLD_AUDIT_DISCLAIMER = (
    "Scoring threshold audit records are local provenance consistency checks only. "
    "They verify that scoring thresholds recorded in the pipeline config match "
    "the active scoring config version — not that the thresholds are scientifically "
    "calibrated. An audit pass does not authorize external submission or "
    "constitute a detection claim."
)

ALLOWED_THRESHOLD_AUDIT_VERDICTS = frozenset({"pass", "fail", "warning", "not_checked"})


def _default_threshold_audit_fixture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "scoring_threshold_audit.json"
    )


@dataclass
class ScoringThresholdAuditEntry:
    audit_id: str
    config_id: str
    scoring_config_version: str
    track: str
    threshold_name: str
    expected_value: float
    observed_value: float
    verdict: str
    audit_utc: str
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "config_id": self.config_id,
            "scoring_config_version": self.scoring_config_version,
            "track": self.track,
            "threshold_name": self.threshold_name,
            "expected_value": self.expected_value,
            "observed_value": self.observed_value,
            "verdict": self.verdict,
            "audit_utc": self.audit_utc,
            "notes": self.notes,
        }


def load_threshold_audit_entries(
    fixture_path: Path | str | None = None,
) -> list[ScoringThresholdAuditEntry]:
    path = (
        Path(fixture_path)
        if fixture_path is not None
        else _default_threshold_audit_fixture_path()
    )
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = []
    for entry in data.get("scoring_threshold_audit_entries", []):
        entries.append(
            ScoringThresholdAuditEntry(
                audit_id=entry["audit_id"],
                config_id=entry["config_id"],
                scoring_config_version=entry["scoring_config_version"],
                track=entry["track"],
                threshold_name=entry["threshold_name"],
                expected_value=float(entry["expected_value"]),
                observed_value=float(entry["observed_value"]),
                verdict=entry["verdict"],
                audit_utc=entry["audit_utc"],
                notes=entry.get("notes", ""),
            )
        )
    return entries


def scoring_threshold_audit_summary(
    fixture_path: Path | str | None = None,
) -> dict[str, Any]:
    entries = load_threshold_audit_entries(fixture_path)
    by_verdict: dict[str, int] = {}
    by_track: dict[str, int] = {}
    fail_count = 0
    for e in entries:
        by_verdict[e.verdict] = by_verdict.get(e.verdict, 0) + 1
        by_track[e.track] = by_track.get(e.track, 0) + 1
        if e.verdict == "fail":
            fail_count += 1
    pass_count = by_verdict.get("pass", 0)
    tracks_covered = sorted(by_track.keys())
    return {
        "disclaimer": SCORING_THRESHOLD_AUDIT_DISCLAIMER,
        "schema_version": SCORING_THRESHOLD_AUDIT_SCHEMA_VERSION,
        "entry_count": len(entries),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "warning_count": by_verdict.get("warning", 0),
        "not_checked_count": by_verdict.get("not_checked", 0),
        "by_verdict": by_verdict,
        "by_track": by_track,
        "tracks_covered": tracks_covered,
        "all_passed": fail_count == 0 and pass_count > 0,
    }
