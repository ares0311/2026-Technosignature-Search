"""Interpretable rule-based baseline classifier for Milestone 10 scaffolding.

This module implements a decision-tree-style baseline that reproduces the
current scoring-model pathway logic using explicitly named boolean rules.
It must precede any learned model and serves as the audit reference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

BASELINE_MODEL_VERSION = "baseline_v0"

BASELINE_MODEL_DISCLAIMER = (
    "This rule-based baseline is an interpretable scaffold for Milestone 10. "
    "It reproduces the current scoring pathway logic using explicit named rules. "
    "Baseline outputs are not detections, discoveries, confirmations, or external "
    "validation. They are local development diagnostics only."
)


@dataclass
class BaselineResult:
    predicted_pathway: str
    rule_trace: list[str]
    rule_coverage: float
    model_version: str
    disclaimer: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "predicted_pathway": self.predicted_pathway,
            "rule_trace": list(self.rule_trace),
            "rule_coverage": self.rule_coverage,
            "model_version": self.model_version,
            "disclaimer": self.disclaimer,
        }


_KNOWN_OBJECT_RULES = (
    "posterior.known_object >= 0.80",
)

_FALSE_POSITIVE_RULES = (
    "scores.false_positive_probability >= 0.80",
)

_CANDIDATE_REVIEW_RULES = (
    "posterior.technosignature_interest >= 0.60",
    "scores.false_positive_probability <= 0.40",
    "scores.signal_reality_confidence >= 0.70",
    "scores.review_readiness >= 0.70",
)

_HUMAN_REVIEW_RULES = (
    "scores.signal_reality_confidence >= 0.40",
    "scores.false_positive_probability < 0.80",
)

_ALL_RULES: tuple[str, ...] = (
    *_KNOWN_OBJECT_RULES,
    *_FALSE_POSITIVE_RULES,
    *_CANDIDATE_REVIEW_RULES,
    *_HUMAN_REVIEW_RULES,
)

_TOTAL_RULE_COUNT = len(_ALL_RULES)


class RuleBasedBaselineClassifier:
    """Explicit decision-tree-style classifier mirroring the scoring model pathways."""

    model_version: str = BASELINE_MODEL_VERSION

    def predict(self, candidate_packet: dict[str, Any]) -> BaselineResult:
        posterior = candidate_packet.get("posterior", {})
        scores = candidate_packet.get("scores", {})

        trace: list[str] = []
        evaluated: list[str] = []

        def _check(rule_name: str, value: bool) -> bool:
            evaluated.append(rule_name)
            if value:
                trace.append(rule_name)
            return value

        known_object = float(posterior.get("known_object", 0.0))
        if _check("posterior.known_object >= 0.80", known_object >= 0.80):
            return self._result("known_object_annotation", trace, evaluated)

        fp_prob = float(scores.get("false_positive_probability", 1.0))
        if _check("scores.false_positive_probability >= 0.80", fp_prob >= 0.80):
            return self._result("do_not_submit_false_positive", trace, evaluated)

        ts_interest = float(posterior.get("technosignature_interest", 0.0))
        signal_conf = float(scores.get("signal_reality_confidence", 0.0))
        review_ready = float(scores.get("review_readiness", 0.0))

        candidate_rules = [
            _check("posterior.technosignature_interest >= 0.60", ts_interest >= 0.60),
            _check("scores.false_positive_probability <= 0.40", fp_prob <= 0.40),
            _check("scores.signal_reality_confidence >= 0.70", signal_conf >= 0.70),
            _check("scores.review_readiness >= 0.70", review_ready >= 0.70),
        ]
        if all(candidate_rules):
            return self._result("candidate_review_packet", trace, evaluated)

        human_rules = [
            _check("scores.signal_reality_confidence >= 0.40", signal_conf >= 0.40),
            _check("scores.false_positive_probability < 0.80", fp_prob < 0.80),
        ]
        if all(human_rules):
            return self._result("human_review_queue", trace, evaluated)

        return self._result("github_reproducibility_only", trace, evaluated)

    def _result(
        self,
        pathway: str,
        trace: list[str],
        evaluated: list[str],
    ) -> BaselineResult:
        return BaselineResult(
            predicted_pathway=pathway,
            rule_trace=trace,
            rule_coverage=len(evaluated) / _TOTAL_RULE_COUNT if _TOTAL_RULE_COUNT > 0 else 0.0,
            model_version=self.model_version,
            disclaimer=BASELINE_MODEL_DISCLAIMER,
        )


def predict_pathway(candidate_packet: dict[str, Any]) -> BaselineResult:
    """Convenience wrapper for single-packet baseline prediction."""
    return RuleBasedBaselineClassifier().predict(candidate_packet)
