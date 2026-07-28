from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

EVIDENCE_PATH = Path("docs/evidence/hunter_v1_2_65_acceptance.json")
STATUS_PATH = Path("docs/data_collection_status.json")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_status_by_script() -> dict[str, dict[str, object]]:
    document = _load_json(STATUS_PATH)
    return {
        item["script"]: item
        for item in document["attempts"]
        if item["script"].startswith("hunter_search__")
    }


def test_v1_2_65_acceptance_covers_both_installed_hunter_modes() -> None:
    evidence = _load_json(EVIDENCE_PATH)
    searches = {item["mode"]: item for item in evidence["searches"]}

    assert evidence["schema_version"] == "hunter_live_acceptance_v1"
    assert evidence["release"] == {
        "app_version": "1.2.65",
        "code_commit": "65b3eb0",
    }
    assert set(searches) == {"new", "follow-up"}
    assert searches["new"]["search_id"] == "SEARCH-20260728T042942Z-7572B240"
    assert searches["new"]["run_id"] == (
        "RUN-2026-07-28_043711Z-YJGV-hunter-search"
    )
    assert searches["new"]["target_ids"] == ["HIP61099"]
    assert searches["new"]["known_explanation_state_counts"] == {
        "known": 0,
        "unknown": 0,
        "unresolved": 1,
    }
    assert searches["new"]["history_records_appended"] == 1
    assert searches["new"]["follow_up_required_count"] == 1
    assert searches["new"]["source_scan_count"] == 1

    assert searches["follow-up"]["search_id"] == (
        "SEARCH-20260728T042946Z-5988937F"
    )
    assert searches["follow-up"]["run_id"] == (
        "RUN-2026-07-28_043903Z-OPNJ-hunter-search"
    )
    assert searches["follow-up"]["target_ids"] == ["GJ699"]
    assert searches["follow-up"]["known_explanation_state_counts"] == {
        "known": 1,
        "unknown": 0,
        "unresolved": 0,
    }
    assert searches["follow-up"]["history_records_appended"] == 1
    assert searches["follow-up"]["follow_up_observation_fulfilled_count"] == 1
    assert searches["follow-up"]["source_scan_count"] == 6

    for search in searches.values():
        assert search["target_count"] == 1
        assert search["candidate_count"] == 1
        assert search["plot_artifacts_synthetic"] == [False]


def test_v1_2_65_acceptance_is_fail_closed_and_not_a_detection_claim() -> None:
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

    assert evidence["post_merge_validation"]["canonical_validation_passed"] is True
    assert evidence["post_merge_validation"]["verification_freshness_passed"] is True
    assert evidence["candidate_pool"]["ranking_eligible_targets"] == 4862
    assert evidence["candidate_pool"]["ranking_eligible_targets"] < (
        evidence["candidate_pool"]["durable_queue_targets"]
    )
    assert evidence["candidate_pool"]["unresolved_archive_labels"] > 0


def test_acceptance_matches_committed_data_collection_status() -> None:
    evidence = _load_json(EVIDENCE_PATH)
    latest_status = _latest_status_by_script()

    for search in evidence["searches"]:
        status = latest_status[f"hunter_search__{search['search_id']}"]
        assert status["ok"] is True
        assert status["app_version"] == evidence["release"]["app_version"]
        assert status["completed_count"] == search["target_count"]
        assert status["failed_count"] == 0
        assert status["targets_attempted"] == search["target_count"]
        assert status["total_targets_in_manifest"] == search["target_count"]
        assert status["candidate_report_manifests_total"] == search["candidate_count"]
        assert status["newly_processed_targets"] == search["target_ids"]

    new_status = latest_status[
        "hunter_search__SEARCH-20260728T042942Z-7572B240"
    ]
    assert new_status["downloaded_targets"] == ["HIP61099"]
    assert new_status["evicted_targets"] == ["HIP61099"]

    follow_up_status = latest_status[
        "hunter_search__SEARCH-20260728T042946Z-5988937F"
    ]
    assert follow_up_status["local_dat_reuse_targets"] == ["GJ699"]


def test_acceptance_artifact_hashes_are_valid_and_match_when_local_outputs_exist() -> None:
    evidence = _load_json(EVIDENCE_PATH)
    artifacts = [
        artifact
        for search in evidence["searches"]
        for artifact in search["artifacts"]
    ]
    paths = [Path(artifact["path"]) for artifact in artifacts]

    assert len(artifacts) == 12
    assert len({artifact["role"] for artifact in artifacts}) == 6
    assert all(re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]) for artifact in artifacts)
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
