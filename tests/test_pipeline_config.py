from __future__ import annotations

import json
from pathlib import Path

from techno_search.pipeline_config import (
    ALLOWED_PIPELINE_STATUSES,
    PIPELINE_CONFIG_DISCLAIMER,
    PIPELINE_CONFIG_SCHEMA_VERSION,
    PipelineConfigRecord,
    load_pipeline_configs,
    pipeline_config_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pipeline_configs.json"


def test_schema_version():
    assert PIPELINE_CONFIG_SCHEMA_VERSION == "pipeline_config_v1"


def test_disclaimer_present():
    assert len(PIPELINE_CONFIG_DISCLAIMER) > 20
    assert "scheduling" in PIPELINE_CONFIG_DISCLAIMER.lower()


def test_disclaimer_no_external_submission():
    assert "does not authorize external submission" in PIPELINE_CONFIG_DISCLAIMER.lower()


def test_allowed_statuses():
    assert "active" in ALLOWED_PIPELINE_STATUSES
    assert "staging" in ALLOWED_PIPELINE_STATUSES
    assert "deprecated" in ALLOWED_PIPELINE_STATUSES
    assert "stub" in ALLOWED_PIPELINE_STATUSES


def test_load_returns_list():
    records = load_pipeline_configs(FIXTURE_PATH)
    assert isinstance(records, list)


def test_load_count():
    records = load_pipeline_configs(FIXTURE_PATH)
    assert len(records) == 4


def test_record_fields():
    records = load_pipeline_configs(FIXTURE_PATH)
    r = records[0]
    assert isinstance(r, PipelineConfigRecord)
    assert r.config_id == "pcfg-001"
    assert r.pipeline_status == "active"
    assert isinstance(r.active_tracks, list)
    assert len(r.active_tracks) == 3


def test_record_as_dict():
    records = load_pipeline_configs(FIXTURE_PATH)
    d = records[0].as_dict()
    assert "config_id" in d
    assert "scoring_config_version" in d
    assert "inference_backend" in d
    assert "active_tracks" in d


def test_all_statuses_valid():
    records = load_pipeline_configs(FIXTURE_PATH)
    for r in records:
        assert r.pipeline_status in ALLOWED_PIPELINE_STATUSES


def test_summary_config_count():
    summary = pipeline_config_summary(FIXTURE_PATH)
    assert summary["config_count"] == 4


def test_summary_active_count():
    summary = pipeline_config_summary(FIXTURE_PATH)
    assert summary["active_count"] == 1


def test_summary_active_config_id():
    summary = pipeline_config_summary(FIXTURE_PATH)
    assert summary["active_config_id"] == "pcfg-001"


def test_summary_active_model_id():
    summary = pipeline_config_summary(FIXTURE_PATH)
    assert summary["active_model_id"] == "mdl-001"


def test_summary_by_status():
    summary = pipeline_config_summary(FIXTURE_PATH)
    bs = summary["by_status"]
    assert bs["active"] == 1
    assert bs["staging"] == 1
    assert bs["stub"] == 1
    assert bs["deprecated"] == 1


def test_summary_by_backend():
    summary = pipeline_config_summary(FIXTURE_PATH)
    bb = summary["by_backend"]
    assert "baseline_rule" in bb
    assert "pytorch_stub" in bb


def test_summary_schema_version():
    summary = pipeline_config_summary(FIXTURE_PATH)
    assert summary["schema_version"] == "pipeline_config_v1"


def test_summary_disclaimer():
    summary = pipeline_config_summary(FIXTURE_PATH)
    assert len(summary["disclaimer"]) > 20


def test_fixture_json_valid():
    data = json.loads(FIXTURE_PATH.read_text())
    assert "pipeline_configs" in data
    assert len(data["pipeline_configs"]) >= 4


def test_fixture_required_fields():
    data = json.loads(FIXTURE_PATH.read_text())
    required = {
        "config_id", "label", "scoring_config_version", "serving_id",
        "model_id", "inference_backend", "active_tracks",
        "pipeline_status", "created_utc",
    }
    for entry in data["pipeline_configs"]:
        for field in required:
            assert field in entry, f"Missing {field} in {entry.get('config_id')}"
