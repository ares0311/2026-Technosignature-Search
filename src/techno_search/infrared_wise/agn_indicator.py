"""Real WISE W1-W2 color AGN indicator (Phase 3: natural contaminant rejection).

Stern et al. (2012, ApJ 753, 30) established W1-W2 >= 0.8 (Vega system) as a
simple, highly reliable mid-infrared AGN selection criterion from a 2 deg^2
COSMOS-field study against Spitzer-confirmed AGN: 95% reliability and 78%
completeness for W2 < 15.05 at SNR > 10. Assef et al. (2013) later showed a
looser W1-W2 > 0.5 cut is ~90% complete relative to Spitzer/IRAC-selected AGN
candidates, at the cost of more contamination.

Both thresholds cross-verified 2026-07-02 via live web search against
multiple independent sources describing the Stern et al. (2012) and Assef et
al. (2013) papers, not from memory. This module reports a real W1-W2 color
directly against these two literature thresholds -- it does not invent a new
cutoff.

A WISE-color-only check cannot distinguish a genuine debris disk or
young-stellar-object dust excess from an otherwise-unexplained W3/W4 excess;
that distinction needs stellar age or resolved imaging, which is out of
scope here and not attempted.
"""

from __future__ import annotations

from dataclasses import dataclass

STERN_2012_RELIABLE_AGN_THRESHOLD = 0.8
ASSEF_2013_COMPLETE_AGN_THRESHOLD = 0.5
STERN_2012_RELIABILITY_MAG_LIMIT_W2 = 15.05


@dataclass(frozen=True)
class WiseAgnIndicatorResult:
    """Real WISE color-based AGN indicator result."""

    computable: bool
    reason: str | None = None
    w1_minus_w2: float | None = None
    meets_stern_2012_reliable_threshold: bool | None = None
    meets_assef_2013_complete_threshold: bool | None = None
    within_stern_2012_magnitude_limit: bool | None = None

    def agn_indicator_score(self) -> float:
        """Real, non-invented [0, 1] score from the two literature thresholds.

        0.0: W1-W2 below both thresholds (color gives no AGN indication).
        0.5: meets the looser Assef et al. (2013) completeness cut only.
        1.0: meets the Stern et al. (2012) high-reliability cut.
        """
        if not self.computable:
            return 0.0
        if self.meets_stern_2012_reliable_threshold:
            return 1.0
        if self.meets_assef_2013_complete_threshold:
            return 0.5
        return 0.0


def wise_agn_indicator(
    w1_mag: float | None,
    w2_mag: float | None,
    *,
    w2_mag_for_reliability_limit: float | None = None,
) -> WiseAgnIndicatorResult:
    """Check a real WISE W1-W2 color against the Stern (2012)/Assef (2013) cuts."""

    if w1_mag is None or w2_mag is None:
        return WiseAgnIndicatorResult(
            computable=False,
            reason="W1 and W2 magnitudes are both required.",
        )

    w1_minus_w2 = w1_mag - w2_mag
    meets_stern = w1_minus_w2 >= STERN_2012_RELIABLE_AGN_THRESHOLD
    meets_assef = w1_minus_w2 >= ASSEF_2013_COMPLETE_AGN_THRESHOLD

    within_limit = None
    if w2_mag_for_reliability_limit is not None:
        within_limit = w2_mag_for_reliability_limit < STERN_2012_RELIABILITY_MAG_LIMIT_W2

    return WiseAgnIndicatorResult(
        computable=True,
        w1_minus_w2=w1_minus_w2,
        meets_stern_2012_reliable_threshold=meets_stern,
        meets_assef_2013_complete_threshold=meets_assef,
        within_stern_2012_magnitude_limit=within_limit,
    )
