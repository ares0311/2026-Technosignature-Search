"""Automatic known/unknown/unresolved resolution for production radio runs."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from techno_search.schemas import Candidate, Track
from techno_search.track_a_crossmatch import cross_match_known_sources
from techno_search.track_a_satellites import match_satellite_transmitter
from techno_search.track_b_gate import track_b_unknown_candidate_gate

KNOWN_EXPLANATION_RESOLUTION_SCHEMA_VERSION = "known_explanation_resolution_v1"
KNOWN_EXPLANATION_DISCLAIMER = (
    "This deterministic state records whether implemented known-explanation checks "
    "explained the observation. unknown means every required check completed and none "
    "matched; it is not a positive technosignature label, detection, or discovery."
)

CrossmatchRunner = Callable[..., dict[str, Any]]
SatelliteRunner = Callable[..., dict[str, Any]]


def resolve_radio_known_explanations(
    candidate: Candidate,
    *,
    project_root: Path | None = None,
    crossmatch_runner: CrossmatchRunner = cross_match_known_sources,
    satellite_runner: SatelliteRunner = match_satellite_transmitter,
) -> dict[str, Any]:
    """Run every available deterministic radio known-explanation check.

    Missing inputs or local catalogs are preserved as unresolved evidence. A
    decisive known explanation remains ``known`` even if a different check is
    unavailable; otherwise every required check must explicitly pass before the
    state can be ``unknown``.
    """

    if candidate.track != Track.RADIO:
        raise ValueError("known-explanation resolution currently supports radio only")

    if bool(candidate.features.get("zero_hit_non_detection")):
        return {
            "schema_version": KNOWN_EXPLANATION_RESOLUTION_SCHEMA_VERSION,
            "disclaimer": KNOWN_EXPLANATION_DISCLAIMER,
            "candidate_id": candidate.candidate_id,
            "classification_state": "known",
            "classification_reason": "known_non_detection_no_hits_above_search_threshold",
            "known_explanations": [
                {
                    "condition_id": "non_detection",
                    "description": "No detector hits were present above the search threshold",
                    "satisfied": False,
                    "evidence": {
                        "zero_hit_non_detection": True,
                        "hit_count": candidate.features.get("hit_count", 0),
                    },
                }
            ],
            "track_a_crossmatch": None,
            "satellite_match": None,
            "gate_result": None,
            "eligible_for_unknown_candidate": False,
            "adversarial_review_required": False,
            "detection_claimed": False,
            "external_submission_allowed": False,
        }

    crossmatch_result = _run_crossmatch(
        candidate,
        project_root=project_root,
        runner=crossmatch_runner,
    )
    satellite_result = _run_satellite_match(
        candidate,
        project_root=project_root,
        runner=satellite_runner,
    )
    gate = track_b_unknown_candidate_gate(
        candidate,
        crossmatch_result=crossmatch_result,
        satellite_result=satellite_result,
    )
    state = str(gate["classification_state"])
    if state == "known":
        reason = "one_or_more_known_explanation_checks_matched"
    elif state == "unknown":
        reason = "all_required_known_explanation_checks_completed_without_match"
    else:
        reason = "required_known_explanation_evidence_or_checks_unavailable"
    return {
        "schema_version": KNOWN_EXPLANATION_RESOLUTION_SCHEMA_VERSION,
        "disclaimer": KNOWN_EXPLANATION_DISCLAIMER,
        "candidate_id": candidate.candidate_id,
        "classification_state": state,
        "classification_reason": reason,
        "known_explanations": list(gate["known_explanations"]),
        "unresolved_count": int(gate["unresolved_count"]),
        "track_a_crossmatch": crossmatch_result,
        "satellite_match": satellite_result,
        "gate_result": gate,
        "eligible_for_unknown_candidate": bool(gate["eligible_for_unknown_candidate"]),
        "adversarial_review_required": state == "unknown",
        "ranking_evidence": dict(gate["ranking_evidence"]),
        "detection_claimed": False,
        "external_submission_allowed": False,
    }


def _run_crossmatch(
    candidate: Candidate,
    *,
    project_root: Path | None,
    runner: CrossmatchRunner,
) -> dict[str, Any]:
    missing = _missing_values(candidate, ("ra_deg", "dec_deg"))
    if missing:
        return _unresolved_result("track_a_crossmatch", missing)
    try:
        return runner(
            float(_value(candidate, "ra_deg")),
            float(_value(candidate, "dec_deg")),
            project_root=project_root,
        )
    except Exception as exc:  # noqa: BLE001 - failure is persisted as unresolved evidence
        return _failed_result("track_a_crossmatch", exc)


def _run_satellite_match(
    candidate: Candidate,
    *,
    project_root: Path | None,
    runner: SatelliteRunner,
) -> dict[str, Any]:
    required = (
        "frequency_hz",
        "observation_time_utc",
        "ra_deg",
        "dec_deg",
        "observer_lat_deg",
        "observer_lon_deg",
        "observer_elevation_m",
    )
    missing = _missing_values(candidate, required)
    if missing:
        return _unresolved_result("satellite_transmitter_match", missing)
    try:
        observed_at = datetime.fromisoformat(
            str(_value(candidate, "observation_time_utc")).replace("Z", "+00:00")
        )
        return runner(
            frequency_hz=float(_value(candidate, "frequency_hz")),
            observation_time_utc=observed_at,
            ra_deg=float(_value(candidate, "ra_deg")),
            dec_deg=float(_value(candidate, "dec_deg")),
            observer_lat_deg=float(_value(candidate, "observer_lat_deg")),
            observer_lon_deg=float(_value(candidate, "observer_lon_deg")),
            observer_elevation_m=float(_value(candidate, "observer_elevation_m")),
            project_root=project_root,
        )
    except Exception as exc:  # noqa: BLE001 - failure is persisted as unresolved evidence
        return _failed_result("satellite_transmitter_match", exc)


def _value(candidate: Candidate, field: str) -> Any:
    for mapping in (candidate.features, candidate.provenance):
        value = mapping.get(field)
        if value not in (None, ""):
            return value
    return None


def _missing_values(candidate: Candidate, fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if _value(candidate, field) is None]


def _unresolved_result(check: str, missing: list[str]) -> dict[str, Any]:
    return {
        "classification": "low_confidence",
        "check": check,
        "status": "missing_inputs",
        "missing_candidate_fields": missing,
        "error": None,
    }


def _failed_result(check: str, exc: Exception) -> dict[str, Any]:
    return {
        "classification": "low_confidence",
        "check": check,
        "status": "evaluation_failed",
        "missing_candidate_fields": [],
        "error": f"{type(exc).__name__}: {exc}",
    }
