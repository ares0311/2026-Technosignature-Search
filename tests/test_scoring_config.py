"""Tests for scoring configuration summary and route coverage."""

from __future__ import annotations

import json
import subprocess
import sys


def test_scoring_config_summary_keys() -> None:
    from techno_search.scoring_config import scoring_config_summary

    result = scoring_config_summary()
    assert "schema_version" in result
    assert "disclaimer" in result
    assert "threshold_count" in result
    assert "pathway_thresholds" in result
    assert "local_performance_defaults" in result


def test_scoring_config_summary_schema_version() -> None:
    from techno_search.scoring_config import (
        SCORING_CONFIG_SCHEMA_VERSION,
        scoring_config_summary,
    )

    result = scoring_config_summary()
    assert result["schema_version"] == SCORING_CONFIG_SCHEMA_VERSION


def test_scoring_config_summary_disclaimer() -> None:
    from techno_search.scoring_config import (
        SCORING_CONFIG_DISCLAIMER,
        scoring_config_summary,
    )

    result = scoring_config_summary()
    assert result["disclaimer"] == SCORING_CONFIG_DISCLAIMER
    assert "synthetic" in str(result["disclaimer"]).lower()


def test_scoring_config_threshold_count_positive() -> None:
    from techno_search.scoring_config import scoring_config_summary

    result = scoring_config_summary()
    assert isinstance(result["threshold_count"], int)
    assert result["threshold_count"] >= 1


def test_scoring_config_thresholds_are_floats() -> None:
    from techno_search.scoring_config import scoring_config_summary

    result = scoring_config_summary()
    thresholds = result["pathway_thresholds"]
    assert isinstance(thresholds, dict)
    for key, val in thresholds.items():
        assert isinstance(val, float), f"threshold {key} is not float: {val}"


def test_scoring_config_worker_defaults_positive() -> None:
    from techno_search.scoring_config import scoring_config_summary

    result = scoring_config_summary()
    assert isinstance(result["cpu_heavy_workers"], int)
    assert result["cpu_heavy_workers"] >= 1
    assert isinstance(result["memory_budget_gb"], int)
    assert result["memory_budget_gb"] >= 1


def test_scoring_config_cli_exits_zero() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "scoring-config-summary"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    parsed = json.loads(proc.stdout)
    assert "threshold_count" in parsed
    assert "disclaimer" in parsed


def test_scoring_config_schema_in_schema_paths() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "schema-paths"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    paths = json.loads(proc.stdout)
    assert "scoring_config_summary" in paths


def test_scoring_config_schema_file_exists() -> None:
    from techno_search.cli import default_project_root

    schema_path = default_project_root() / "schemas" / "scoring_config_summary.schema.json"
    assert schema_path.exists(), f"Missing schema: {schema_path}"
    with schema_path.open() as f:
        schema = json.load(f)
    assert schema.get("title") == "ScoringConfigSummary"
    assert "schema_version" in schema.get("required", [])


def test_route_coverage_summary_keys() -> None:
    from techno_search.baseline_eval import route_coverage_summary

    result = route_coverage_summary()
    assert "total_pathway_values" in result
    assert "covered_pathway_count" in result
    assert "uncovered_pathway_count" in result
    assert "covered_pathways" in result
    assert "by_pathway_case_count" in result
    assert "full_coverage" in result


def test_route_coverage_summary_pathway_counts() -> None:
    from techno_search.baseline_eval import route_coverage_summary
    from techno_search.schemas import Pathway

    result = route_coverage_summary()
    assert result["total_pathway_values"] == len(list(Pathway))
    assert isinstance(result["covered_pathway_count"], int)
    assert result["covered_pathway_count"] == len(list(Pathway))
    assert result["uncovered_pathway_count"] == 0
    assert result["uncovered_pathways"] == []
    assert result["full_coverage"] is True


def test_route_coverage_summary_covered_pathways_are_valid() -> None:
    from techno_search.baseline_eval import route_coverage_summary
    from techno_search.schemas import Pathway

    result = route_coverage_summary()
    valid_pathways = {p.value for p in Pathway}
    assert "external_followup_candidate" in result["covered_pathways"]
    for pw in result["covered_pathways"]:
        assert pw in valid_pathways, f"Unknown pathway in coverage: {pw}"


def test_route_coverage_cli_exits_zero() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "route-coverage-summary"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    parsed = json.loads(proc.stdout)
    assert "covered_pathway_count" in parsed
    assert "disclaimer" in parsed
