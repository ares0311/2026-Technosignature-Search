from __future__ import annotations

from techno_search.intake_queue_log import (
    ALLOWED_INTAKE_SOURCE_KINDS,
    ALLOWED_INTAKE_STATUSES,
    INTAKE_QUEUE_DISCLAIMER,
    INTAKE_QUEUE_SCHEMA_VERSION,
    IntakeQueueEntry,
    intake_queue_summary,
    load_intake_queue_entries,
)


def test_schema_version() -> None:
    assert INTAKE_QUEUE_SCHEMA_VERSION == "intake_queue_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in INTAKE_QUEUE_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in INTAKE_QUEUE_DISCLAIMER


def test_disclaimer_no_live_provider() -> None:
    assert "live-provider access" in INTAKE_QUEUE_DISCLAIMER


def test_disclaimer_intake_blocked() -> None:
    assert "Intake remains blocked" in INTAKE_QUEUE_DISCLAIMER


def test_allowed_statuses() -> None:
    assert "queued" in ALLOWED_INTAKE_STATUSES
    assert "blocked" in ALLOWED_INTAKE_STATUSES
    assert "intake_ready" in ALLOWED_INTAKE_STATUSES
    assert "intake_complete" in ALLOWED_INTAKE_STATUSES
    assert "cancelled" in ALLOWED_INTAKE_STATUSES


def test_allowed_source_kinds() -> None:
    assert "radio_survey" in ALLOWED_INTAKE_SOURCE_KINDS
    assert "infrared_catalog" in ALLOWED_INTAKE_SOURCE_KINDS
    assert "archival_image" in ALLOWED_INTAKE_SOURCE_KINDS
    assert "spectral_archive" in ALLOWED_INTAKE_SOURCE_KINDS
    assert "unknown" in ALLOWED_INTAKE_SOURCE_KINDS


def test_load_entries_count() -> None:
    entries = load_intake_queue_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_intake_queue_entries()
    for e in entries:
        assert isinstance(e, IntakeQueueEntry)


def test_first_entry_fields() -> None:
    entries = load_intake_queue_entries()
    e = entries[0]
    assert e.intake_id == "intake-001"
    assert e.source_kind == "radio_survey"
    assert e.status == "blocked"
    assert e.queue_position == 1
    assert e.requested_by == "operator-alpha"
    assert e.blocking_reason is not None
    assert e.intake_utc is None


def test_blocked_entries_count() -> None:
    entries = load_intake_queue_entries()
    blocked = [e for e in entries if e.status == "blocked"]
    assert len(blocked) == 2


def test_queued_entry_present() -> None:
    entries = load_intake_queue_entries()
    queued = [e for e in entries if e.status == "queued"]
    assert len(queued) == 1
    assert queued[0].intake_id == "intake-003"


def test_intake_ready_entry_present() -> None:
    entries = load_intake_queue_entries()
    ready = [e for e in entries if e.status == "intake_ready"]
    assert len(ready) == 1
    assert ready[0].intake_id == "intake-004"


def test_cancelled_entry_present() -> None:
    entries = load_intake_queue_entries()
    cancelled = [e for e in entries if e.status == "cancelled"]
    assert len(cancelled) == 1
    assert cancelled[0].intake_id == "intake-005"


def test_blocked_entries_have_blocking_reason() -> None:
    entries = load_intake_queue_entries()
    blocked = [e for e in entries if e.status == "blocked"]
    for e in blocked:
        assert e.blocking_reason is not None


def test_as_dict_keys() -> None:
    entries = load_intake_queue_entries()
    d = entries[0].as_dict()
    expected = {
        "intake_id", "source_kind", "source_description", "status",
        "queue_position", "requested_by", "requested_utc",
        "blocking_reason", "intake_utc", "notes",
    }
    assert set(d.keys()) == expected


def test_as_dict_values_match() -> None:
    entries = load_intake_queue_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["intake_id"] == e.intake_id
    assert d["status"] == e.status
    assert d["queue_position"] == e.queue_position


def test_summary_entry_count() -> None:
    s = intake_queue_summary()
    assert s["entry_count"] == 5


def test_summary_blocked_count() -> None:
    s = intake_queue_summary()
    assert s["blocked_count"] == 2


def test_summary_queued_count() -> None:
    s = intake_queue_summary()
    assert s["queued_count"] == 1


def test_summary_ready_count() -> None:
    s = intake_queue_summary()
    assert s["ready_count"] == 1


def test_summary_by_status() -> None:
    s = intake_queue_summary()
    bs = s["by_status"]
    assert bs.get("blocked", 0) == 2
    assert bs.get("queued", 0) == 1
    assert bs.get("intake_ready", 0) == 1
    assert bs.get("cancelled", 0) == 1


def test_summary_by_kind() -> None:
    s = intake_queue_summary()
    bk = s["by_kind"]
    assert "radio_survey" in bk
    assert "infrared_catalog" in bk
    assert "archival_image" in bk


def test_summary_schema_version() -> None:
    s = intake_queue_summary()
    assert s["schema_version"] == INTAKE_QUEUE_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = intake_queue_summary()
    assert "disclaimer" in s
    assert "detection claim" in s["disclaimer"]
