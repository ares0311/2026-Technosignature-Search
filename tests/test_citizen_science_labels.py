from __future__ import annotations

import json
from pathlib import Path

from techno_search.citizen_science_labels import (
    CadenceHit,
    _audit_label,
    _primary_label,
    cadence_abacab_review_summary,
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


def _write_review_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "Corrected_Frequency,Drift_Rate,SNR,scan_role,target_id,source_artifact",
                "1420.0,1.0,21.0,on,HIP99427,a.dat",
                "1420.0,1.0,22.0,on,HIP99427,c.dat",
                "1420.0,1.0,23.0,on,HIP99427,e.dat",
                "1421.0,-2.0,31.0,on,HIP99427,a.dat",
                "1421.0,-2.0,32.0,off,HIP100670,b.dat",
                "1421.0,-2.0,33.0,off,HIP99560,d.dat",
                "1421.0,-2.0,34.0,off,HIP99759,f.dat",
            ]
        )
        + "\n",
        encoding="utf-8",
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


def test_cadence_abacab_review_summary_counts_follow_up_candidates(tmp_path: Path) -> None:
    cadence_csv = tmp_path / "cadence.csv"
    _write_review_csv(cadence_csv)

    summary = cadence_abacab_review_summary(
        cadence_csv,
        cadence_id="test-cadence",
        limit=1,
    )

    assert summary["ok"] is True
    assert summary["row_count"] == 7
    assert summary["evidence_group_count"] == 2
    assert summary["source_artifact_count"] == 6
    assert summary["label_counts"] == {
        "false_positive": 1,
        "follow_up": 1,
    }
    assert summary["follow_up_candidate_count"] == 1
    assert summary["false_positive_count"] == 1
    assert summary["external_submission_authorized"] is False
    follow_up = summary["top_follow_up_candidates"][0]
    assert follow_up["candidate_id"].startswith("test-cadence-group-001-")
    assert follow_up["on_scan_count"] == 3
    assert follow_up["off_scan_count"] == 0
    assert follow_up["follow_up_candidate_score"] == 0.75


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

