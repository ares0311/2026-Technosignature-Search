from __future__ import annotations

import json
from pathlib import Path

FIXTURE_PATHS = (
    Path(__file__).parent
    / "fixtures"
    / "ai_hardening_hip17147_zero_hit_evidence.json",
    Path(__file__).parent
    / "fixtures"
    / "ai_hardening_hip39826_zero_hit_evidence.json",
)
CLOSURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "ai_hardening_injection_grid_closure_evidence.json"
)


def _load_fixtures() -> list[dict[str, object]]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in FIXTURE_PATHS]


def test_zero_hit_evidence_bundles_are_review_safe() -> None:
    for bundle in _load_fixtures():
        assert bundle["schema_version"] == "ai_hardening_evidence_bundle_v1"
        assert bundle["decision"] == "DECISION-134"
        assert bundle["raw_payload_committed"] is False
        assert bundle["detection_claimed"] is False
        assert bundle["expert_review_claimed"] is False
        assert bundle["external_validation_claimed"] is False
        assert bundle["external_submission_allowed"] is False
        assert bundle["production_promotion_allowed"] is False


def test_zero_hit_artifacts_are_relative_and_uncommitted() -> None:
    for bundle in _load_fixtures():
        artifacts = bundle["raw_artifacts"]

        assert isinstance(artifacts, list)
        assert len(artifacts) == 3
        for artifact in artifacts:
            assert isinstance(artifact, dict)
            rel_path = artifact["relative_path"]
            assert isinstance(rel_path, str)
            assert not rel_path.startswith("/")
            assert ".." not in Path(rel_path).parts
            assert artifact["committed"] is False
            assert isinstance(artifact["sha256"], str)
            assert len(artifact["sha256"]) == 64


def test_zero_hit_runs_preserve_method_abstentions() -> None:
    for bundle in _load_fixtures():
        run = bundle["turboseti_run"]
        reviews = bundle["method_reviews"]

        assert isinstance(run, dict)
        assert run["valid_hit_count"] == 0
        assert isinstance(reviews, list)
        assert len(reviews) >= 2
        assert {review["status"] for review in reviews if isinstance(review, dict)} == {
            "abstained"
        }
        assert all(
            review["negative_evidence_preserved"] is True
            for review in reviews
            if isinstance(review, dict)
        )


def test_zero_hit_evidence_does_not_close_decision_134() -> None:
    for bundle in _load_fixtures():
        blockers = bundle["open_blockers_after_run"]
        conclusion = bundle["conclusion"]

        assert isinstance(blockers, list)
        assert any("valid hit rows" in str(blocker) for blocker in blockers)
        assert isinstance(conclusion, str)
        assert "does not close DECISION-134" in conclusion


def test_injection_grid_bundle_is_review_safe_but_not_promotion_evidence() -> None:
    bundle = json.loads(CLOSURE_PATH.read_text(encoding="utf-8"))

    assert bundle["schema_version"] == "ai_hardening_evidence_bundle_v1"
    assert bundle["decision"] == "DECISION-134"
    assert bundle["raw_payload_committed"] is False
    assert bundle["status"] == "historical_injection_recovery_evidence_only"
    assert bundle["superseded_by"] == "DECISION-144"
    assert bundle["production_promotion_allowed"] is False
    assert bundle["production_promotion_scope"] == "blocked"
    assert bundle["detection_claimed"] is False
    assert bundle["expert_review_claimed"] is False
    assert bundle["external_validation_claimed"] is False
    assert bundle["external_submission_allowed"] is False


def test_injection_grid_closure_bundle_records_recovery_and_rows() -> None:
    bundle = json.loads(CLOSURE_PATH.read_text(encoding="utf-8"))
    grid = bundle["injection_grid"]
    rows = bundle["candidate_rows"]

    assert grid["committed"] is False
    assert grid["total_injections"] == 75
    assert grid["completed_injections"] == 75
    assert grid["failed_injection_count"] == 0
    assert grid["recovered_count"] == 75
    assert grid["recovery_fraction"] == 1.0
    assert rows["valid_dat_file_count"] == 75
    assert rows["valid_hit_row_count"] > 0
    assert len(grid["manifest_sha256"]) == 64


def test_injection_grid_closure_bundle_preserves_abstentions() -> None:
    bundle = json.loads(CLOSURE_PATH.read_text(encoding="utf-8"))
    reviews = bundle["method_reviews"]

    statuses = {review["method_id"]: review["status"] for review in reviews}
    recorded = [review for review in reviews if review["status"] == "recorded"]
    abstained = [review for review in reviews if review["status"] == "abstained"]

    assert len(recorded) >= 2
    assert statuses["rule_based_scoring"] == "recorded"
    assert statuses["globular_dense_cluster_filter"] == "recorded"
    assert statuses["semisupervised_anomaly_scorer"] == "recorded"
    assert statuses["learned_logistic_regression"] == "abstained"
    assert statuses["cross_target_rfi_suppression"] == "abstained"
    assert abstained
    assert all(review["negative_evidence_preserved"] is True for review in reviews)


def test_injection_grid_closure_artifacts_are_relative_and_uncommitted() -> None:
    bundle = json.loads(CLOSURE_PATH.read_text(encoding="utf-8"))
    source = bundle["source_real_noise"]
    grid = bundle["injection_grid"]

    for artifact in (source, grid):
        rel_path = artifact["relative_path"]
        assert isinstance(rel_path, str)
        assert not rel_path.startswith("/")
        assert ".." not in Path(rel_path).parts
        assert artifact["committed"] is False
