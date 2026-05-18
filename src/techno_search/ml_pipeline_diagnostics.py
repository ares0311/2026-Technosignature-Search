"""ML pipeline diagnostics: aggregate comparison of baseline vs registered learned models."""

from __future__ import annotations

from typing import Any

ML_PIPELINE_DIAGNOSTICS_DISCLAIMER = (
    "ML pipeline diagnostics are operational scheduling summaries only. "
    "They do not constitute detection claims, discovery announcements, or external validation. "
    "No learned model should be used operationally unless it exceeds baseline pathway accuracy."
)


def ml_pipeline_diagnostics_summary() -> dict[str, Any]:
    from techno_search.baseline_eval import evaluate_baseline
    from techno_search.ml_model_registry import model_registry_summary

    baseline_result = evaluate_baseline()
    baseline_accuracy = float(baseline_result.get("pathway_accuracy", 0.0))

    registry = model_registry_summary()
    registry_count = int(registry.get("registry_count", 0))
    above_baseline_count = int(registry.get("above_baseline_count", 0))
    below_baseline_count = int(registry.get("below_baseline_count", 0))
    validated_count = int(registry.get("validated_count", 0))

    if registry_count == 0:
        pipeline_ml_status = "no_models"
    elif below_baseline_count > 0:
        pipeline_ml_status = "some_below_baseline"
    else:
        pipeline_ml_status = "all_above_baseline"

    return {
        "disclaimer": ML_PIPELINE_DIAGNOSTICS_DISCLAIMER,
        "baseline_accuracy": baseline_accuracy,
        "registered_model_count": registry_count,
        "above_baseline_count": above_baseline_count,
        "below_baseline_count": below_baseline_count,
        "validated_model_count": validated_count,
        "pipeline_ml_status": pipeline_ml_status,
    }
