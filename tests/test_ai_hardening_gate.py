from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from techno_search.ai_hardening_gate import (
    ai_hardening_gate_summary,
    load_ai_hardening_gate,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ai_hardening_gate.json"


def _write_docs(root: Path, *, include_phrase: bool = True) -> None:
    docs = root / "docs"
    docs.mkdir()
    text = (
        "AI hardening production blocker DECISION-134 blocks production "
        "promotion."
        if include_phrase
        else "Production status is intentionally stale."
    )
    for name in (
        "PRODUCTION_READINESS.md",
        "PROJECT_STATUS.md",
        "DECISIONS.md",
        "ROADMAP.md",
        "AI_HARDENING_REVIEW_PROTOCOL.md",
    ):
        (docs / name).write_text(text, encoding="utf-8")


def _open_gate_data() -> dict[str, object]:
    data = load_ai_hardening_gate(FIXTURE_PATH)
    data["status"] = "open"
    data["production_promotion_allowed"] = False
    data["production_promotion_scope"] = "blocked"
    data["closure_evidence_bundle_path"] = ""
    for method in cast(list[dict[str, Any]], data["independent_methods"]):
        method["recorded"] = False
    for requirement in cast(list[dict[str, Any]], data["requirements"]):
        requirement["satisfied"] = False
        requirement["blocking"] = True
    return data


def _write_gate(
    root: Path,
    *,
    open_gate: bool = False,
    **overrides: object,
) -> Path:
    data = _open_gate_data() if open_gate else load_ai_hardening_gate(FIXTURE_PATH)
    data.update(overrides)
    path = root / "gate.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_ai_hardening_gate_fixture() -> None:
    gate = load_ai_hardening_gate(FIXTURE_PATH)

    assert gate["schema_version"] == "ai_hardening_gate_v1"
    assert gate["status"] == "closed"
    assert gate["production_promotion_allowed"] is True
    assert gate["production_promotion_scope"] == "local_citizen_science_operations_only"
    assert gate["external_submission_allowed"] is False


def test_ai_hardening_gate_default_project_is_closed_and_local_only() -> None:
    summary = ai_hardening_gate_summary()

    assert summary["ok"] is True
    assert summary["status"] == "closed"
    assert summary["production_promotion_allowed"] is True
    assert summary["production_promotion_scope"] == "local_citizen_science_operations_only"
    assert summary["external_submission_allowed"] is False
    assert summary["detection_claimed"] is False
    assert summary["expert_review_claimed"] is False
    assert summary["open_blocking_requirement_count"] == 0
    assert summary["satisfied_requirement_count"] == 4
    assert summary["independent_methods_required"] == 2
    assert summary["independent_methods_recorded_count"] >= 2
    assert summary["closure_evidence_bundle_exists"] is True
    assert summary["missing_document_phrase_count"] == 0


def test_ai_hardening_gate_detects_missing_document_visibility(tmp_path: Path) -> None:
    _write_docs(tmp_path, include_phrase=False)
    gate_path = _write_gate(tmp_path, open_gate=True)

    summary = ai_hardening_gate_summary(gate_path, project_root=tmp_path)

    assert summary["ok"] is False
    assert summary["missing_document_phrase_count"] == 10
    assert any("visibility" in issue for issue in summary["issues"])


def test_ai_hardening_gate_detects_unsafe_promotion(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    gate_path = _write_gate(
        tmp_path,
        open_gate=True,
        production_promotion_allowed=True,
        external_submission_allowed=True,
        detection_claimed=True,
        expert_review_claimed=True,
    )

    summary = ai_hardening_gate_summary(gate_path, project_root=tmp_path)

    assert summary["ok"] is False
    assert summary["production_promotion_allowed"] is True
    assert summary["external_submission_allowed"] is True
    assert summary["detection_claimed"] is True
    assert summary["expert_review_claimed"] is True
    assert any("under review" in issue for issue in summary["issues"])


def test_ai_hardening_gate_detects_nonlocal_closed_promotion(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text("{}", encoding="utf-8")
    gate_path = _write_gate(
        tmp_path,
        production_promotion_scope="blocked",
        closure_evidence_bundle_path="bundle.json",
    )

    summary = ai_hardening_gate_summary(gate_path, project_root=tmp_path)

    assert summary["ok"] is False
    assert summary["status"] == "closed"
    assert any("local-only" in issue for issue in summary["issues"])


def test_ai_hardening_gate_detects_premature_closure(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    gate_path = _write_gate(
        tmp_path,
        open_gate=True,
        status="closed",
        production_promotion_allowed=True,
        production_promotion_scope="local_citizen_science_operations_only",
    )

    summary = ai_hardening_gate_summary(gate_path, project_root=tmp_path)

    assert summary["ok"] is False
    assert summary["status"] == "closed"
    assert summary["open_blocking_requirement_count"] == 4
    assert any("closed with blocking" in issue for issue in summary["issues"])


def test_ai_hardening_gate_distinguishes_empty_and_populated_evidence_paths(
    tmp_path: Path,
) -> None:
    _write_docs(tmp_path)
    gate_path = _write_gate(tmp_path, open_gate=True)
    empty_path = tmp_path / "data" / "extended_corpus"
    populated_path = tmp_path / "data" / "meerkat_hits"
    empty_path.mkdir(parents=True)
    populated_path.mkdir(parents=True)
    (populated_path / "hits.ndjson").write_text("{}", encoding="utf-8")

    summary = ai_hardening_gate_summary(gate_path, project_root=tmp_path)

    assert summary["existing_evidence_path_count"] == 2
    assert summary["populated_evidence_path_count"] == 1
    assert summary["empty_existing_evidence_path_count"] == 1
    assert summary["total_evidence_file_count"] == 1
    assert summary["evidence_file_counts"]["data/extended_corpus"] == 0
    assert summary["evidence_file_counts"]["data/meerkat_hits"] == 1
    assert summary["empty_existing_evidence_paths"] == ["data/extended_corpus"]


def test_ai_hardening_gate_marks_local_calibration_holdout_as_provisional(
    tmp_path: Path,
) -> None:
    _write_docs(tmp_path)
    gate_path = _write_gate(tmp_path, open_gate=True)
    calibration_path = tmp_path / "data" / "calibration_corpus"
    calibration_path.mkdir(parents=True)
    (calibration_path / "spliced_HIP99427_0033.dat").write_text(
        "training cadence", encoding="utf-8"
    )
    (calibration_path / "spliced_HIP100670_0034.dat").write_text(
        "held out target", encoding="utf-8"
    )
    (calibration_path / "Voyager1_test.dat").write_text(
        "voyager target", encoding="utf-8"
    )

    summary = ai_hardening_gate_summary(gate_path, project_root=tmp_path)

    assert summary["local_calibration_holdout_exists"] is True
    assert summary["local_calibration_holdout_dat_file_count"] == 3
    assert summary["local_calibration_holdout_non_training_dat_file_count"] == 2
    assert summary["local_calibration_holdout_non_training_targets"] == [
        "HIP100670",
        "VOYAGER-1",
    ]
    assert summary["local_calibration_holdout_provisional_only"] is True
    assert summary["local_calibration_holdout_gate_closure_ready"] is False
