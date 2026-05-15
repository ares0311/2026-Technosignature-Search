"""Tests for the operator weekly review template."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from techno_search.cli import main
from techno_search.weekly_review import (
    WEEKLY_REVIEW_DISCLAIMER,
    WEEKLY_REVIEW_SCHEMA_VERSION,
    build_weekly_review_template,
    write_weekly_review_template,
)


def _synthetic_digest(
    *,
    run_count: int = 3,
    reviewed_count: int = 2,
    needs_follow_up_count: int = 1,
    blocking_issue_total: int = 0,
    network_access_allowed_count: int = 0,
    external_submission_approved_count: int = 0,
) -> dict:
    return {
        "schema_version": "sqlite_weekly_digest_v1",
        "run_count": run_count,
        "reviewed_count": reviewed_count,
        "needs_follow_up_count": needs_follow_up_count,
        "blocking_issue_total": blocking_issue_total,
        "network_access_allowed_count": network_access_allowed_count,
        "external_submission_approved_count": external_submission_approved_count,
        "window_start_utc": "2026-05-08T00:00:00+00:00",
        "ok": network_access_allowed_count == 0 and external_submission_approved_count == 0,
    }


def _synthetic_ct_summary(
    *,
    reference_count: int = 4,
    multi_track_reference_count: int = 2,
    blocking_issue_total: int = 1,
) -> dict:
    return {
        "schema_version": "cross_track_references_v1",
        "reference_count": reference_count,
        "multi_track_reference_count": multi_track_reference_count,
        "blocking_issue_total": blocking_issue_total,
    }


def test_weekly_review_template_schema_version():
    template = build_weekly_review_template(
        digest=_synthetic_digest(),
        ct_summary=_synthetic_ct_summary(),
    )
    assert template.schema_version == WEEKLY_REVIEW_SCHEMA_VERSION


def test_weekly_review_template_disclaimer():
    template = build_weekly_review_template(
        digest=_synthetic_digest(),
        ct_summary=_synthetic_ct_summary(),
    )
    assert WEEKLY_REVIEW_DISCLAIMER in template.disclaimer
    d = template.as_dict()
    assert WEEKLY_REVIEW_DISCLAIMER in d["disclaimer"]


def test_weekly_review_template_network_zero_confirmed():
    template = build_weekly_review_template(
        digest=_synthetic_digest(network_access_allowed_count=0),
        ct_summary=_synthetic_ct_summary(),
    )
    assert template.network_access_confirmed_zero is True
    assert template.external_submission_confirmed_zero is True


def test_weekly_review_template_nonzero_network_detected():
    template = build_weekly_review_template(
        digest=_synthetic_digest(network_access_allowed_count=1),
        ct_summary=_synthetic_ct_summary(),
    )
    assert template.network_access_confirmed_zero is False


def test_weekly_review_template_nonzero_external_submission_detected():
    template = build_weekly_review_template(
        digest=_synthetic_digest(external_submission_approved_count=1),
        ct_summary=_synthetic_ct_summary(),
    )
    assert template.external_submission_confirmed_zero is False


def test_weekly_review_template_covers_all_three_sections():
    template = build_weekly_review_template(
        digest=_synthetic_digest(needs_follow_up_count=2, blocking_issue_total=1),
        ct_summary=_synthetic_ct_summary(blocking_issue_total=1),
    )
    d = template.as_dict()
    assert d["digest"]["run_count"] == 3
    assert d["cross_track_summary"]["reference_count"] == 4
    assert len(d["recommended_next_actions"]) >= 1


def test_weekly_review_template_markdown_contains_gates():
    template = build_weekly_review_template(
        digest=_synthetic_digest(),
        ct_summary=_synthetic_ct_summary(),
    )
    md = template.as_markdown()
    assert "Gate Confirmations" in md
    assert "confirmed zero" in md
    assert "Run Summary" in md
    assert "Cross-Track References" in md
    assert "Recommended Next Actions" in md
    assert "not a discovery claim" in md.lower() or "operational" in md.lower()


def test_weekly_review_template_operator_notes():
    template = build_weekly_review_template(
        digest=_synthetic_digest(),
        ct_summary=_synthetic_ct_summary(),
        operator_notes="Scheduled maintenance window this week.",
    )
    md = template.as_markdown()
    assert "Scheduled maintenance window" in md


def test_write_weekly_review_template(tmp_path):
    template = build_weekly_review_template(
        digest=_synthetic_digest(),
        ct_summary=_synthetic_ct_summary(),
        generated_at_utc="2026-05-15T00:00:00+00:00",
    )
    md_path, json_path = write_weekly_review_template(template, tmp_path)
    assert md_path.exists()
    assert json_path.exists()
    data = json.loads(json_path.read_text())
    assert data["schema_version"] == WEEKLY_REVIEW_SCHEMA_VERSION
    assert WEEKLY_REVIEW_DISCLAIMER in data["disclaimer"]


def test_cli_weekly_review_template_stdout(tmp_path):
    """CLI produces JSON with required gate fields when run against a temp SQLite db."""
    db_path = tmp_path / "test.sqlite3"
    out = StringIO()
    ret = main(
        ["weekly-review-template", "--db-path", str(db_path)],
        stdout=out,
    )
    assert ret == 0
    data = json.loads(out.getvalue())
    assert "schema_version" in data
    assert "network_access_confirmed_zero" in data
    assert "external_submission_confirmed_zero" in data
    assert WEEKLY_REVIEW_DISCLAIMER in data["disclaimer"]


def test_cli_weekly_review_template_output_dir(tmp_path):
    """CLI writes Markdown and JSON files when --output-dir is given."""
    db_path = tmp_path / "test.sqlite3"
    out_dir = tmp_path / "review"
    out = StringIO()
    ret = main(
        [
            "weekly-review-template",
            "--db-path",
            str(db_path),
            "--output-dir",
            str(out_dir),
        ],
        stdout=out,
    )
    assert ret == 0
    data = json.loads(out.getvalue())
    assert data["ok"] is True
    assert Path(data["markdown_path"]).exists()
    assert Path(data["json_path"]).exists()


def test_weekly_review_template_next_actions_include_validate():
    template = build_weekly_review_template(
        digest=_synthetic_digest(),
        ct_summary=_synthetic_ct_summary(),
    )
    all_actions = " ".join(template.recommended_next_actions)
    assert "validate-all" in all_actions
