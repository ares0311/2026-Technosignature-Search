from __future__ import annotations

import json
from pathlib import Path

from techno_search.project_status_consistency import (
    load_project_status_expectations,
    project_status_consistency_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "project_status_consistency.json"


def _write_expected(path: Path, *, schema_count: int = 2) -> Path:
    expected_path = path / "expected.json"
    expected_path.write_text(
        json.dumps(
            {
                "schema_version": "project_status_consistency_v1",
                "expected_status": {
                    "latest_milestone_number": 33,
                    "latest_milestone_label": (
                        "Production Readiness Status Consistency Gates"
                    ),
                    "latest_decision_number": 80,
                    "schema_count": schema_count,
                    "require_zero_real_data_authorization": True,
                    "project_status_completed_phrase": (
                        "Project status consistency gates added"
                    ),
                },
            }
        ),
        encoding="utf-8",
    )
    return expected_path


def _write_project(
    path: Path,
    *,
    production_milestone: int = 33,
    schema_count: int = 2,
    latest_milestone: int = 33,
    latest_decision: int = 80,
) -> None:
    docs = path / "docs"
    schemas = path / "schemas"
    docs.mkdir()
    schemas.mkdir()
    (docs / "ROADMAP.md").write_text(
        f"# Milestone {latest_milestone} — Production Readiness Status Consistency Gates\n",
        encoding="utf-8",
    )
    (docs / "DECISIONS.md").write_text(
        f"# DECISION-{latest_decision:03d}: Status Consistency\n",
        encoding="utf-8",
    )
    (docs / "PRODUCTION_READINESS.md").write_text(
        "\n".join(
            [
                "# Production Readiness Assessment",
                "",
                (
                    f"**Current milestone:** {production_milestone} "
                    "(Production Readiness Status Consistency Gates)"
                ),
                "",
                "## What Is Complete",
                "",
                "| Capability | Status |",
                "|---|---|",
                f"| {schema_count} JSON schema artifacts | Complete |",
            ]
        ),
        encoding="utf-8",
    )
    (docs / "PROJECT_STATUS.md").write_text(
        "Project status consistency gates added\n",
        encoding="utf-8",
    )
    for index in range(schema_count):
        (schemas / f"schema_{index}.schema.json").write_text("{}", encoding="utf-8")


def test_load_project_status_expectations_fixture() -> None:
    expected = load_project_status_expectations(FIXTURE_PATH)

    assert expected["latest_milestone_number"] == 65
    assert expected["latest_decision_number"] == 112
    assert expected["schema_count"] == 182


def test_project_status_consistency_custom_project_passes(tmp_path: Path) -> None:
    expected_path = _write_expected(tmp_path)
    _write_project(tmp_path)

    summary = project_status_consistency_summary(expected_path, tmp_path)

    assert summary["ok"] is True
    assert summary["issue_count"] == 0
    assert summary["roadmap_latest_milestone"] == 33
    assert summary["actual_schema_count"] == 2
    assert summary["rfi_database_admission_real_data_authorized_count"] == 0
    assert summary["curated_dataset_admission_real_data_authorized_count"] == 0


def test_project_status_consistency_detects_stale_production_milestone(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    _write_project(tmp_path, production_milestone=31)

    summary = project_status_consistency_summary(expected_path, tmp_path)

    assert summary["ok"] is False
    assert any("current milestone 31 != expected 33" in issue for issue in summary["issues"])


def test_project_status_consistency_detects_schema_count_mismatch(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path, schema_count=3)
    _write_project(tmp_path, schema_count=2)

    summary = project_status_consistency_summary(expected_path, tmp_path)

    assert summary["ok"] is False
    assert any("schema artifact count 2 != expected 3" in issue for issue in summary["issues"])
    assert any("schema count 2 != expected 3" in issue for issue in summary["issues"])


def test_project_status_consistency_default_project_passes() -> None:
    summary = project_status_consistency_summary()

    assert summary["schema_version"] == "project_status_consistency_v1"
    assert summary["ok"] is True
    assert summary["expected_latest_milestone"] == 65
    assert summary["expected_latest_decision"] == 112
    assert summary["expected_schema_count"] == 182
