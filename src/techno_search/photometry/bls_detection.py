"""Real Box Least Squares (BLS) periodic-transit search.

Wraps ``lightkurve.LightCurve.to_periodogram(method="bls", **kwargs)``, which
dispatches to ``lightkurve.periodogram.BoxLeastSquaresPeriodogram.from_lightcurve``
and, underneath, ``astropy.timeseries.BoxLeastSquares`` (confirmed by reading
the installed packages' real source with ``inspect.getsource()``, not from
memory or documentation). All statistics below come directly from
``BoxLeastSquares.compute_stats()`` -- none are synthetic or invented.

``compute_stats`` documents (astropy 6.x, verified via ``inspect.getdoc``):
  - depth / depth_odd / depth_even / depth_half / depth_phased: (value, error)
    tuples for the fiducial, odd-period, even-period, half-period, and
    phase-shifted transit models. A large odd/even mismatch relative to the
    fiducial depth is the standard vetting signature of a blended eclipsing
    binary, not evidence of a transiting body.
  - harmonic_amplitude / harmonic_delta_log_likelihood: best-fit sinusoidal
    model amplitude and its log-likelihood advantage over the transit model.
    A positive delta favors a pulsating/rotating star over a real transit.
  - per_transit_log_likelihood: per-transit fit quality. High relative
    dispersion across transits indicates the signal is not well described by
    one strictly periodic, fixed-depth model (e.g. stellar activity crossing
    transits, TTVs, or genuinely irregular dimming events).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from lightkurve import LightCurve


@dataclass(frozen=True)
class BlsTransitResult:
    """Real BLS best-fit transit parameters and vetting statistics."""

    period_days: float
    duration_days: float
    transit_time_value: float
    transit_time_format: str
    max_power: float
    depth: float
    depth_err: float
    depth_odd: float
    depth_odd_err: float
    depth_even: float
    depth_even_err: float
    depth_half: float
    depth_half_err: float
    harmonic_amplitude: float
    harmonic_delta_log_likelihood: float
    transit_count: int
    per_transit_log_likelihood_cv: float | None

    def odd_even_depth_mismatch(self) -> float:
        """Fractional odd/even depth mismatch relative to the fiducial depth.

        0.0 means the odd- and even-numbered transits have identical depth
        (consistent with a single periodic occulter). Large values are the
        standard indicator of a blended eclipsing binary at twice the
        recovered period.
        """
        if self.depth <= 0.0:
            return 0.0
        return abs(self.depth_odd - self.depth_even) / self.depth

    def half_period_depth_ratio(self) -> float:
        """Ratio of the half-period depth to the fiducial depth.

        A ratio near 1.0 means a model at half the recovered period fits
        almost as well as the fiducial model -- a sign the true period may be
        half of what was recovered (common BLS period-aliasing artifact).
        """
        if self.depth <= 0.0:
            return 0.0
        return self.depth_half / self.depth


def run_bls_transit_search(
    lc: LightCurve,
    *,
    duration: Any = None,
    period: Any = None,
    minimum_period: float | None = None,
    maximum_period: float | None = None,
    frequency_factor: float | None = None,
) -> BlsTransitResult:
    """Run a real BLS periodic-transit search on a real light curve.

    ``lc`` should already reflect the caller's chosen detrending state
    (normalized, optionally flattened) -- this function does not silently
    mutate it, since flattening choices materially affect recovered depth.
    """

    kwargs: dict[str, Any] = {}
    if duration is not None:
        kwargs["duration"] = duration
    if period is not None:
        kwargs["period"] = period
    if minimum_period is not None:
        kwargs["minimum_period"] = minimum_period
    if maximum_period is not None:
        kwargs["maximum_period"] = maximum_period
    if frequency_factor is not None:
        kwargs["frequency_factor"] = frequency_factor

    periodogram = lc.to_periodogram(method="bls", **kwargs)

    period_at_max = periodogram.period_at_max_power
    duration_at_max = periodogram.duration_at_max_power
    transit_time_at_max = periodogram.transit_time_at_max_power

    stats = periodogram.compute_stats(
        period=period_at_max,
        duration=duration_at_max,
        transit_time=transit_time_at_max,
    )

    depth, depth_err = _value_pair(stats["depth"])
    depth_odd, depth_odd_err = _value_pair(stats["depth_odd"])
    depth_even, depth_even_err = _value_pair(stats["depth_even"])
    depth_half, depth_half_err = _value_pair(stats["depth_half"])

    per_transit_ll = np.asarray(_quantity_value(stats["per_transit_log_likelihood"]))
    per_transit_cv = _coefficient_of_variation(per_transit_ll)

    return BlsTransitResult(
        period_days=_quantity_value(period_at_max),
        duration_days=_quantity_value(duration_at_max),
        transit_time_value=float(transit_time_at_max.value),
        transit_time_format=str(transit_time_at_max.format),
        max_power=_quantity_value(periodogram.max_power),
        depth=depth,
        depth_err=depth_err,
        depth_odd=depth_odd,
        depth_odd_err=depth_odd_err,
        depth_even=depth_even,
        depth_even_err=depth_even_err,
        depth_half=depth_half,
        depth_half_err=depth_half_err,
        harmonic_amplitude=_quantity_value(stats["harmonic_amplitude"]),
        harmonic_delta_log_likelihood=_quantity_value(stats["harmonic_delta_log_likelihood"]),
        transit_count=int(np.asarray(stats["per_transit_count"]).size),
        per_transit_log_likelihood_cv=per_transit_cv,
    )


def _quantity_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _value_pair(pair: tuple[Any, Any]) -> tuple[float, float]:
    value, error = pair
    return float(_quantity_value(value)), float(_quantity_value(error))


def _coefficient_of_variation(values: np.ndarray) -> float | None:
    if values.size < 2:
        return None
    mean = float(np.mean(values))
    if mean == 0.0:
        return None
    return float(np.std(values) / mean)
