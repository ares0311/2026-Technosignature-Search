from __future__ import annotations

import json
from pathlib import Path

from techno_search.production_blocker_consistency import (
    load_production_blocker_expectations,
    production_blocker_consistency_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "production_blocker_consistency.json"


def _write_expected(path: Path) -> Path:
    expected_path = path / "expected.json"
    expected_path.write_text(
        json.dumps(
            {
                "schema_version": "production_blocker_consistency_v1",
                "expected_blockers": {
                    "required_tier1_blocker_phrases": [
                        "Calibrated scoring thresholds",
                        "Real site-specific RFI database",
                    ],
                    "min_tier1_blocker_count": 2,
                    "expected_real_data_authorization_total": 0,
                    "require_zero_external_submission_authorization": True,
                    "require_admission_blockers_visible": True,
                    "require_operations_readiness_blocked_for_real_data": True,
                },
            }
        ),
        encoding="utf-8",
    )
    return expected_path


def _write_project(path: Path, *, omit_phrase: str | None = None) -> None:
    docs = path / "docs"
    docs.mkdir()
    phrases = [
        "Calibrated scoring thresholds",
        "Real site-specific RFI database",
    ]
    visible_phrases = [phrase for phrase in phrases if phrase != omit_phrase]
    rows = "\n".join(f"| **{phrase}** | Large |" for phrase in visible_phrases)
    (docs / "PRODUCTION_READINESS.md").write_text(
        "\n".join(
            [
                "# Production Readiness Assessment",
                "",
                "### Tier 1 — Blockers",
                "",
                "| Gap | Effort estimate |",
                "|---|---|",
                rows,
            ]
        ),
        encoding="utf-8",
    )


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


def _readiness_summary(
    *,
    recommendation: str = "blocked_for_real_data",
    real_data_blocker_count: int = 5,
    external_submission_approved_count: int = 0,
    network_access_allowed_count: int = 0,
) -> dict[str, object]:
    return {
        "recommendation": recommendation,
        "real_data_blocker_count": real_data_blocker_count,
        "external_submission_approved_count": external_submission_approved_count,
        "network_access_allowed_count": network_access_allowed_count,
    }


def test_load_production_blocker_expectations_fixture() -> None:
    expected = load_production_blocker_expectations(FIXTURE_PATH)

    assert expected["min_tier1_blocker_count"] == 2
    assert "Calibrated scoring thresholds" in expected[
        "required_tier1_blocker_phrases"
    ]


def test_production_blocker_consistency_custom_project_passes(tmp_path: Path) -> None:
    expected_path = _write_expected(tmp_path)
    _write_project(tmp_path)

    summary = production_blocker_consistency_summary(
        expected_path,
        project_root=tmp_path,
        rfi_admission=_rfi_summary(),
        curated_admission=_curated_summary(),
        readiness=_readiness_summary(),
    )

    assert summary["ok"] is True
    assert summary["issue_count"] == 0
    assert summary["actual_tier1_blocker_count"] == 2
    assert summary["real_data_authorized_total"] == 0


def test_production_blocker_consistency_detects_missing_tier1_blocker(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    _write_project(tmp_path, omit_phrase="Real site-specific RFI database")

    summary = production_blocker_consistency_summary(
        expected_path,
        project_root=tmp_path,
        rfi_admission=_rfi_summary(),
        curated_admission=_curated_summary(),
        readiness=_readiness_summary(),
    )

    assert summary["ok"] is False
    assert "Real site-specific RFI database" in summary["missing_tier1_blockers"]


def test_production_blocker_consistency_detects_authorization_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    _write_project(tmp_path)

    summary = production_blocker_consistency_summary(
        expected_path,
        project_root=tmp_path,
        rfi_admission=_rfi_summary(real_data_authorized_count=1),
        curated_admission=_curated_summary(),
        readiness=_readiness_summary(external_submission_approved_count=1),
    )

    assert summary["ok"] is False
    assert summary["real_data_authorized_total"] == 1
    assert summary["external_submission_authorized_total"] == 1


def test_production_blocker_consistency_detects_missing_admission_blockers(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    _write_project(tmp_path)

    summary = production_blocker_consistency_summary(
        expected_path,
        project_root=tmp_path,
        rfi_admission=_rfi_summary(blocked_count=0),
        curated_admission=_curated_summary(blocked_count=0),
        readiness=_readiness_summary(),
    )

    assert summary["ok"] is False
    assert any("RFI database admission blockers" in issue for issue in summary["issues"])
    assert any("curated dataset admission blockers" in issue for issue in summary["issues"])


def test_production_blocker_consistency_detects_readiness_drift(
    tmp_path: Path,
) -> None:
    expected_path = _write_expected(tmp_path)
    _write_project(tmp_path)

    summary = production_blocker_consistency_summary(
        expected_path,
        project_root=tmp_path,
        rfi_admission=_rfi_summary(),
        curated_admission=_curated_summary(),
        readiness=_readiness_summary(
            recommendation="operator_review_required",
            real_data_blocker_count=0,
        ),
    )

    assert summary["ok"] is False
    assert summary["operations_readiness_recommendation"] == "operator_review_required"
    assert any("blocked_for_real_data" in issue for issue in summary["issues"])


def test_production_blocker_consistency_default_project_passes() -> None:
    summary = production_blocker_consistency_summary()

    assert summary["schema_version"] == "production_blocker_consistency_v1"
    assert summary["ok"] is True
    assert summary["actual_tier1_blocker_count"] == 2
    assert summary["rfi_database_admission_blocked_count"] == 4
    assert summary["curated_dataset_admission_blocked_count"] == 3
    assert summary["real_data_authorized_total"] == 1
