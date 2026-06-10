"""Preflight gates for proposed real-data admission."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from techno_search.curated_dataset_admission import curated_dataset_admission_summary
from techno_search.production_blocker_consistency import (
    production_blocker_consistency_summary,
)
from techno_search.rfi_database_admission import rfi_database_admission_summary

REAL_DATA_ADMISSION_PREFLIGHT_SCHEMA_VERSION = "real_data_admission_preflight_v1"

REAL_DATA_ADMISSION_PREFLIGHT_DISCLAIMER = (
    "Real-data admission preflight records are local readiness checks only. "
    "They expose required evidence, blockers, review status, and disabled "
    "authorization state as real observations, labels, scoring calibration, "
    "site-specific RFI records, or public reproducibility evidence change local "
    "admission "
    "state. They do not themselves ingest observation data, calibrate thresholds, "
    "clear blockers, authorize live data access, "
    "authorize external submission, or constitute detections, discoveries, or "
    "external validation."
)

ALLOWED_PREFLIGHT_REVIEW_STATUSES = frozenset(
    {
        "blocked_pending_observation_data",
        "blocked_pending_labeled_dataset",
        "blocked_pending_calibration",
        "blocked_pending_rfi_database",
        "blocked_pending_peer_review",
        "blocked_pending_public_reproducibility",
        "ready_for_local_review",
    }
)

REQUIRED_PREFLIGHT_CATEGORY_IDS = (
    "real_observation_data",
    "real_labeled_dataset",
    "scoring_calibration",
    "site_specific_rfi_database",
    "public_reproducibility_review",
)


def _default_preflight_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "real_data_admission_preflight.json"
    )


@dataclass(frozen=True)
class RealDataAdmissionPreflightCategory:
    category_id: str
    label: str
    required_evidence: tuple[str, ...]
    current_evidence_count: int
    blocker_count: int
    review_status: str
    real_data_authorized: bool
    live_data_authorized: bool
    external_submission_authorized: bool
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "category_id": self.category_id,
            "label": self.label,
            "required_evidence": list(self.required_evidence),
            "current_evidence_count": self.current_evidence_count,
            "blocker_count": self.blocker_count,
            "review_status": self.review_status,
            "real_data_authorized": self.real_data_authorized,
            "live_data_authorized": self.live_data_authorized,
            "external_submission_authorized": self.external_submission_authorized,
            "notes": self.notes,
        }


def load_real_data_admission_preflight_categories(
    path: Path | None = None,
) -> list[RealDataAdmissionPreflightCategory]:
    preflight_path = path if path is not None else _default_preflight_path()
    raw = json.loads(preflight_path.read_text(encoding="utf-8"))
    categories: list[RealDataAdmissionPreflightCategory] = []
    for item in raw.get("preflight_categories", []):
        categories.append(
            RealDataAdmissionPreflightCategory(
                category_id=str(item["category_id"]),
                label=str(item["label"]),
                required_evidence=tuple(str(value) for value in item["required_evidence"]),
                current_evidence_count=int(item.get("current_evidence_count", 0)),
                blocker_count=int(item.get("blocker_count", 0)),
                review_status=str(item["review_status"]),
                real_data_authorized=bool(item.get("real_data_authorized", False)),
                live_data_authorized=bool(item.get("live_data_authorized", False)),
                external_submission_authorized=bool(
                    item.get("external_submission_authorized", False)
                ),
                notes=str(item.get("notes", "")),
            )
        )
    return categories


def load_real_data_admission_preflight_expectations(
    path: Path | None = None,
) -> dict[str, Any]:
    preflight_path = path if path is not None else _default_preflight_path()
    raw = json.loads(preflight_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_preflight"])


def _int_value(summary: dict[str, Any], key: str) -> int:
    value = summary.get(key, 0)
    return int(value) if isinstance(value, (int, float)) else 0


def validate_real_data_admission_preflight_categories(
    categories: list[RealDataAdmissionPreflightCategory],
) -> dict[str, Any]:
    issues: list[str] = []
    seen_ids: set[str] = set()
    for category in categories:
        prefix = f"{category.category_id}: "
        if category.category_id in seen_ids:
            issues.append(prefix + "duplicate category_id")
        seen_ids.add(category.category_id)
        if category.review_status not in ALLOWED_PREFLIGHT_REVIEW_STATUSES:
            issues.append(prefix + f"unknown review_status {category.review_status!r}")
        if category.current_evidence_count < 0:
            issues.append(prefix + "current_evidence_count cannot be negative")
        if category.blocker_count < 0:
            issues.append(prefix + "blocker_count cannot be negative")
        if category.current_evidence_count > len(category.required_evidence):
            issues.append(prefix + "current_evidence_count exceeds required evidence")
        if category.review_status.startswith("blocked_") and category.blocker_count <= 0:
            issues.append(prefix + "blocked review_status requires visible blockers")
        if category.review_status == "ready_for_local_review" and category.blocker_count != 0:
            issues.append(prefix + "ready_for_local_review requires zero blockers")
        if category.real_data_authorized and category.blocker_count != 0:
            issues.append(prefix + "real data authorization requires zero blockers")
        if (
            category.real_data_authorized
            and category.current_evidence_count != len(category.required_evidence)
        ):
            issues.append(prefix + "real data authorization requires complete evidence")
        if category.live_data_authorized and not category.real_data_authorized:
            issues.append(prefix + "live data authorization requires real data authorization")
        if category.external_submission_authorized and not category.real_data_authorized:
            issues.append(
                prefix + "external submission authorization requires real data authorization"
            )
    missing_ids = [
        category_id
        for category_id in REQUIRED_PREFLIGHT_CATEGORY_IDS
        if category_id not in seen_ids
    ]
    if missing_ids:
        issues.append("missing preflight category ID(s): " + ", ".join(missing_ids))
    return {"ok": not issues, "issue_count": len(issues), "issues": issues}


def real_data_admission_preflight_summary(
    path: Path | None = None,
    *,
    rfi_admission: dict[str, Any] | None = None,
    curated_admission: dict[str, Any] | None = None,
    production_blockers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    categories = load_real_data_admission_preflight_categories(path)
    expected = load_real_data_admission_preflight_expectations(path)
    validation = validate_real_data_admission_preflight_categories(categories)
    rfi = rfi_admission if rfi_admission is not None else rfi_database_admission_summary()
    curated = (
        curated_admission
        if curated_admission is not None
        else curated_dataset_admission_summary()
    )
    blocker_gate = (
        production_blockers
        if production_blockers is not None
        else production_blocker_consistency_summary()
    )

    category_count = len(categories)
    blocker_total = sum(category.blocker_count for category in categories)
    blocked_category_count = sum(
        1 for category in categories if category.review_status.startswith("blocked_")
    )
    real_data_authorized_total = sum(
        1 for category in categories if category.real_data_authorized
    )
    live_data_authorized_total = sum(
        1 for category in categories if category.live_data_authorized
    )
    external_submission_authorized_total = sum(
        1 for category in categories if category.external_submission_authorized
    )
    expected_category_count = int(expected.get("category_count", 0))
    min_blocker_total = int(expected.get("min_blocker_total", 0))
    expected_real_data_total = int(
        expected.get(
            "expected_real_data_authorization_total",
            0 if expected.get("require_zero_real_data_authorization", True) else -1,
        )
    )
    require_zero_live_data = bool(expected.get("require_zero_live_data_authorization", True))
    require_zero_external = bool(
        expected.get("require_zero_external_submission_authorization", True)
    )
    require_rfi_blockers = bool(expected.get("require_rfi_admission_blockers_visible", True))
    require_curated_blockers = bool(
        expected.get("require_curated_dataset_admission_blockers_visible", True)
    )
    require_production_blocker_gate = bool(
        expected.get("require_production_blocker_consistency_ok", True)
    )
    expected_rfi_authorized = int(
        expected.get("expected_rfi_database_authorization_total", 0)
    )
    expected_curated_authorized = int(
        expected.get("expected_curated_dataset_authorization_total", 0)
    )

    rfi_blocked_count = _int_value(rfi, "blocked_count")
    curated_blocked_count = _int_value(curated, "blocked_count")
    rfi_real_data_authorized_count = _int_value(rfi, "real_data_authorized_count")
    curated_real_data_authorized_count = _int_value(curated, "real_data_authorized_count")
    production_blocker_ok = bool(blocker_gate.get("ok", False))
    production_blocker_issue_count = _int_value(blocker_gate, "issue_count")

    issues = list(validation["issues"])
    if category_count != expected_category_count:
        issues.append(f"category count {category_count} != expected {expected_category_count}")
    if blocker_total < min_blocker_total:
        issues.append(f"blocker total {blocker_total} < minimum {min_blocker_total}")
    if expected_real_data_total >= 0 and real_data_authorized_total != expected_real_data_total:
        issues.append(
            "real data authorization total "
            f"{real_data_authorized_total} != expected {expected_real_data_total}"
        )
    if require_zero_live_data and live_data_authorized_total != 0:
        issues.append(
            f"live data authorization total {live_data_authorized_total} is nonzero"
        )
    if require_zero_external and external_submission_authorized_total != 0:
        issues.append(
            "external submission authorization total "
            f"{external_submission_authorized_total} is nonzero"
        )
    if require_rfi_blockers and rfi_blocked_count <= 0:
        issues.append("RFI database admission blockers are not visible")
    if require_curated_blockers and curated_blocked_count <= 0:
        issues.append("curated dataset admission blockers are not visible")
    if rfi_real_data_authorized_count != expected_rfi_authorized:
        issues.append(
            "RFI database admission real-data authorization "
            f"{rfi_real_data_authorized_count} != expected {expected_rfi_authorized}"
        )
    if curated_real_data_authorized_count != expected_curated_authorized:
        issues.append(
            "curated dataset admission real-data authorization "
            f"{curated_real_data_authorized_count} != expected "
            f"{expected_curated_authorized}"
        )
    if require_production_blocker_gate and not production_blocker_ok:
        issues.append("production blocker consistency gate is not ok")

    return {
        "schema_version": REAL_DATA_ADMISSION_PREFLIGHT_SCHEMA_VERSION,
        "disclaimer": REAL_DATA_ADMISSION_PREFLIGHT_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "validation_ok": bool(validation["ok"]),
        "validation_issue_count": int(validation["issue_count"]),
        "expected_category_count": expected_category_count,
        "category_count": category_count,
        "category_ids": [category.category_id for category in categories],
        "blocked_category_count": blocked_category_count,
        "blocker_total": blocker_total,
        "min_blocker_total": min_blocker_total,
        "real_data_authorized_total": real_data_authorized_total,
        "expected_real_data_authorized_total": expected_real_data_total,
        "live_data_authorized_total": live_data_authorized_total,
        "external_submission_authorized_total": external_submission_authorized_total,
        "rfi_database_admission_blocked_count": rfi_blocked_count,
        "curated_dataset_admission_blocked_count": curated_blocked_count,
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
        "production_blocker_consistency_ok": production_blocker_ok,
        "production_blocker_consistency_issue_count": production_blocker_issue_count,
        "records": [category.as_dict() for category in categories],
    }
