from __future__ import annotations

from techno_search.multi_modal_crossmatch import (
    CandidatePosition,
    candidate_positions_from_reports,
    find_multi_modal_groups,
    multi_modal_crossmatch_summary,
)


def test_two_tracks_at_the_same_position_form_a_multi_modal_group() -> None:
    candidates = [
        CandidatePosition("radio-1", "radio", ra_deg=10.0, dec_deg=20.0),
        CandidatePosition("photometry-1", "transit_photometry", ra_deg=10.001, dec_deg=20.001),
    ]

    groups = find_multi_modal_groups(candidates, match_radius_arcsec=60.0)

    assert len(groups) == 1
    assert groups[0].is_multi_modal is True
    assert groups[0].distinct_track_count == 2
    assert set(groups[0].candidate_ids) == {"radio-1", "photometry-1"}


def test_distant_candidates_do_not_group() -> None:
    candidates = [
        CandidatePosition("radio-1", "radio", ra_deg=10.0, dec_deg=20.0),
        CandidatePosition("infrared-1", "infrared", ra_deg=200.0, dec_deg=-40.0),
    ]

    groups = find_multi_modal_groups(candidates, match_radius_arcsec=60.0)

    assert groups == []


def test_same_track_matches_are_grouped_but_not_multi_modal() -> None:
    candidates = [
        CandidatePosition("radio-1", "radio", ra_deg=10.0, dec_deg=20.0),
        CandidatePosition("radio-2", "radio", ra_deg=10.0005, dec_deg=20.0005),
    ]

    groups = find_multi_modal_groups(candidates, match_radius_arcsec=60.0)

    assert len(groups) == 1
    assert groups[0].is_multi_modal is False
    assert groups[0].distinct_track_count == 1


def test_transitive_grouping_across_three_candidates() -> None:
    # A matches B, B matches C, but A and C are just outside each other's
    # radius directly -- real union-find must still join all three via B.
    candidates = [
        CandidatePosition("radio-1", "radio", ra_deg=10.0, dec_deg=20.0),
        CandidatePosition(
            "photometry-1", "transit_photometry", ra_deg=10.0 + 0.005, dec_deg=20.0
        ),
        CandidatePosition("infrared-1", "infrared", ra_deg=10.0 + 0.010, dec_deg=20.0),
    ]

    groups = find_multi_modal_groups(candidates, match_radius_arcsec=20.0)

    assert len(groups) == 1
    assert groups[0].distinct_track_count == 3
    assert set(groups[0].candidate_ids) == {"radio-1", "photometry-1", "infrared-1"}


def test_candidate_positions_from_reports_skips_missing_coordinates() -> None:
    reports = [
        {
            "candidate_id": "a",
            "track": "radio",
            "recommended_pathway": "human_review_queue",
            "features": {"ra_deg": 10.0, "dec_deg": 20.0},
        },
        {
            "candidate_id": "b",
            "track": "anomaly",
            "recommended_pathway": "human_review_queue",
            "features": {},
        },
    ]

    positions = candidate_positions_from_reports(reports)

    assert len(positions) == 1
    assert positions[0].candidate_id == "a"


def test_multi_modal_crossmatch_summary_reports_real_counts() -> None:
    reports = [
        {
            "candidate_id": "radio-1",
            "track": "radio",
            "recommended_pathway": "human_review_queue",
            "features": {"ra_deg": 10.0, "dec_deg": 20.0},
        },
        {
            "candidate_id": "photometry-1",
            "track": "transit_photometry",
            "recommended_pathway": "candidate_review_packet",
            "features": {"ra_deg": 10.001, "dec_deg": 20.001},
        },
        {
            "candidate_id": "infrared-1",
            "track": "infrared",
            "recommended_pathway": "human_review_queue",
            "features": {},
        },
    ]

    summary = multi_modal_crossmatch_summary(reports)

    assert summary["candidate_count_with_position"] == 2
    assert summary["candidate_count_without_position"] == 1
    assert summary["multi_modal_group_count"] == 1
    assert summary["multi_modal_groups"][0]["distinct_track_count"] == 2
    assert "detection" in summary["disclaimer"] or "triage" in summary["disclaimer"]
