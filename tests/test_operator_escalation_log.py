from __future__ import annotations

from techno_search.operator_escalation_log import (
    ALLOWED_OPERATOR_ESCALATION_SEVERITIES,
    ALLOWED_OPERATOR_ESCALATION_STATUSES,
    OPERATOR_ESCALATION_DISCLAIMER,
    OPERATOR_ESCALATION_SCHEMA_VERSION,
    OperatorEscalationEntry,
    load_operator_escalation_entries,
    operator_escalation_summary,
)


def test_schema_version() -> None:
    assert OPERATOR_ESCALATION_SCHEMA_VERSION == "operator_escalation_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in OPERATOR_ESCALATION_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in OPERATOR_ESCALATION_DISCLAIMER


def test_disclaimer_no_pathway_modification() -> None:
    assert "pathway routing" in OPERATOR_ESCALATION_DISCLAIMER


def test_disclaimer_severity_is_scheduling_priority() -> None:
    assert "scheduling priority" in OPERATOR_ESCALATION_DISCLAIMER


def test_allowed_severities() -> None:
    assert "routine" in ALLOWED_OPERATOR_ESCALATION_SEVERITIES
    assert "urgent" in ALLOWED_OPERATOR_ESCALATION_SEVERITIES
    assert "critical" in ALLOWED_OPERATOR_ESCALATION_SEVERITIES


def test_allowed_statuses() -> None:
    assert "open" in ALLOWED_OPERATOR_ESCALATION_STATUSES
    assert "acknowledged" in ALLOWED_OPERATOR_ESCALATION_STATUSES
    assert "resolved" in ALLOWED_OPERATOR_ESCALATION_STATUSES


def test_load_entries_count() -> None:
    entries = load_operator_escalation_entries()
    assert len(entries) == 4


def test_load_entries_types() -> None:
    entries = load_operator_escalation_entries()
    for e in entries:
        assert isinstance(e, OperatorEscalationEntry)


def test_first_entry_fields() -> None:
    entries = load_operator_escalation_entries()
    e = entries[0]
    assert e.escalation_id == "esc-001"
    assert e.candidate_id == "anomaly-clean-candidate"
    assert e.from_operator == "operator-beta"
    assert e.to_operator == "operator-alpha"
    assert e.severity == "critical"
    assert e.status == "open"
    assert e.resolved_utc is None


def test_acknowledged_entry_present() -> None:
    entries = load_operator_escalation_entries()
    ack = [e for e in entries if e.status == "acknowledged"]
    assert len(ack) == 1
    assert ack[0].escalation_id == "esc-002"


def test_resolved_entries_have_resolved_utc() -> None:
    entries = load_operator_escalation_entries()
    resolved = [e for e in entries if e.status == "resolved"]
    assert len(resolved) == 2
    for e in resolved:
        assert e.resolved_utc is not None


def test_open_entry_has_no_resolved_utc() -> None:
    entries = load_operator_escalation_entries()
    open_entries = [e for e in entries if e.status == "open"]
    assert len(open_entries) == 1
    assert open_entries[0].resolved_utc is None


def test_linked_alert_ids_populated() -> None:
    entries = load_operator_escalation_entries()
    e = entries[0]
    assert isinstance(e.linked_alert_ids, list)
    assert len(e.linked_alert_ids) >= 1


def test_as_dict_keys() -> None:
    entries = load_operator_escalation_entries()
    d = entries[0].as_dict()
    expected = {
        "escalation_id", "candidate_id", "from_operator", "to_operator",
        "escalation_reason", "severity", "status", "escalated_utc",
        "resolved_utc", "linked_alert_ids", "notes",
    }
    assert set(d.keys()) == expected


def test_as_dict_values_match() -> None:
    entries = load_operator_escalation_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["escalation_id"] == e.escalation_id
    assert d["severity"] == e.severity
    assert d["status"] == e.status


def test_summary_entry_count() -> None:
    s = operator_escalation_summary()
    assert s["entry_count"] == 4


def test_summary_open_count() -> None:
    s = operator_escalation_summary()
    assert s["open_count"] == 1


def test_summary_acknowledged_count() -> None:
    s = operator_escalation_summary()
    assert s["acknowledged_count"] == 1


def test_summary_resolved_count() -> None:
    s = operator_escalation_summary()
    assert s["resolved_count"] == 2


def test_summary_by_severity() -> None:
    s = operator_escalation_summary()
    bs = s["by_severity"]
    assert bs.get("critical", 0) == 2
    assert bs.get("urgent", 0) == 1
    assert bs.get("routine", 0) == 1


def test_summary_by_status() -> None:
    s = operator_escalation_summary()
    bst = s["by_status"]
    assert bst.get("open", 0) == 1
    assert bst.get("acknowledged", 0) == 1
    assert bst.get("resolved", 0) == 2


def test_summary_schema_version() -> None:
    s = operator_escalation_summary()
    assert s["schema_version"] == OPERATOR_ESCALATION_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = operator_escalation_summary()
    assert "disclaimer" in s
    assert "scheduling priority" in s["disclaimer"]
