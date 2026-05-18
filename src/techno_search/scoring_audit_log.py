"""Scoring audit log — append-only record of score events per candidate per model version."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCORING_AUDIT_LOG_SCHEMA_VERSION = "scoring_audit_log_v1"

SCORING_AUDIT_LOG_DISCLAIMER = (
    "Scoring audit log entries are append-only provenance records for reproducibility only. "
    "They do not constitute detections, discoveries, or external validation. "
    "Audit events are local scheduling records tied to synthetic development fixtures."
)

ALLOWED_AUDIT_EVENT_KINDS = frozenset(
    {"initial_score", "rescore", "baseline_comparison", "model_version_change"}
)


def _default_audit_log_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "scoring_audit_log.json"
    )


@dataclass
class ScoringAuditEntry:
    audit_id: str
    candidate_id: str
    model_id: str
    model_version: str
    event_kind: str
    score: float
    pathway: str
    serving_id: str
    event_utc: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "candidate_id": self.candidate_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "event_kind": self.event_kind,
            "score": self.score,
            "pathway": self.pathway,
            "serving_id": self.serving_id,
            "event_utc": self.event_utc,
            "notes": self.notes,
        }


def load_scoring_audit_entries(
    fixture_path: Path | None = None,
) -> list[ScoringAuditEntry]:
    import json

    path = fixture_path or _default_audit_log_path()
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    entries = []
    for item in raw.get("audit_entries", []):
        entries.append(
            ScoringAuditEntry(
                audit_id=item["audit_id"],
                candidate_id=item["candidate_id"],
                model_id=item["model_id"],
                model_version=item["model_version"],
                event_kind=item["event_kind"],
                score=float(item["score"]),
                pathway=item["pathway"],
                serving_id=item["serving_id"],
                event_utc=item["event_utc"],
                notes=item["notes"],
            )
        )
    return entries


def scoring_audit_log_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_scoring_audit_entries(fixture_path)

    by_event_kind: dict[str, int] = {}
    by_model_id: dict[str, int] = {}
    unique_candidates: set[str] = set()
    rescore_count = 0

    for e in entries:
        by_event_kind[e.event_kind] = by_event_kind.get(e.event_kind, 0) + 1
        by_model_id[e.model_id] = by_model_id.get(e.model_id, 0) + 1
        unique_candidates.add(e.candidate_id)
        if e.event_kind == "rescore":
            rescore_count += 1

    return {
        "disclaimer": SCORING_AUDIT_LOG_DISCLAIMER,
        "schema_version": SCORING_AUDIT_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "unique_candidate_count": len(unique_candidates),
        "rescore_count": rescore_count,
        "by_event_kind": by_event_kind,
        "by_model_id": by_model_id,
    }
