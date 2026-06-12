"""Operator review dashboard — aggregate view of open review actions.

Pulls from existing summary helpers to surface what needs human attention now:
open flags, overdue deadlines, queue depth, pipeline blockers, and current
real-label scoring accuracy.

Scientific guardrail: dashboard entries are local scheduling aids only.
None of these outputs modify candidate scores, authorize external submission,
or constitute a detection claim.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

REVIEW_DASHBOARD_DISCLAIMER = (
    "Review dashboard entries are local operator scheduling aids only. "
    "No dashboard output modifies candidate scores, authorizes external "
    "submission, or constitutes a detection claim."
)

_REAL_LABEL_PATH = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "real_labeled"
    / "hip99427_citizen_science_labels_v1.json"
)


def review_dashboard_summary() -> dict[str, Any]:
    """Return a consolidated operator review dashboard.

    Aggregates open flags, overdue deadlines, queue depth, pipeline blockers,
    real-label accuracy, and watchlist elevated targets into a single dict.
    All counts are zero-safe — missing fixtures return 0, not errors.
    """
    from techno_search.aggregate_blockers import aggregate_blockers_summary
    from techno_search.baseline_eval import eval_against_labels
    from techno_search.candidate_flags import candidate_flags_summary
    from techno_search.review_deadlines import review_deadlines_summary
    from techno_search.review_queue import review_queue_summary
    from techno_search.target_watchlist import target_watchlist_summary

    flags: dict[str, Any] = candidate_flags_summary()
    open_flags = int(flags.get("open_flag_count") or 0)
    flag_critical = int(flags.get("critical_flag_count") or 0)

    deadlines: dict[str, Any] = review_deadlines_summary()
    overdue = int(deadlines.get("overdue_count") or 0)
    upcoming = int(deadlines.get("deadline_count") or 0) - overdue

    queue: dict[str, Any] = review_queue_summary()
    queue_depth = int(queue.get("total_items") or 0)
    queue_needs_review = int(queue.get("needs_human_review_count") or 0)

    blockers: dict[str, Any] = aggregate_blockers_summary()
    blocker_count = int(blockers.get("total_blocker_count") or 0)
    unique_blocked_candidates = int(blockers.get("unique_candidate_count") or 0)

    watchlist: dict[str, Any] = target_watchlist_summary()
    elevated_count = int(watchlist.get("elevated_count") or 0)
    watchlist_conflicts = int(watchlist.get("conflict_count") or 0)

    # Real-label scoring accuracy (regression gate)
    real_label_accuracy: float | None = None
    real_label_entry_count = 0
    if _REAL_LABEL_PATH.exists():
        real_eval = eval_against_labels(_REAL_LABEL_PATH)
        real_label_entry_count = int(real_eval.get("entry_count") or 0)
        _acc = real_eval.get("accuracy")
        if isinstance(_acc, (int, float)):
            real_label_accuracy = float(_acc)

    # Action summary — anything > 0 needs operator attention
    action_items: list[dict[str, Any]] = []
    if open_flags > 0:
        action_items.append({
            "kind": "open_flags",
            "count": open_flags,
            "critical_count": flag_critical,
            "message": f"{open_flags} open candidate flag(s); {flag_critical} critical",
        })
    if overdue > 0:
        action_items.append({
            "kind": "overdue_deadlines",
            "count": overdue,
            "message": f"{overdue} review deadline(s) overdue",
        })
    if queue_needs_review > 0:
        action_items.append({
            "kind": "review_queue",
            "count": queue_needs_review,
            "message": f"{queue_needs_review} candidate(s) in human_review_queue",
        })
    if watchlist_conflicts > 0:
        action_items.append({
            "kind": "watchlist_conflict",
            "count": watchlist_conflicts,
            "message": f"{watchlist_conflicts} watchlist conflict(s) require resolution",
        })
    if real_label_accuracy is not None and real_label_accuracy < 0.70:
        action_items.append({
            "kind": "accuracy_regression",
            "count": 1,
            "message": (
                f"Scoring accuracy {real_label_accuracy:.4f} below gate 0.70 — "
                "model regression detected"
            ),
        })

    needs_attention = len(action_items) > 0

    return {
        "disclaimer": REVIEW_DASHBOARD_DISCLAIMER,
        "needs_attention": needs_attention,
        "action_item_count": len(action_items),
        "action_items": action_items,
        "open_flags": open_flags,
        "critical_flags": flag_critical,
        "overdue_deadlines": overdue,
        "upcoming_deadlines": upcoming,
        "review_queue_depth": queue_depth,
        "review_queue_needs_human_review": queue_needs_review,
        "pipeline_blocker_count": blocker_count,
        "unique_blocked_candidates": unique_blocked_candidates,
        "elevated_watchlist_targets": elevated_count,
        "watchlist_conflicts": watchlist_conflicts,
        "real_label_accuracy": real_label_accuracy,
        "real_label_entry_count": real_label_entry_count,
        "real_label_accuracy_gate_ok": (
            real_label_accuracy is None or real_label_accuracy >= 0.70
        ),
    }
