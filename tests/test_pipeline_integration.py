from __future__ import annotations

from techno_search.pipeline_integration import (
    PIPELINE_INTEGRATION_DISCLAIMER,
    pipeline_integration_summary,
    run_pipeline_smoke_test,
)


def test_disclaimer_present():
    assert len(PIPELINE_INTEGRATION_DISCLAIMER) > 20
    assert "local scheduling" in PIPELINE_INTEGRATION_DISCLAIMER.lower()


def test_disclaimer_no_authorization():
    lower = PIPELINE_INTEGRATION_DISCLAIMER.lower()
    assert "do not authorize external submission" in lower


def test_smoke_test_radio_returns_dict():
    result = run_pipeline_smoke_test("radio-clean-candidate")
    assert isinstance(result, dict)
    assert result["candidate_id"] == "radio-clean-candidate"


def test_smoke_test_provenance_consistent_for_radio():
    result = run_pipeline_smoke_test("radio-clean-candidate")
    assert result["provenance_consistent"] is True


def test_smoke_test_active_config_present():
    result = run_pipeline_smoke_test("radio-clean-candidate")
    assert result["active_pipeline_config_id"] is not None


def test_smoke_test_active_model_present():
    result = run_pipeline_smoke_test("radio-clean-candidate")
    assert result["active_serving_model_id"] is not None


def test_smoke_test_audit_entries_found():
    result = run_pipeline_smoke_test("radio-clean-candidate")
    assert result["audit_entry_count"] >= 1


def test_smoke_test_stages_reached():
    result = run_pipeline_smoke_test("radio-clean-candidate")
    stages = result["stages_reached"]
    assert "pipeline_config" in stages
    assert "model_serving" in stages
    assert "scoring_audit" in stages


def test_smoke_test_rescore_events():
    result = run_pipeline_smoke_test("radio-clean-candidate")
    assert result["rescore_event_count"] >= 1


def test_smoke_test_handoff_templates():
    result = run_pipeline_smoke_test("radio-clean-candidate")
    assert result["handoff_template_count"] >= 1


def test_smoke_test_unknown_candidate():
    result = run_pipeline_smoke_test("unknown-candidate-xyz")
    assert result["audit_entry_count"] == 0
    assert result["rescore_event_count"] == 0
    assert result["handoff_template_count"] == 0


def test_integration_summary_returns_dict():
    summary = pipeline_integration_summary()
    assert isinstance(summary, dict)
    assert "results" in summary


def test_integration_summary_candidates_tested():
    summary = pipeline_integration_summary()
    assert len(summary["candidates_tested"]) == 3


def test_integration_summary_consistent_count():
    summary = pipeline_integration_summary()
    assert summary["consistent_count"] >= 1


def test_integration_summary_disclaimer():
    summary = pipeline_integration_summary()
    assert len(summary["disclaimer"]) > 20
