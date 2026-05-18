from __future__ import annotations

import json
from pathlib import Path

from techno_search.pipeline_telemetry import (
    ALLOWED_TELEMETRY_STAGES,
    PIPELINE_TELEMETRY_DISCLAIMER,
    PIPELINE_TELEMETRY_SCHEMA_VERSION,
    PipelineTelemetryEntry,
    load_telemetry_entries,
    pipeline_telemetry_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pipeline_telemetry.json"


def test_schema_version():
    assert PIPELINE_TELEMETRY_SCHEMA_VERSION == "pipeline_telemetry_v1"


def test_disclaimer_present():
    assert len(PIPELINE_TELEMETRY_DISCLAIMER) > 20
    assert "provenance" in PIPELINE_TELEMETRY_DISCLAIMER.lower()


def test_disclaimer_no_authorization():
    lower = PIPELINE_TELEMETRY_DISCLAIMER.lower()
    assert "does not authorize external submission" in lower


def test_allowed_stages():
    assert "scoring" in ALLOWED_TELEMETRY_STAGES
    assert "model_serving" in ALLOWED_TELEMETRY_STAGES
    assert "audit_log" in ALLOWED_TELEMETRY_STAGES
    assert "rescore" in ALLOWED_TELEMETRY_STAGES
    assert "handoff" in ALLOWED_TELEMETRY_STAGES
    assert "submission_check" in ALLOWED_TELEMETRY_STAGES


def test_load_returns_list():
    entries = load_telemetry_entries(FIXTURE_PATH)
    assert isinstance(entries, list)


def test_load_count():
    entries = load_telemetry_entries(FIXTURE_PATH)
    assert len(entries) == 6


def test_entry_fields():
    entries = load_telemetry_entries(FIXTURE_PATH)
    e = entries[0]
    assert isinstance(e, PipelineTelemetryEntry)
    assert e.entry_id == "tel-001"
    assert e.stage == "scoring"
    assert isinstance(e.latency_ms, float)
    assert e.success is True
    assert e.error_message is None


def test_entry_as_dict():
    entries = load_telemetry_entries(FIXTURE_PATH)
    d = entries[0].as_dict()
    assert "entry_id" in d
    assert "candidate_id" in d
    assert "stage" in d
    assert "latency_ms" in d
    assert "success" in d
    assert "error_message" in d


def test_all_stages_covered():
    entries = load_telemetry_entries(FIXTURE_PATH)
    covered = {e.stage for e in entries}
    assert "scoring" in covered
    assert "model_serving" in covered
    assert "audit_log" in covered
    assert "rescore" in covered
    assert "handoff" in covered
    assert "submission_check" in covered


def test_all_stages_valid():
    entries = load_telemetry_entries(FIXTURE_PATH)
    for e in entries:
        assert e.stage in ALLOWED_TELEMETRY_STAGES


def test_all_successful():
    entries = load_telemetry_entries(FIXTURE_PATH)
    for e in entries:
        assert e.success is True


def test_positive_latencies():
    entries = load_telemetry_entries(FIXTURE_PATH)
    for e in entries:
        assert e.latency_ms > 0


def test_summary_entry_count():
    summary = pipeline_telemetry_summary(FIXTURE_PATH)
    assert summary["entry_count"] == 6


def test_summary_success_count():
    summary = pipeline_telemetry_summary(FIXTURE_PATH)
    assert summary["success_count"] == 6
    assert summary["failure_count"] == 0


def test_summary_stages_covered():
    summary = pipeline_telemetry_summary(FIXTURE_PATH)
    stages = summary["stages_covered"]
    assert "scoring" in stages
    assert "submission_check" in stages


def test_summary_mean_latency():
    summary = pipeline_telemetry_summary(FIXTURE_PATH)
    assert summary["mean_latency_ms"] > 0


def test_summary_max_latency():
    summary = pipeline_telemetry_summary(FIXTURE_PATH)
    assert summary["max_latency_ms"] >= summary["mean_latency_ms"]


def test_summary_by_stage():
    summary = pipeline_telemetry_summary(FIXTURE_PATH)
    by_stage = summary["by_stage"]
    for stage in ALLOWED_TELEMETRY_STAGES:
        assert stage in by_stage


def test_summary_disclaimer():
    summary = pipeline_telemetry_summary(FIXTURE_PATH)
    assert len(summary["disclaimer"]) > 20


def test_fixture_json_valid():
    data = json.loads(FIXTURE_PATH.read_text())
    assert "pipeline_telemetry_entries" in data
    assert len(data["pipeline_telemetry_entries"]) >= 6


def test_fixture_required_fields():
    data = json.loads(FIXTURE_PATH.read_text())
    required = {
        "entry_id", "candidate_id", "stage", "latency_ms", "success", "recorded_utc",
    }
    for entry in data["pipeline_telemetry_entries"]:
        for f in required:
            assert f in entry, f"Missing {f} in {entry.get('entry_id')}"
