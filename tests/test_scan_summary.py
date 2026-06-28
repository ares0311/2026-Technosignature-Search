"""Tests for anomaly ranking report (Task 6)."""
from __future__ import annotations

import json
from pathlib import Path

from techno_search.scan_summary import (
    SCAN_SUMMARY_DISCLAIMER,
    SCAN_SUMMARY_SCHEMA_VERSION,
    scan_summary,
    scan_summary_from_batch_dir,
)


def _cand(cid: str, score: float, pathway: str, target: str, snr: float = 50.0) -> dict:
    return {
        "candidate_id": cid,
        "score": score,
        "recommended_pathway": pathway,
        "target_name": target,
        "frequency_hz": 1420e6,
        "snr": snr,
        "drift_rate_hz_per_sec": 0.5,
        "normalized_drift_hz_s_per_ghz": 0.352112676056338,
        "is_earth_drift_consistent": True,
    }


class TestScanSummary:
    def test_ranking_is_descending(self) -> None:
        cands = [
            _cand("c1", 0.3, "human_review_queue", "A"),
            _cand("c2", 0.9, "candidate_review_packet", "B"),
            _cand("c3", 0.6, "human_review_queue", "C"),
        ]
        result = scan_summary(cands)
        top = result["top_candidates"]
        assert top[0]["candidate_id"] == "c2"
        assert top[1]["candidate_id"] == "c3"
        assert top[2]["candidate_id"] == "c1"

    def test_top_k_respected(self) -> None:
        cands = [_cand(f"c{i}", float(i) / 10, "human_review_queue", "A")
                 for i in range(20)]
        result = scan_summary(cands, top_k=5)
        assert len(result["top_candidates"]) == 5

    def test_follow_up_count(self) -> None:
        cands = [
            _cand("c1", 0.8, "candidate_review_packet", "A"),
            _cand("c2", 0.5, "human_review_queue", "B"),
            _cand("c3", 0.1, "do_not_submit_false_positive", "C"),
        ]
        result = scan_summary(cands)
        assert result["follow_up_count"] == 2
        assert result["candidate_review_count"] == 1

    def test_candidate_review_count(self) -> None:
        cands = [
            _cand("c1", 0.9, "candidate_review_packet", "A"),
            _cand("c2", 0.8, "candidate_review_packet", "B"),
        ]
        result = scan_summary(cands)
        assert result["candidate_review_count"] == 2

    def test_total_candidates(self) -> None:
        cands = [_cand(f"c{i}", 0.5, "human_review_queue", "A") for i in range(7)]
        result = scan_summary(cands)
        assert result["total_candidates"] == 7

    def test_targets_scanned(self) -> None:
        cands = [
            _cand("c1", 0.5, "human_review_queue", "HIP99427"),
            _cand("c2", 0.5, "human_review_queue", "HIP100670"),
            _cand("c3", 0.5, "human_review_queue", "HIP99427"),
        ]
        result = scan_summary(cands)
        assert result["targets_scanned"] == 2

    def test_disclaimer_present(self) -> None:
        result = scan_summary([])
        assert result["disclaimer"] == SCAN_SUMMARY_DISCLAIMER
        assert "detection claim" in result["disclaimer"]

    def test_schema_version(self) -> None:
        result = scan_summary([])
        assert result["schema_version"] == SCAN_SUMMARY_SCHEMA_VERSION

    def test_empty_candidates(self) -> None:
        result = scan_summary([])
        assert result["total_candidates"] == 0
        assert result["top_candidates"] == []

    def test_rank_starts_at_one(self) -> None:
        cands = [_cand("c1", 0.5, "human_review_queue", "A")]
        result = scan_summary(cands)
        assert result["top_candidates"][0]["rank"] == 1

    def test_top_candidates_preserve_normalized_drift_evidence(self) -> None:
        result = scan_summary([_cand("c1", 0.5, "human_review_queue", "A")])
        top = result["top_candidates"][0]

        assert top["normalized_drift_hz_s_per_ghz"] == 0.352112676056338
        assert top["is_earth_drift_consistent"] is True


class TestScanSummaryFromBatchDir:
    def test_reads_manifest_files(self, tmp_path: Path) -> None:
        manifest = {
            "candidate_id": "test-cand",
            "candidate_score": 0.75,
            "recommended_pathway": "human_review_queue",
            "frequency_hz": 1420e6,
            "snr": 55.0,
            "normalized_drift_hz_s_per_ghz": 0.28169014084507044,
            "is_earth_drift_consistent": True,
        }
        (tmp_path / "test_manifest.json").write_text(json.dumps(manifest))
        result = scan_summary_from_batch_dir(tmp_path)
        assert result["total_candidates"] == 1
        assert result["top_candidates"][0]["normalized_drift_hz_s_per_ghz"] == (
            0.28169014084507044
        )
        assert result["top_candidates"][0]["is_earth_drift_consistent"] is True

    def test_empty_dir_returns_zero(self, tmp_path: Path) -> None:
        result = scan_summary_from_batch_dir(tmp_path)
        assert result["total_candidates"] == 0

    def test_non_manifest_files_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "not_a_manifest.txt").write_text("hello")
        result = scan_summary_from_batch_dir(tmp_path)
        assert result["total_candidates"] == 0
