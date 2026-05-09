from pathlib import Path

import pytest

from techno_search.background_search import (
    BACKGROUND_FOLLOW_UP_TEST_DISCLAIMER,
    BACKGROUND_NEEDS_FOLLOW_UP_DISCLAIMER,
    BACKGROUND_REPORT_READINESS_DISCLAIMER,
    BACKGROUND_REVIEWED_LOG_DISCLAIMER,
    BACKGROUND_SEARCH_LEDGER_DISCLAIMER,
    CANDIDATE_EXTRACTION_HANDOFF_DISCLAIMER,
    MANDATORY_FOLLOW_UP_TESTS,
    TARGET_PRIORITY_DISCLAIMER,
    background_follow_up_test_summary,
    background_needs_follow_up_summary,
    background_report_readiness_summary,
    background_review_workflow_summary,
    background_reviewed_log_summary,
    background_search_ledger_summary,
    candidate_extraction_handoff_summary,
    load_background_follow_up_tests,
    load_background_needs_follow_up_log,
    load_background_priority_config,
    load_background_report_readiness,
    load_background_reviewed_log,
    load_background_search_ledger,
    load_background_targets,
    load_candidate_extraction_handoffs,
    run_local_background_search_once,
    target_priority_score,
    target_priority_summary,
    target_selection_score,
)


def test_background_targets_load_with_conservative_disclaimer() -> None:
    targets = load_background_targets()

    assert len(targets) == 4
    assert {target.track.value for target in targets} == {
        "anomaly",
        "infrared",
        "radio",
    }
    assert TARGET_PRIORITY_DISCLAIMER.endswith("discovery claim.")
    assert all(0.0 <= target.false_positive_probability <= 1.0 for target in targets)


def test_target_priority_score_prefers_cleaner_high_value_target() -> None:
    config = load_background_priority_config()
    targets = load_background_targets()
    scores = {
        target.target_id: target_priority_score(target, config=config)
        for target in targets
    }

    assert scores["target-radio-clean-drift"] == 0.7515
    assert scores["target-infrared-excess-review"] == 0.613
    assert scores["target-radio-never-reviewed"] == 0.6915
    assert scores["target-anomaly-weak-context"] == 0.335
    assert max(scores, key=scores.__getitem__) == "target-radio-clean-drift"


