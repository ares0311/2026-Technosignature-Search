from __future__ import annotations

from typing import Any

CANDIDATE_METHODS_DISCLAIMER = (
    "Candidate methods summary is an operational dashboard only. "
    "It mirrors existing fixture data and does not authorize external submission, "
    "does not modify candidate posteriors, and does not constitute a detection claim."
)


def candidate_methods_summary() -> dict[str, Any]:
    from techno_search.curated_dataset_intake import curated_dataset_intake_summary

    intake = curated_dataset_intake_summary()

    return {
        "disclaimer": CANDIDATE_METHODS_DISCLAIMER,
        "pipeline_status": "no_active_model",
        "active_serving_model_id": None,
        "active_inference_backend": None,
        "scoring_events_total": 0,
        "scoring_unique_candidates": 0,
        "rescore_event_count": 0,
        "rescore_pathway_change_count": 0,
        "approved_handoffs": 0,
        "pending_handoffs": 0,
        "approved_intake_datasets": intake.get("approved_count", 0),
        "total_intake_records": intake.get("record_count", 0),
    }
