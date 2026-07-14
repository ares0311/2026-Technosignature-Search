"""Tests for BLC1-inspired deterministic frequency-family diagnostics."""

from __future__ import annotations

from techno_search.radio_frequency_families import frequency_family_summary


def _hit(candidate_id: str, frequency_hz: float) -> dict[str, object]:
    return {"candidate_id": candidate_id, "frequency_hz": frequency_hz}


def test_detects_paper_method_harmonic_sequence() -> None:
    result = frequency_family_summary(
        [
            _hit("h2", 200_000_400.0),
            _hit("h3", 299_999_300.0),
            _hit("unrelated", 712_345_678.0),
        ]
    )

    assert result["method"]["arxiv_id"] == "2111.06350"
    assert result["method"]["max_harmonic"] == 20
    assert result["method"]["match_tolerance_hz"] == 1000.0
    family = next(
        item for item in result["harmonic_families"] if item["fundamental_hz"] == 100_000_000.0
    )
    assert family["candidate_ids"] == ["h2", "h3"]
    assert family["member_count"] == 2
    assert result["frequency_family_evidence_present"] is True
    assert "not labels" in result["disclaimer"]


def test_does_not_create_family_from_one_hit_or_same_harmonic() -> None:
    result = frequency_family_summary(
        [
            _hit("duplicate-a", 200_000_100.0),
            _hit("duplicate-b", 200_000_200.0),
        ]
    )

    assert result["harmonic_family_count"] == 0
    assert result["frequency_family_evidence_present"] is False


def test_clock_spacing_requires_explicit_clock_frequency() -> None:
    rows = [
        _hit("blc1-like", 982_002_400.0),
        _hit("lookalike", 1_062_002_560.0),
    ]

    without_clock = frequency_family_summary(rows)
    with_clock = frequency_family_summary(rows, clock_frequencies_hz=[2_000_004.0])

    assert without_clock["clock_spacing_family_count"] == 0
    assert with_clock["clock_spacing_family_count"] == 1
    family = with_clock["clock_spacing_families"][0]
    assert family["clock_frequency_hz"] == 2_000_004.0
    assert family["pairs"][0]["clock_multiplier"] == 40


def test_invalid_or_missing_frequency_rows_are_not_labeled() -> None:
    result = frequency_family_summary(
        [{"candidate_id": "missing"}, {"candidate_id": "invalid", "frequency_hz": "nan"}]
    )

    assert result["hit_count"] == 0
    assert result["flagged_hit_count"] == 0
    assert result["harmonic_families"] == []
