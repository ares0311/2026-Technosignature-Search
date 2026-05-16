"""Tests for candidate_audit_trail module."""

from __future__ import annotations

from techno_search.candidate_audit_trail import (
    ALLOWED_AUDIT_ACTION_TYPES,
    CANDIDATE_AUDIT_TRAIL_DISCLAIMER,
    CANDIDATE_AUDIT_TRAIL_SCHEMA_VERSION,
    CandidateAuditAction,
    audit_trail_summary,
    load_audit_trail,
)


def test_load_audit_trail_returns_list():
    actions = load_audit_trail()
    assert isinstance(actions, list)
    assert len(actions) >= 6


def test_audit_action_is_dataclass():
    actions = load_audit_trail()
    for action in actions:
        assert isinstance(action, CandidateAuditAction)
        assert action.action_id
        assert action.candidate_id
        assert action.action_type in ALLOWED_AUDIT_ACTION_TYPES
        assert action.operator_id


def test_audit_trail_has_multiple_candidates():
    actions = load_audit_trail()
    candidates = {a.candidate_id for a in actions}
    assert len(candidates) >= 2


def test_audit_trail_has_multiple_operators():
    actions = load_audit_trail()
    operators = {a.operator_id for a in actions}
    assert len(operators) >= 2


def test_audit_trail_has_irreversible_actions():
    actions = load_audit_trail()
    irreversible = [a for a in actions if not a.is_reversible]
    assert len(irreversible) >= 3


def test_audit_trail_has_reversible_actions():
    actions = load_audit_trail()
    reversible = [a for a in actions if a.is_reversible]
    assert len(reversible) >= 1


def test_audit_trail_summary_schema_version():
    summary = audit_trail_summary()
    assert summary["schema_version"] == CANDIDATE_AUDIT_TRAIL_SCHEMA_VERSION


def test_audit_trail_summary_disclaimer():
    summary = audit_trail_summary()
    assert CANDIDATE_AUDIT_TRAIL_DISCLAIMER in summary["disclaimer"]


def test_audit_trail_summary_counts():
    summary = audit_trail_summary()
    assert isinstance(summary["action_count"], int)
    assert summary["action_count"] >= 6
    assert isinstance(summary["unique_operator_count"], int)
    assert summary["unique_operator_count"] >= 2
    assert isinstance(summary["irreversible_action_count"], int)
    assert summary["irreversible_action_count"] >= 3


def test_audit_trail_summary_by_action_type():
    summary = audit_trail_summary()
    by_action = summary["by_action_type"]
    assert isinstance(by_action, dict)
    assert len(by_action) >= 3


def test_audit_trail_summary_by_candidate():
    summary = audit_trail_summary()
    by_candidate = summary["by_candidate"]
    assert isinstance(by_candidate, dict)
    assert len(by_candidate) >= 2


def test_candidate_audit_action_as_dict():
    actions = load_audit_trail()
    d = actions[0].as_dict()
    for key in ("action_id", "candidate_id", "action_type", "operator_id",
                "timestamp_utc", "detail", "is_reversible"):
        assert key in d


def test_allowed_audit_action_types():
    assert "triage_note_added" in ALLOWED_AUDIT_ACTION_TYPES
    assert "stage_transition" in ALLOWED_AUDIT_ACTION_TYPES
    assert "observation_scheduled" in ALLOWED_AUDIT_ACTION_TYPES
    assert "observation_completed" in ALLOWED_AUDIT_ACTION_TYPES
    assert "archived" in ALLOWED_AUDIT_ACTION_TYPES
    assert "human_reviewed" in ALLOWED_AUDIT_ACTION_TYPES
