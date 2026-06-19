from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from techno_search.production_scan import (
    ProductionConsole,
    production_diagnostics,
    run_production_scan,
)

RUN_ID = "RUN-2026-06-18_201325Z-A7K4-prod-scan"


def _write_result_pair(
    base: Path,
    target_name: str,
    candidate_id: str,
    pathway: str,
    score: float,
    *,
    snr: float = 55.0,
) -> None:
    target_dir = base / target_name
    target_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = target_dir / f"{candidate_id}.json"
    candidate_path.write_text(
        json.dumps(
            {
                "candidate_id": candidate_id,
                "recommended_pathway": pathway,
                "features": {
                    "frequency_hz": 1420000000.0,
                    "snr": snr,
                    "drift_rate_hz_per_sec": 0.2,
                    "multi_epoch_persistence_score": 0.4,
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


def test_plain_console_prints_compact_target_rows() -> None:
    stdout = StringIO()
    console = ProductionConsole(stdout, use_rich=False)

    console.print_target_rows(
        [
            {
                "index_id": "FU-2026-06-18_201325Z-A7K4-001",
                "target_name": "HIP99427",
                "target_kind": "stellar target",
                "follow_up_required": True,
                "composite_score": 0.91,
                "top_pathway": "candidate_review_packet",
            }
        ]
    )

    rendered = stdout.getvalue()
    assert "Completed target evaluations:" in rendered
    assert "HIP99427 | stellar target | follow-up=yes | score=0.910" in rendered
    assert "candidate_review_packet" in rendered


def test_run_production_scan_writes_artifacts_and_compact_output(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    scans_dir = tmp_path / "scans"
    _write_result_pair(
        results_dir,
        "HIP99427",
        "candidate",
        "candidate_review_packet",
        0.9,
    )
    stdout = StringIO()

    result = run_production_scan(
        results_dir=results_dir,
        scans_dir=scans_dir,
        stdout=stdout,
        run_id=RUN_ID,
        use_rich=False,
        validate_func=lambda: {"ok": True},
        dashboard_func=lambda: {"needs_attention": False},
    )

    run_dir = scans_dir / RUN_ID
    rendered = stdout.getvalue()
    assert result.target_count == 1
    assert result.follow_up_required_count == 1
    assert "Production scan RUN-2026-06-18_201325Z-A7K4-prod-scan" in rendered
    assert "OK validate-all" in rendered
    assert "HIP99427 | stellar target | follow-up=yes | score=0.900" in rendered
    assert (run_dir / "validate_all.json").exists()
    assert (run_dir / f"{RUN_ID}_scan_summary.json").exists()
    assert (run_dir / "cross_target_rfi.json").exists()
    assert (run_dir / "escalations" / "summary.json").exists()
    assert (run_dir / f"{RUN_ID}_review_dashboard.json").exists()
    assert (run_dir / f"{RUN_ID}_target_status.json").exists()
    assert (run_dir / f"{RUN_ID}_terminal_summary.json").exists()
    target_status = json.loads(
        (run_dir / f"{RUN_ID}_target_status.json").read_text(encoding="utf-8")
    )
    assert target_status["entries"][0]["index_id"] == "FU-2026-06-18_201325Z-A7K4-001"
    assert target_status["entries"][0]["score_basis"] == "pipeline_score"
    assert target_status["entries"][0]["detection_claimed"] is False


def test_run_production_scan_resume_skips_existing_artifacts(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    scans_dir = tmp_path / "scans"
    _write_result_pair(results_dir, "HIP99427", "candidate", "known_object_annotation", 0.1)
    first_stdout = StringIO()
    first = run_production_scan(
        results_dir=results_dir,
        scans_dir=scans_dir,
        stdout=first_stdout,
        run_id=RUN_ID,
        use_rich=False,
        validate_func=lambda: {"ok": True},
        dashboard_func=lambda: {"needs_attention": False},
    )
    second_stdout = StringIO()

    second = run_production_scan(
        results_dir=results_dir,
        scans_dir=scans_dir,
        stdout=second_stdout,
        resume_run_dir=first.run_dir,
        use_rich=False,
        validate_func=lambda: {"ok": False},
        dashboard_func=lambda: {"needs_attention": True},
    )

    rendered = second_stdout.getvalue()
    assert second.run_id == RUN_ID
    assert second.target_count == 1
    assert second.skipped_step_count >= 5
    assert "SKIP validate-all" in rendered
    assert "SKIP prod-write-outcomes" in rendered


def test_production_diagnostics_compact_output(tmp_path: Path) -> None:
    stdout = StringIO()

    diagnostics = production_diagnostics(
        scans_dir=tmp_path,
        stdout=stdout,
        use_rich=False,
        validate_func=lambda: {"ok": True},
        dashboard_func=lambda: {"needs_attention": False},
    )

    assert diagnostics["validate_all_ok"] is True
    assert diagnostics["review_dashboard_needs_attention"] is False
    assert "Diagnostics: validate_all_ok=True needs_attention=False" in stdout.getvalue()
