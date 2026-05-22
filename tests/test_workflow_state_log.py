from __future__ import annotations

from techno_search.workflow_state_log import (
    ALLOWED_WORKFLOW_STATES,
    ALLOWED_WORKFLOW_TRANSITION_KINDS,
    WORKFLOW_STATE_DISCLAIMER,
    WORKFLOW_STATE_SCHEMA_VERSION,
    WorkflowStateEntry,
    load_workflow_state_entries,
    workflow_state_summary,
)


def test_schema_version() -> None:
    assert WORKFLOW_STATE_SCHEMA_VERSION == "workflow_state_log_v1"


def test_disclaimer_no_detection_claim() -> None:
    assert "detection claim" in WORKFLOW_STATE_DISCLAIMER


def test_disclaimer_no_external_submission() -> None:
    assert "authorize external submission" in WORKFLOW_STATE_DISCLAIMER


def test_disclaimer_no_pathway_modification() -> None:
    assert "pathway routing" in WORKFLOW_STATE_DISCLAIMER


def test_disclaimer_scheduling_aids() -> None:
    assert "scheduling aids" in WORKFLOW_STATE_DISCLAIMER


def test_allowed_states() -> None:
    assert "assigned" in ALLOWED_WORKFLOW_STATES
    assert "in_review" in ALLOWED_WORKFLOW_STATES
    assert "pending_second_opinion" in ALLOWED_WORKFLOW_STATES
    assert "escalated" in ALLOWED_WORKFLOW_STATES
    assert "closed" in ALLOWED_WORKFLOW_STATES
    assert "deferred" in ALLOWED_WORKFLOW_STATES


def test_allowed_transition_kinds() -> None:
    assert "initial_assign" in ALLOWED_WORKFLOW_TRANSITION_KINDS
    assert "state_change" in ALLOWED_WORKFLOW_TRANSITION_KINDS
    assert "reassign" in ALLOWED_WORKFLOW_TRANSITION_KINDS
    assert "close" in ALLOWED_WORKFLOW_TRANSITION_KINDS
    assert "reopen" in ALLOWED_WORKFLOW_TRANSITION_KINDS


def test_load_entries_count() -> None:
    entries = load_workflow_state_entries()
    assert len(entries) == 5


def test_load_entries_types() -> None:
    entries = load_workflow_state_entries()
    for e in entries:
        assert isinstance(e, WorkflowStateEntry)


def test_first_entry_fields() -> None:
    entries = load_workflow_state_entries()
    e = entries[0]
    assert e.transition_id == "wf-001"
    assert e.candidate_id == "radio-clean-candidate"
    assert e.transition_kind == "initial_assign"
    assert e.from_state is None
    assert e.to_state == "assigned"
    assert e.operator_id == "operator-alpha"
    assert e.assignment_id == "assign-001"


def test_initial_assign_has_null_from_state() -> None:
    entries = load_workflow_state_entries()
    initial = [e for e in entries if e.transition_kind == "initial_assign"]
    assert len(initial) == 2
    for e in initial:
        assert e.from_state is None


def test_close_transition_present() -> None:
    entries = load_workflow_state_entries()
    closed = [e for e in entries if e.transition_kind == "close"]
    assert len(closed) == 1
    assert closed[0].to_state == "closed"
    assert closed[0].transition_id == "wf-005"


def test_pending_second_opinion_entry() -> None:
    entries = load_workflow_state_entries()
    pending = [e for e in entries if e.to_state == "pending_second_opinion"]
    assert len(pending) == 1
    assert pending[0].transition_id == "wf-004"


def test_multiple_candidates_tracked() -> None:
    entries = load_workflow_state_entries()
    candidates = {e.candidate_id for e in entries}
    assert len(candidates) >= 2


def test_as_dict_keys() -> None:
    entries = load_workflow_state_entries()
    d = entries[0].as_dict()
    expected = {
        "transition_id", "candidate_id", "transition_kind",
        "from_state", "to_state", "operator_id", "transitioned_utc",
        "assignment_id", "notes",
    }
    assert set(d.keys()) == expected


def test_as_dict_values_match() -> None:
    entries = load_workflow_state_entries()
    e = entries[0]
    d = e.as_dict()
    assert d["transition_id"] == e.transition_id
    assert d["to_state"] == e.to_state
    assert d["transition_kind"] == e.transition_kind


def test_summary_entry_count() -> None:
    s = workflow_state_summary()
    assert s["entry_count"] == 5


def test_summary_unique_candidate_count() -> None:
    s = workflow_state_summary()
    assert s["unique_candidate_count"] == 3


def test_summary_closed_count() -> None:
    s = workflow_state_summary()
    assert s["closed_count"] == 1


def test_summary_open_transition_count() -> None:
    s = workflow_state_summary()
    assert s["open_transition_count"] == 4


def test_summary_by_to_state() -> None:
    s = workflow_state_summary()
    bts = s["by_to_state"]
    assert bts.get("assigned", 0) == 2
    assert bts.get("in_review", 0) == 1
    assert bts.get("pending_second_opinion", 0) == 1
    assert bts.get("closed", 0) == 1


def test_summary_by_kind() -> None:
    s = workflow_state_summary()
    bk = s["by_kind"]
    assert bk.get("initial_assign", 0) == 2
    assert bk.get("state_change", 0) == 2
    assert bk.get("close", 0) == 1


def test_summary_schema_version() -> None:
    s = workflow_state_summary()
    assert s["schema_version"] == WORKFLOW_STATE_SCHEMA_VERSION


def test_summary_disclaimer_present() -> None:
    s = workflow_state_summary()
    assert "disclaimer" in s
    assert "detection claim" in s["disclaimer"]
