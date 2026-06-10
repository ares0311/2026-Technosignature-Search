"""Project status consistency checks for readiness documentation.

These checks keep local status documents aligned with validation gates. They do
not ingest data, authorize live access, or change scientific interpretation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from techno_search.curated_dataset_admission import curated_dataset_admission_summary
from techno_search.rfi_database_admission import rfi_database_admission_summary

PROJECT_STATUS_CONSISTENCY_SCHEMA_VERSION = "project_status_consistency_v1"

PROJECT_STATUS_CONSISTENCY_DISCLAIMER = (
    "Project status consistency checks are documentation and validation drift "
    "guards only. They do not ingest real observation data, calibrate scoring "
    "thresholds, authorize live data access, authorize external submission, or "
    "constitute detections, discoveries, or external validation."
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_expected_path() -> Path:
    return _project_root() / "tests" / "fixtures" / "project_status_consistency.json"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_project_status_expectations(path: Path | None = None) -> dict[str, Any]:
    expectation_path = path if path is not None else _default_expected_path()
    raw = json.loads(expectation_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_status"])


def _extract_int(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match is None:
        return None
    return int(match.group(1))


def _extract_latest_int(pattern: str, text: str) -> int | None:
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    if not matches:
        return None
    return max(int(match) for match in matches)


def _extract_current_milestone_label(text: str) -> str:
    match = re.search(
        r"^\*\*Current milestone:\*\*\s+\d+\s+\(([^)]+)\)",
        text,
        flags=re.MULTILINE,
    )
    return match.group(1) if match else ""


def project_status_consistency_summary(
    expected_path: Path | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    root = project_root if project_root is not None else _project_root()
    expected = load_project_status_expectations(expected_path)

    roadmap_text = _read_text(root / "docs" / "ROADMAP.md")
    decisions_text = _read_text(root / "docs" / "DECISIONS.md")
    production_text = _read_text(root / "docs" / "PRODUCTION_READINESS.md")
    project_status_text = _read_text(root / "docs" / "PROJECT_STATUS.md")
    normalized_project_status_text = " ".join(project_status_text.split())

    latest_milestone = _extract_latest_int(r"^# Milestone (\d+)", roadmap_text)
    latest_decision = _extract_latest_int(r"^# DECISION-(\d+)", decisions_text)
    production_current_milestone = _extract_int(
        r"^\*\*Current milestone:\*\*\s+(\d+)",
        production_text,
    )
    production_schema_count = _extract_int(
        r"^\|\s*(\d+)\s+JSON schema artifacts\s*\|",
        production_text,
    )
    production_current_label = _extract_current_milestone_label(production_text)
    actual_schema_count = len(list((root / "schemas").glob("*.schema.json")))
    rfi_real_data_authorized_count = int(
        rfi_database_admission_summary().get("real_data_authorized_count", 0)
    )
    curated_real_data_authorized_count = int(
        curated_dataset_admission_summary().get("real_data_authorized_count", 0)
    )

    expected_milestone = int(expected["latest_milestone_number"])
    expected_decision = int(expected["latest_decision_number"])
    expected_schema_count = int(expected["schema_count"])
    expected_label = str(expected["latest_milestone_label"])
    expected_rfi_authorized = int(
        expected.get(
            "expected_rfi_real_data_authorization_total",
            0 if expected.get("require_zero_real_data_authorization", True) else -1,
        )
    )
    expected_curated_authorized = int(
        expected.get(
            "expected_curated_real_data_authorization_total",
            0 if expected.get("require_zero_real_data_authorization", True) else -1,
        )
    )
    required_status_phrase = str(expected.get("project_status_completed_phrase", ""))

    issues: list[str] = []
    if latest_milestone != expected_milestone:
        issues.append(
            f"ROADMAP latest milestone {latest_milestone} != expected {expected_milestone}"
        )
    if latest_decision != expected_decision:
        issues.append(
            f"DECISIONS latest decision {latest_decision} != expected {expected_decision}"
        )
    if production_current_milestone != expected_milestone:
        issues.append(
            "PRODUCTION_READINESS current milestone "
            f"{production_current_milestone} != expected {expected_milestone}"
        )
    if production_current_label != expected_label:
        issues.append(
            "PRODUCTION_READINESS current milestone label "
            f"{production_current_label!r} != expected {expected_label!r}"
        )
    if actual_schema_count != expected_schema_count:
        issues.append(
            f"schema artifact count {actual_schema_count} != expected {expected_schema_count}"
        )
    if production_schema_count != expected_schema_count:
        issues.append(
            "PRODUCTION_READINESS schema count "
            f"{production_schema_count} != expected {expected_schema_count}"
        )
    required_status_phrase_present = (
        required_status_phrase in normalized_project_status_text
        if required_status_phrase
        else True
    )
    if not required_status_phrase_present:
        issues.append(
            "PROJECT_STATUS missing required completed phrase "
            f"{required_status_phrase!r}"
        )
    if (
        expected_rfi_authorized >= 0
        and rfi_real_data_authorized_count != expected_rfi_authorized
    ):
        issues.append(
            "RFI database admission real-data authorization "
            f"{rfi_real_data_authorized_count} != expected {expected_rfi_authorized}"
        )
    if (
        expected_curated_authorized >= 0
        and curated_real_data_authorized_count != expected_curated_authorized
    ):
        issues.append(
            "curated dataset admission real-data authorization "
            f"{curated_real_data_authorized_count} != expected "
            f"{expected_curated_authorized}"
        )

    return {
        "schema_version": PROJECT_STATUS_CONSISTENCY_SCHEMA_VERSION,
        "disclaimer": PROJECT_STATUS_CONSISTENCY_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_latest_milestone": expected_milestone,
        "roadmap_latest_milestone": latest_milestone,
        "production_readiness_current_milestone": production_current_milestone,
        "production_readiness_current_milestone_label": production_current_label,
        "expected_latest_decision": expected_decision,
        "decisions_latest_decision": latest_decision,
        "expected_schema_count": expected_schema_count,
        "actual_schema_count": actual_schema_count,
        "production_readiness_schema_count": production_schema_count,
        "rfi_database_admission_real_data_authorized_count": (
            rfi_real_data_authorized_count
        ),
        "curated_dataset_admission_real_data_authorized_count": (
            curated_real_data_authorized_count
        ),
        "expected_rfi_database_admission_real_data_authorized_count": (
            expected_rfi_authorized
        ),
        "expected_curated_dataset_admission_real_data_authorized_count": (
            expected_curated_authorized
        ),
        "required_status_phrase_present": required_status_phrase_present,
    }
