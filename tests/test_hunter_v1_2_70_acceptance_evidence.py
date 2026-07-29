from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from techno_search.production_scan import PRODUCTION_SCAN_DISCLAIMER

EVIDENCE_PATH = Path("docs/evidence/hunter_v1_2_70_acceptance.json")
STATUS_PATH = Path("docs/data_collection_status.json")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _attempts_by_script() -> dict[str, dict[str, object]]:
    document = _load_json(STATUS_PATH)
    return {item["script"]: item for item in document["attempts"]}


def test_v1_2_70_evidence_closes_both_canonical_hunter_modes() -> None:
    evidence = _load_json(EVIDENCE_PATH)
    searches = {item["mode"]: item for item in evidence["searches"]}

    assert evidence["schema_version"] == "hunter_live_acceptance_v2"
    assert evidence["release"] == {
        "science_acceptance_app_version": "1.2.69",
        "science_acceptance_code_commit": "1da324c",
        "closure_app_version": "1.2.70",
        "closure_code_commit": "e359546fc41d9ec62eaeee8c2b684a0152096300",
        "closure_delta": (
            "production terminal-summary scope terminology only; selection, "
            "acquisition, scoring, interpretation, persistence, and follow-up "
            "logic are unchanged"
        ),
    }
    assert evidence["release"]["closure_app_version"] == "1.2.70"
    assert set(searches) == {"new", "follow-up"}
    assert evidence["scope"]["installed_entry_point"] == "Techno-Hunter"
    assert evidence["scope"]["canonical_commands"] == [
        "/Create-New-Search --targets 1 --mode new",
        "/Create-New-Search --targets 1 --mode follow-up",
        "/Run-New-Search",
        "/Show-Follow-Ups",
    ]

    new = searches["new"]
    assert new["search_id"] == "SEARCH-20260729T055045Z-125D2215"
    assert new["run_id"] == "RUN-2026-07-29_055553Z-YI5F-hunter-search"
    assert new["target_ids"] == ["HIP3419"]
    assert new["known_explanation_state_counts"] == {
        "known": 0,
        "unknown": 0,
        "unresolved": 1,
    }
    assert new["downloaded_count"] == new["evicted_count"] == 1
    assert new["history_records_appended"] == 1
    assert new["follow_up_required_count"] == 1
    assert new["source_scan_count"] == 1

    follow_up = searches["follow-up"]
    assert follow_up["search_id"] == "SEARCH-20260729T055057Z-7321B0CB"
    assert follow_up["run_id"] == "RUN-2026-07-29_055650Z-G60U-hunter-search"
    assert follow_up["target_ids"] == ["HIP103039"]
    assert follow_up["known_explanation_state_counts"] == {
        "known": 0,
        "unknown": 1,
        "unresolved": 0,
    }
    assert follow_up["required_known_explanation_condition_count"] == 10
    assert follow_up["required_known_explanation_satisfied_count"] == 10
    assert follow_up["automatic_adversarial_review_count"] == 1
    assert follow_up["adversarial_blocking_issue_count"] == 1
    assert follow_up["requires_human_expert_review"] is False
    assert follow_up["ranking_probability_interpretation_allowed"] is False
    assert follow_up["downloaded_scan_count"] == follow_up["evicted_scan_count"] == 6
    assert follow_up["consumed_follow_up_count"] == 8
    assert follow_up["follow_up_observation_fulfilled_count"] == 1
    assert follow_up["source_scan_count"] == 6
    assert follow_up["cadence_hit_row_count"] == 72

    for search in searches.values():
        assert search["target_count"] == 1
        assert search["candidate_count"] == 1
        assert search["event_sequence"] == [
            "created",
            "run_started",
            "run_completed",
        ]
        assert search["plot_artifacts_synthetic"] == [False]


def test_v1_2_70_evidence_is_fail_closed_and_not_a_claim() -> None:
    evidence = _load_json(EVIDENCE_PATH)
    scope = evidence["scope"]

    for claim in (
        "detection_claimed",
        "discovery_claimed",
        "expert_review_claimed",
        "external_validation_claimed",
        "external_submission_allowed",
    ):
        assert scope[claim] is False

    lifecycle = evidence["lifecycle_falsification"]
    assert lifecycle["completed_search_rerun_exit_code"] != 0
    assert lifecycle["event_counts_unchanged"] is True
    assert lifecycle["history_count_before"] == lifecycle["history_count_after"]
    assert lifecycle["raw_hdf5_retained_count"] == 0
    assert lifecycle["storage_cap_gb"] == 100

    assert "local production-triage records" in PRODUCTION_SCAN_DISCLAIMER
    assert "citizen-science" not in PRODUCTION_SCAN_DISCLAIMER


def test_v1_2_70_evidence_matches_collection_status_and_eviction() -> None:
    evidence = _load_json(EVIDENCE_PATH)
    attempts = _attempts_by_script()

    for search in evidence["searches"]:
        status = attempts[f"hunter_search__{search['search_id']}"]
        assert status["ok"] is True
        assert status["app_version"] == (
            evidence["release"]["science_acceptance_app_version"]
        )
        assert status["completed_count"] == search["target_count"]
        assert status["failed_count"] == 0
        assert status["targets_attempted"] == search["target_count"]
        assert status["candidate_report_manifests_total"] == search["candidate_count"]
        assert status["newly_processed_targets"] == search["target_ids"]

    new_status = attempts[
        "hunter_search__SEARCH-20260729T055045Z-125D2215"
    ]
    assert new_status["downloaded_targets"] == ["HIP3419"]
    assert new_status["evicted_targets"] == ["HIP3419"]

    cadence_status = attempts[
        "ingest_gbt_cadence__GBT_HIP103039_2017-06-25_ABACAD__20260729T055650Z"
    ]
    assert cadence_status["ok"] is True
    assert cadence_status["scan_count"] == 6
    assert [scan["scan_role"] for scan in cadence_status["processed_scans"]] == [
        "on",
        "off",
        "on",
        "off",
        "on",
        "off",
    ]
    assert all(scan["raw_evicted"] is True for scan in cadence_status["processed_scans"])
    assert all(scan["archive_md5"] for scan in cadence_status["processed_scans"])


def test_v1_2_70_acceptance_hashes_match_wholly_present_local_outputs() -> None:
    evidence = _load_json(EVIDENCE_PATH)
    artifacts = [
        artifact
        for search in evidence["searches"]
        for artifact in search["artifacts"]
    ]
    paths = [Path(artifact["path"]) for artifact in artifacts]

    assert len(artifacts) == 15
    assert all(
        re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
        for artifact in artifacts
    )
    assert len({artifact["sha256"] for artifact in artifacts}) == len(artifacts)

    present = [path.exists() for path in paths]
    assert all(present) or not any(present), (
        "acceptance runtime artifacts must be either wholly present or absent"
    )
    if not any(present):
        return

    for artifact, path in zip(artifacts, paths, strict=True):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == artifact["sha256"], artifact["path"]
