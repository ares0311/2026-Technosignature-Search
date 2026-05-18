from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANDIDATE_RESCORE_SCHEMA_VERSION = "candidate_rescore_v1"

CANDIDATE_RESCORE_DISCLAIMER = (
    "Candidate re-score events are append-only provenance records only. "
    "Re-scoring does not automatically reroute committed candidate packets — "
    "pathway changes require human review and operator approval before any "
    "external action is taken. No re-score event constitutes a discovery claim."
)

ALLOWED_RESCORE_TRIGGERS = frozenset(
    {"new_model_registered", "model_version_change", "operator_request", "drift_detected"}
)


def _default_rescore_fixture_path() -> Path:
    return Path(__file__).parent.parent.parent / "tests" / "fixtures" / "candidate_rescore.json"


@dataclass
class RescoreEvent:
    rescore_id: str
    candidate_id: str
    prior_model_id: str
    new_model_id: str
    prior_score: float
    new_score: float
    prior_pathway: str
    new_pathway: str
    trigger: str
    serving_id: str
    event_utc: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "rescore_id": self.rescore_id,
            "candidate_id": self.candidate_id,
            "prior_model_id": self.prior_model_id,
            "new_model_id": self.new_model_id,
            "prior_score": self.prior_score,
            "new_score": self.new_score,
            "prior_pathway": self.prior_pathway,
            "new_pathway": self.new_pathway,
            "trigger": self.trigger,
            "serving_id": self.serving_id,
            "event_utc": self.event_utc,
            "notes": self.notes,
        }


def load_rescore_events(fixture_path: Path | None = None) -> list[RescoreEvent]:
    path = fixture_path or _default_rescore_fixture_path()
    data = json.loads(Path(path).read_text())
    events = []
    for entry in data.get("rescore_events", []):
        events.append(
            RescoreEvent(
                rescore_id=entry["rescore_id"],
                candidate_id=entry["candidate_id"],
                prior_model_id=entry["prior_model_id"],
                new_model_id=entry["new_model_id"],
                prior_score=float(entry["prior_score"]),
                new_score=float(entry["new_score"]),
                prior_pathway=entry["prior_pathway"],
                new_pathway=entry["new_pathway"],
                trigger=entry["trigger"],
                serving_id=entry["serving_id"],
                event_utc=entry["event_utc"],
                notes=entry.get("notes", ""),
            )
        )
    return events


def candidate_rescore_summary(fixture_path: Path | None = None) -> dict[str, Any]:
    events = load_rescore_events(fixture_path)
    unique_candidates = {e.candidate_id for e in events}
    pathway_changes = [e for e in events if e.prior_pathway != e.new_pathway]
    by_trigger: dict[str, int] = {}
    for e in events:
        by_trigger[e.trigger] = by_trigger.get(e.trigger, 0) + 1
    score_deltas = [abs(e.new_score - e.prior_score) for e in events]
    max_delta = max(score_deltas) if score_deltas else 0.0
    return {
        "schema_version": CANDIDATE_RESCORE_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_RESCORE_DISCLAIMER,
        "event_count": len(events),
        "unique_candidate_count": len(unique_candidates),
        "pathway_change_count": len(pathway_changes),
        "by_trigger": by_trigger,
        "max_score_delta": round(max_delta, 4),
    }