def test_target_priority_summary_ranks_targets_and_exposes_weights() -> None:
    summary = target_priority_summary()

    assert summary["schema_version"] == "background_target_priority_v1"
    assert summary["config_version"] == "background_priority_v0"
    assert summary["target_count"] == 4
    assert summary["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 2}
    assert summary["selected_target_id"] == "target-radio-clean-drift"
    assert summary["selected_priority_score"] == 0.7515
    assert summary["selected_selection_score"] == 0.8315
    assert summary["weights"]["false_positive_probability"] < 0
    assert summary["never_reviewed_target_boost"] == 0.08
    assert summary["prior_review_penalty_per_entry"] == 0.04
    assert summary["needs_follow_up_priority_threshold"] == 0.7
    assert summary["passive_runner_requires_opt_in"] is True
    assert summary["network_access_enabled"] is False
    assert "not evidence" in summary["disclaimer"]
    assert [
        target["target_id"] for target in summary["ranked_targets"]
    ] == [
        "target-radio-clean-drift",
        "target-radio-never-reviewed",
        "target-infrared-excess-review",
        "target-anomaly-weak-context",
    ]


def test_target_selection_summary_boosts_unreviewed_promising_targets() -> None:
    summary = target_priority_summary(
        ledger_path=Path("tests/fixtures/background_search_ledger.json")
    )

    assert summary["selected_target_id"] == "target-radio-never-reviewed"
    assert summary["selected_priority_score"] == 0.6915
    assert summary["selected_selection_score"] == 0.7715
    ranked = summary["ranked_targets"]
    assert ranked[0]["target_id"] == "target-radio-never-reviewed"
    assert ranked[0]["prior_review_count"] == 0
    assert ranked[1]["target_id"] == "target-radio-clean-drift"
    assert ranked[1]["prior_review_count"] == 2


def test_target_selection_score_penalizes_previous_reviews() -> None:
    config = load_background_priority_config()
    target = next(
        target
        for target in load_background_targets()
        if target.target_id == "target-radio-clean-drift"
    )

    assert target_selection_score(target, config=config, prior_review_count=0) == 0.8315
    assert target_selection_score(target, config=config, prior_review_count=2) == 0.6715


def test_background_search_ledger_loads_audited_search_entries() -> None:
    entries = load_background_search_ledger()

    assert len(entries) == 4
    assert entries[0].run_id == "background-demo-001"
    assert entries[0].recommended_pathways == ("candidate_review_packet",)
    assert entries[0].candidate_packet_ids == ("radio-clean-001",)
    assert entries[1].reviewed_workflow_status == "review_blocked"
    assert entries[2].negative_result_logged is True
    assert entries[2].candidate_count == 0
    assert entries[3].execution_mode == "local_non_network_fixture_runner"
    assert entries[3].reviewed_workflow_status == "local_scheduling_only"
    assert BACKGROUND_SEARCH_LEDGER_DISCLAIMER.endswith("discovery claims.")


def test_background_search_ledger_summary_counts_searched_targets() -> None:
    summary = background_search_ledger_summary()

    assert summary["schema_version"] == "background_search_ledger_v1"
    assert summary["entry_count"] == 4
    assert summary["searched_target_count"] == 3
    assert summary["candidate_count"] == 2
    assert summary["candidate_packet_id_count"] == 2
    assert summary["blocking_issue_count"] == 4
    assert summary["negative_result_logged_count"] == 2
    assert summary["requires_human_review_count"] == 2
    assert summary["scheduling_only_count"] == 1
    assert summary["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 2}
    assert summary["by_status"] == {
        "completed": 1,
        "completed_with_blockers": 1,
        "local_fixture_search_logged": 1,
        "searched_no_candidate": 1,
    }
    assert summary["by_reviewed_workflow_status"] == {
        "candidate_packet_ready": 1,
        "local_scheduling_only": 1,
        "negative_search_recorded": 1,
        "review_blocked": 1,
    }
    assert summary["by_recommended_pathway"] == {
        "candidate_review_packet": 1,
        "github_reproducibility_only": 2,
        "human_review_queue": 1,
    }
    assert summary["target_ids"] == [
        "target-anomaly-weak-context",
        "target-infrared-excess-review",
        "target-radio-clean-drift",
    ]
    assert "not discovery claims" in summary["disclaimer"]


def test_background_reviewed_log_loads_conservative_outcomes() -> None:
    entries = load_background_reviewed_log()

    assert len(entries) == 2
    assert entries[0].outcome_status == "reviewed_no_follow_up"
    assert entries[0].recommended_next_action == "retain_in_reviewed_log"
    assert all(entry.network_access_allowed is False for entry in entries)
    assert "not external validation" in BACKGROUND_REVIEWED_LOG_DISCLAIMER


def test_background_reviewed_log_summary_counts_negative_evidence() -> None:
    summary = background_reviewed_log_summary()

    assert summary["schema_version"] == "background_reviewed_log_v1"
    assert summary["entry_count"] == 2
    assert summary["negative_evidence_count"] == 4
    assert summary["blocking_issue_count"] == 3
    assert summary["network_access_allowed_count"] == 0
    assert summary["by_track"] == {"anomaly": 1, "radio": 1}
    assert summary["by_outcome_status"] == {"reviewed_no_follow_up": 2}
    assert "local_scheduling_only" in summary["reason_codes"]
    assert "not external validation" in summary["disclaimer"]


def test_background_needs_follow_up_log_loads_approval_gate() -> None:
    entries = load_background_needs_follow_up_log()

    assert len(entries) == 2
    assert entries[0].follow_up_status == "needs_follow_up_required"
    assert entries[0].required_tests == MANDATORY_FOLLOW_UP_TESTS
    assert all(entry.human_review_required is True for entry in entries)
    assert all(entry.submission_requires_user_approval is True for entry in entries)
    assert all(entry.network_access_allowed is False for entry in entries)
    assert "not detections" in BACKGROUND_NEEDS_FOLLOW_UP_DISCLAIMER


def test_background_needs_follow_up_summary_counts_mandatory_tests() -> None:
    summary = background_needs_follow_up_summary()

    assert summary["schema_version"] == "background_needs_follow_up_log_v1"
    assert summary["entry_count"] == 2
    assert summary["required_test_count"] == 12
    assert summary["mandatory_test_coverage_count"] == 6
    assert summary["blocking_issue_count"] == 1
    assert summary["report_required_count"] == 2
    assert summary["human_review_required_count"] == 2
    assert summary["submission_requires_user_approval_count"] == 2
    assert summary["network_access_allowed_count"] == 0
    assert summary["by_track"] == {"infrared": 1, "radio": 1}
    assert summary["by_trigger_type"] == {
        "quantitative_threshold": 2,
        "rule_based_blocking_issue": 1,
    }
    assert "human_review_checklist" in summary["required_tests"]
    assert "not detections" in summary["disclaimer"]


def test_background_follow_up_tests_load_mandatory_local_checks() -> None:
    records = load_background_follow_up_tests()

    assert len(records) == 12
    assert records[0].test_name == "provenance_check"
    assert records[0].status == "pass"
    assert records[5].test_name == "human_review_checklist"
    assert records[5].status == "ready"
    assert {record.follow_up_id for record in records} == {
        "follow-up-background-demo-001",
        "follow-up-background-demo-002",
    }
    assert set(MANDATORY_FOLLOW_UP_TESTS) <= {record.test_name for record in records}
    assert all(record.network_access_allowed is False for record in records)
    assert "not external validation" in BACKGROUND_FOLLOW_UP_TEST_DISCLAIMER


def test_background_follow_up_test_summary_counts_statuses() -> None:
    summary = background_follow_up_test_summary()

    assert summary["schema_version"] == "background_follow_up_tests_v1"
    assert summary["result_count"] == 12
    assert summary["follow_up_count"] == 2
    assert summary["complete_follow_up_test_set_count"] == 2
    assert summary["mandatory_test_count"] == 6
    assert summary["blocking_issue_count"] == 4
    assert summary["uncertainty_note_count"] == 12
    assert summary["network_access_allowed_count"] == 0
    assert summary["by_track"] == {"infrared": 6, "radio": 6}
    assert summary["by_status"] == {
        "blocked": 2,
        "pass": 7,
        "ready": 1,
        "uncertain": 2,
    }
    assert summary["complete_follow_up_ids"] == [
        "follow-up-background-demo-001",
        "follow-up-background-demo-002",
    ]
    assert "human_review_checklist" in summary["required_tests"]
    assert "not external validation" in summary["disclaimer"]


def test_background_report_readiness_loads_submission_gate() -> None:
    records = load_background_report_readiness()

    assert len(records) == 2
    assert records[0].readiness_status == "ready_for_draft_report"
    assert records[0].ready_to_draft_report is True
    assert len(records[0].top_three_recommendations) == 3
    assert records[1].readiness_status == "blocked_pending_tests"
    assert records[1].top_three_recommendations[0].destination == "Do not submit yet"
    assert all(record.user_approval_required is True for record in records)
    assert all(record.external_submission_allowed is False for record in records)
    assert all(record.network_access_allowed is False for record in records)
    assert "not discoveries" in BACKGROUND_REPORT_READINESS_DISCLAIMER


def test_background_report_readiness_summary_counts_top_three() -> None:
    summary = background_report_readiness_summary()

    assert summary["schema_version"] == "background_report_readiness_v1"
    assert summary["record_count"] == 2
    assert summary["ready_to_draft_report_count"] == 1
    assert summary["blocked_count"] == 1
    assert summary["report_required_count"] == 2
    assert summary["user_approval_required_count"] == 2
    assert summary["external_submission_allowed_count"] == 0
    assert summary["network_access_allowed_count"] == 0
    assert summary["top_three_recommendation_count"] == 6
    assert summary["by_track"] == {"infrared": 1, "radio": 1}
    assert summary["by_readiness_status"] == {
        "blocked_pending_tests": 1,
        "ready_for_draft_report": 1,
    }
    assert summary["by_destination_action"] == {
        "do_not_submit_yet": 1,
        "internal_review": 2,
        "request_more_tests": 3,
    }
    assert "not discoveries" in summary["disclaimer"]


def test_background_review_workflow_summary_exposes_review_semantics() -> None:
    summary = background_review_workflow_summary()

    assert summary["schema_version"] == "background_search_ledger_v1"
    assert summary["entry_count"] == 4
    assert summary["reviewed_workflow_status_count"] == 4
    assert summary["target_selection_rationale_count"] == 12
    assert summary["negative_result_logged_count"] == 2
    assert summary["requires_human_review_count"] == 2
    assert summary["local_only_entry_count"] == 1
    assert summary["scheduling_only_count"] == 1
    assert summary["candidate_packet_id_count"] == 2
    assert summary["blocked_entry_count"] == 3
    assert summary["by_execution_mode"] == {
        "local_non_network_fixture_runner": 1,
        "synthetic_priority_demo": 3,
    }
    assert summary["by_reviewed_workflow_status"] == {
        "candidate_packet_ready": 1,
        "local_scheduling_only": 1,
        "negative_search_recorded": 1,
        "review_blocked": 1,
    }
    assert summary["local_only_run_ids"] == ["background-demo-004"]


def test_candidate_extraction_handoffs_load_local_only_contract() -> None:
    records = load_candidate_extraction_handoffs()

    assert len(records) == 4
    assert {record.track.value for record in records} == {
        "anomaly",
        "infrared",
        "radio",
    }
    assert records[0].handoff_id == "handoff-radio-ready-001"
    assert records[0].expected_candidate_packet_ids == ("radio-clean-001",)
    assert records[1].extraction_status == "blocked"
    assert records[2].negative_result_required is True
    assert records[3].execution_mode == "local_non_network_fixture_runner"
    assert all(record.network_access_allowed is False for record in records)
    assert "not detections" in CANDIDATE_EXTRACTION_HANDOFF_DISCLAIMER


def test_candidate_extraction_handoff_summary_counts_readiness() -> None:
    summary = candidate_extraction_handoff_summary()

    assert summary["schema_version"] == "candidate_extraction_handoff_v1"
    assert summary["record_count"] == 4
    assert summary["ready_count"] == 1
    assert summary["blocked_count"] == 1
    assert summary["no_candidate_expected_count"] == 1
    assert summary["scheduling_only_count"] == 1
    assert summary["expected_candidate_packet_count"] == 2
    assert summary["candidate_fixture_count"] == 2
    assert summary["blocking_issue_count"] == 3
    assert summary["negative_result_required_count"] == 2
    assert summary["requires_human_review_count"] == 2
    assert summary["network_access_allowed_count"] == 0
    assert summary["required_input_count"] == 12
    assert summary["available_input_count"] == 10
    assert summary["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 2}
    assert summary["by_extraction_status"] == {
        "blocked": 1,
        "no_candidate_expected": 1,
        "ready_for_extraction": 1,
        "scheduling_only": 1,
    }
    assert summary["expected_candidate_packet_ids"] == [
        "infrared-clean-001",
        "radio-clean-001",
    ]
    assert "not detections" in summary["disclaimer"]


def test_background_search_rejects_wrong_schema_version(tmp_path: Path) -> None:
    target_path = tmp_path / "targets.json"
    target_path.write_text(
        '{"schema_version": "wrong", "targets": []}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported target priority schema"):
        load_background_targets(target_path)


def test_candidate_extraction_handoff_rejects_wrong_schema_version(
    tmp_path: Path,
) -> None:
    handoff_path = tmp_path / "handoffs.json"
    handoff_path.write_text(
        '{"schema_version": "wrong", "handoffs": []}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported candidate extraction handoff"):
        load_candidate_extraction_handoffs(handoff_path)


def test_background_priority_config_loads_versioned_weights() -> None:
    config = load_background_priority_config()

    assert config.config_version == "background_priority_v0"
    assert config.weights["followup_value"] == 0.35
    assert config.weights["false_positive_probability"] == -0.3
    assert config.blocking_issue_penalty_per_issue == 0.05
    assert config.max_blocking_issue_penalty == 0.25
    assert config.never_reviewed_target_boost == 0.08
    assert config.prior_review_penalty_per_entry == 0.04
    assert config.max_prior_review_penalty == 0.12
    assert config.needs_follow_up_priority_threshold == 0.7
    assert config.passive_runner_requires_opt_in is True
    assert config.network_access_enabled is False
    assert config.local_runner_pathway == "github_reproducibility_only"


def test_local_background_run_requires_explicit_opt_in(tmp_path: Path) -> None:
    ledger_path = tmp_path / "background_ledger.json"

    with pytest.raises(ValueError, match="explicit opt-in"):
        run_local_background_search_once(ledger_path)


def test_local_background_run_appends_non_network_ledger_entry(tmp_path: Path) -> None:
    ledger_path = tmp_path / "background_ledger.json"

    result = run_local_background_search_once(
        ledger_path,
        run_id="local-test-run-001",
        code_commit="test-commit",
        opt_in=True,
    )
    entry = result["appended_entry"]
    summary = result["ledger_summary"]

    assert result["ok"] is True
    assert ledger_path.exists()
    assert entry["run_id"] == "local-test-run-001"
    assert entry["target_id"] == "target-radio-clean-drift"
    assert entry["status"] == "needs_follow_up_logged"
    assert entry["config_version"] == "background_priority_v0"
    assert entry["candidate_count"] == 0
    assert entry["recommended_pathways"] == [
        "human_review_queue",
        "local_follow_up_tests",
    ]
    assert entry["query_parameters"]["mode"] == "local_non_network_fixture_runner"
    assert entry["query_parameters"]["selected_priority_score"] == 0.7515
    assert entry["query_parameters"]["selected_selection_score"] == 0.8315
    assert entry["query_parameters"]["prior_review_count"] == 0
    assert entry["execution_mode"] == "local_non_network_fixture_runner"
    assert entry["selected_priority_score"] == 0.7515
    assert entry["negative_result_logged"] is False
    assert entry["requires_human_review"] is True
    assert entry["reviewed_workflow_status"] == "needs_follow_up_required"
    assert entry["target_selection_rationale"] == [
        "highest configured scheduler selection score",
        "false-positive probability and blocking issues penalized",
        "never-reviewed targets receive an explicit scheduling boost",
        "previously reviewed targets receive a bounded review-history penalty",
        "local fixture runner does not query live providers",
    ]
    assert summary["entry_count"] == 1
    assert summary["candidate_count"] == 0
    assert summary["by_status"] == {"needs_follow_up_logged": 1}
    assert result["review_workflow_summary"]["local_only_entry_count"] == 1
    assert result["review_workflow_summary"]["requires_human_review_count"] == 1
    assert result["outcome_log"]["outcome"] == "needs_follow_up"
    assert result["outcome_log"]["summary"]["entry_count"] == 1
    assert (tmp_path / "background_needs_follow_up_log.json").exists()


def test_local_background_run_appends_to_existing_ledger(tmp_path: Path) -> None:
    ledger_path = tmp_path / "background_ledger.json"
    ledger_path.write_text(
        Path("tests/fixtures/background_search_ledger.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = run_local_background_search_once(
        ledger_path,
        run_id="local-test-run-002",
        opt_in=True,
    )

    assert result["appended_entry"]["target_id"] == "target-radio-never-reviewed"
    assert result["appended_entry"]["query_parameters"]["prior_review_count"] == 0
    assert result["ledger_summary"]["entry_count"] == 5
    assert result["ledger_summary"]["run_ids"][-1] == "local-test-run-002"
    assert result["review_workflow_summary"]["local_only_entry_count"] == 2
