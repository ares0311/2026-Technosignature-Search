from pathlib import Path

import pytest

from techno_search.background_search import (
    BACKGROUND_SEARCH_LEDGER_DISCLAIMER,
    TARGET_PRIORITY_DISCLAIMER,
    background_search_ledger_summary,
    load_background_search_ledger,
    load_background_targets,
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
    targets = load_background_targets()
    scores = {
        target.target_id: target_priority_score(target)
        for target in targets
    }

    assert scores["target-radio-clean-drift"] == 0.7515
    assert scores["target-infrared-excess-review"] == 0.613
    assert scores["target-anomaly-weak-context"] == 0.335
    assert max(scores, key=scores.__getitem__) == "target-radio-clean-drift"


def test_target_priority_summary_ranks_targets_and_exposes_weights() -> None:
    summary = target_priority_summary()

    assert summary["schema_version"] == "background_target_priority_v1"
    assert summary["target_count"] == 3
    assert summary["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert summary["selected_target_id"] == "target-radio-clean-drift"
    assert summary["selected_priority_score"] == 0.7515
    assert summary["weights"]["false_positive_probability"] < 0
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

    assert len(entries) == 3
    assert entries[0].run_id == "background-demo-001"
    assert entries[0].recommended_pathways == ("candidate_review_packet",)
    assert entries[2].candidate_count == 0
    assert BACKGROUND_SEARCH_LEDGER_DISCLAIMER.endswith("discovery claims.")


def test_background_search_ledger_summary_counts_searched_targets() -> None:
    summary = background_search_ledger_summary()

    assert summary["schema_version"] == "background_search_ledger_v1"
    assert summary["entry_count"] == 3
    assert summary["searched_target_count"] == 3
    assert summary["candidate_count"] == 2
    assert summary["blocking_issue_count"] == 3
    assert summary["by_track"] == {"anomaly": 1, "infrared": 1, "radio": 1}
    assert summary["by_status"] == {
        "completed": 1,
        "completed_with_blockers": 1,
        "searched_no_candidate": 1,
    }
    assert summary["by_recommended_pathway"] == {
        "candidate_review_packet": 1,
        "github_reproducibility_only": 1,
        "human_review_queue": 1,
    }
    assert summary["target_ids"] == [
        "target-anomaly-weak-context",
        "target-infrared-excess-review",
        "target-radio-clean-drift",
    ]
    assert "not discovery claims" in summary["disclaimer"]


def test_background_search_rejects_wrong_schema_version(tmp_path: Path) -> None:
    target_path = tmp_path / "targets.json"
    target_path.write_text(
        '{"schema_version": "wrong", "targets": []}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported target priority schema"):
        load_background_targets(target_path)
