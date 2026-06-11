"""Tests for calibration_corpus_admission module and fixture."""

from __future__ import annotations

import json
from pathlib import Path

from techno_search.calibration_corpus_admission import (
    ALLOWED_CALIBRATION_CORPUS_ADMISSION_STATUSES,
    CALIBRATION_CORPUS_ADMISSION_DISCLAIMER,
    CALIBRATION_CORPUS_ADMISSION_SCHEMA_VERSION,
    CalibrationCorpusAdmissionRecord,
    calibration_corpus_admission_summary,
    load_calibration_corpus_admission_records,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "calibration_corpus_admission.json"
)


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------


def test_fixture_exists():
    assert FIXTURE_PATH.exists()


def test_fixture_is_valid_json():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "calibration_corpus_admission_records" in data


def test_load_returns_records():
    records = load_calibration_corpus_admission_records(FIXTURE_PATH)
    assert len(records) >= 1
    assert all(isinstance(r, CalibrationCorpusAdmissionRecord) for r in records)


def test_fixture_has_five_records():
    records = load_calibration_corpus_admission_records(FIXTURE_PATH)
    assert len(records) == 5


# ---------------------------------------------------------------------------
# Record fields
# ---------------------------------------------------------------------------


def test_all_statuses_valid():
    records = load_calibration_corpus_admission_records(FIXTURE_PATH)
    for r in records:
        assert r.admission_status in ALLOWED_CALIBRATION_CORPUS_ADMISSION_STATUSES, (
            f"{r.corpus_id}: unexpected status '{r.admission_status}'"
        )


def test_no_record_has_real_data_authorized():
    records = load_calibration_corpus_admission_records(FIXTURE_PATH)
    for r in records:
        assert r.real_data_authorized is False, (
            f"{r.corpus_id}: real_data_authorized must be False"
        )


def test_voyager1_is_already_admitted():
    records = load_calibration_corpus_admission_records(FIXTURE_PATH)
    voyager = next((r for r in records if r.target_id == "Voyager1"), None)
    assert voyager is not None
    assert voyager.admission_status == "already_admitted"
    assert voyager.h5_downloaded is True
    assert voyager.turboseti_validated is True
    assert voyager.provenance_reviewed is True


def test_new_targets_are_blocked():
    records = load_calibration_corpus_admission_records(FIXTURE_PATH)
    for r in records:
        if r.target_id == "Voyager1":
            continue
        assert r.admission_status.startswith("blocked_"), (
            f"{r.target_id} should be blocked"
        )
        assert r.h5_downloaded is False
        assert r.blocker_count > 0


def test_all_records_have_corpus_id():
    records = load_calibration_corpus_admission_records(FIXTURE_PATH)
    ids = {r.corpus_id for r in records}
    assert len(ids) == len(records), "corpus_id values must be unique"


def test_hip_targets_present():
    records = load_calibration_corpus_admission_records(FIXTURE_PATH)
    target_ids = {r.target_id for r in records}
    for hip in ("HIP65803", "HIP4436", "HIP8102", "HIP16537"):
        assert hip in target_ids, f"{hip} not in admission fixture"


def test_all_records_have_notes():
    records = load_calibration_corpus_admission_records(FIXTURE_PATH)
    for r in records:
        assert r.notes and len(r.notes.strip()) > 10, (
            f"{r.corpus_id} has empty or very short notes"
        )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def test_summary_ok():
    summary = calibration_corpus_admission_summary(FIXTURE_PATH)
    assert summary["ok"] is True
    assert summary["record_count"] == 5
    assert summary["safety_ok"] is True
    assert summary["real_data_authorized_count"] == 0


def test_summary_admitted_count():
    summary = calibration_corpus_admission_summary(FIXTURE_PATH)
    assert summary["admitted_count"] == 1


def test_summary_blocked_count():
    summary = calibration_corpus_admission_summary(FIXTURE_PATH)
    assert summary["blocked_count"] == 4


