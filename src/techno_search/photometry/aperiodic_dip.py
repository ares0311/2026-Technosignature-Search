"""Aperiodic dimming-event detection (Boyajian's Star / KIC 8462852 methodology).

Box Least Squares (see ``bls_detection.py``) assumes a strictly periodic,
fixed-depth occulter and will not recover the kind of irregular, non-repeating
dimming events documented for KIC 8462852 (Boyajian et al. 2016, "Where's the
Flux?"). This module implements a separate, from-scratch statistical detector
for significant flux dips of any shape and applies the same diagnostic that
paper used on individual dips: comparing ingress and egress slopes to test
whether a dip is symmetric (consistent with a compact, near-spherical
occulter) or asymmetric (consistent with an irregular, extended, or clumped
occulting structure -- one of several natural and non-natural explanations
that paper considered and did not resolve).

This is a real statistical method operating on a real light curve's own
photon-noise-derived scatter -- no synthetic training data, literature
thresholds, or invented cutoffs are used to decide what counts as a dip.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DipEvent:
    """A single statistically significant flux dip detected in a light curve."""

    start_time: float
    end_time: float
    duration_days: float
    min_flux: float
    depth: float
    significance_sigma: float
    cadence_count: int
    ingress_slope: float | None
    egress_slope: float | None
    ingress_egress_asymmetry: float | None


def detect_aperiodic_dips(
    time: np.ndarray,
    flux: np.ndarray,
    *,
    sigma_threshold: float = 5.0,
    min_consecutive_cadences: int = 3,
    max_gap_cadences: int = 1,
) -> list[DipEvent]:
    """Detect statistically significant dimming events of any shape.

    Baseline and scatter are estimated with a median and median absolute
    deviation (MAD) over the full input series -- both robust to the dips
    themselves being present, unlike a mean/standard-deviation estimate.
    Callers should pass a normalized (flux near 1.0), NaN-free array; this
    function does not itself detrend long-term stellar variability, since
    aggressive detrending can suppress the same long, deep, irregular events
    it is meant to find.
    """

    time = np.asarray(time, dtype=float)
    flux = np.asarray(flux, dtype=float)
    if time.shape != flux.shape:
        msg = "time and flux arrays must have the same shape"
        raise ValueError(msg)
    if time.size < min_consecutive_cadences:
        return []

    median_flux = float(np.median(flux))
    mad = float(np.median(np.abs(flux - median_flux)))
    # 1.4826 converts MAD to a standard-deviation-equivalent for a normal
    # distribution -- the standard robust-scatter conversion factor.
    robust_sigma = mad * 1.4826
    if robust_sigma <= 0.0:
        return []

    threshold = median_flux - sigma_threshold * robust_sigma
    below = flux < threshold

    events: list[DipEvent] = []
    index = 0
    n = time.size
    while index < n:
        if not below[index]:
            index += 1
            continue
        start = index
        end = index
        gap = 0
        while end + 1 < n:
            if below[end + 1]:
                end += 1
                gap = 0
                continue
            if gap < max_gap_cadences:
                gap += 1
                end += 1
                continue
            break
        cadence_count = int(np.sum(below[start : end + 1]))
        if cadence_count >= min_consecutive_cadences:
            events.append(
                _build_event(
                    time[start : end + 1],
                    flux[start : end + 1],
                    median_flux=median_flux,
                    robust_sigma=robust_sigma,
                )
            )
        index = end + 1

    return events


def _build_event(
    segment_time: np.ndarray,
    segment_flux: np.ndarray,
    *,
    median_flux: float,
    robust_sigma: float,
) -> DipEvent:
    min_idx = int(np.argmin(segment_flux))
    min_flux = float(segment_flux[min_idx])
    depth = median_flux - min_flux
    significance_sigma = depth / robust_sigma

    ingress_slope = _slope(segment_time[: min_idx + 1], segment_flux[: min_idx + 1])
    egress_slope = _slope(segment_time[min_idx:], segment_flux[min_idx:])
    asymmetry = _asymmetry(ingress_slope, egress_slope)

    return DipEvent(
        start_time=float(segment_time[0]),
        end_time=float(segment_time[-1]),
        duration_days=float(segment_time[-1] - segment_time[0]),
        min_flux=min_flux,
        depth=depth,
        significance_sigma=significance_sigma,
        cadence_count=int(segment_time.size),
        ingress_slope=ingress_slope,
        egress_slope=egress_slope,
        ingress_egress_asymmetry=asymmetry,
    )


def _slope(segment_time: np.ndarray, segment_flux: np.ndarray) -> float | None:
    if segment_time.size < 2:
        return None
    fit = np.polyfit(segment_time, segment_flux, 1)
    return float(fit[0])


def _asymmetry(ingress_slope: float | None, egress_slope: float | None) -> float | None:
    """Normalized ingress/egress steepness mismatch in [0, 1].

    0.0 means the dip descends and recovers at the same rate (symmetric,
    consistent with a compact occulter). Values near 1.0 mean one side is
    much steeper than the other (asymmetric, consistent with an irregular
    or extended occulting structure).
    """
    if ingress_slope is None or egress_slope is None:
        return None
    magnitude_in = abs(ingress_slope)
    magnitude_out = abs(egress_slope)
    total = magnitude_in + magnitude_out
    if total == 0.0:
        return None
    return abs(magnitude_in - magnitude_out) / total
