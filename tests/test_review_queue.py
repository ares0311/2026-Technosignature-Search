from techno_search.review_queue import (
    CONSENSUS_LABEL_DISCLAIMER,
    REVIEW_QUEUE_DISCLAIMER,
    allowed_consensus_labels,
    allowed_triage_labels,
    consensus_summary,
    load_consensus_items,
    load_review_queue_items,
    review_queue_summary,
)


def test_review_queue_fixture_loads_allowed_labels_and_notes() -> None:
    items = load_review_queue_items()

    assert len(items) == 5
    assert allowed_triage_labels() == (
        "follow_up_target",
        "insufficient_evidence",
        "known_object_annotation",
        "likely_false_positive",
        "needs_human_review",
    )
    assert {item.triage_label.value for item in items} == set(allowed_triage_labels())
    assert items[0].reviewer_notes[0].reviewer_id == "synthetic-reviewer-a"
    assert "not discovery claims" in REVIEW_QUEUE_DISCLAIMER


def test_review_queue_summary_counts_tracks_labels_and_notes() -> None:
    summary = review_queue_summary()

    assert summary["schema_version"] == "human_review_queue_v1"
    assert summary["item_count"] == 5
    assert summary["note_count"] == 4
    assert summary["by_track"] == {"anomaly": 2, "infrared": 1, "radio": 2}
    assert summary["by_triage_label"] == {
        "follow_up_target": 1,
        "insufficient_evidence": 1,
        "known_object_annotation": 1,
        "likely_false_positive": 1,
        "needs_human_review": 1,
    }
    assert summary["by_recommended_pathway"] == {
        "candidate_review_packet": 2,
        "do_not_submit_false_positive": 1,
        "github_reproducibility_only": 1,
        "known_object_annotation": 1,
    }
    assert summary["items_missing_notes"] == ["low-confidence-demo"]
    assert summary["blocking_issue_total"] == 3
    assert summary["negative_evidence_total"] == 16


def test_consensus_fixture_loads_allowed_labels_and_decisions() -> None:
    items = load_consensus_items()

    assert len(items) == 5
    assert allowed_consensus_labels() == (
        "follow_up_target",
        "insufficient_evidence",
        "known_object_annotation",
        "likely_false_positive",
        "no_consensus",
    )
    assert {item.consensus_label.value for item in items} == set(allowed_consensus_labels())
    assert items[0].reviewer_decisions[0].reviewer_id == "synthetic-reviewer-a"
    assert "not discovery claims" in CONSENSUS_LABEL_DISCLAIMER


def test_consensus_summary_counts_labels_tracks_and_reviewer_counts() -> None:
    summary = consensus_summary()

    assert summary["schema_version"] == "human_review_consensus_labels_v1"
    assert summary["item_count"] == 5
    assert summary["decision_count"] == 13
    assert summary["unique_reviewer_count"] == 4
    assert summary["by_track"] == {"anomaly": 2, "infrared": 1, "radio": 2}
    assert summary["by_consensus_label"] == {
        "follow_up_target": 1,
        "insufficient_evidence": 1,
        "known_object_annotation": 1,
        "likely_false_positive": 1,
        "no_consensus": 1,
    }
    assert summary["by_decision_label"] == {
        "follow_up_target": 3,
        "insufficient_evidence": 2,
        "known_object_annotation": 2,
        "likely_false_positive": 4,
        "needs_human_review": 2,
    }
    assert summary["by_reviewer_decision_count"] == {"2": 2, "3": 3}
