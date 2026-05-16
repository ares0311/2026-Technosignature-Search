"""Aggregate blockers — collects blocking issues across triage, lifecycle, and handoffs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

AGGREGATE_BLOCKERS_DISCLAIMER = (
    "Aggregate blocker summaries collect blocking issues from local scheduling and "
    "provenance records only. They are operational aids to identify candidates "
    "stalled in the pipeline. They do not constitute external validation, detection "
    "claims, or discovery announcements."
)


def aggregate_blockers_summary(
    triage_fixture_path: Path | None = None,
    lifecycle_fixture_path: Path | None = None,
    handoff_fixture_path: Path | None = None,
    observation_notes_fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return a consolidated summary of blocking issues across pipeline stages."""

    from techno_search.candidate_lifecycle import (
        CandidateLifecycleEntry,
        load_lifecycle_entries,
    )
    from techno_search.candidate_observation_notes import (
        CandidateObservationNote,
        load_observation_notes,
    )
    from techno_search.candidate_triage import CandidateTriageNote, load_triage_notes

    raw_triage: list[CandidateTriageNote] = load_triage_notes(triage_fixture_path)
    raw_lifecycle: list[CandidateLifecycleEntry] = load_lifecycle_entries(lifecycle_fixture_path)
    raw_obs_notes: list[CandidateObservationNote] = load_observation_notes(
        observation_notes_fixture_path
    )

    triage_blockers: list[dict[str, Any]] = []
    for t_note in raw_triage:
        for reason in t_note.blocking_reasons:
            triage_blockers.append(
                {
                    "source": "triage",
                    "candidate_id": t_note.candidate_id,
                    "track": t_note.track,
                    "blocking_reason": reason,
                    "triage_label": t_note.triage_label,
                }
            )

    lifecycle_blockers: list[dict[str, Any]] = []
    for lc_entry in raw_lifecycle:
        for reason in lc_entry.blocking_reasons:
            lifecycle_blockers.append(
                {
                    "source": "lifecycle",
                    "candidate_id": lc_entry.candidate_id,
                    "track": lc_entry.track,
                    "blocking_reason": reason,
                    "stage": lc_entry.stage,
                }
            )

    observation_blockers: list[dict[str, Any]] = []
    for obs_note in raw_obs_notes:
        for flag in obs_note.quality_flags:
            observation_blockers.append(
                {
                    "source": "observation_note",
                    "candidate_id": obs_note.candidate_id,
                    "track": obs_note.track,
                    "blocking_reason": flag,
                    "outcome": obs_note.outcome,
                }
            )

    handoff_blockers: list[dict[str, Any]] = []
    if handoff_fixture_path is not None or _default_handoff_path().exists():
        try:
            from techno_search.background_search import load_candidate_extraction_handoffs

            handoffs = load_candidate_extraction_handoffs(handoff_fixture_path)
            for handoff in handoffs:
                for reason in handoff.blocking_issues:
                    handoff_blockers.append(
                        {
                            "source": "handoff",
                            "candidate_id": handoff.target_id,
                            "track": handoff.track.value,
                            "blocking_reason": reason,
                            "handoff_status": handoff.extraction_status,
                        }
                    )
        except Exception:  # pragma: no cover — fixture may not always exist
            pass

    all_blockers = triage_blockers + lifecycle_blockers + observation_blockers + handoff_blockers

    by_source: dict[str, int] = {}
    by_track: dict[str, int] = {}
    by_candidate: dict[str, int] = {}

    for blocker in all_blockers:
        src = str(blocker["source"])
        trk = str(blocker["track"])
        cid = str(blocker["candidate_id"])
        by_source[src] = by_source.get(src, 0) + 1
        by_track[trk] = by_track.get(trk, 0) + 1
        by_candidate[cid] = by_candidate.get(cid, 0) + 1

    candidates_with_blockers = sorted(by_candidate.keys())

    return {
        "disclaimer": AGGREGATE_BLOCKERS_DISCLAIMER,
        "total_blocker_count": len(all_blockers),
        "unique_candidate_count": len(by_candidate),
        "candidates_with_blockers": candidates_with_blockers,
        "by_source": dict(sorted(by_source.items())),
        "by_track": dict(sorted(by_track.items())),
        "triage_blocker_count": len(triage_blockers),
        "lifecycle_blocker_count": len(lifecycle_blockers),
        "observation_blocker_count": len(observation_blockers),
        "handoff_blocker_count": len(handoff_blockers),
        "blockers": all_blockers,
    }


def _default_handoff_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "candidate_extraction_handoffs.json"
    )
