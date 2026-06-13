"""Tests for cross-store candidate deduplication (Task 12)."""
from __future__ import annotations

import math

import pytest

from techno_search.cross_store_dedup import (
    CROSS_STORE_DEDUP_DISCLAIMER,
    CROSS_STORE_DEDUP_SCHEMA_VERSION,
    cross_store_dedup_summary,
    find_cross_store_matches,
)


def _make_candidate(
    cid: str,
    track: str,
    ra: float,
    dec: float,
    pathway: str = "human_review_queue",
) -> dict:
    return {
        "candidate_id": cid,
        "track": track,
        "ra_deg": ra,
        "dec_deg": dec,
        "recommended_pathway": pathway,
    }


class TestFindCrossStoreMatches:
    def test_match_across_stores(self) -> None:
        radio = [_make_candidate("r1", "radio", 10.0, 20.0)]
        infrared = [_make_candidate("ir1", "infrared", 10.0, 20.0)]
        matches = find_cross_store_matches(
            [radio, infrared], ["bl_gbt", "gaia_wise"], tolerance_arcsec=10.0
        )
        assert len(matches) == 1
        assert matches[0].candidate_id_a == "r1"
        assert matches[0].candidate_id_b == "ir1"

    def test_no_match_outside_tolerance(self) -> None:
        radio = [_make_candidate("r1", "radio", 10.0, 20.0)]
        infrared = [_make_candidate("ir1", "infrared", 10.1, 20.0)]
        sep_arcsec = 10.1 * 3600 * math.cos(math.radians(20.0))
        find_cross_store_matches(
            [radio, infrared], ["bl_gbt", "gaia_wise"],
            tolerance_arcsec=min(30.0, sep_arcsec - 1),
        )
        # At 0.1 deg separation (~360 arcsec at dec=20) with 30 arcsec tolerance
        matches2 = find_cross_store_matches(
            [radio, infrared], ["bl_gbt", "gaia_wise"], tolerance_arcsec=30.0
        )
        assert len(matches2) == 0

    def test_same_store_not_matched(self) -> None:
        cands = [
            _make_candidate("a1", "radio", 10.0, 20.0),
            _make_candidate("a2", "radio", 10.0, 20.0),
        ]
        matches = find_cross_store_matches(
            [cands], ["bl_gbt"], tolerance_arcsec=100.0
        )
        assert len(matches) == 0

    def test_candidates_without_coords_skipped(self) -> None:
        radio = [{"candidate_id": "r_no_coords", "track": "radio"}]
        infrared = [_make_candidate("ir1", "infrared", 10.0, 20.0)]
        matches = find_cross_store_matches(
            [radio, infrared], ["bl_gbt", "gaia_wise"], tolerance_arcsec=100.0
        )
        assert len(matches) == 0

    def test_match_fields_populated(self) -> None:
        radio = [_make_candidate("r1", "radio", 0.0, 0.0)]
        infrared = [_make_candidate("ir1", "infrared", 0.0, 0.0)]
        matches = find_cross_store_matches(
            [radio, infrared], ["bl_gbt", "gaia_wise"]
        )
        assert len(matches) == 1
        m = matches[0]
        assert m.store_a == "bl_gbt"
        assert m.store_b == "gaia_wise"
        assert m.separation_arcsec >= 0.0
        assert "radio" in m.tracks_matched or "infrared" in m.tracks_matched
        assert m.disclaimer == CROSS_STORE_DEDUP_DISCLAIMER
        assert m.schema_version == CROSS_STORE_DEDUP_SCHEMA_VERSION

    def test_pair_reported_once(self) -> None:
        radio = [_make_candidate("r1", "radio", 5.0, 10.0)]
        infrared = [
            _make_candidate("ir1", "infrared", 5.0, 10.0),
            _make_candidate("ir2", "infrared", 5.0, 10.0),
        ]
        matches = find_cross_store_matches(
            [radio, infrared], ["bl_gbt", "gaia_wise"], tolerance_arcsec=100.0
        )
        # r1 can match ir1 and ir2 — two pairs, all across stores
        assert len(matches) == 2

    def test_multi_track_corroboration(self) -> None:
        radio = [_make_candidate("r1", "radio", 0.0, 0.0)]
        infrared = [_make_candidate("ir1", "infrared", 0.0, 0.0)]
        matches = find_cross_store_matches(
            [radio, infrared], ["bl_gbt", "gaia_wise"]
        )
        assert len(matches[0].tracks_matched) == 2
        assert set(matches[0].tracks_matched) == {"radio", "infrared"}

    def test_mismatched_lengths_raises(self) -> None:
        with pytest.raises(ValueError):
            find_cross_store_matches([[]], ["a", "b"])

    def test_zero_candidates(self) -> None:
        matches = find_cross_store_matches([[], []], ["bl_gbt", "gaia_wise"])
        assert matches == []


class TestCrossStoreDedupSummary:
    def test_summary_fields_present(self) -> None:
        radio = [_make_candidate("r1", "radio", 0.0, 0.0)]
        infrared = [_make_candidate("ir1", "infrared", 0.0, 0.0)]
        result = cross_store_dedup_summary(
            [radio, infrared], ["bl_gbt", "gaia_wise"]
        )
        for field in (
            "total_candidates",
            "stores_compared",
            "store_names",
            "cross_store_match_count",
            "multi_track_corroboration_count",
            "tolerance_arcsec",
            "matches",
            "schema_version",
            "disclaimer",
        ):
            assert field in result, f"missing field: {field}"

    def test_total_candidates_correct(self) -> None:
        radio = [_make_candidate(f"r{i}", "radio", float(i), 0.0) for i in range(3)]
        infrared = [_make_candidate(f"ir{i}", "infrared", float(i) + 50, 0.0)
                    for i in range(2)]
        result = cross_store_dedup_summary([radio, infrared], ["a", "b"])
        assert result["total_candidates"] == 5

    def test_no_matches_when_far_apart(self) -> None:
        radio = [_make_candidate("r1", "radio", 0.0, 0.0)]
        infrared = [_make_candidate("ir1", "infrared", 90.0, 0.0)]
        result = cross_store_dedup_summary(
            [radio, infrared], ["bl_gbt", "gaia_wise"], tolerance_arcsec=10.0
        )
        assert result["cross_store_match_count"] == 0

    def test_disclaimer_and_version(self) -> None:
        result = cross_store_dedup_summary([[], []], ["a", "b"])
        assert "detection claim" in result["disclaimer"]
        assert result["schema_version"] == CROSS_STORE_DEDUP_SCHEMA_VERSION

    def test_match_as_dict_serialisable(self) -> None:
        import json
        radio = [_make_candidate("r1", "radio", 1.0, 1.0)]
        infrared = [_make_candidate("ir1", "infrared", 1.0, 1.0)]
        result = cross_store_dedup_summary([radio, infrared], ["bl_gbt", "gaia"])
        json.dumps(result)  # must not raise
