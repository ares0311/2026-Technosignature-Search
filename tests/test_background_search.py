from pathlib import Path

import pytest

from techno_search.background_search import (
    BACKGROUND_SEARCH_LEDGER_DISCLAIMER,
    TARGET_PRIORITY_DISCLAIMER,
    background_review_workflow_summary,
    background_search_ledger_summary,
    load_background_priority_config,
    load_background_search_ledger,
    load_background_targets,
    run_local_background_search_once,
    target_priority_score,
    target_priority_summary,
)


def test_background_targets_load_with_conservative_disclaimer() -> None:
    targets = load_background_targets()

    assert len(targets) == 3
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
    assert scores["target-anomaly-weak-context"] == 0.335
    assert max(scores, key=scores.__getitem__) == "target-radio-clean-drift"


def test_target_priority_summary_ranks_targets_and_exposes_weights() -> None:
    summary = target_priority_summary()

    assert summary["schema_version"] == "background_target_priority_v1"
    assert summary["config_version"] == "background_priority_v0"
    assert summary["target_count"] == 3
    assert summary["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert summary["selected_target_id"] == "target-radio-clean-drift"
    assert summary["selected_priority_score"] == 0.7515
    assert summary["weights"]["false_positive_probability"] < 0
    assert summary["passive_runner_requires_opt_in"] is True
    assert summary["network_access_enabled"] is False
    assert "not evidence" in summary["disclaimer"]
    assert [
        target["target_id"] for target in summary["ranked_targets"]
    ] == [
        "target-radio-clean-drift",
        "target-infrared-excess-review",
        "target-anomaly-weak-context",
    ]


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


def test_background_search_rejects_wrong_schema_version(tmp_path: Path) -> None:
    target_path = tmp_path / "targets.json"
    target_path.write_text(
        '{"schema_version": "wrong", "targets": []}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported target priority schema"):
        load_background_targets(target_path)


def test_background_priority_config_loads_versioned_weights() -> None:
    config = load_background_priority_config()

    assert config.config_version == "background_priority_v0"
    assert config.weights["followup_value"] == 0.35
    assert config.weights["false_positive_probability"] == -0.3
    assert config.blocking_issue_penalty_per_issue == 0.05
    assert config.max_blocking_issue_penalty == 0.25
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
    assert entry["status"] == "local_fixture_search_logged"
    assert entry["config_version"] == "background_priority_v0"
    assert entry["candidate_count"] == 0
    assert entry["recommended_pathways"] == ["github_reproducibility_only"]
    assert entry["query_parameters"]["mode"] == "local_non_network_fixture_runner"
    assert entry["query_parameters"]["selected_priority_score"] == 0.7515
    assert entry["execution_mode"] == "local_non_network_fixture_runner"
    assert entry["selected_priority_score"] == 0.7515
    assert entry["negative_result_logged"] is True
    assert entry["requires_human_review"] is False
    assert entry["reviewed_workflow_status"] == "local_scheduling_only"
    assert entry["target_selection_rationale"] == [
        "highest configured target-priority score",
        "false-positive probability and blocking issues penalized",
        "local fixture runner does not query live providers",
    ]
    assert summary["entry_count"] == 1
    assert summary["candidate_count"] == 0
    assert summary["by_status"] == {"local_fixture_search_logged": 1}
    assert result["review_workflow_summary"]["local_only_entry_count"] == 1
    assert result["review_workflow_summary"]["negative_result_logged_count"] == 1


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

    assert result["ledger_summary"]["entry_count"] == 5
    assert result["ledger_summary"]["run_ids"][-1] == "local-test-run-002"
    assert result["review_workflow_summary"]["local_only_entry_count"] == 2
