from __future__ import annotations

import json
from pathlib import Path

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
    ):
        (docs / name).write_text(text, encoding="utf-8")


def _write_gate(root: Path, **overrides: object) -> Path:
    data = load_ai_hardening_gate(FIXTURE_PATH)
    data.update(overrides)
    path = root / "gate.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_ai_hardening_gate_fixture() -> None:
    gate = load_ai_hardening_gate(FIXTURE_PATH)

    assert gate["schema_version"] == "ai_hardening_gate_v1"
    assert gate["status"] == "open"
    assert gate["production_promotion_allowed"] is False


def test_ai_hardening_gate_default_project_is_open_and_safe() -> None:
    summary = ai_hardening_gate_summary()

    assert summary["ok"] is True
    assert summary["status"] == "open"
    assert summary["production_promotion_allowed"] is False
    assert summary["open_blocking_requirement_count"] == 4
    assert summary["independent_methods_required"] == 2
    assert summary["missing_document_phrase_count"] == 0


def test_ai_hardening_gate_detects_missing_document_visibility(tmp_path: Path) -> None:
    _write_docs(tmp_path, include_phrase=False)
    gate_path = _write_gate(tmp_path)

    summary = ai_hardening_gate_summary(gate_path, project_root=tmp_path)

    assert summary["ok"] is False
    assert summary["missing_document_phrase_count"] == 8
    assert any("visibility" in issue for issue in summary["issues"])


def test_ai_hardening_gate_detects_unsafe_promotion(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    gate_path = _write_gate(
        tmp_path,
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


def test_ai_hardening_gate_detects_premature_closure(tmp_path: Path) -> None:
    _write_docs(tmp_path)
    gate_path = _write_gate(tmp_path, status="closed")

    summary = ai_hardening_gate_summary(gate_path, project_root=tmp_path)

    assert summary["ok"] is False
    assert summary["status"] == "closed"
    assert summary["open_blocking_requirement_count"] == 4
    assert any("closed with blocking" in issue for issue in summary["issues"])
