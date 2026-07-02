"""Real transit-shape (flat-bottom vs. V-shape) discrimination.

A grazing eclipsing binary produces a V-shaped (triangular) dip -- depth
rises linearly from zero at first/last contact to a peak at mid-eclipse,
with no flat "floor." A genuine transiting body large enough for full
occultation produces a flat-bottomed (box-shaped) dip -- roughly constant
depth for the full transit duration, with only brief ingress/egress ramps.
Comparing which shape fits the real phase-folded in-transit photometry
better is a standard transit-vetting statistic (the same idea as Kepler's
own Data Validation "transit shape" diagnostics) for telling apart a
grazing/blended eclipsing binary from a real transit -- independent of the
odd/even-depth and harmonic-vs-transit checks in ``bls_detection.py``.

Both models are fit by ordinary least squares directly against the real
observed in-transit depths (``1 - flux``); no external data or invented
thresholds are used.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from techno_search.photometry.bls_detection import BlsTransitResult

_MIN_IN_TRANSIT_POINTS = 3


@dataclass(frozen=True)
class TransitShapeResult:
    """Real flat-bottom-vs-V-shape model comparison for one BLS transit fit."""

    computable: bool
    reason: str | None = None
    in_transit_point_count: int = 0
    box_model_depth: float = 0.0
    box_model_rss: float = 0.0
    triangular_model_depth: float = 0.0
    triangular_model_rss: float = 0.0

    def flat_bottom_score(self) -> float:
        """Model-comparison score in [-1, 1].

        Positive means the flat-bottomed (box) model fits the real
        phase-folded in-transit data better -- consistent with a genuine
        full transit. Negative means the V-shaped (triangular) model fits
        better -- the standard signature of a grazing or blended eclipsing
        binary, not a real transiting body.
        """
        total = self.box_model_rss + self.triangular_model_rss
        if total <= 0.0:
            return 0.0
        return (self.triangular_model_rss - self.box_model_rss) / total

    def grazing_eclipse_score(self) -> float:
        """Clamped [0, 1] evidence score for a grazing/blended-EB V-shape."""
        return min(1.0, max(0.0, -self.flat_bottom_score()))


def classify_transit_shape(
    time: np.ndarray,
    flux: np.ndarray,
    bls_result: BlsTransitResult,
) -> TransitShapeResult:
    """Fit flat-bottom and V-shape models to the real phase-folded transit."""

    time = np.asarray(time, dtype=float)
    flux = np.asarray(flux, dtype=float)
    period = bls_result.period_days
    duration = bls_result.duration_days
    if period <= 0.0 or duration <= 0.0:
        return TransitShapeResult(computable=False, reason="Invalid period or duration.")

    half_duration = duration / 2.0
    transit_time = bls_result.transit_time_value
    # Signed offset from the nearest transit center, in days, range
    # [-period/2, period/2].
    phase_offset = ((time - transit_time + period / 2.0) % period) - period / 2.0

    in_transit = np.abs(phase_offset) <= half_duration
    n_in = int(np.sum(in_transit))
    if n_in < _MIN_IN_TRANSIT_POINTS:
        return TransitShapeResult(
            computable=False,
            reason=f"Only {n_in} in-transit points (need >= {_MIN_IN_TRANSIT_POINTS}).",
            in_transit_point_count=n_in,
        )

    normalized_offset = phase_offset[in_transit] / half_duration
    observed_depth = 1.0 - flux[in_transit]

    box_depth = float(np.mean(observed_depth))
    box_rss = float(np.sum((observed_depth - box_depth) ** 2))

    triangular_weight = 1.0 - np.abs(normalized_offset)
    weight_sq_sum = float(np.sum(triangular_weight**2))
    triangular_depth = (
        float(np.sum(observed_depth * triangular_weight) / weight_sq_sum)
        if weight_sq_sum > 0.0
        else 0.0
    )
    triangular_rss = float(
        np.sum((observed_depth - triangular_depth * triangular_weight) ** 2)
    )

    return TransitShapeResult(
        computable=True,
        in_transit_point_count=n_in,
        box_model_depth=box_depth,
        box_model_rss=box_rss,
        triangular_model_depth=triangular_depth,
        triangular_model_rss=triangular_rss,
    )
