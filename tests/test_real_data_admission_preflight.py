from __future__ import annotations

import json
from pathlib import Path

from techno_search.real_data_admission_preflight import (
    load_real_data_admission_preflight_categories,
    load_real_data_admission_preflight_expectations,
    real_data_admission_preflight_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "real_data_admission_preflight.json"


def _category(category_id: str, status: str) -> dict[str, object]:
    return {
        "category_id": category_id,
        "label": category_id.replace("_", " ").title(),
        "required_evidence": ["evidence a", "evidence b"],
        "current_evidence_count": 0,
        "blocker_count": 2,
        "review_status": status,
        "real_data_authorized": False,
        "live_data_authorized": False,
        "external_submission_authorized": False,
        "notes": "Blocked local preflight fixture.",
    }


def _write_fixture(
    path: Path,
    *,
    categories: list[dict[str, object]] | None = None,
) -> Path:
    fixture_path = path / "preflight.json"
    fixture_path.write_text(
        json.dumps(
            {
                "schema_version": "real_data_admission_preflight_v1",
                "preflight_categories": categories
                if categories is not None
                else [
                    _category(
                        "real_observation_data",
                        "blocked_pending_observation_data",
                    ),
                    _category(
                        "real_labeled_dataset",
                        "blocked_pending_labeled_dataset",
                    ),
                    _category("scoring_calibration", "blocked_pending_calibration"),
                    _category(
                        "site_specific_rfi_database",
                        "blocked_pending_rfi_database",
                    ),
                    _category("peer_review", "blocked_pending_peer_review"),
                ],
                "expected_preflight": {
                    "category_count": 5,
                    "min_blocker_total": 5,
                    "require_zero_real_data_authorization": True,
                    "require_zero_live_data_authorization": True,
                    "require_zero_external_submission_authorization": True,
                    "require_rfi_admission_blockers_visible": True,
                    "require_curated_dataset_admission_blockers_visible": True,
                    "require_production_blocker_consistency_ok": True,
                },
            }
        ),
        encoding="utf-8",
    )
    return fixture_path


def _rfi_summary(
    *,
    blocked_count: int = 3,
    real_data_authorized_count: int = 0,
) -> dict[str, object]:
    return {
        "blocked_count": blocked_count,
        "real_data_authorized_count": real_data_authorized_count,
    }


def _curated_summary(
    *,
    blocked_count: int = 3,
    real_data_authorized_count: int = 0,
) -> dict[str, object]:
    return {
        "blocked_count": blocked_count,
        "real_data_authorized_count": real_data_authorized_count,
    }


def _production_blockers(*, ok: bool = True, issue_count: int = 0) -> dict[str, object]:
    return {"ok": ok, "issue_count": issue_count}


def test_load_real_data_admission_preflight_fixture() -> None:
    categories = load_real_data_admission_preflight_categories(FIXTURE_PATH)
    expected = load_real_data_admission_preflight_expectations(FIXTURE_PATH)

    assert len(categories) == 5
    assert categories[0].category_id == "real_observation_data"
    assert expected["category_count"] == 5


def test_real_data_admission_preflight_custom_fixture_passes(tmp_path: Path) -> None:
    fixture_path = _write_fixture(tmp_path)

    summary = real_data_admission_preflight_summary(
        fixture_path,
        rfi_admission=_rfi_summary(),
        curated_admission=_curated_summary(),
        production_blockers=_production_blockers(),
    )

    assert summary["ok"] is True
    assert summary["category_count"] == 5
    assert summary["blocked_category_count"] == 5
    assert summary["blocker_total"] == 10
    assert summary["real_data_authorized_total"] == 0
    assert summary["live_data_authorized_total"] == 0


def test_real_data_admission_preflight_detects_missing_category(
    tmp_path: Path,
) -> None:
    categories = [
        _category("real_observation_data", "blocked_pending_observation_data"),
        _category("real_labeled_dataset", "blocked_pending_labeled_dataset"),
        _category("scoring_calibration", "blocked_pending_calibration"),
        _category("site_specific_rfi_database", "blocked_pending_rfi_database"),
    ]
    fixture_path = _write_fixture(tmp_path, categories=categories)

    summary = real_data_admission_preflight_summary(
        fixture_path,
        rfi_admission=_rfi_summary(),
        curated_admission=_curated_summary(),
        production_blockers=_production_blockers(),
    )

    assert summary["ok"] is False
    assert any("peer_review" in issue for issue in summary["issues"])
    assert summary["category_count"] == 4


def test_real_data_admission_preflight_detects_authorization_drift(
    tmp_path: Path,
) -> None:
    categories = [
        _category("real_observation_data", "blocked_pending_observation_data"),
        _category("real_labeled_dataset", "blocked_pending_labeled_dataset"),
        _category("scoring_calibration", "blocked_pending_calibration"),
        _category("site_specific_rfi_database", "blocked_pending_rfi_database"),
        _category("peer_review", "blocked_pending_peer_review"),
    ]
    categories[0]["real_data_authorized"] = True
    categories[1]["live_data_authorized"] = True
    categories[2]["external_submission_authorized"] = True
    fixture_path = _write_fixture(tmp_path, categories=categories)

    summary = real_data_admission_preflight_summary(
        fixture_path,
        rfi_admission=_rfi_summary(real_data_authorized_count=1),
        curated_admission=_curated_summary(real_data_authorized_count=1),
        production_blockers=_production_blockers(),
    )

    assert summary["ok"] is False
    assert summary["real_data_authorized_total"] == 1
    assert summary["live_data_authorized_total"] == 1
    assert summary["external_submission_authorized_total"] == 1
    assert any("RFI database admission" in issue for issue in summary["issues"])


def test_real_data_admission_preflight_detects_cross_gate_drift(
    tmp_path: Path,
) -> None:
    fixture_path = _write_fixture(tmp_path)

    summary = real_data_admission_preflight_summary(
        fixture_path,
        rfi_admission=_rfi_summary(blocked_count=0),
        curated_admission=_curated_summary(blocked_count=0),
        production_blockers=_production_blockers(ok=False, issue_count=2),
    )

    assert summary["ok"] is False
    assert summary["production_blocker_consistency_ok"] is False
    assert summary["production_blocker_consistency_issue_count"] == 2
    assert any("RFI database admission blockers" in issue for issue in summary["issues"])
    assert any("curated dataset admission blockers" in issue for issue in summary["issues"])


def test_real_data_admission_preflight_detects_evidence_count_drift(
    tmp_path: Path,
) -> None:
    categories = [
        _category("real_observation_data", "blocked_pending_observation_data"),
        _category("real_labeled_dataset", "blocked_pending_labeled_dataset"),
        _category("scoring_calibration", "blocked_pending_calibration"),
        _category("site_specific_rfi_database", "blocked_pending_rfi_database"),
        _category("peer_review", "blocked_pending_peer_review"),
    ]
    categories[0]["current_evidence_count"] = 3
    fixture_path = _write_fixture(tmp_path, categories=categories)

    summary = real_data_admission_preflight_summary(
        fixture_path,
        rfi_admission=_rfi_summary(),
        curated_admission=_curated_summary(),
        production_blockers=_production_blockers(),
    )

    assert summary["ok"] is False
    assert any("exceeds required evidence" in issue for issue in summary["issues"])


def test_real_data_admission_preflight_default_project_passes() -> None:
    summary = real_data_admission_preflight_summary()

    assert summary["schema_version"] == "real_data_admission_preflight_v1"
    assert summary["ok"] is True
    assert summary["category_count"] == 5
    assert summary["blocked_category_count"] == 5
    assert summary["real_data_authorized_total"] == 0
    assert summary["live_data_authorized_total"] == 0
    assert summary["external_submission_authorized_total"] == 0
