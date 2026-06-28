"""Tests for cross-target RFI suppression (Task 5)."""
from __future__ import annotations

from techno_search.cross_target_rfi import (
    CROSS_TARGET_RFI_DISCLAIMER,
    CROSS_TARGET_RFI_SCHEMA_VERSION,
    cross_target_rfi_summary,
    flag_cross_target_rfi,
)


def _cand(cid: str, freq: float, target: str) -> dict:
    return {"candidate_id": cid, "frequency_hz": freq, "target_name": target}


class TestFlagCrossTargetRfi:
    def test_same_freq_different_targets_flagged(self) -> None:
        lists = [
            [_cand("r1", 1420e6, "HIP99427")],
            [_cand("r2", 1420e6, "HIP100670")],
        ]
        flagged = flag_cross_target_rfi(lists)
        assert "r1" in flagged
        assert "r2" in flagged

    def test_same_freq_same_target_not_flagged(self) -> None:
        lists = [
            [_cand("r1", 1420e6, "HIP99427"), _cand("r2", 1420e6, "HIP99427")]
        ]
        flagged = flag_cross_target_rfi(lists)
        assert len(flagged) == 0

    def test_within_tolerance_flagged(self) -> None:
        lists = [
            [_cand("r1", 1420000000.0, "A")],
            [_cand("r2", 1420000200.0, "B")],  # 200 Hz apart < 500 Hz default
        ]
        flagged = flag_cross_target_rfi(lists, freq_tolerance_hz=500.0)
        assert "r1" in flagged
        assert "r2" in flagged

    def test_outside_tolerance_not_flagged(self) -> None:
        lists = [
            [_cand("r1", 1420000000.0, "A")],
            [_cand("r2", 1420001000.0, "B")],  # 1000 Hz apart > 500 Hz default
        ]
        flagged = flag_cross_target_rfi(lists, freq_tolerance_hz=500.0)
        assert len(flagged) == 0

    def test_flag_record_fields(self) -> None:
        lists = [
            [_cand("r1", 1420e6, "A")],
            [_cand("r2", 1420e6, "B")],
        ]
        flagged = flag_cross_target_rfi(lists)
        assert flagged["r1"]["flagged"] is True
        assert flagged["r1"]["reason"] == "cross_target_rfi"
        assert flagged["r1"]["match_count"] >= 1
        assert flagged["r1"]["matched_target_names"] == ["A", "B"]
        assert flagged["r1"]["matched_candidate_ids"] == ["r1", "r2"]

    def test_empty_lists_returns_empty(self) -> None:
        assert flag_cross_target_rfi([[], []]) == {}

    def test_zero_frequency_observation_records_are_not_flagged(self) -> None:
        lists = [
            [
                {
                    "candidate_id": "zero-a",
                    "frequency_hz": 0.0,
                    "target_name": "HIP17147",
                    "observation_only": True,
                }
            ],
            [
                {
                    "candidate_id": "zero-b",
                    "frequency_hz": 0.0,
                    "target_name": "HIP39826",
                    "observation_only": True,
                }
            ],
        ]

        assert flag_cross_target_rfi(lists) == {}

    def test_single_target_no_flags(self) -> None:
        lists = [[_cand("r1", 1420e6, "A"), _cand("r2", 1421e6, "A")]]
        assert flag_cross_target_rfi(lists) == {}

    def test_three_targets_all_flagged(self) -> None:
        lists = [
            [_cand("r1", 1420e6, "A")],
            [_cand("r2", 1420e6, "B")],
            [_cand("r3", 1420e6, "C")],
        ]
        flagged = flag_cross_target_rfi(lists)
        assert "r1" in flagged
        assert "r2" in flagged
        assert "r3" in flagged


class TestCrossTargetRfiSummary:
    def test_summary_fields_present(self) -> None:
        lists = [
            [_cand("r1", 1420e6, "A")],
            [_cand("r2", 1420e6, "B")],
        ]
        result = cross_target_rfi_summary(lists)
        for field in (
            "total_candidates",
            "flagged_count",
            "flag_rate",
            "schema_version",
            "disclaimer",
        ):
            assert field in result, f"missing field: {field}"

    def test_flag_rate_correct(self) -> None:
        lists = [
            [_cand("r1", 1420e6, "A"), _cand("r3", 1500e6, "A")],
            [_cand("r2", 1420e6, "B"), _cand("r4", 1600e6, "B")],
        ]
        result = cross_target_rfi_summary(lists)
        # r1 and r2 match, r3 and r4 do not
        assert result["flagged_count"] == 2
        assert result["total_candidates"] == 4

    def test_disclaimer_and_schema_version(self) -> None:
        result = cross_target_rfi_summary([[], []])
        assert "detection claim" not in result["disclaimer"]  # softer language
        assert result["schema_version"] == CROSS_TARGET_RFI_SCHEMA_VERSION
        assert result["disclaimer"] == CROSS_TARGET_RFI_DISCLAIMER
