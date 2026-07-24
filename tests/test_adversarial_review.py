from __future__ import annotations

from techno_search.adversarial_review import build_adversarial_review_dossier


def _base_report(**overrides: object) -> dict[str, object]:
    report: dict[str, object] = {
        "candidate_id": "test-candidate",
        "track": "radio",
        "recommended_pathway": "candidate_review_packet",
        "scores": {"false_positive_probability": 0.2},
        "score_calibration": {
            "status": "uncalibrated",
            "probability_interpretation_allowed": False,
            "limitation": "Routing scores are not calibrated probabilities.",
        },
        "positive_evidence": ["High SNR supports signal reality."],
        "negative_evidence": [],
        "blocking_issues": [],
    }
    report.update(overrides)
    return report


def test_zero_refutations_and_advancing_pathway_requires_human_review() -> None:
    dossier = build_adversarial_review_dossier(
        _base_report(),
        track_b_gate_result={"eligible_for_unknown_candidate": True, "conditions": []},
    )

    assert dossier.refutation_count == 0
    assert dossier.requires_human_expert_review is True


def test_any_negative_evidence_is_a_refutation_and_blocks_advancement() -> None:
    report = _base_report(
        track="infrared",
        negative_evidence=["Frequency overlaps known or suspected RFI."],
        recommended_pathway="do_not_submit_false_positive",
    )

    dossier = build_adversarial_review_dossier(report)

    assert dossier.refutation_count == 1
    assert dossier.refutations[0].source == "scoring_negative_evidence"
    assert dossier.requires_human_expert_review is False


def test_radio_scoring_concerns_do_not_masquerade_as_refutations() -> None:
    report = _base_report(
        negative_evidence=["No strong repeat observation support is present."],
        recommended_pathway="human_review_queue",
    )

    dossier = build_adversarial_review_dossier(
        report,
        track_b_gate_result={"eligible_for_unknown_candidate": True, "conditions": []},
    )

    assert dossier.refutation_count == 0
    assert dossier.review_concerns == (
        "No strong repeat observation support is present.",
    )
    assert dossier.requires_human_expert_review is True


def test_blocking_issues_prevent_human_review_requirement_even_with_zero_refutations() -> None:
    report = _base_report(blocking_issues=["Observation metadata is incomplete."])

    dossier = build_adversarial_review_dossier(report)

    assert dossier.refutation_count == 0
    assert "Observation metadata is incomplete." in dossier.blocking_issues
    assert any("Track B gate" in item for item in dossier.blocking_issues)
    assert dossier.requires_human_expert_review is False


def test_human_review_queue_pathway_does_not_require_expert_review() -> None:
    report = _base_report(recommended_pathway="human_review_queue")

    dossier = build_adversarial_review_dossier(
        report,
        track_b_gate_result={"eligible_for_unknown_candidate": True, "conditions": []},
    )

    assert dossier.requires_human_expert_review is True


def test_uncalibrated_ranking_does_not_block_deterministic_review() -> None:
    report = _base_report(
        recommended_pathway="human_review_queue",
        blocking_issues=[
            "Candidate-review promotion is blocked because scoring is an "
            "uncalibrated local-routing heuristic."
        ],
    )

    dossier = build_adversarial_review_dossier(
        report,
        track_b_gate_result={"eligible_for_unknown_candidate": True, "conditions": []},
    )

    assert dossier.requires_human_expert_review is True
    assert dossier.blocking_issues == ()
    assert dossier.ranking_limitations
    assert dossier.routing_false_positive_score == 0.2
    assert dossier.score_calibration["probability_interpretation_allowed"] is False


def test_radio_advancement_without_track_b_gate_is_fail_closed() -> None:
    dossier = build_adversarial_review_dossier(_base_report())

    assert dossier.requires_human_expert_review is False
    assert any("Track B gate" in item for item in dossier.blocking_issues)


def test_track_b_gate_unsatisfied_condition_is_a_real_refutation() -> None:
    report = _base_report()
    track_b_result = {
        "eligible_for_unknown_candidate": False,
        "conditions": [
            {
                "condition_id": "rfi_database_overlap",
                "description": "No known RFI database overlap at this frequency.",
                "satisfied": False,
                "evidence": {},
            },
            {
                "condition_id": "cadence_pass",
                "description": "ABACAB cadence passes.",
                "satisfied": True,
                "evidence": {},
            },
        ],
    }

    dossier = build_adversarial_review_dossier(report, track_b_gate_result=track_b_result)

    assert dossier.refutation_count == 1
    assert dossier.refutations[0].source == "track_b_gate"
    assert dossier.requires_human_expert_review is False


def test_track_b_gate_all_satisfied_but_not_eligible_still_blocks() -> None:
    report = _base_report()
    track_b_result = {
        "eligible_for_unknown_candidate": False,
        "conditions": [
            {
                "condition_id": "anomaly_threshold",
                "description": "Anomaly score exceeds a calibrated threshold.",
                "satisfied": None,
                "evidence": {},
            },
        ],
    }

    dossier = build_adversarial_review_dossier(report, track_b_gate_result=track_b_result)

    assert dossier.refutation_count == 0
    assert dossier.requires_human_expert_review is False


def test_as_dict_includes_track_b_gate_result() -> None:
    report = _base_report()
    track_b_result = {"eligible_for_unknown_candidate": True, "conditions": []}

    dossier = build_adversarial_review_dossier(report, track_b_gate_result=track_b_result)
    payload = dossier.as_dict()

    assert payload["track_b_gate_result"] == track_b_result
    assert payload["routing_false_positive_score"] == 0.2
    assert "false_positive_probability" not in payload
    assert payload["ranking_limitations"] == [
        "Routing scores are not calibrated probabilities."
    ]
    assert payload["review_concerns"] == []
    assert payload["requires_human_expert_review"] is True
