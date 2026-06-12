from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.baseline_eval import eval_against_labels
from techno_search.citizen_science_labels import (
    CadenceHit,
    _audit_label,
    _primary_label,
    group_cadence_hits,
)
from techno_search.labeled_dataset import labeled_dataset_summary

DATASET = Path(
    "examples/real_labeled/hip99427_citizen_science_labels_v1.json"
)


def _hit(
    frequency_hz: float,
    role: str,
    artifact: str,
    *,
    target: str = "HIP99427",
) -> CadenceHit:
    return CadenceHit(
        frequency_hz=frequency_hz,
        drift_rate_hz_per_sec=5.0,
        snr=20.0,
        scan_role=role,
        target_id=target,
        source_artifact=artifact,
    )


def test_grouping_prevents_row_level_pseudo_replication() -> None:
    groups = group_cadence_hits(
        [
            _hit(1_420_000_000.0, "on", "a"),
            _hit(1_420_000_000.0, "on", "b"),
            _hit(1_421_000_000.0, "off", "c"),
        ]
    )

    assert len(groups) == 2
    assert sorted(len(group) for group in groups) == [1, 2]


def test_primary_and_audit_methods_agree_on_off_recurrence() -> None:
    group = [
        _hit(1_420_000_000.0, "on", "a"),
        _hit(1_420_000_000.0, "off", "b", target="comparison"),
    ]

    assert _primary_label(group) == (
        "false_positive",
        "off_target_recurrence",
        0.99,
    )
    assert _audit_label(group, ("a", "b", "c", "d", "e", "f")) == (
        "false_positive"
    )


def test_primary_method_reserves_follow_up_for_all_three_on_scans() -> None:
    complete = [
        _hit(1_420_000_000.0, "on", "a"),
        _hit(1_420_000_000.0, "on", "c"),
        _hit(1_420_000_000.0, "on", "e"),
    ]
    partial = complete[:2]

    assert _primary_label(complete)[0] == "follow_up"
    assert _primary_label(partial)[0] == "insufficient_evidence"


def test_committed_real_dataset_is_reviewed_and_conservative() -> None:
    payload = json.loads(DATASET.read_text(encoding="utf-8"))

    assert payload["total_entries"] == 124
    assert payload["label_counts"] == {
        "false_positive": 81,
        "follow_up": 2,
        "insufficient_evidence": 41,
    }
    assert payload["review_summary"]["agreement_count"] == 124
    assert payload["review_summary"]["disagreement_count"] == 0
    assert payload["expert_review_claimed"] is False
    assert payload["external_validation_claimed"] is False
    assert payload["external_submission_authorized"] is False
    assert all(
        entry["primary_label"] == entry["audit_label"]
        for entry in payload["entries"]
    )


def test_real_labeled_dataset_summary_preserves_review_limits() -> None:
    summary = labeled_dataset_summary(DATASET)

    assert summary["entry_count"] == 124
    assert summary["real_observation_label_count"] == 124
    assert summary["review_policy"] == "citizen_science_reproducibility_v1"
    assert summary["expert_review_claimed"] is False
    assert summary["external_validation_claimed"] is False
    assert "not expert labels" in summary["disclaimer"]


def test_real_label_evaluation_is_recorded_without_threshold_tuning() -> None:
    evaluation = eval_against_labels(DATASET)

    assert evaluation["entry_count"] == 124
    assert evaluation["correct_count"] == 96
    assert evaluation["accuracy"] == pytest.approx(0.7742)
    assert evaluation["by_label_accuracy"]["false_positive"] == pytest.approx(
        65 / 81, rel=1e-2
    )
    assert evaluation["by_label_accuracy"]["follow_up"] == pytest.approx(1.0)
    assert evaluation["by_label_accuracy"]["insufficient_evidence"] == pytest.approx(
        29 / 41, rel=1e-2
    )
    assert evaluation["expert_review_claimed"] is False
    assert evaluation["external_validation_claimed"] is False
