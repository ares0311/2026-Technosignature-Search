from __future__ import annotations

import json
from pathlib import Path

from techno_search.operator_handoff_template import (
    ALLOWED_HANDOFF_STATUSES,
    OPERATOR_HANDOFF_DISCLAIMER,
    OPERATOR_HANDOFF_SCHEMA_VERSION,
    OperatorHandoffTemplate,
    load_handoff_templates,
    operator_handoff_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "operator_handoff_templates.json"


def test_schema_version():
    assert OPERATOR_HANDOFF_SCHEMA_VERSION == "operator_handoff_template_v1"


def test_disclaimer_present():
    assert len(OPERATOR_HANDOFF_DISCLAIMER) > 20
    assert "scheduling" in OPERATOR_HANDOFF_DISCLAIMER.lower()


def test_disclaimer_no_submission_authorization():
    lower = OPERATOR_HANDOFF_DISCLAIMER.lower()
    assert "does not authorize external submission" in lower


def test_allowed_statuses():
    assert "approved" in ALLOWED_HANDOFF_STATUSES
    assert "rejected" in ALLOWED_HANDOFF_STATUSES
    assert "pending_review" in ALLOWED_HANDOFF_STATUSES
    assert "draft" in ALLOWED_HANDOFF_STATUSES
    assert "expired" in ALLOWED_HANDOFF_STATUSES


def test_load_handoff_templates_returns_list():
    templates = load_handoff_templates(FIXTURE_PATH)
    assert isinstance(templates, list)


def test_load_handoff_templates_count():
    templates = load_handoff_templates(FIXTURE_PATH)
    assert len(templates) == 4


def test_handoff_template_fields():
    templates = load_handoff_templates(FIXTURE_PATH)
    t = templates[0]
    assert isinstance(t, OperatorHandoffTemplate)
    assert t.handoff_id == "hnd-001"
    assert t.candidate_id == "radio-clean-candidate"
    assert t.model_id == "mdl-002"
    assert t.inference_backend == "pytorch_stub"
    assert 0.0 <= t.score <= 1.0


def test_handoff_template_as_dict():
    templates = load_handoff_templates(FIXTURE_PATH)
    d = templates[0].as_dict()
    assert "handoff_id" in d
    assert "model_version" in d
    assert "inference_backend" in d
    assert "serving_id" in d
    assert "pathway" in d


def test_all_statuses_valid():
    templates = load_handoff_templates(FIXTURE_PATH)
    for t in templates:
        assert t.handoff_status in ALLOWED_HANDOFF_STATUSES


def test_scores_in_range():
    templates = load_handoff_templates(FIXTURE_PATH)
    for t in templates:
        assert 0.0 <= t.score <= 1.0


def test_summary_template_count():
    summary = operator_handoff_summary(FIXTURE_PATH)
    assert summary["template_count"] == 4


def test_summary_approved_count():
    summary = operator_handoff_summary(FIXTURE_PATH)
    assert summary["approved_count"] == 1


def test_summary_pending_count():
    summary = operator_handoff_summary(FIXTURE_PATH)
    assert summary["pending_count"] == 1


def test_summary_rejected_count():
    summary = operator_handoff_summary(FIXTURE_PATH)
    assert summary["rejected_count"] == 1


def test_summary_draft_count():
    summary = operator_handoff_summary(FIXTURE_PATH)
    assert summary["draft_count"] == 1


def test_summary_by_pathway():
    summary = operator_handoff_summary(FIXTURE_PATH)
    bp = summary["by_pathway"]
    assert "candidate_review_packet" in bp
    assert "human_review_queue" in bp


def test_summary_by_model_id():
    summary = operator_handoff_summary(FIXTURE_PATH)
    bm = summary["by_model_id"]
    assert "mdl-001" in bm
    assert "mdl-002" in bm


def test_summary_schema_version():
    summary = operator_handoff_summary(FIXTURE_PATH)
    assert summary["schema_version"] == "operator_handoff_template_v1"


def test_summary_disclaimer():
    summary = operator_handoff_summary(FIXTURE_PATH)
    assert len(summary["disclaimer"]) > 20


def test_fixture_json_valid():
    data = json.loads(FIXTURE_PATH.read_text())
    assert "handoff_templates" in data
    assert len(data["handoff_templates"]) >= 4


def test_fixture_required_fields():
    data = json.loads(FIXTURE_PATH.read_text())
    required = {
        "handoff_id", "candidate_id", "model_id", "model_version",
        "inference_backend", "serving_id", "score", "pathway",
        "handoff_status", "operator_id", "created_utc",
    }
    for entry in data["handoff_templates"]:
        for field in required:
            assert field in entry, f"Missing {field} in {entry.get('handoff_id')}"
