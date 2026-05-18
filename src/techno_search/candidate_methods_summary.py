from __future__ import annotations

from typing import Any

CANDIDATE_METHODS_DISCLAIMER = (
    "Candidate methods summary is an operational dashboard only. "
    "It mirrors existing fixture data and does not authorize external submission, "
    "does not modify candidate posteriors, and does not constitute a detection claim."
)


def candidate_methods_summary() -> dict[str, Any]:
    from techno_search.candidate_rescore import candidate_rescore_summary
    from techno_search.curated_dataset_intake import curated_dataset_intake_summary
    from techno_search.model_serving import model_serving_summary
    from techno_search.operator_handoff_template import operator_handoff_summary
    from techno_search.scoring_audit_log import scoring_audit_log_summary

    serving = model_serving_summary()
    audit = scoring_audit_log_summary()
    intake = curated_dataset_intake_summary()
    rescore = candidate_rescore_summary()
    handoff = operator_handoff_summary()

    active_ids: list[str] = serving.get("active_model_ids", [])
    active_model_id = active_ids[0] if active_ids else None

    return {
        "disclaimer": CANDIDATE_METHODS_DISCLAIMER,
        "pipeline_status": (
            "operational" if serving.get("active_count", 0) >= 1 else "no_active_model"
        ),
        "active_serving_model_id": active_model_id,
        "active_inference_backend": serving.get("by_backend", {}) and next(
            (b for b, c in serving.get("by_backend", {}).items() if c > 0), None
        ),
        "scoring_events_total": audit.get("entry_count", 0),
        "scoring_unique_candidates": audit.get("unique_candidate_count", 0),
        "rescore_event_count": rescore.get("event_count", 0),
        "rescore_pathway_change_count": rescore.get("pathway_change_count", 0),
        "approved_handoffs": handoff.get("approved_count", 0),
        "pending_handoffs": handoff.get("pending_count", 0),
        "approved_intake_datasets": intake.get("approved_count", 0),
        "total_intake_records": intake.get("record_count", 0),
    }
