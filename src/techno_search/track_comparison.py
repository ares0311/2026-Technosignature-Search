"""Track comparison — side-by-side metrics for radio, infrared, and anomaly tracks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

TRACK_COMPARISON_DISCLAIMER = (
    "Track comparison summaries are local operational dashboards only. "
    "Per-track counts reflect synthetic fixture data and scheduling provenance "
    "records. They do not constitute survey coverage estimates, relative track "
    "sensitivity assessments, or scientific performance comparisons."
)

COMPARISON_TRACKS = ("radio", "infrared", "anomaly")


def track_comparison_summary(
    triage_fixture_path: Path | None = None,
    lifecycle_fixture_path: Path | None = None,
    flags_fixture_path: Path | None = None,
    deadlines_fixture_path: Path | None = None,
    epoch_plan_fixture_path: Path | None = None,
    obs_notes_fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return a side-by-side per-track comparison of pipeline metrics."""

    from techno_search.candidate_flags import CandidateFlag, load_candidate_flags
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
    from techno_search.review_deadlines import ReviewDeadline, load_review_deadlines

    raw_triage: list[CandidateTriageNote] = load_triage_notes(triage_fixture_path)
    raw_lifecycle: list[CandidateLifecycleEntry] = load_lifecycle_entries(lifecycle_fixture_path)
    raw_flags: list[CandidateFlag] = load_candidate_flags(flags_fixture_path)
    raw_deadlines: list[ReviewDeadline] = load_review_deadlines(deadlines_fixture_path)
    raw_epoch: list[EpochPlanEntry] = load_epoch_plan(epoch_plan_fixture_path)
    raw_obs: list[CandidateObservationNote] = load_observation_notes(obs_notes_fixture_path)

    per_track: dict[str, dict[str, int]] = {}
    for track in COMPARISON_TRACKS:
        per_track[track] = {
            "triage_count": sum(1 for t in raw_triage if t.track == track),
            "triage_blocked": sum(
                1 for t in raw_triage if t.track == track and len(t.blocking_reasons) > 0
            ),
            "lifecycle_count": sum(1 for lc in raw_lifecycle if lc.track == track),
            "lifecycle_blocked": sum(
                1 for lc in raw_lifecycle if lc.track == track and len(lc.blocking_reasons) > 0
            ),
            "open_flags": sum(
                1 for fl in raw_flags if fl.track == track and fl.status == "open"
            ),
            "critical_flags": sum(
                1 for fl in raw_flags if fl.track == track and fl.severity == "critical"
            ),
            "pending_deadlines": sum(
                1 for dl in raw_deadlines
                if dl.track == track and dl.status in ("pending", "overdue")
            ),
            "overdue_deadlines": sum(
                1 for dl in raw_deadlines if dl.track == track and dl.status == "overdue"
            ),
            "pending_epoch_requests": sum(
                1 for ep in raw_epoch if ep.track == track and ep.status == "pending"
            ),
            "observation_follow_up": sum(
                1 for ob in raw_obs if ob.track == track and ob.follow_up_recommended
            ),
        }

    total_open_flags = sum(v["open_flags"] for v in per_track.values())
    total_overdue = sum(v["overdue_deadlines"] for v in per_track.values())

    return {
        "disclaimer": TRACK_COMPARISON_DISCLAIMER,
        "tracks": COMPARISON_TRACKS,
        "per_track": per_track,
        "total_open_flags": total_open_flags,
        "total_overdue_deadlines": total_overdue,
    }
