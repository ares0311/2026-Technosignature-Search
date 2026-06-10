"""Tests for the peer review package generator."""
from __future__ import annotations

from pathlib import Path

from techno_search.peer_review_package import (
    PEER_REVIEW_ITEMS_REQUIRED,
    PEER_REVIEW_PACKAGE_DISCLAIMER,
    generate_peer_review_package,
)


def test_generate_creates_output_dir(tmp_path: Path) -> None:
    result = generate_peer_review_package(tmp_path / "peer_review")
    assert result["ok"] is True
    assert Path(result["output_dir"]).is_dir()


def test_generate_creates_readme(tmp_path: Path) -> None:
    generate_peer_review_package(tmp_path)
    assert (tmp_path / "PEER_REVIEW_README.md").exists()


def test_generate_creates_methodology_json(tmp_path: Path) -> None:
    generate_peer_review_package(tmp_path)
    assert (tmp_path / "methodology_summary.json").exists()


def test_generate_creates_checklist(tmp_path: Path) -> None:
    generate_peer_review_package(tmp_path)
    assert (tmp_path / "review_checklist.md").exists()


def test_readme_has_disclaimer(tmp_path: Path) -> None:
    generate_peer_review_package(tmp_path)
    readme = (tmp_path / "PEER_REVIEW_README.md").read_text(encoding="utf-8")
    assert "NOT FOR EXTERNAL SUBMISSION" in readme
    assert "synthetic" in readme.lower()


def test_readme_lists_review_items(tmp_path: Path) -> None:
    generate_peer_review_package(tmp_path)
    readme = (tmp_path / "PEER_REVIEW_README.md").read_text(encoding="utf-8")
    for item in PEER_REVIEW_ITEMS_REQUIRED[:3]:
        assert item.split("(")[0].strip() in readme


def test_methodology_summary_has_tier1_gaps(tmp_path: Path) -> None:
    import json

    generate_peer_review_package(tmp_path)
    methodology = json.loads(
        (tmp_path / "methodology_summary.json").read_text(encoding="utf-8")
    )
    assert len(methodology["tier_1_gaps"]) == 4
    assert "GBT ABACAD cadence" in methodology["data_status"]


def test_result_lists_files_written(tmp_path: Path) -> None:
    result = generate_peer_review_package(tmp_path)
    assert len(result["files_written"]) >= 3


def test_disclaimer_is_conservative() -> None:
    assert "does not constitute a detection claim" in PEER_REVIEW_PACKAGE_DISCLAIMER
    assert "does not authorize external submission" in PEER_REVIEW_PACKAGE_DISCLAIMER
    assert "synthetic" in PEER_REVIEW_PACKAGE_DISCLAIMER


def test_checklist_has_false_positive_item(tmp_path: Path) -> None:
    generate_peer_review_package(tmp_path)
    checklist = (tmp_path / "review_checklist.md").read_text(encoding="utf-8")
    assert "False-positive" in checklist or "false-positive" in checklist


def test_cli_generate_peer_review_package(tmp_path: Path) -> None:
    from techno_search.cli import main

    exit_code = main(["generate-peer-review-package", str(tmp_path / "pr_out")])
    assert exit_code == 0
    assert (tmp_path / "pr_out" / "PEER_REVIEW_README.md").exists()
