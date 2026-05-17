"""Pipeline throughput — per-stage candidate counts and transition rate metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

PIPELINE_THROUGHPUT_DISCLAIMER = (
    "Pipeline throughput summaries are local operational metrics only. "
    "Stage counts and transition rates reflect local fixture data for scheduling "
    "and provenance purposes. They do not constitute survey performance estimates, "
    "detection claims, or calibrated pipeline efficiency metrics."
)

PIPELINE_STAGES = (
    "identified",
    "feature_extraction",
    "scored",
    "human_review",
    "follow_up_scheduled",
    "archived",
    "rejected",
)

PIPELINE_HEALTH_TRACKS = ("radio", "infrared", "anomaly")


def pipeline_throughput_summary(
    lifecycle_fixture_path: Path | None = None,
    triage_fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Return per-stage throughput counts and transition rate metrics."""

    from techno_search.candidate_lifecycle import (
        CandidateLifecycleEntry,
        load_lifecycle_entries,
    )
    from techno_search.candidate_triage import CandidateTriageNote, load_triage_notes

    raw_lifecycle: list[CandidateLifecycleEntry] = load_lifecycle_entries(
        lifecycle_fixture_path
    )
    raw_triage: list[CandidateTriageNote] = load_triage_notes(triage_fixture_path)

    stage_counts: dict[str, int] = {stage: 0 for stage in PIPELINE_STAGES}
    by_track: dict[str, dict[str, int]] = {
        track: {stage: 0 for stage in PIPELINE_STAGES}
        for track in PIPELINE_HEALTH_TRACKS
    }

    for entry in raw_lifecycle:
        stage = entry.stage
        if stage in stage_counts:
            stage_counts[stage] += 1
        track = entry.track
        if track in by_track and stage in by_track[track]:
            by_track[track][stage] += 1

    triage_count = len(raw_triage)
    triage_blocked_count = sum(
        1 for t in raw_triage if len(t.blocking_reasons) > 0
    )
    triage_cleared_count = triage_count - triage_blocked_count

    total_lifecycle = len(raw_lifecycle)
    blocked_lifecycle = sum(
        1 for e in raw_lifecycle if len(e.blocking_reasons) > 0
    )
    cleared_lifecycle = total_lifecycle - blocked_lifecycle

    throughput_rate = (
        round(cleared_lifecycle / total_lifecycle, 3) if total_lifecycle > 0 else 0.0
    )

    return {
        "disclaimer": PIPELINE_THROUGHPUT_DISCLAIMER,
        "total_lifecycle_entries": total_lifecycle,
        "total_triage_notes": triage_count,
        "lifecycle_cleared_count": cleared_lifecycle,
        "lifecycle_blocked_count": blocked_lifecycle,
        "triage_cleared_count": triage_cleared_count,
        "triage_blocked_count": triage_blocked_count,
        "throughput_rate": throughput_rate,
        "stage_counts": stage_counts,
        "by_track": {
            track: dict(counts) for track, counts in by_track.items()
        },
    }
