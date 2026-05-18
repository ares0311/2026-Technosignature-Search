"""Tests for model serving scaffold module."""

from __future__ import annotations

import json
import subprocess
import sys

from techno_search.model_serving import (
    ALLOWED_INFERENCE_BACKENDS,
    ALLOWED_SERVING_STATUSES,
    MODEL_SERVING_DISCLAIMER,
    MODEL_SERVING_SCHEMA_VERSION,
    ModelServingRecord,
    load_serving_records,
    model_serving_summary,
)


def test_load_records_returns_list():
    result = load_serving_records()
    assert isinstance(result, list)


def test_load_records_returns_dataclass_instances():
    result = load_serving_records()
    assert all(isinstance(r, ModelServingRecord) for r in result)


def test_fixture_has_four_records():
    result = load_serving_records()
    assert len(result) == 4


def test_all_statuses_valid():
    result = load_serving_records()
    for r in result:
        assert r.serving_status in ALLOWED_SERVING_STATUSES


def test_all_backends_valid():
    result = load_serving_records()
    for r in result:
        assert r.inference_backend in ALLOWED_INFERENCE_BACKENDS


def test_at_least_one_active():
    result = load_serving_records()
    assert any(r.serving_status == "active" for r in result)


def test_at_least_one_stub():
    result = load_serving_records()
    assert any(r.serving_status == "stub" for r in result)


def test_stub_does_not_beat_baseline():
    result = load_serving_records()
    for r in result:
        if r.serving_status == "stub":
            assert r.beats_baseline is False


def test_inference_provenance_tag_non_empty():
    result = load_serving_records()
    for r in result:
        assert len(r.inference_provenance_tag) > 0


def test_as_dict_returns_expected_keys():
    r = load_serving_records()[0]
    d = r.as_dict()
    assert "serving_id" in d
    assert "model_id" in d
    assert "inference_backend" in d
    assert "serving_status" in d
    assert "beats_baseline" in d
    assert "inference_provenance_tag" in d


def test_summary_returns_dict():
    result = model_serving_summary()
    assert isinstance(result, dict)


def test_summary_schema_version():
    result = model_serving_summary()
    assert result["schema_version"] == MODEL_SERVING_SCHEMA_VERSION


def test_summary_disclaimer():
    result = model_serving_summary()
    assert result["disclaimer"] == MODEL_SERVING_DISCLAIMER
    assert "no live model weights" in result["disclaimer"].lower()


def test_summary_record_count():
    result = model_serving_summary()
    assert result["record_count"] == 4


def test_summary_active_count():
    result = model_serving_summary()
    assert result["active_count"] == 1


def test_summary_stub_count():
    result = model_serving_summary()
    assert result["stub_count"] == 1


def test_summary_active_model_ids():
    result = model_serving_summary()
    assert "mdl-001" in result["active_model_ids"]


def test_summary_by_status_keys():
    result = model_serving_summary()
    assert "active" in result["by_status"]
    assert "stub" in result["by_status"]
    assert "retired" in result["by_status"]


def test_cli_model_serving_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "model-serving-summary"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_model_serving_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "model-serving-summary"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert "record_count" in data
    assert "active_count" in data
    assert "by_status" in data
