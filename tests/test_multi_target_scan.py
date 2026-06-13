"""Tests for multi-target scan orchestration (Task 3)."""
from __future__ import annotations

from techno_search.multi_target_scan import (
    MULTI_TARGET_SCAN_DISCLAIMER,
    MULTI_TARGET_SCAN_SCHEMA_VERSION,
    MultiTargetScanResult,
)


class TestMultiTargetScanResult:
    def test_as_dict_all_fields_present(self) -> None:
        r = MultiTargetScanResult(
            targets_attempted=2,
            targets_succeeded=2,
            targets_failed=0,
            total_candidates=5,
            follow_up_count=1,
            candidate_review_count=0,
            target_results=[],
        )
        d = r.as_dict()
        for key in (
            "schema_version",
            "disclaimer",
            "targets_attempted",
            "targets_succeeded",
            "targets_failed",
            "total_candidates",
            "follow_up_count",
            "candidate_review_count",
            "target_results",
        ):
            assert key in d, f"missing key: {key}"

    def test_schema_version(self) -> None:
        r = MultiTargetScanResult(0, 0, 0, 0, 0, 0, [])
        assert r.schema_version == MULTI_TARGET_SCAN_SCHEMA_VERSION

    def test_disclaimer(self) -> None:
        r = MultiTargetScanResult(0, 0, 0, 0, 0, 0, [])
        assert "detection claim" in r.disclaimer
        assert r.disclaimer == MULTI_TARGET_SCAN_DISCLAIMER

    def test_zero_targets(self) -> None:
        r = MultiTargetScanResult(0, 0, 0, 0, 0, 0, [])
        d = r.as_dict()
        assert d["targets_attempted"] == 0
        assert d["total_candidates"] == 0

    def test_target_results_list(self) -> None:
        r = MultiTargetScanResult(1, 1, 0, 3, 0, 0, [{"target": "HIP99427"}])
        assert isinstance(r.as_dict()["target_results"], list)

    def test_follow_up_count(self) -> None:
        r = MultiTargetScanResult(2, 2, 0, 10, 3, 1, [])
        d = r.as_dict()
        assert d["follow_up_count"] == 3
        assert d["candidate_review_count"] == 1

    def test_failed_targets_tracked(self) -> None:
        r = MultiTargetScanResult(3, 2, 1, 4, 0, 0, [])
        d = r.as_dict()
        assert d["targets_failed"] == 1
        assert d["targets_succeeded"] == 2

    def test_as_dict_json_serialisable(self) -> None:
        import json
        r = MultiTargetScanResult(1, 1, 0, 5, 2, 1, [{"t": "x"}])
        json.dumps(r.as_dict())  # must not raise

    def test_operator_external_submission_not_authorized(self) -> None:
        r = MultiTargetScanResult(0, 0, 0, 0, 0, 0, [])
        d = r.as_dict()
        assert "external submission" in d["disclaimer"]
