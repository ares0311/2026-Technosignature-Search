from __future__ import annotations

import json
from pathlib import Path

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "ai_hardening_hip17147_zero_hit_evidence.json"
)


def _load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_hip17147_evidence_bundle_is_review_safe() -> None:
    bundle = _load_fixture()

    assert bundle["schema_version"] == "ai_hardening_evidence_bundle_v1"
    assert bundle["decision"] == "DECISION-134"
    assert bundle["raw_payload_committed"] is False
    assert bundle["detection_claimed"] is False
    assert bundle["expert_review_claimed"] is False
    assert bundle["external_validation_claimed"] is False
    assert bundle["external_submission_allowed"] is False
    assert bundle["production_promotion_allowed"] is False


def test_hip17147_artifacts_are_relative_and_uncommitted() -> None:
    bundle = _load_fixture()
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


def test_hip17147_zero_hit_run_preserves_method_abstentions() -> None:
    bundle = _load_fixture()
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


def test_hip17147_evidence_does_not_close_decision_134() -> None:
    bundle = _load_fixture()

    blockers = bundle["open_blockers_after_run"]
    conclusion = bundle["conclusion"]

    assert isinstance(blockers, list)
    assert any("valid hit rows" in str(blocker) for blocker in blockers)
    assert isinstance(conclusion, str)
    assert "does not close DECISION-134" in conclusion
