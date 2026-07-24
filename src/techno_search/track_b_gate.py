"""Deterministic known-explanation resolution for radio candidates.

``unknown`` is constructed only when every required known-explanation and
readiness check completes and none explains the event. ``known`` means at
least one completed check supplies an explanation. ``unresolved`` means no
explanation was found but required evidence is missing.

    1. not confidently pulsar
    2. not confidently FRB
    3. not cross-matched to known blazar/AGN/gamma source
    4. not known satellite/transmitter at observation time and beam direction
    5. not known RFI region
    6. not instrument/band-edge/notch artifact
    7. passes ON/OFF cadence checks
    8. has preserved provenance and a reproducible extraction script

Anomaly/OOD scores are retained as ranking evidence only. They never define or
block the known/unknown boundary and no score threshold is invented here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from techno_search.schemas import Candidate

TRACK_B_GATE_SCHEMA_VERSION = "track_b_unknown_candidate_gate_v2"

TRACK_B_GATE_DISCLAIMER = (
    "This is a Track B known-explanation gate evaluation, not a detection or "
    "discovery claim. unknown_candidate is a local triage queue state only: "
    "it means every implemented known-source, RFI, instrument-artifact, and "
    "cadence check failed to explain the event, not that the event has been "
    "confirmed as anomalous or technosignature-relevant. No condition here "
    "authorizes external submission or expert review."
)

# The brief's Phase 4 gate. instrumental_artifact / rfi_overlap / cadence
# thresholds are conservative pass/fail cuts on the existing radio pipeline
# features (radio/prototype.py); they are not new scientific claims, they
# re-use scores already computed elsewhere in this codebase.
INSTRUMENTAL_ARTIFACT_MAX_SCORE = 0.3
RFI_OVERLAP_MAX_SCORE = 0.5
CADENCE_PASS_SCORE = 1.0

TRACK_B_PACKET_READINESS_SCHEMA_VERSION = "track_b_candidate_packet_readiness_v1"

TRACK_B_CANDIDATE_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "ra_deg": ("ra_deg", "best_hit_ra_deg", "target_ra_deg"),
    "dec_deg": ("dec_deg", "best_hit_dec_deg", "target_dec_deg"),
    "frequency_hz": ("frequency_hz", "best_hit_frequency_hz"),
    "observation_time_utc": ("observation_time_utc", "timestamp_utc", "time_utc"),
    "observer_lat_deg": ("observer_lat_deg", "telescope_lat_deg"),
    "observer_lon_deg": ("observer_lon_deg", "telescope_lon_deg"),
    "observer_elevation_m": ("observer_elevation_m", "telescope_elevation_m"),
}

TRACK_B_REQUIRED_CANDIDATE_FEATURES = (
    "rfi_band_overlap_score",
    "instrumental_artifact_score",
    "abacab_cadence_score",
)

KNOWN_EXPLANATION_CONDITION_IDS = frozenset(
    {
        "not_confidently_pulsar",
        "not_confidently_frb",
        "not_known_blazar_agn_or_gamma",
        "not_known_satellite_transmitter",
        "not_locally_identified_known_object",
        "not_known_rfi_region",
        "not_instrument_artifact",
        "not_below_search_threshold",
        "passes_cadence_checks",
    }
)


@dataclass(frozen=True)
class GateCondition:
    """One of the nine Phase 4 conditions."""

    condition_id: str
    description: str
    satisfied: bool | None
    evidence: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "description": self.description,
            "satisfied": self.satisfied,
            "evidence": self.evidence,
        }


def _catalog_conditions(crossmatch_result: dict[str, Any]) -> list[GateCondition]:
    classification = str(crossmatch_result.get("classification", "low_confidence"))
    class_by_condition = {
        "not_confidently_pulsar": "known_pulsar",
        "not_confidently_frb": "known_frb",
        "not_known_blazar_agn_or_gamma": None,  # checked below (two classes)
    }
    conditions = []
    for condition_id, known_class in class_by_condition.items():
        if condition_id == "not_known_blazar_agn_or_gamma":
            matched = classification in {"known_blazar_agn", "known_gamma_ray_source"}
        else:
            matched = classification == known_class

        if classification == "low_confidence":
            satisfied: bool | None = None
        else:
            satisfied = not matched

        described_class = known_class or "blazar_agn/gamma_ray_source"
        conditions.append(
            GateCondition(
                condition_id=condition_id,
                description=(
                    f"Track A catalog cross-match does not classify as {described_class}"
                ),
                satisfied=satisfied,
                evidence={"crossmatch_classification": classification},
            )
        )
    return conditions


def _satellite_condition(satellite_result: dict[str, Any] | None) -> GateCondition:
    if satellite_result is None:
        return GateCondition(
            condition_id="not_known_satellite_transmitter",
            description="Event is not explained by a known satellite transmitter",
            satisfied=None,
            evidence={"note": "satellite match not evaluated (no result supplied)"},
        )
    classification = str(satellite_result.get("classification", "low_confidence"))
    if classification == "low_confidence":
        satisfied: bool | None = None
    else:
        satisfied = classification != "satellite_transmitter"
    return GateCondition(
        condition_id="not_known_satellite_transmitter",
        description="Event is not explained by a known satellite transmitter",
        satisfied=satisfied,
        evidence={"satellite_match_classification": classification},
    )


def _local_known_object_condition(candidate: Candidate) -> GateCondition:
    score = candidate.features.get("known_object_score", 0.0)
    matched = float(score or 0.0) >= 0.9
    return GateCondition(
        condition_id="not_locally_identified_known_object",
        description="Local provenance does not identify a known calibration object",
        satisfied=not matched,
        evidence={
            "known_object_score": score,
            "reason": candidate.features.get("local_known_object_reason"),
        },
    )


def _rfi_condition(candidate: Candidate) -> GateCondition:
    score = candidate.features.get("rfi_band_overlap_score")
    if score is None:
        return GateCondition(
            condition_id="not_known_rfi_region",
            description="Event frequency does not overlap a known RFI band/database entry",
            satisfied=None,
            evidence={"rfi_band_overlap_score": None},
        )
    satisfied = float(score) <= RFI_OVERLAP_MAX_SCORE
    return GateCondition(
        condition_id="not_known_rfi_region",
        description="Event frequency does not overlap a known RFI band/database entry",
        satisfied=satisfied,
        evidence={"rfi_band_overlap_score": score, "max_allowed": RFI_OVERLAP_MAX_SCORE},
    )


def _instrument_artifact_condition(candidate: Candidate) -> GateCondition:
    score = candidate.features.get("instrumental_artifact_score")
    if score is None:
        return GateCondition(
            condition_id="not_instrument_artifact",
            description="Event is not a known instrument/band-edge/notch artifact",
            satisfied=None,
            evidence={"instrumental_artifact_score": None},
        )
    satisfied = float(score) <= INSTRUMENTAL_ARTIFACT_MAX_SCORE
    return GateCondition(
        condition_id="not_instrument_artifact",
        description="Event is not a known instrument/band-edge/notch artifact",
        satisfied=satisfied,
        evidence={
            "instrumental_artifact_score": score,
            "max_allowed": INSTRUMENTAL_ARTIFACT_MAX_SCORE,
        },
    )


def _cadence_condition(candidate: Candidate) -> GateCondition:
    score = candidate.features.get("abacab_cadence_score")
    if score is None:
        return GateCondition(
            condition_id="passes_cadence_checks",
            description="Event passes ABACAB ON/OFF cadence rejection",
            satisfied=None,
            evidence={"abacab_cadence_score": None},
        )
    score_f = float(score)
    satisfied = score_f >= CADENCE_PASS_SCORE if score_f != 0.5 else None
    return GateCondition(
        condition_id="passes_cadence_checks",
        description="Event passes ABACAB ON/OFF cadence rejection",
        satisfied=satisfied,
        evidence={"abacab_cadence_score": score},
    )


def _search_threshold_condition(candidate: Candidate) -> GateCondition:
    snr = candidate.features.get("snr")
    threshold = candidate.provenance.get("processing_snr_threshold")
    hit_count = int(candidate.features.get("hit_count", 0) or 0)
    validated_hit_table = (
        str(candidate.provenance.get("reader_type", "")) == "turboSETI_csv"
        and str(candidate.provenance.get("source_file", "")).lower().endswith(".dat")
        and hit_count > 0
    )
    if snr is None:
        return GateCondition(
            condition_id="not_below_search_threshold",
            description="Event is above the provenance-stamped detector search threshold",
            satisfied=None,
            evidence={
                "snr": snr,
                "processing_snr_threshold": threshold,
                "validated_hit_table": validated_hit_table,
            },
        )
    if threshold in (None, "") or float(threshold) <= 0.0:
        return GateCondition(
            condition_id="not_below_search_threshold",
            description="Event is above the detector threshold recorded by its hit table",
            satisfied=True if validated_hit_table else None,
            evidence={
                "snr": snr,
                "processing_snr_threshold": threshold,
                "validated_hit_table": validated_hit_table,
                "evidence_basis": (
                    "validated_hit_bearing_turboseti_dat"
                    if validated_hit_table
                    else "numeric_threshold_and_validated_hit_table_unavailable"
                ),
            },
        )
    satisfied = float(snr) >= float(threshold)
    return GateCondition(
        condition_id="not_below_search_threshold",
        description="Event is above the provenance-stamped detector search threshold",
        satisfied=satisfied,
        evidence={"snr": snr, "processing_snr_threshold": threshold},
    )


def _provenance_condition(candidate: Candidate) -> GateCondition:
    has_source_ids = len(candidate.source_ids) > 0
    has_provenance = len(candidate.provenance) > 0
    satisfied: bool | None = True if has_source_ids and has_provenance else None
    return GateCondition(
        condition_id="has_preserved_provenance",
        description="Event has preserved source provenance and a reproducible extraction path",
        satisfied=satisfied,
        evidence={
            "source_id_count": len(candidate.source_ids),
            "provenance_field_count": len(candidate.provenance),
        },
    )


def track_b_unknown_candidate_gate(
    candidate: Candidate,
    *,
    crossmatch_result: dict[str, Any],
    satellite_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve one radio candidate as known, unknown, or unresolved.

    Callers must first run track_a_crossmatch.cross_match_known_sources()
    and (optionally) track_a_satellites.match_satellite_transmitter() and
    pass their results in -- this function only combines already-computed
    evidence, it does not perform any network or catalog lookups itself.

    Returns eligible_for_unknown_candidate=True only when every required
    condition is explicitly satisfied. Missing evidence remains unresolved;
    anomaly/OOD scoring is recorded separately as ranking evidence.
    """

    conditions: list[GateCondition] = []
    conditions.extend(_catalog_conditions(crossmatch_result))
    conditions.append(_satellite_condition(satellite_result))
    conditions.append(_local_known_object_condition(candidate))
    conditions.append(_rfi_condition(candidate))
    conditions.append(_instrument_artifact_condition(candidate))
    conditions.append(_cadence_condition(candidate))
    conditions.append(_search_threshold_condition(candidate))
    conditions.append(_provenance_condition(candidate))

    satisfied_count = sum(1 for c in conditions if c.satisfied is True)
    failed_count = sum(1 for c in conditions if c.satisfied is False)
    unresolved_count = sum(1 for c in conditions if c.satisfied is None)
    known_explanations = [
        condition
        for condition in conditions
        if condition.condition_id in KNOWN_EXPLANATION_CONDITION_IDS
        and condition.satisfied is False
    ]
    if known_explanations:
        classification_state = "known"
    elif unresolved_count:
        classification_state = "unresolved"
    else:
        classification_state = "unknown"
    eligible = classification_state == "unknown"

    return {
        "schema_version": TRACK_B_GATE_SCHEMA_VERSION,
        "disclaimer": TRACK_B_GATE_DISCLAIMER,
        "candidate_id": candidate.candidate_id,
        "condition_count": len(conditions),
        "satisfied_count": satisfied_count,
        "failed_count": failed_count,
        "unresolved_count": unresolved_count,
        "eligible_for_unknown_candidate": eligible,
        "classification_state": classification_state,
        "known_explanation_count": len(known_explanations),
        "known_explanations": [condition.as_dict() for condition in known_explanations],
        "ranking_evidence": {
            "semisupervised_anomaly_score": candidate.features.get(
                "semisupervised_anomaly_score"
            ),
            "calibrated_threshold_applied": False,
            "affects_classification_state": False,
        },
        "conditions": [c.as_dict() for c in conditions],
    }


