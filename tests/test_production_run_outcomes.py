from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from techno_search.production_run_outcomes import (
    PRODUCTION_FOLLOW_UPS_SCHEMA_VERSION,
    PRODUCTION_NON_DETECTIONS_SCHEMA_VERSION,
    PRODUCTION_OUTCOME_DISCLAIMER,
    PRODUCTION_RUN_MANIFEST_SCHEMA_VERSION,
    build_production_outcomes,
    make_production_run_id,
    production_run_file,
    production_run_list,
    production_run_summary,
    write_production_outcomes,
)
from techno_search.scan_summary import scan_summary_from_batch_dir

RUN_ID = "RUN-2026-06-18_201325Z-A7K4-prod-scan"


def _candidate(
    candidate_id: str,
    pathway: str,
    *,
    target_name: str = "HIP99427",
    score: float = 0.5,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "target_name": target_name,
        "track": "radio",
        "recommended_pathway": pathway,
        "score": score,
        "frequency_hz": 1420000000.0,
        "snr": 44.0,
    }


def _write_result_pair(
    base, target_name: str, candidate_id: str, pathway: str, score: float
) -> None:
    target_dir = base / target_name
    target_dir.mkdir(parents=True)
    candidate_path = target_dir / f"{candidate_id}.json"
    candidate_path.write_text(
        json.dumps(
            {
                "candidate_id": candidate_id,
                "recommended_pathway": pathway,
                "features": {
                    "frequency_hz": 1420000000.0,
                    "snr": 44.0,
                    "drift_rate_hz_per_sec": 0.1,
                },
                "scores": {"followup_value": score},
                "track": "radio",
            }
        ),
        encoding="utf-8",
    )
    (target_dir / f"{candidate_id}.manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": candidate_id,
                "recommended_pathway": pathway,
                "json_path": candidate_path.name,
            }
        ),
        encoding="utf-8",
    )


def test_make_production_run_id_is_human_readable_and_deterministic() -> None:
    run_id = make_production_run_id(
        now=datetime(2026, 6, 18, 20, 13, 25, tzinfo=UTC),
        token="a7k4",
    )

    assert run_id == RUN_ID


def test_build_production_outcomes_splits_non_detections_and_follow_ups() -> None:
    outcomes = build_production_outcomes(
        [
            _candidate("cand-neg", "known_object_annotation", score=0.1),
            _candidate("cand-fu", "candidate_review_packet", score=0.9),
        ],
        run_id=RUN_ID,
        started_at_utc="2026-06-18T20:13:25Z",
        completed_at_utc="2026-06-18T20:13:30Z",
    )

    manifest = outcomes["manifest"]
    non_detections = outcomes["non_detections"]
    follow_ups = outcomes["follow_ups"]
    assert manifest["schema_version"] == PRODUCTION_RUN_MANIFEST_SCHEMA_VERSION
    assert non_detections["schema_version"] == PRODUCTION_NON_DETECTIONS_SCHEMA_VERSION
    assert follow_ups["schema_version"] == PRODUCTION_FOLLOW_UPS_SCHEMA_VERSION
    assert manifest["non_detection_count"] == 1
    assert manifest["follow_up_count"] == 1
    assert non_detections["entries"][0]["non_detection_id"] == (
        "NEG-2026-06-18_201325Z-A7K4-001"
    )
    assert follow_ups["entries"][0]["follow_up_id"] == (
        "FU-2026-06-18_201325Z-A7K4-001"
    )
    assert manifest["detection_claimed"] is False
    assert follow_ups["external_submission_allowed"] is False
    assert "detection" in PRODUCTION_OUTCOME_DISCLAIMER


def test_build_production_outcomes_records_scan_level_negative_result() -> None:
    outcomes = build_production_outcomes(
        [_candidate("cand-neg", "known_object_annotation", score=0.1)],
        run_id=RUN_ID,
        started_at_utc="2026-06-18T20:13:25Z",
        completed_at_utc="2026-06-18T20:13:30Z",
    )

    assert outcomes["manifest"]["scan_level_negative_result"]["applies"] is True
    assert outcomes["non_detections"]["scan_level_negative_result"]["reason"] == (
        "no_follow_up_pathway_candidates"
    )


def test_write_and_read_production_outcomes(tmp_path) -> None:
    results_dir = tmp_path / "results"
    run_dir = results_dir / "scans" / RUN_ID
    _write_result_pair(results_dir, "HIP99427", "cand-neg", "known_object_annotation", 0.1)
    _write_result_pair(results_dir, "HIP100670", "cand-fu", "candidate_review_packet", 0.9)

    written = write_production_outcomes(
        results_dir=results_dir,
        run_dir=run_dir,
        run_id=RUN_ID,
        started_at_utc="2026-06-18T20:13:25Z",
        completed_at_utc="2026-06-18T20:13:30Z",
    )

    assert written["candidate_count"] == 2
    assert (run_dir / f"{RUN_ID}_manifest.json").exists()
    assert (run_dir / f"{RUN_ID}_non_detections.json").exists()
    assert (run_dir / f"{RUN_ID}_follow_ups.json").exists()
    assert production_run_summary(run_dir)["follow_up_count"] == 1
    assert production_run_file(run_dir, "follow_ups")["entry_count"] == 1
    assert production_run_file(run_dir, "non_detections")["entry_count"] == 1
    assert production_run_list(results_dir / "scans")["run_count"] == 1


def test_scan_summary_ignores_production_run_manifest(tmp_path) -> None:
    results_dir = tmp_path / "results"
    run_dir = results_dir / "scans" / RUN_ID
    run_dir.mkdir(parents=True)
    _write_result_pair(results_dir, "HIP99427", "cand-neg", "known_object_annotation", 0.1)
    (run_dir / f"{RUN_ID}_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": PRODUCTION_RUN_MANIFEST_SCHEMA_VERSION,
                "artifact_kind": "production_run_manifest",
                "run_id": RUN_ID,
            }
        ),
        encoding="utf-8",
    )

    summary = scan_summary_from_batch_dir(results_dir)

    assert summary["total_candidates"] == 1


def test_invalid_run_id_token_rejected() -> None:
    with pytest.raises(ValueError):
        make_production_run_id(token="toolong")
