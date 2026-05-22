from __future__ import annotations

from techno_search.alert_resolution_log import (
    ALERT_RESOLUTION_DISCLAIMER,
    ALERT_RESOLUTION_SCHEMA_VERSION,
    ALLOWED_ALERT_RESOLUTION_KINDS,
    ALLOWED_ALERT_RESOLUTION_STATUSES,
    AlertResolutionEntry,
    alert_resolution_summary,
    load_alert_resolution_entries,
)


def test_schema_version() -> None:
    assert ALERT_RESOLUTION_SCHEMA_VERSION == "alert_resolution_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in ALERT_RESOLUTION_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in ALERT_RESOLUTION_DISCLAIMER


def test_disclaimer_no_pathway_modification() -> None:
    assert "pathway routing" in ALERT_RESOLUTION_DISCLAIMER


def test_disclaimer_follow_up_is_local_action() -> None:
    assert "local scheduling action only" in ALERT_RESOLUTION_DISCLAIMER


def test_allowed_statuses() -> None:
    assert "resolved_false_positive" in ALLOWED_ALERT_RESOLUTION_STATUSES
    assert "resolved_follow_up" in ALLOWED_ALERT_RESOLUTION_STATUSES
    assert "resolved_archived" in ALLOWED_ALERT_RESOLUTION_STATUSES
    assert "resolved_operator_closed" in ALLOWED_ALERT_RESOLUTION_STATUSES
    assert "open" in ALLOWED_ALERT_RESOLUTION_STATUSES


def test_allowed_kinds() -> None:
    assert "operator_review" in ALLOWED_ALERT_RESOLUTION_KINDS
    assert "automated_consistency_check" in ALLOWED_ALERT_RESOLUTION_KINDS
    assert "deadline_expiry" in ALLOWED_ALERT_RESOLUTION_KINDS
    assert "pathway_confirmed" in ALLOWED_ALERT_RESOLUTION_KINDS
    assert "watchlist_action" in ALLOWED_ALERT_RESOLUTION_KINDS


def test_load_entries_count() -> None:
    entries = load_alert_resolution_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_alert_resolution_entries()
    for e in entries:
        assert isinstance(e, AlertResolutionEntry)


def test_first_entry_fields() -> None:
    entries = load_alert_resolution_entries()
    e = entries[0]
    assert e.resolution_id == "ares-001"
    assert e.candidate_id == "radio-clean-candidate"
    assert e.status == "resolved_false_positive"
    assert e.resolution_kind == "operator_review"
    assert e.resolving_operator == "operator-alpha"
    assert "alrt-001" in e.linked_alert_ids


def test_open_entry_present() -> None:
    entries = load_alert_resolution_entries()
    open_entries = [e for e in entries if e.status == "open"]
    assert len(open_entries) == 1
    assert open_entries[0].resolution_id == "ares-005"


def test_resolved_false_positive_count() -> None:
    entries = load_alert_resolution_entries()
    fp_entries = [e for e in entries if e.status == "resolved_false_positive"]
    assert len(fp_entries) == 2


def test_linked_alert_ids_list() -> None:
    entries = load_alert_resolution_entries()
    # ares-004 has no linked alerts
    empty = [e for e in entries if e.resolution_id == "ares-004"]
    assert len(empty) == 1
    assert empty[0].linked_alert_ids == []


def test_multiple_linked_alerts() -> None:
    entries = load_alert_resolution_entries()
    multi = [e for e in entries if e.resolution_id == "ares-005"]
    assert len(multi) == 1
    assert len(multi[0].linked_alert_ids) == 2


def test_as_dict_keys() -> None:
    entries = load_alert_resolution_entries()
    d = entries[0].as_dict()
    expected = {
        "resolution_id", "candidate_id", "linked_alert_ids",
        "status", "resolution_kind", "resolving_operator",
        "resolution_utc", "notes",
    }
    assert set(d.keys()) == expected


def test_as_dict_values_match() -> None:
    entries = load_alert_resolution_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["resolution_id"] == e.resolution_id
    assert d["status"] == e.status
    assert d["linked_alert_ids"] == e.linked_alert_ids


def test_summary_entry_count() -> None:
    s = alert_resolution_summary()
    assert s["entry_count"] == 5


def test_summary_open_count() -> None:
    s = alert_resolution_summary()
    assert s["open_count"] == 1


def test_summary_resolved_count() -> None:
    s = alert_resolution_summary()
    assert s["resolved_count"] == 4


def test_summary_by_status() -> None:
    s = alert_resolution_summary()
    bs = s["by_status"]
    assert bs.get("resolved_false_positive", 0) == 2
    assert bs.get("resolved_follow_up", 0) == 1
    assert bs.get("resolved_archived", 0) == 1
    assert bs.get("open", 0) == 1


def test_summary_by_kind() -> None:
    s = alert_resolution_summary()
    bk = s["by_kind"]
    assert "operator_review" in bk
    assert "pathway_confirmed" in bk
    assert "automated_consistency_check" in bk


def test_summary_schema_version() -> None:
    s = alert_resolution_summary()
    assert s["schema_version"] == ALERT_RESOLUTION_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = alert_resolution_summary()
    assert "disclaimer" in s
    assert "detection claim" in s["disclaimer"]
