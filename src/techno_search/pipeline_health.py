"""Pipeline health summary — per-track health dashboard aggregating pipeline state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

PIPELINE_HEALTH_DISCLAIMER = (
    "Pipeline health summaries are local operational dashboards only. "
    "They aggregate scheduling, provenance, and review-state records to surface "
    "candidates stalled in the pipeline. They do not constitute detections, "
    "discoveries, external validation, or calibrated survey performance estimates."
)

PIPELINE_HEALTH_TRACKS = ("radio", "infrared", "anomaly")


def pipeline_health_summary(
    triage_fixture_path: Path | None = None,
    lifecycle_fixture_path: Path | None = None,
    assignment_fixture_path: Path | None = None,
    epoch_plan_fixture_path: Path | None = None,
    obs_notes_fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return a per-track pipeline health dashboard."""

    from techno_search.candidate_lifecycle import (
        CandidateLifecycleEntry,
        load_lifecycle_entries,
    )
    from techno_search.candidate_observation_notes import (
        CandidateObservationNote,
        load_observation_notes,
    )
    from techno_search.candidate_triage import CandidateTriageNote, load_triage_notes
    from techno_search.epoch_plan import EpochPlanEntry, load_epoch_plan
    from techno_search.operator_assignment import (
        OperatorAssignment,
        load_operator_assignments,
    )

    raw_triage: list[CandidateTriageNote] = load_triage_notes(triage_fixture_path)
    raw_lifecycle: list[CandidateLifecycleEntry] = load_lifecycle_entries(lifecycle_fixture_path)
    raw_assignments: list[OperatorAssignment] = load_operator_assignments(assignment_fixture_path)
    raw_epoch: list[EpochPlanEntry] = load_epoch_plan(epoch_plan_fixture_path)
    raw_obs: list[CandidateObservationNote] = load_observation_notes(obs_notes_fixture_path)

    per_track: dict[str, dict[str, Any]] = {}
    for track in PIPELINE_HEALTH_TRACKS:
        triage_count = sum(1 for t in raw_triage if t.track == track)
        triage_blocked = sum(
            1 for t in raw_triage if t.track == track and len(t.blocking_reasons) > 0
        )
        lifecycle_count = sum(1 for lc in raw_lifecycle if lc.track == track)
        lifecycle_blocked = sum(
            1 for lc in raw_lifecycle if lc.track == track and len(lc.blocking_reasons) > 0
        )
        pending_assignments = sum(
            1
            for a in raw_assignments
            if a.track == track and a.assignment_status in ("pending", "in_progress")
        )
        escalated_assignments = sum(
            1
            for a in raw_assignments
            if a.track == track and a.assignment_status == "escalated"
        )
        pending_epochs = sum(
            1 for ep in raw_epoch if ep.track == track and ep.status == "pending"
        )
        obs_follow_up = sum(
            1 for ob in raw_obs if ob.track == track and ob.follow_up_recommended
        )
        per_track[track] = {
            "triage_count": triage_count,
            "triage_blocked_count": triage_blocked,
            "lifecycle_count": lifecycle_count,
            "lifecycle_blocked_count": lifecycle_blocked,
            "pending_assignments": pending_assignments,
            "escalated_assignments": escalated_assignments,
            "pending_epoch_requests": pending_epochs,
            "observation_follow_up_recommended": obs_follow_up,
        }

    total_blocked = sum(
        v["triage_blocked_count"] + v["lifecycle_blocked_count"]
        for v in per_track.values()
    )
    total_escalated = sum(v["escalated_assignments"] for v in per_track.values())

    return {
        "disclaimer": PIPELINE_HEALTH_DISCLAIMER,
        "tracks": PIPELINE_HEALTH_TRACKS,
        "per_track": per_track,
        "total_blocked_count": total_blocked,
        "total_escalated_count": total_escalated,
    }
