"""Admission records for calibration corpus targets.

These records gate whether a Breakthrough Listen archive target has completed
the provenance, turboSETI validation, and human-approval checks required before
its hit tables can be admitted into the noise_threshold_calibration corpus.

They do not ingest real observation data, modify candidate scores, or authorize
external submission.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CALIBRATION_CORPUS_ADMISSION_SCHEMA_VERSION = "calibration_corpus_admission_v1"

CALIBRATION_CORPUS_ADMISSION_DISCLAIMER = (
    "Calibration corpus admission records are local readiness checks for "
    "proposed BL archive observation targets. They do not ingest real "
    "observation data, modify scoring thresholds, calibrate detection "
    "sensitivities, authorize external submission, or constitute a "
    "detection claim, discovery, or external validation."
)

ALLOWED_CALIBRATION_CORPUS_ADMISSION_STATUSES = frozenset(
    {
        "already_admitted",
        "blocked_pending_download",
        "blocked_pending_provenance",
        "blocked_pending_turboseti",
        "blocked_pending_review",
        "ready_for_local_calibration",
    }
)


def _default_admission_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "calibration_corpus_admission.json"
    )


@dataclass(frozen=True)
class CalibrationCorpusAdmissionRecord:
    corpus_id: str
    target_id: str
    source_label: str
    admission_status: str
    h5_downloaded: bool
    turboseti_validated: bool
    provenance_reviewed: bool
    human_approval_status: str
    real_data_authorized: bool
    blocker_count: int
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "corpus_id": self.corpus_id,
            "target_id": self.target_id,
            "source_label": self.source_label,
            "admission_status": self.admission_status,
            "h5_downloaded": self.h5_downloaded,
            "turboseti_validated": self.turboseti_validated,
            "provenance_reviewed": self.provenance_reviewed,
            "human_approval_status": self.human_approval_status,
            "real_data_authorized": self.real_data_authorized,
            "blocker_count": self.blocker_count,
            "notes": self.notes,
        }


def load_calibration_corpus_admission_records(
    path: Path | None = None,
) -> list[CalibrationCorpusAdmissionRecord]:
    admission_path = path if path is not None else _default_admission_path()
    raw = json.loads(admission_path.read_text(encoding="utf-8"))
    records_raw = raw.get("calibration_corpus_admission_records", [])
    return [
        CalibrationCorpusAdmissionRecord(
            corpus_id=str(r["corpus_id"]),
            target_id=str(r["target_id"]),
            source_label=str(r["source_label"]),
            admission_status=str(r["admission_status"]),
            h5_downloaded=bool(r.get("h5_downloaded", False)),
            turboseti_validated=bool(r.get("turboseti_validated", False)),
            provenance_reviewed=bool(r.get("provenance_reviewed", False)),
            human_approval_status=str(r.get("human_approval_status", "pending")),
            real_data_authorized=bool(r.get("real_data_authorized", False)),
            blocker_count=int(r.get("blocker_count", 0)),
            notes=str(r.get("notes", "")),
        )
        for r in records_raw
    ]


def calibration_corpus_admission_summary(
    path: Path | None = None,
) -> dict[str, Any]:
    records = load_calibration_corpus_admission_records(path)
    total = len(records)
    _admitted_statuses = frozenset({"already_admitted", "ready_for_local_calibration"})
    admitted = sum(1 for r in records if r.admission_status in _admitted_statuses)
    blocked = sum(
        1 for r in records if r.admission_status.startswith("blocked_")
    )
    real_authorized = sum(1 for r in records if r.real_data_authorized)
    total_blockers = sum(r.blocker_count for r in records)

    safety_ok = real_authorized == 0

    issues: list[str] = []
    for r in records:
        if r.admission_status not in ALLOWED_CALIBRATION_CORPUS_ADMISSION_STATUSES:
            issues.append(
                f"{r.corpus_id}: unknown admission_status '{r.admission_status}'"
            )
        if r.real_data_authorized:
            issues.append(
                f"{r.corpus_id}: real_data_authorized=true — "
                "calibration corpus admission does not authorize real-data use; "
                "this must be tracked through observation_artifact provenance."
            )
        if r.human_approval_status == "approved" and r.blocker_count > 0:
            issues.append(
                f"{r.corpus_id}: human_approval_status=approved but "
                f"blocker_count={r.blocker_count} — inconsistent state."
            )

    return {
        "schema_version": CALIBRATION_CORPUS_ADMISSION_SCHEMA_VERSION,
        "disclaimer": CALIBRATION_CORPUS_ADMISSION_DISCLAIMER,
        "ok": not issues,
        "record_count": total,
        "admitted_count": admitted,
        "blocked_count": blocked,
        "real_data_authorized_count": real_authorized,
        "total_blocker_count": total_blockers,
        "safety_ok": safety_ok,
        "records": [r.as_dict() for r in records],
        "issues": issues,
    }
