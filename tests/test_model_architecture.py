"""Tests for model architecture scaffold module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.model_architecture import (
    ALLOWED_ARCHITECTURE_KINDS,
    ALLOWED_ARCHITECTURE_STATUSES,
    MODEL_ARCHITECTURE_DISCLAIMER,
    MODEL_ARCHITECTURE_SCHEMA_VERSION,
    ModelArchitectureEntry,
    load_architecture_entries,
    model_architecture_summary,
)


def test_load_entries_returns_list():
    result = load_architecture_entries()
    assert isinstance(result, list)


def test_load_entries_returns_dataclass_instances():
    result = load_architecture_entries()
    assert all(isinstance(e, ModelArchitectureEntry) for e in result)


def test_fixture_has_five_entries():
    result = load_architecture_entries()
    assert len(result) == 5


def test_all_five_kinds_present():
    result = load_architecture_entries()
    kinds = {e.kind for e in result}
    assert kinds == ALLOWED_ARCHITECTURE_KINDS


def test_all_entries_are_stubs():
    result = load_architecture_entries()
    for e in result:
        assert e.status in ALLOWED_ARCHITECTURE_STATUSES


def test_no_weights_available():
    result = load_architecture_entries()
    for e in result:
        assert e.weights_available is False


def test_all_have_layer_descriptor():
    result = load_architecture_entries()
    for e in result:
        assert len(e.layer_descriptor) > 0


def test_all_have_input_feature_schema_version():
    result = load_architecture_entries()
    for e in result:
        assert e.input_feature_schema_version.startswith("candidate_feature_vector")


def test_as_dict_returns_expected_keys():
    e = load_architecture_entries()[0]
    d = e.as_dict()
    assert "arch_id" in d
    assert "kind" in d
    assert "label" in d
    assert "track" in d
    assert "status" in d
    assert "weights_available" in d
    assert "layer_descriptor" in d


def test_summary_returns_dict():
    result = model_architecture_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = model_architecture_summary()
    assert result["schema_version"] == MODEL_ARCHITECTURE_SCHEMA_VERSION


def test_summary_disclaimer():
    result = model_architecture_summary()
    assert result["disclaimer"] == MODEL_ARCHITECTURE_DISCLAIMER
    assert "no weights" in result["disclaimer"].lower()


def test_summary_architecture_count():
    result = model_architecture_summary()
    assert result["architecture_count"] == 5


def test_summary_weights_available_count_zero():
    result = model_architecture_summary()
    assert result["weights_available_count"] == 0


def test_summary_by_kind_covers_all_five():
    result = model_architecture_summary()
    assert set(result["by_kind"]) == ALLOWED_ARCHITECTURE_KINDS


def test_summary_by_status_all_stub():
    result = model_architecture_summary()
    assert "stub" in result["by_status"]
    assert result["by_status"]["stub"] == 5


def test_summary_kinds_defined_sorted():
    result = model_architecture_summary()
    assert result["kinds_defined"] == sorted(ALLOWED_ARCHITECTURE_KINDS)


def test_cli_model_architecture_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "model-architecture-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_model_architecture_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "model-architecture-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "architecture_count" in data
    assert "weights_available_count" in data
    assert "kinds_defined" in data
