"""Phase 5: deterministic adversarial-review dossier (Step 2 of the review chain).

AGENTS.md's review chain requires a Step 2 "adversarial review agent...
attempting to refute [a candidate] with every known natural or instrumental
explanation" before any candidate can advance toward Step 3 (third-party
expert review). This module implements that step as a deterministic,
reproducible aggregation of every refutation check this project's scoring
pipeline has already computed for a candidate -- it does not invent new
checks and does not call an external LLM.

This design follows the real, published precedent for technosignature
candidate vetting: Sheikh et al. 2021 (Nature Astronomy), "Analysis of the
Breakthrough Listen signal of interest blc1 with a technosignature
verification framework," used a deterministic, itemized checklist (verify
instrumentation, check OFF-scan absence, check catalogued RFI, re-observe
with independent instruments, etc.) to rule out Breakthrough Listen's one
real signal of interest -- not a freeform argumentative pass. A structured
checklist is also the design this project already uses for the Track B
Phase 4 gate (`track_b_gate.py`); this module generalizes the same
philosophy (false positive is the default hypothesis until every known
check fails to explain the candidate) across all tracks, using whatever
per-track refutation evidence ``scoring.py`` already produced.

A candidate that survives this dossier with zero refutations and zero
blocking issues is not confirmed or validated -- it is flagged as requiring
real human expert review (Step 3), per AGENTS.md: "No candidate advances to
step 3 without surviving step 2." The local routing score may order follow-up
work, but neither its value nor its calibration status decides whether a
known explanation was found. An optional freeform LLM "devil's advocate"
critique could layer on top of this deterministic dossier in the future; it
is not required for this step and is out of scope here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

ADVERSARIAL_REVIEW_SCHEMA_VERSION = "adversarial_review_v2"
ADVERSARIAL_REVIEW_DISCLAIMER = (
    "This dossier aggregates deterministic refutation checks already "
    "computed by the scoring pipeline. A candidate reported as "
    "'requires_human_expert_review: true' has not been refuted by any "
    "known-explanation check implemented so far -- it is not a detection, "
    "discovery, confirmed technosignature, or external-submission "
    "authorization. Per AGENTS.md, no candidate advances to third-party "
    "expert review (Step 3) without surviving this deterministic "
    "adversarial dossier (Step 2)."
)
_ADVANCING_PATHWAYS = frozenset({"candidate_review_packet", "external_followup_candidate"})


@dataclass(frozen=True)
class RefutationCheckResult:
    """One deterministic refutation check's outcome for a candidate."""

    source: str
    detail: str
    refuted: bool


@dataclass(frozen=True)
class AdversarialReviewDossier:
    """Deterministic aggregation of every refutation check for one candidate."""

    candidate_id: str
    track: str
    recommended_pathway: str
    routing_false_positive_score: float
    score_calibration: Mapping[str, Any] = field(default_factory=dict)
    refutations: tuple[RefutationCheckResult, ...] = field(default_factory=tuple)
    unrefuted_signals: tuple[str, ...] = field(default_factory=tuple)
    review_concerns: tuple[str, ...] = field(default_factory=tuple)
    ranking_limitations: tuple[str, ...] = field(default_factory=tuple)
    blocking_issues: tuple[str, ...] = field(default_factory=tuple)
    track_b_gate_result: Mapping[str, Any] | None = None

    @property
    def refutation_count(self) -> int:
        return len(self.refutations)

    @property
    def requires_human_expert_review(self) -> bool:
        """True only if nothing refuted this candidate and nothing blocks review.

        This does not mean the candidate is real or confirmed -- it means
        the deterministic checks implemented so far have nothing further to
        say, and per AGENTS.md's review chain, a real human must review
        this dossier before any Step 3 (expert) escalation is considered.
        """
        if self.refutation_count > 0 or self.blocking_issues:
            return False
        if self.track == "radio":
            if self.track_b_gate_result is None:
                return False
            return bool(
                self.track_b_gate_result.get("eligible_for_unknown_candidate", False)
            )
        return self.recommended_pathway in _ADVANCING_PATHWAYS

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": ADVERSARIAL_REVIEW_SCHEMA_VERSION,
            "disclaimer": ADVERSARIAL_REVIEW_DISCLAIMER,
            "candidate_id": self.candidate_id,
            "track": self.track,
            "recommended_pathway": self.recommended_pathway,
            "routing_false_positive_score": self.routing_false_positive_score,
            "score_calibration": dict(self.score_calibration),
            "refutation_count": self.refutation_count,
            "refutations": [
                {"source": r.source, "detail": r.detail, "refuted": r.refuted}
                for r in self.refutations
            ],
            "unrefuted_signal_count": len(self.unrefuted_signals),
            "unrefuted_signals": list(self.unrefuted_signals),
            "review_concern_count": len(self.review_concerns),
            "review_concerns": list(self.review_concerns),
            "ranking_limitation_count": len(self.ranking_limitations),
            "ranking_limitations": list(self.ranking_limitations),
            "blocking_issue_count": len(self.blocking_issues),
            "blocking_issues": list(self.blocking_issues),
            "track_b_gate_result": (
                dict(self.track_b_gate_result) if self.track_b_gate_result else None
            ),
            "requires_human_expert_review": self.requires_human_expert_review,
        }


