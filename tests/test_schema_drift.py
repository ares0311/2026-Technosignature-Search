"""Tests for schema_drift module."""

from __future__ import annotations

import json

from techno_search.schema_drift import SCHEMA_DRIFT_DISCLAIMER, detect_schema_drift


def test_detect_schema_drift_returns_dict():
    result = detect_schema_drift()
    assert isinstance(result, dict)


def test_detect_schema_drift_ok_on_committed_schemas():
    result = detect_schema_drift()
    assert result["ok"] is True
    assert result["drift_count"] == 0


def test_detect_schema_drift_schema_count():
    result = detect_schema_drift()
    assert isinstance(result["schema_count"], int)
    assert result["schema_count"] >= 31


def test_detect_schema_drift_disclaimer():
    result = detect_schema_drift()
    assert SCHEMA_DRIFT_DISCLAIMER in result["disclaimer"]


def test_detect_schema_drift_drift_details_empty_when_ok():
    result = detect_schema_drift()
    if result["ok"]:
        assert result["drift_details"] == []


def test_detect_schema_drift_detects_missing_schema_key(tmp_path):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    bad_schema = schemas_dir / "bad.schema.json"
    bad_schema.write_text(json.dumps({
        "title": "Bad schema",
        "type": "object",
        "required": ["foo"],
    }))
    result = detect_schema_drift(schemas_dir)
    assert result["drift_count"] >= 1
    assert result["ok"] is False


def test_detect_schema_drift_detects_non_object_type(tmp_path):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    bad_schema = schemas_dir / "bad2.schema.json"
    bad_schema.write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Bad schema",
        "type": "array",
        "required": ["foo"],
    }))
    result = detect_schema_drift(schemas_dir)
    assert result["drift_count"] >= 1


def test_detect_schema_drift_detects_empty_required(tmp_path):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    bad_schema = schemas_dir / "bad3.schema.json"
    bad_schema.write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Bad schema",
        "type": "object",
        "required": [],
    }))
    result = detect_schema_drift(schemas_dir)
    assert result["drift_count"] >= 1
