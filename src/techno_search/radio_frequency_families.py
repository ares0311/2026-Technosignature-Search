"""BLC1-inspired frequency-family diagnostics for real radio hit tables.

The harmonic search follows Sheikh et al. (2021), arXiv:2111.06350:
fundamentals from 100--1,000 MHz on a 1 kHz grid, the first 20 harmonics,
and a 1 kHz match tolerance.  A match is RFI-family evidence only; it is
not a physical-origin label or a candidate classification.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

FREQUENCY_FAMILY_SCHEMA_VERSION = "radio_frequency_family_summary_v1"
FREQUENCY_FAMILY_DISCLAIMER = (
    "Frequency-family matches are deterministic RFI-forensics evidence only. "
    "They are not labels, detections, discoveries, or proof of physical origin."
)
METHOD_ARXIV_ID = "2111.06350"
METHOD_DOI = "10.1038/s41550-021-01508-8"
DEFAULT_FUNDAMENTAL_MIN_HZ = 100_000_000.0
DEFAULT_FUNDAMENTAL_MAX_HZ = 1_000_000_000.0
DEFAULT_FUNDAMENTAL_STEP_HZ = 1_000.0
DEFAULT_MAX_HARMONIC = 20
DEFAULT_MATCH_TOLERANCE_HZ = 1_000.0


def frequency_family_summary(
    hit_rows: Sequence[Mapping[str, Any]],
    *,
    clock_frequencies_hz: Sequence[float] = (),
    fundamental_min_hz: float = DEFAULT_FUNDAMENTAL_MIN_HZ,
    fundamental_max_hz: float = DEFAULT_FUNDAMENTAL_MAX_HZ,
    fundamental_step_hz: float = DEFAULT_FUNDAMENTAL_STEP_HZ,
    max_harmonic: int = DEFAULT_MAX_HARMONIC,
    match_tolerance_hz: float = DEFAULT_MATCH_TOLERANCE_HZ,
    max_returned_families: int = 20,
) -> dict[str, Any]:
    """Summarize harmonic and explicitly configured clock-spacing families."""
    _validate_parameters(
        fundamental_min_hz=fundamental_min_hz,
        fundamental_max_hz=fundamental_max_hz,
        fundamental_step_hz=fundamental_step_hz,
        max_harmonic=max_harmonic,
        match_tolerance_hz=match_tolerance_hz,
        max_returned_families=max_returned_families,
    )
    clocks = tuple(
        sorted(
            {
                _positive_float(value, "clock frequency")
                for value in clock_frequencies_hz
            }
        )
    )
    hits = _normalise_hits(hit_rows)
    harmonic_families = _harmonic_families(
        hits,
        fundamental_min_hz=fundamental_min_hz,
        fundamental_max_hz=fundamental_max_hz,
        fundamental_step_hz=fundamental_step_hz,
        max_harmonic=max_harmonic,
        match_tolerance_hz=match_tolerance_hz,
    )
    clock_families = _clock_spacing_families(
        hits,
        clocks=clocks,
        match_tolerance_hz=match_tolerance_hz,
    )
    flagged_ids = sorted(
        {
            candidate_id
            for family in (*harmonic_families, *clock_families)
            for candidate_id in family["candidate_ids"]
        }
    )
    return {
        "schema_version": FREQUENCY_FAMILY_SCHEMA_VERSION,
        "disclaimer": FREQUENCY_FAMILY_DISCLAIMER,
        "method": {
            "paper": "Sheikh et al. (2021) BLC1 verification framework",
            "arxiv_id": METHOD_ARXIV_ID,
            "doi": METHOD_DOI,
            "fundamental_min_hz": float(fundamental_min_hz),
            "fundamental_max_hz": float(fundamental_max_hz),
            "fundamental_step_hz": float(fundamental_step_hz),
            "max_harmonic": int(max_harmonic),
            "match_tolerance_hz": float(match_tolerance_hz),
        },
        "hit_count": len(hits),
        "configured_clock_frequencies_hz": list(clocks),
        "harmonic_family_count": len(harmonic_families),
        "clock_spacing_family_count": len(clock_families),
        "frequency_family_evidence_present": bool(harmonic_families or clock_families),
        "flagged_hit_count": len(flagged_ids),
        "flagged_candidate_ids": flagged_ids,
        "harmonic_families": harmonic_families[:max_returned_families],
        "harmonic_family_count_returned": min(len(harmonic_families), max_returned_families),
        "clock_spacing_families": clock_families[:max_returned_families],
        "clock_spacing_family_count_returned": min(
            len(clock_families), max_returned_families
        ),
    }


def _normalise_hits(hit_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for index, row in enumerate(hit_rows, start=1):
        try:
            frequency_hz = float(row["frequency_hz"])
        except (KeyError, TypeError, ValueError):
            continue
        if not math.isfinite(frequency_hz) or frequency_hz <= 0:
            continue
        hits.append(
            {
                "candidate_id": str(row.get("candidate_id") or f"hit:{index}"),
                "frequency_hz": frequency_hz,
            }
        )
    return sorted(hits, key=lambda item: (item["frequency_hz"], item["candidate_id"]))


def _harmonic_families(
    hits: Sequence[Mapping[str, Any]],
    *,
    fundamental_min_hz: float,
    fundamental_max_hz: float,
    fundamental_step_hz: float,
    max_harmonic: int,
    match_tolerance_hz: float,
) -> list[dict[str, Any]]:
    groups: dict[float, dict[str, tuple[int, float, float]]] = defaultdict(dict)
    for hit in hits:
        candidate_id = str(hit["candidate_id"])
        frequency_hz = float(hit["frequency_hz"])
        for harmonic in range(1, max_harmonic + 1):
            raw_index = frequency_hz / (harmonic * fundamental_step_hz)
            for grid_index in {math.floor(raw_index), round(raw_index), math.ceil(raw_index)}:
                fundamental_hz = grid_index * fundamental_step_hz
                if not fundamental_min_hz <= fundamental_hz <= fundamental_max_hz:
                    continue
                residual_hz = abs(frequency_hz - harmonic * fundamental_hz)
                if residual_hz > match_tolerance_hz:
                    continue
                previous = groups[fundamental_hz].get(candidate_id)
                if previous is None or residual_hz < previous[1]:
                    groups[fundamental_hz][candidate_id] = (
                        harmonic,
                        residual_hz,
                        frequency_hz,
                    )

    families: list[dict[str, Any]] = []
    for fundamental_hz, members_by_id in groups.items():
        members = sorted(
            (
                {
                    "candidate_id": candidate_id,
                    "frequency_hz": values[2],
                    "harmonic": values[0],
                    "residual_hz": values[1],
                }
                for candidate_id, values in members_by_id.items()
            ),
            key=lambda item: (item["harmonic"], item["frequency_hz"], item["candidate_id"]),
        )
        if len(members) < 2 or len({item["harmonic"] for item in members}) < 2:
            continue
        families.append(
            {
                "family_type": "harmonic_sequence",
                "fundamental_hz": fundamental_hz,
                "member_count": len(members),
                "candidate_ids": [str(item["candidate_id"]) for item in members],
                "members": members,
                "max_residual_hz": max(
                    values[1] for values in members_by_id.values()
                ),
            }
        )
    return sorted(
        families,
        key=lambda item: (
            -int(item["member_count"]),
            float(item["max_residual_hz"]),
            float(item["fundamental_hz"]),
        ),
    )


def _clock_spacing_families(
    hits: Sequence[Mapping[str, Any]],
    *,
    clocks: Sequence[float],
    match_tolerance_hz: float,
) -> list[dict[str, Any]]:
    if not clocks:
        return []
    groups: dict[float, list[dict[str, Any]]] = defaultdict(list)
    for left_index, left in enumerate(hits):
        for right in hits[left_index + 1 :]:
            spacing_hz = float(right["frequency_hz"]) - float(left["frequency_hz"])
            for clock_hz in clocks:
                multiplier = round(spacing_hz / clock_hz)
                if multiplier < 1:
                    continue
                residual_hz = abs(spacing_hz - multiplier * clock_hz)
                if residual_hz <= match_tolerance_hz:
                    groups[clock_hz].append(
                        {
                            "left_candidate_id": str(left["candidate_id"]),
                            "right_candidate_id": str(right["candidate_id"]),
                            "spacing_hz": spacing_hz,
                            "clock_multiplier": multiplier,
                            "residual_hz": residual_hz,
                        }
                    )
    families: list[dict[str, Any]] = []
    for clock_hz, pairs in groups.items():
        candidate_ids = sorted(
            {
                candidate_id
                for pair in pairs
                for candidate_id in (
                    pair["left_candidate_id"],
                    pair["right_candidate_id"],
                )
            }
        )
        families.append(
            {
                "family_type": "clock_spacing_sequence",
                "clock_frequency_hz": clock_hz,
                "member_count": len(candidate_ids),
                "pair_count": len(pairs),
                "candidate_ids": candidate_ids,
                "pairs": sorted(
                    pairs,
                    key=lambda item: (
                        int(item["clock_multiplier"]),
                        float(item["residual_hz"]),
                        str(item["left_candidate_id"]),
                    ),
                ),
            }
        )
    return sorted(
        families,
        key=lambda item: (-int(item["member_count"]), float(item["clock_frequency_hz"])),
    )


def _validate_parameters(
    *,
    fundamental_min_hz: float,
    fundamental_max_hz: float,
    fundamental_step_hz: float,
    max_harmonic: int,
    match_tolerance_hz: float,
    max_returned_families: int,
) -> None:
    if fundamental_min_hz <= 0 or fundamental_max_hz < fundamental_min_hz:
        raise ValueError("fundamental frequency bounds must be positive and ordered")
    if fundamental_step_hz <= 0:
        raise ValueError("fundamental_step_hz must be positive")
    if max_harmonic < 2:
        raise ValueError("max_harmonic must be at least 2")
    if match_tolerance_hz < 0:
        raise ValueError("match_tolerance_hz must be non-negative")
    if max_returned_families < 0:
        raise ValueError("max_returned_families must be non-negative")


def _positive_float(value: float, label: str) -> float:
    converted = float(value)
    if not math.isfinite(converted) or converted <= 0:
        raise ValueError(f"{label} must be a finite positive number")
    return converted
