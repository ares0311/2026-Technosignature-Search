"""Pipeline audit summary — aggregate dashboard over the candidate audit trail."""

from __future__ import annotations

from typing import Any

PIPELINE_AUDIT_DISCLAIMER = (
    "Pipeline audit summaries are local operational provenance records only. "
    "Audit coverage reflects how many candidates have recorded scheduling actions, "
    "not scientific validation status. Audit action counts are not evidence of a "
    "technosignature and do not constitute independent review of candidate quality."
)


def pipeline_audit_summary() -> dict[str, Any]:
    from techno_search.candidate_audit_trail import load_audit_trail

    trail = load_audit_trail()

    by_action: dict[str, int] = {}
    by_track: dict[str, int] = {}
    operator_ids: set[str] = set()
    candidate_ids: set[str] = set()
    most_recent_utc = ""

    for entry in trail:
        action = getattr(entry, "action_type", None) or str(
            entry.as_dict().get("action_type", "unknown")
        )
        track = getattr(entry, "track", None) or str(
            entry.as_dict().get("track", "unknown")
        )
        operator = getattr(entry, "operator_id", None) or str(
            entry.as_dict().get("operator_id", "")
        )
        candidate = getattr(entry, "candidate_id", None) or str(
            entry.as_dict().get("candidate_id", "")
        )
        action_utc = getattr(entry, "action_utc", None) or str(
            entry.as_dict().get("action_utc", "")
        )

        by_action[action] = by_action.get(action, 0) + 1
        by_track[track] = by_track.get(track, 0) + 1
        if operator:
            operator_ids.add(operator)
        if candidate:
            candidate_ids.add(candidate)
        if action_utc and action_utc > most_recent_utc:
            most_recent_utc = action_utc

    total_actions = len(trail)
    overall_coverage = "adequate" if total_actions >= 5 else "sparse"

    return {
        "disclaimer": PIPELINE_AUDIT_DISCLAIMER,
        "total_audit_actions": total_actions,
        "unique_candidates_audited": len(candidate_ids),
        "unique_operators": len(operator_ids),
        "action_type_breakdown": dict(sorted(by_action.items())),
        "track_breakdown": dict(sorted(by_track.items())),
        "most_recent_action_utc": most_recent_utc,
        "overall_audit_coverage": overall_coverage,
    }