def _candidate_evidence_value(candidate: Candidate, field_id: str) -> Any:
    aliases = TRACK_B_CANDIDATE_FIELD_ALIASES[field_id]
    for mapping in (candidate.features, candidate.provenance):
        for alias in aliases:
            value = mapping.get(alias)
            if value not in (None, ""):
                return value
    return None


def _missing_candidate_fields(candidate: Candidate, field_ids: tuple[str, ...]) -> list[str]:
    return [
        field_id
        for field_id in field_ids
        if _candidate_evidence_value(candidate, field_id) is None
    ]


def _evidence_status(*, provided: bool, missing_inputs: list[str]) -> str:
    if provided:
        return "provided"
    if missing_inputs:
        return "missing_inputs"
    return "ready_to_run"


def track_b_candidate_packet_readiness(
    candidate: Candidate,
    *,
    crossmatch_result: dict[str, Any] | None = None,
    satellite_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit whether a real candidate packet is ready for Track B evaluation.

    This function is deliberately fail-closed. It reports the exact packet
    metadata and evidence JSON needed to evaluate the gate, but it does not
    infer sky position, observation time, telescope location, or catalog
    classifications. When crossmatch evidence is supplied, it also runs the
    existing Track B gate so operators can see the concrete blocking
    conditions for the same packet.
    """

    missing_crossmatch_inputs = _missing_candidate_fields(candidate, ("ra_deg", "dec_deg"))
    missing_satellite_inputs = _missing_candidate_fields(
        candidate,
        (
            "frequency_hz",
            "observation_time_utc",
            "ra_deg",
            "dec_deg",
            "observer_lat_deg",
            "observer_lon_deg",
            "observer_elevation_m",
        ),
    )
    missing_candidate_features = [
        field for field in TRACK_B_REQUIRED_CANDIDATE_FEATURES if field not in candidate.features
    ]
    provenance_ready = bool(candidate.source_ids) and bool(candidate.provenance)
    is_radio = candidate.track.value == "radio"
    is_zero_hit_non_detection = bool(candidate.features.get("zero_hit_non_detection"))

    blocking_reasons: list[str] = []
    if not is_radio:
        blocking_reasons.append("candidate_track_is_not_radio")
    if is_zero_hit_non_detection:
        blocking_reasons.append("zero_hit_non_detection_is_not_a_track_b_candidate")
    if missing_candidate_features:
        blocking_reasons.append("missing_track_b_candidate_features")
    if not provenance_ready:
        blocking_reasons.append("missing_source_ids_or_provenance")
    if crossmatch_result is None:
        blocking_reasons.append("missing_track_a_crossmatch_json")
    if satellite_result is None:
        blocking_reasons.append("missing_satellite_match_json")

    gate_result = None
    if crossmatch_result is not None:
        gate_result = track_b_unknown_candidate_gate(
            candidate,
            crossmatch_result=crossmatch_result,
            satellite_result=satellite_result,
        )

    return {
        "schema_version": TRACK_B_PACKET_READINESS_SCHEMA_VERSION,
        "disclaimer": TRACK_B_GATE_DISCLAIMER,
        "candidate_id": candidate.candidate_id,
        "candidate_track": candidate.track.value,
        "zero_hit_non_detection": is_zero_hit_non_detection,
        "provenance_ready": provenance_ready,
        "missing_candidate_feature_ids": missing_candidate_features,
        "track_a_crossmatch": {
            "status": _evidence_status(
                provided=crossmatch_result is not None,
                missing_inputs=missing_crossmatch_inputs,
            ),
            "provided": crossmatch_result is not None,
            "missing_candidate_fields": missing_crossmatch_inputs,
            "required_candidate_fields": ["ra_deg", "dec_deg"],
        },
        "satellite_match": {
            "status": _evidence_status(
                provided=satellite_result is not None,
                missing_inputs=missing_satellite_inputs,
            ),
            "provided": satellite_result is not None,
            "missing_candidate_fields": missing_satellite_inputs,
            "required_candidate_fields": [
                "frequency_hz",
                "observation_time_utc",
                "ra_deg",
                "dec_deg",
                "observer_lat_deg",
                "observer_lon_deg",
                "observer_elevation_m",
            ],
        },
        "gate_evaluated": gate_result is not None,
        "eligible_for_unknown_candidate": (
            gate_result["eligible_for_unknown_candidate"] if gate_result else False
        ),
        "blocking_reason_ids": blocking_reasons,
        "gate_result": gate_result,
    }