def build_adversarial_review_dossier(
    scored_report: Mapping[str, Any],
    *,
    track_b_gate_result: Mapping[str, Any] | None = None,
) -> AdversarialReviewDossier:
    """Build a deterministic adversarial-review dossier from a scored candidate report.

    ``scored_report`` is the dict form of a ``ScoredCandidate``
    (``ScoredCandidate.as_dict()`` / a written candidate report JSON file),
    which already carries ``negative_evidence`` (known-explanation matches --
    each one a real refutation), ``blocking_issues`` (data/metadata gaps that
    block full review), and ``positive_evidence`` (checks the candidate
    survived without a natural explanation).
    """

    negative_evidence = [str(item) for item in scored_report.get("negative_evidence", [])]
    positive_evidence = [str(item) for item in scored_report.get("positive_evidence", [])]
    blocking_issues = [str(item) for item in scored_report.get("blocking_issues", [])]
    score_calibration = scored_report.get("score_calibration", {})
    if not isinstance(score_calibration, Mapping):
        score_calibration = {}
    ranking_limitations: list[str] = []
    calibration_limitation = str(score_calibration.get("limitation", "")).strip()
    if calibration_limitation:
        ranking_limitations.append(calibration_limitation)

    # Version 1 dossiers incorrectly treated this ranking limitation as a
    # missing scientific check. Filter it when rebuilding old reports so the
    # known/unknown decision remains independent of score calibration.
    legacy_calibration_blocker = (
        "Candidate-review promotion is blocked because scoring is an "
        "uncalibrated local-routing heuristic."
    )
    if legacy_calibration_blocker in blocking_issues:
        blocking_issues.remove(legacy_calibration_blocker)
        if legacy_calibration_blocker not in ranking_limitations:
            ranking_limitations.append(legacy_calibration_blocker)
    if (
        str(scored_report.get("track", "")) == "radio"
        and str(scored_report.get("recommended_pathway", "")) in _ADVANCING_PATHWAYS
        and track_b_gate_result is None
    ):
        blocking_issues.append(
            "Radio expert-review escalation requires an explicit eligible Track B gate result."
        )

    # Radio known-explanation results are structured in Track B. The legacy
    # scoring evidence mixes actual explanations with missing corroboration
    # (for example, no repeat epoch), so it is review context rather than a
    # refutation. Non-radio tracks do not yet have an equivalent structured
    # known-explanation gate and retain their existing conservative behavior.
    review_concerns: list[str] = []
    if (
        str(scored_report.get("track", "")) == "radio"
        and track_b_gate_result is not None
    ):
        refutations: list[RefutationCheckResult] = []
        review_concerns.extend(negative_evidence)
    else:
        refutations = [
            RefutationCheckResult(
                source="scoring_negative_evidence", detail=item, refuted=True
            )
            for item in negative_evidence
        ]

    if track_b_gate_result is not None:
        for condition in track_b_gate_result.get("conditions", []):
            if condition.get("satisfied") is False:
                refutations.append(
                    RefutationCheckResult(
                        source="track_b_gate",
                        detail=str(condition.get("description", condition.get("condition_id", ""))),
                        refuted=True,
                    )
                )

    scores = scored_report.get("scores", {})
    routing_false_positive_score = float(scores.get("false_positive_probability", 1.0))

    return AdversarialReviewDossier(
        candidate_id=str(scored_report.get("candidate_id", "")),
        track=str(scored_report.get("track", "")),
        recommended_pathway=str(scored_report.get("recommended_pathway", "")),
        routing_false_positive_score=routing_false_positive_score,
        score_calibration=dict(score_calibration),
        refutations=tuple(refutations),
        unrefuted_signals=tuple(positive_evidence),
        review_concerns=tuple(review_concerns),
        ranking_limitations=tuple(ranking_limitations),
        blocking_issues=tuple(blocking_issues),
        track_b_gate_result=track_b_gate_result,
    )
