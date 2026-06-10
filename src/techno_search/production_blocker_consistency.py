"""Consistency checks for production-readiness blocker visibility."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from techno_search.curated_dataset_admission import curated_dataset_admission_summary
from techno_search.operations_readiness import operations_readiness_summary
from techno_search.rfi_database_admission import rfi_database_admission_summary

PRODUCTION_BLOCKER_CONSISTENCY_SCHEMA_VERSION = (
    "production_blocker_consistency_v1"
)

PRODUCTION_BLOCKER_CONSISTENCY_DISCLAIMER = (
    "Production blocker consistency checks are local readiness visibility "
    "gates only. They keep real-data, calibration, RFI, reproducibility-review, and "
    "authorization blockers visible without ingesting real observation data, "
    "calibrating thresholds, clearing blockers, authorizing live data access, "
    "authorizing external submission, or constituting detections, discoveries, "
    "or external validation."
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_expected_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "production_blocker_consistency.json"
    )


def load_production_blocker_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    expectation_path = path if path is not None else _default_expected_path()
    raw = json.loads(expectation_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_blockers"])


def _int_value(summary: dict[str, Any], key: str) -> int:
    value = summary.get(key, 0)
    return int(value) if isinstance(value, (int, float)) else 0


def _normalized_text(text: str) -> str:
    return " ".join(text.lower().split())


def _phrase_present(text: str, phrase: str) -> bool:
    return _normalized_text(phrase) in _normalized_text(text)


def production_blocker_consistency_summary(
    expected_path: Path | None = None,
    *,
    project_root: Path | None = None,
    rfi_admission: dict[str, Any] | None = None,
    curated_admission: dict[str, Any] | None = None,
    readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = project_root if project_root is not None else _project_root()
    expected = load_production_blocker_expectations(expected_path)
    production_text = (root / "docs" / "PRODUCTION_READINESS.md").read_text(
        encoding="utf-8"
    )

    required_phrases = [
        str(phrase) for phrase in expected.get("required_tier1_blocker_phrases", [])
    ]
    present_phrases = [
        phrase for phrase in required_phrases if _phrase_present(production_text, phrase)
    ]
    missing_phrases = [
        phrase for phrase in required_phrases if phrase not in present_phrases
    ]

    rfi = rfi_admission if rfi_admission is not None else rfi_database_admission_summary()
    curated = (
        curated_admission
        if curated_admission is not None
        else curated_dataset_admission_summary()
    )
    readiness_summary = readiness if readiness is not None else operations_readiness_summary()

    min_tier1_blocker_count = int(expected.get("min_tier1_blocker_count", 0))
    expected_real_data_authorized_total = int(
        expected.get(
            "expected_real_data_authorization_total",
            0 if expected.get("require_zero_real_data_authorization", True) else -1,
        )
    )
    require_zero_external = bool(
        expected.get("require_zero_external_submission_authorization", True)
    )
    require_admission_blockers = bool(
        expected.get("require_admission_blockers_visible", True)
    )
    require_readiness_blocked = bool(
        expected.get("require_operations_readiness_blocked_for_real_data", True)
    )

    rfi_blocked_count = _int_value(rfi, "blocked_count")
    curated_blocked_count = _int_value(curated, "blocked_count")
    rfi_real_data_authorized_count = _int_value(rfi, "real_data_authorized_count")
    curated_real_data_authorized_count = _int_value(curated, "real_data_authorized_count")
    real_data_authorized_total = (
        rfi_real_data_authorized_count + curated_real_data_authorized_count
    )
    external_submission_authorized_total = _int_value(
        readiness_summary,
        "external_submission_approved_count",
    )
    network_access_allowed_count = _int_value(
        readiness_summary,
        "network_access_allowed_count",
    )
    operations_real_data_blocker_count = _int_value(
        readiness_summary,
        "real_data_blocker_count",
    )
    operations_recommendation = str(
        readiness_summary.get("recommendation", "unknown")
    )

    issues: list[str] = []
    if missing_phrases:
        issues.append(
            "PRODUCTION_READINESS missing Tier 1 blocker phrase(s): "
            + ", ".join(missing_phrases)
        )
    if len(present_phrases) < min_tier1_blocker_count:
        issues.append(
            "Tier 1 blocker phrase count "
            f"{len(present_phrases)} < minimum {min_tier1_blocker_count}"
        )
    if require_admission_blockers and rfi_blocked_count <= 0:
        issues.append("RFI database admission blockers are not visible")
    if require_admission_blockers and curated_blocked_count <= 0:
        issues.append("curated dataset admission blockers are not visible")
    if (
        expected_real_data_authorized_total >= 0
        and real_data_authorized_total != expected_real_data_authorized_total
    ):
        issues.append(
            "real-data authorization total "
            f"{real_data_authorized_total} != expected "
            f"{expected_real_data_authorized_total}"
        )
    if require_zero_external and external_submission_authorized_total != 0:
        issues.append(
            "external submission authorization total "
            f"{external_submission_authorized_total} is nonzero"
        )
    if require_zero_external and network_access_allowed_count != 0:
        issues.append(f"network access allowed count {network_access_allowed_count} is nonzero")
    if require_readiness_blocked and operations_recommendation != "blocked_for_real_data":
        issues.append(
            "operations readiness recommendation "
            f"{operations_recommendation!r} != 'blocked_for_real_data'"
        )
    if require_readiness_blocked and operations_real_data_blocker_count <= 0:
        issues.append("operations readiness real-data blocker count is not visible")

    return {
        "schema_version": PRODUCTION_BLOCKER_CONSISTENCY_SCHEMA_VERSION,
        "disclaimer": PRODUCTION_BLOCKER_CONSISTENCY_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_tier1_blocker_count": len(required_phrases),
        "min_tier1_blocker_count": min_tier1_blocker_count,
        "actual_tier1_blocker_count": len(present_phrases),
        "present_tier1_blockers": present_phrases,
        "missing_tier1_blockers": missing_phrases,
        "rfi_database_admission_blocked_count": rfi_blocked_count,
        "curated_dataset_admission_blocked_count": curated_blocked_count,
        "rfi_database_admission_real_data_authorized_count": (
            rfi_real_data_authorized_count
        ),
        "curated_dataset_admission_real_data_authorized_count": (
            curated_real_data_authorized_count
        ),
        "real_data_authorized_total": real_data_authorized_total,
        "expected_real_data_authorized_total": (
            expected_real_data_authorized_total
        ),
        "external_submission_authorized_total": external_submission_authorized_total,
        "network_access_allowed_count": network_access_allowed_count,
        "operations_readiness_recommendation": operations_recommendation,
        "operations_readiness_real_data_blocker_count": (
            operations_real_data_blocker_count
        ),
    }