def test_summary_total_blockers():
    summary = calibration_corpus_admission_summary(FIXTURE_PATH)
    assert summary["total_blocker_count"] == 12  # 4 targets × 3 blockers each


def test_summary_schema_version():
    summary = calibration_corpus_admission_summary(FIXTURE_PATH)
    assert summary["schema_version"] == CALIBRATION_CORPUS_ADMISSION_SCHEMA_VERSION


def test_summary_has_disclaimer():
    summary = calibration_corpus_admission_summary(FIXTURE_PATH)
    assert "disclaimer" in summary
    assert "detection claim" in summary["disclaimer"].lower()
    assert "external submission" in summary["disclaimer"].lower()


def test_summary_records_field():
    summary = calibration_corpus_admission_summary(FIXTURE_PATH)
    assert len(summary["records"]) == 5
    for r in summary["records"]:
        assert "corpus_id" in r
        assert "admission_status" in r
        assert "real_data_authorized" in r


# ---------------------------------------------------------------------------
# Safety gate — real_data_authorized must remain False
# ---------------------------------------------------------------------------


def test_safety_fails_if_real_data_authorized(tmp_path):
    """Summary must flag a record that wrongly sets real_data_authorized=True."""
    bad_fixture = {
        "calibration_corpus_admission_records": [
            {
                "corpus_id": "bad-record",
                "target_id": "HIP99999",
                "source_label": "Bad test record",
                "admission_status": "ready_for_local_calibration",
                "h5_downloaded": True,
                "turboseti_validated": True,
                "provenance_reviewed": True,
                "human_approval_status": "approved",
                "real_data_authorized": True,
                "blocker_count": 0,
                "notes": "This has real_data_authorized=true, which must be flagged.",
            }
        ]
    }
    bad_path = tmp_path / "bad_admission.json"
    bad_path.write_text(json.dumps(bad_fixture), encoding="utf-8")
    summary = calibration_corpus_admission_summary(bad_path)
    assert summary["ok"] is False
    assert summary["safety_ok"] is False
    assert summary["real_data_authorized_count"] == 1
    assert any("real_data_authorized=true" in issue for issue in summary["issues"])


def test_safety_flags_inconsistent_approval(tmp_path):
    """approved human_approval_status with blocker_count > 0 must be flagged."""
    bad_fixture = {
        "calibration_corpus_admission_records": [
            {
                "corpus_id": "inconsistent-record",
                "target_id": "HIP11111",
                "source_label": "Inconsistent approval",
                "admission_status": "blocked_pending_review",
                "h5_downloaded": True,
                "turboseti_validated": True,
                "provenance_reviewed": True,
                "human_approval_status": "approved",
                "real_data_authorized": False,
                "blocker_count": 2,
                "notes": "Approved but blockers > 0 — should be flagged.",
            }
        ]
    }
    bad_path = tmp_path / "inconsistent_admission.json"
    bad_path.write_text(json.dumps(bad_fixture), encoding="utf-8")
    summary = calibration_corpus_admission_summary(bad_path)
    assert summary["ok"] is False
    assert any("blocker_count" in issue for issue in summary["issues"])


# ---------------------------------------------------------------------------
# Disclaimer language
# ---------------------------------------------------------------------------


def test_disclaimer_no_detection_claim():
    assert "detection claim" in CALIBRATION_CORPUS_ADMISSION_DISCLAIMER.lower()


def test_disclaimer_no_external_submission():
    assert "external submission" in CALIBRATION_CORPUS_ADMISSION_DISCLAIMER.lower()


def test_disclaimer_no_forbidden_language():
    forbidden = ["confirmed detection", "confirmed technosignature", "definitive"]
    for phrase in forbidden:
        assert phrase.lower() not in CALIBRATION_CORPUS_ADMISSION_DISCLAIMER.lower(), (
            f"Disclaimer must not contain '{phrase}'"
        )
