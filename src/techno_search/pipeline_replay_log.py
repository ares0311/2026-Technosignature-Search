from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PIPELINE_REPLAY_SCHEMA_VERSION = "pipeline_replay_log_v1"

PIPELINE_REPLAY_DISCLAIMER = (
    "Pipeline replay log entries are append-only reproducibility records only. "
    "A replay re-runs scoring on a candidate using a specified pipeline config "
    "for provenance verification — it does not modify committed candidate packets, "
    "authorize external submission, or constitute a detection claim."
)

ALLOWED_REPLAY_OUTCOMES = frozenset(
    {"score_matched", "score_diverged", "config_mismatch", "replay_error"}
)


def _default_replay_fixture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent / "tests" / "fixtures" / "pipeline_replay_log.json"
    )


@dataclass
class PipelineReplayEntry:
    replay_id: str
    candidate_id: str
    original_config_id: str
    replay_config_id: str
    original_score: float
    replayed_score: float
    outcome: str
    score_delta: float
    replay_utc: str
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "replay_id": self.replay_id,
            "candidate_id": self.candidate_id,
            "original_config_id": self.original_config_id,
            "replay_config_id": self.replay_config_id,
            "original_score": self.original_score,
            "replayed_score": self.replayed_score,
            "outcome": self.outcome,
            "score_delta": self.score_delta,
            "replay_utc": self.replay_utc,
            "notes": self.notes,
        }


def load_replay_entries(
    fixture_path: Path | str | None = None,
) -> list[PipelineReplayEntry]:
    path = Path(fixture_path) if fixture_path is not None else _default_replay_fixture_path()
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = []
    for entry in data.get("pipeline_replay_entries", []):
        entries.append(
            PipelineReplayEntry(
                replay_id=entry["replay_id"],
                candidate_id=entry["candidate_id"],
                original_config_id=entry["original_config_id"],
                replay_config_id=entry["replay_config_id"],
                original_score=float(entry["original_score"]),
                replayed_score=float(entry["replayed_score"]),
                outcome=entry["outcome"],
                score_delta=float(entry["score_delta"]),
                replay_utc=entry["replay_utc"],
                notes=entry.get("notes", ""),
            )
        )
    return entries


def pipeline_replay_summary(
    fixture_path: Path | str | None = None,
) -> dict[str, Any]:
    entries = load_replay_entries(fixture_path)
    by_outcome: dict[str, int] = {}
    matched_count = 0
    diverged_count = 0
    deltas: list[float] = []
    for e in entries:
        by_outcome[e.outcome] = by_outcome.get(e.outcome, 0) + 1
        if e.outcome == "score_matched":
            matched_count += 1
        elif e.outcome == "score_diverged":
            diverged_count += 1
        deltas.append(abs(e.score_delta))
    mean_abs_delta = sum(deltas) / len(deltas) if deltas else 0.0
    max_abs_delta = max(deltas) if deltas else 0.0
    return {
        "disclaimer": PIPELINE_REPLAY_DISCLAIMER,
        "schema_version": PIPELINE_REPLAY_SCHEMA_VERSION,
        "entry_count": len(entries),
        "matched_count": matched_count,
        "diverged_count": diverged_count,
        "by_outcome": by_outcome,
        "mean_abs_score_delta": round(mean_abs_delta, 4),
        "max_abs_score_delta": round(max_abs_delta, 4),
    }
