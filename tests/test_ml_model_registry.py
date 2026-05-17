"""Tests for ML model registry module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.ml_model_registry import (
    ALLOWED_MODEL_KINDS,
    ALLOWED_MODEL_STATUSES,
    ML_MODEL_REGISTRY_DISCLAIMER,
    ML_MODEL_REGISTRY_SCHEMA_VERSION,
    MLModelRegistryEntry,
    load_model_registry_entries,
    model_registry_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ml_model_registry.json"


def test_load_entries_returns_list():
    result = load_model_registry_entries()
    assert isinstance(result, list)


def test_load_entries_returns_dataclass_instances():
    result = load_model_registry_entries()
    assert all(isinstance(e, MLModelRegistryEntry) for e in result)


def test_fixture_has_three_entries():
    result = load_model_registry_entries()
    assert len(result) == 3


def test_model_kinds_are_allowed():
    result = load_model_registry_entries()
    for e in result:
        assert e.model_kind in ALLOWED_MODEL_KINDS


def test_model_statuses_are_allowed():
    result = load_model_registry_entries()
    for e in result:
        assert e.status in ALLOWED_MODEL_STATUSES


def test_is_above_baseline_is_bool():
    result = load_model_registry_entries()
    for e in result:
        assert isinstance(e.is_above_baseline, bool)


def test_accuracies_are_floats_in_range():
    result = load_model_registry_entries()
    for e in result:
        assert isinstance(e.baseline_accuracy, float)
        assert isinstance(e.model_accuracy, float)
        assert 0.0 <= e.baseline_accuracy <= 1.0
        assert 0.0 <= e.model_accuracy <= 1.0


def test_as_dict_returns_expected_keys():
    e = load_model_registry_entries()[0]
    d = e.as_dict()
    assert "model_id" in d
    assert "model_kind" in d
    assert "status" in d
    assert "is_above_baseline" in d
    assert "baseline_accuracy" in d
    assert "model_accuracy" in d


def test_summary_returns_dict():
    result = model_registry_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = model_registry_summary()
    assert result["schema_version"] == ML_MODEL_REGISTRY_SCHEMA_VERSION


def test_summary_disclaimer():
    result = model_registry_summary()
    assert result["disclaimer"] == ML_MODEL_REGISTRY_DISCLAIMER
    assert "provenance records" in result["disclaimer"]


def test_summary_registry_count():
    result = model_registry_summary()
    assert result["registry_count"] == 3


def test_summary_above_baseline_count():
    result = model_registry_summary()
    # mdl-001 and mdl-002 are above baseline
    assert result["above_baseline_count"] == 2


def test_summary_below_baseline_count():
    result = model_registry_summary()
    # mdl-003 is below baseline
    assert result["below_baseline_count"] == 1


def test_summary_validated_count():
    result = model_registry_summary()
    assert result["validated_count"] == 1


def test_summary_experimental_count():
    result = model_registry_summary()
    assert result["experimental_count"] == 1


def test_allowed_model_kinds_frozenset():
    assert "cnn_radio" in ALLOWED_MODEL_KINDS
    assert "transformer_radio" in ALLOWED_MODEL_KINDS
    assert "hybrid_rule_learned" in ALLOWED_MODEL_KINDS
    assert "self_supervised" in ALLOWED_MODEL_KINDS
    assert "foundation_embedding" in ALLOWED_MODEL_KINDS
    assert "baseline_rule_based" in ALLOWED_MODEL_KINDS


def test_allowed_model_statuses_frozenset():
    assert "experimental" in ALLOWED_MODEL_STATUSES
    assert "validated" in ALLOWED_MODEL_STATUSES
    assert "deprecated" in ALLOWED_MODEL_STATUSES
    assert "pending_review" in ALLOWED_MODEL_STATUSES


def test_cli_model_registry_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "model-registry-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_model_registry_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "model-registry-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "registry_count" in data
    assert "above_baseline_count" in data
    assert "below_baseline_count" in data


def test_cli_model_registry_with_fixture_path():
    result = subprocess.run(
        [
            sys.executable, "-m", "techno_search.cli",
            "model-registry-summary",
            "--fixture-path", str(FIXTURE_PATH),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["registry_count"] == 3
