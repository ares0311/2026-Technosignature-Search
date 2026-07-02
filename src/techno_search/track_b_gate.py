"""Track B: the unknown_candidate gate (Phase 4 of the dataset brief).

Per docs/technosignature_datasets_agent_brief.md Phase 4, `unknown_candidate`
may only be emitted when nine conditions are all true:

    1. not confidently pulsar
    2. not confidently FRB
    3. not cross-matched to known blazar/AGN/gamma source
    4. not known satellite/transmitter at observation time and beam direction
    5. not known RFI region
    6. not instrument/band-edge/notch artifact
    7. passes ON/OFF cadence checks
    8. has high anomaly/OOD score
    9. has preserved provenance and reproducible extraction script

This is a deliberately separate, additive gate function -- it does NOT add a
value to the shared `Pathway` enum and does NOT change `score_candidate()`.
Real production radio transient pipelines (e.g. CHIME/FRB's L1b -> L2/L3 ->
L4 staged classification) keep this kind of terminal triage decision as a
distinct downstream stage rather than folding it into the primary scorer;
extending a shared enum that existing tested code depends on is also a
well-documented breaking-change risk. This module follows the same additive
pattern already used by track_a_crossmatch.py and track_a_satellites.py.

Condition 8 ("has high anomaly/OOD score") requires a calibrated threshold
that has not been established by any calibration study in this repository.
Rather than inventing one, this module reports the raw anomaly score as
evidence and marks that condition `satisfied=None` (cannot be evaluated)
until real calibration exists. A None condition blocks the overall gate by
construction, so `unknown_candidate` is never emitted on an unsupported
threshold guess -- the gate can only ever be as permissive as its most
conservative unresolved condition.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from techno_search.schemas import Candidate

TRACK_B_GATE_SCHEMA_VERSION = "track_b_unknown_candidate_gate_v1"

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


def _anomaly_condition(candidate: Candidate) -> GateCondition:
    score = candidate.features.get("semisupervised_anomaly_score")
    return GateCondition(
        condition_id="has_high_anomaly_score",
        description="Event has a high anomaly/out-of-distribution score",
        satisfied=None,  # no calibrated "high" threshold exists yet -- see module docstring
        evidence={
            "semisupervised_anomaly_score": score,
            "note": (
                "No calibration study has established a threshold for 'high' on this "
                "score. Reported as evidence only; this condition cannot be resolved "
                "true/false until a real calibration pass exists."
            ),
        },
    )


def _provenance_condition(candidate: Candidate) -> GateCondition:
    has_source_ids = len(candidate.source_ids) > 0
    has_provenance = len(candidate.provenance) > 0
    satisfied = has_source_ids and has_provenance
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
    """Evaluate the Phase 4 nine-condition Track B gate for one radio candidate.

    Callers must first run track_a_crossmatch.cross_match_known_sources()
    and (optionally) track_a_satellites.match_satellite_transmitter() and
    pass their results in -- this function only combines already-computed
    evidence, it does not perform any network or catalog lookups itself.

    Returns eligible_for_unknown_candidate=True only when every condition is
    explicitly satisfied=True. Any condition that is unresolved (satisfied
    is None, e.g. a missing catalog or the uncalibrated anomaly threshold)
    blocks eligibility -- this function never guesses.
    """

    conditions: list[GateCondition] = []
    conditions.extend(_catalog_conditions(crossmatch_result))
    conditions.append(_satellite_condition(satellite_result))
    conditions.append(_rfi_condition(candidate))
    conditions.append(_instrument_artifact_condition(candidate))
    conditions.append(_cadence_condition(candidate))
    conditions.append(_anomaly_condition(candidate))
    conditions.append(_provenance_condition(candidate))

    satisfied_count = sum(1 for c in conditions if c.satisfied is True)
    failed_count = sum(1 for c in conditions if c.satisfied is False)
    unresolved_count = sum(1 for c in conditions if c.satisfied is None)
    eligible = satisfied_count == len(conditions)

    return {
        "schema_version": TRACK_B_GATE_SCHEMA_VERSION,
        "disclaimer": TRACK_B_GATE_DISCLAIMER,
        "candidate_id": candidate.candidate_id,
        "condition_count": len(conditions),
        "satisfied_count": satisfied_count,
        "failed_count": failed_count,
        "unresolved_count": unresolved_count,
        "eligible_for_unknown_candidate": eligible,
        "conditions": [c.as_dict() for c in conditions],
    }
