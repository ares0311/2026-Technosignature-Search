from __future__ import annotations

from typing import Any

PIPELINE_INTEGRATION_DISCLAIMER = (
    "Pipeline integration smoke tests verify that a candidate can flow through "
    "scoring, model serving lookup, audit log lookup, and operator handoff lookup "
    "with consistent provenance. These are local scheduling consistency checks only "
    "and do not authorize external submission or constitute detection claims."
)


def run_pipeline_smoke_test(candidate_id: str) -> dict[str, Any]:
    """Check provenance consistency for a candidate across pipeline stages."""
    from techno_search.candidate_rescore import load_rescore_events
    from techno_search.model_serving import load_serving_records
    from techno_search.operator_handoff_template import load_handoff_templates
    from techno_search.pipeline_config import load_pipeline_configs
    load_scoring_audit_entries: Any = lambda: []  # noqa: E731

    configs = load_pipeline_configs()
    active_configs = [c for c in configs if c.pipeline_status == "active"]
    active_config = active_configs[0] if active_configs else None

    serving_records = load_serving_records()
    active_serving = [r for r in serving_records if r.serving_status == "active"]
    active_serve = active_serving[0] if active_serving else None

    audit_entries = load_scoring_audit_entries()
    candidate_audits = [e for e in audit_entries if e.candidate_id == candidate_id]

    rescore_events = load_rescore_events()
    candidate_rescores = [e for e in rescore_events if e.candidate_id == candidate_id]

    handoff_templates = load_handoff_templates()
    candidate_handoffs = [t for t in handoff_templates if t.candidate_id == candidate_id]

    provenance_consistent = (
        active_config is not None
        and active_serve is not None
        and len(candidate_audits) >= 1
    )

    return {
        "disclaimer": PIPELINE_INTEGRATION_DISCLAIMER,
        "candidate_id": candidate_id,
        "active_pipeline_config_id": active_config.config_id if active_config else None,
        "active_serving_model_id": active_serve.model_id if active_serve else None,
        "audit_entry_count": len(candidate_audits),
        "rescore_event_count": len(candidate_rescores),
        "handoff_template_count": len(candidate_handoffs),
        "provenance_consistent": provenance_consistent,
        "stages_reached": [
            "pipeline_config",
            "model_serving",
            *(["scoring_audit"] if candidate_audits else []),
            *(["candidate_rescore"] if candidate_rescores else []),
            *(["operator_handoff"] if candidate_handoffs else []),
        ],
    }


def pipeline_integration_summary() -> dict[str, Any]:
    """Run smoke tests across known fixture candidates."""
    test_candidates = [
        "radio-clean-candidate",
        "infrared-clean-candidate",
        "anomaly-clean-candidate",
    ]
    results = [run_pipeline_smoke_test(cid) for cid in test_candidates]
    consistent_count = sum(1 for r in results if r["provenance_consistent"])
    return {
        "disclaimer": PIPELINE_INTEGRATION_DISCLAIMER,
        "candidates_tested": test_candidates,
        "consistent_count": consistent_count,
        "inconsistent_count": len(results) - consistent_count,
        "results": results,
    }
