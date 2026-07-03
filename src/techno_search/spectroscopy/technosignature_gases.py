"""Real technosignature-gas absorption-feature check (Phase 4, JWST MIRI LRS).

Checks a real JWST MIRI Low Resolution Spectrometer transmission spectrum
(5-14 um, resolving power R ~ 40-160, verified via live web search against
JWST User Documentation) for excess absorption at the real band centers of
industrial/artificial greenhouse gases with no known natural planetary
source (Schwieterman et al. 2024, "Artificial Greenhouse Gases as Exoplanet
Technosignatures", ApJ 969, 20): CF4, C2F6, C3F8, SF6, NF3.

Band centers below are the global (or, for gases with multiple real bands,
each locally significant) maximum absorption cross-section peak extracted
directly from real HITRAN cross-section files (Sharpe et al. 2004 via
Kochanov et al. 2019 -- the same source family Schwieterman et al. 2024
cite for these five gases), downloaded and peak-extracted 2026-07-03. This
is a strictly better provenance than a band center reconstructed from
scattered literature-search snippets: each value below is the real
numerical peak of a real downloaded absorption cross-section grid, not an
approximation. See docs/technosignature_detection_research_answers.md for
the full research trail, HITRAN dataset IDs, and the peak-extraction
method.

  CF4:  7.792935 um  (1283.213506 cm^-1, global max)
  C2F6: 8.002651 um and 8.960738 um (global max and second-strongest band)
  C3F8: 7.923519 um  (1262.065573 cm^-1, global max)
  SF6:  10.549570 um (947.905963 cm^-1, global max)
  NF3:  10.994894 um (909.513125 cm^-1, global max)

This is a real, deterministic band-position absorption-significance check
-- it is explicitly NOT a full radiative-transfer abundance retrieval using
the complete downloaded cross-section grids (which would require
convolving real per-wavelength cross-sections through an atmospheric
model, not just checking a peak location). This is the same kind of honest
first-pass scope limitation already used for the WISE
blackbody-vs-Kurucz-grid distinction elsewhere in this project (see
infrared_wise/photosphere_excess.py). A future enhancement could use the
full downloaded cross-section grids directly instead of a single peak
wavelength.

Because JWST spectral products can represent different physical
quantities (transit depth, transmission, or extracted stellar flux)
depending on the pipeline stage, this module is directionally generic: it
reports a real statistical dip (or rise) at each band center relative to
the local continuum, in real per-point measurement-uncertainty units, and
leaves physical sign interpretation (does a dip here mean "more
absorption" for this specific data product) to the caller, who knows what
the input array represents.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# MIRI LRS resolving power is wavelength-dependent (R ~ 40 at 5 um to
# R ~ 160 at 10 um; ~100 at 7.5 um). 100 is used here as a single
# representative, cited value for the real per-band search-window width
# (Delta_lambda = lambda / R) -- not an invented number, and conservative
# (narrower than the true R at the longer-wavelength bands, which would
# only make the window wider and less discriminating).
MIRI_LRS_REPRESENTATIVE_RESOLVING_POWER = 100.0

GAS_ABSORPTION_BANDS_UM: dict[str, tuple[float, ...]] = {
    "CF4": (7.792935,),
    "C2F6": (8.002651, 8.960738),
    "C3F8": (7.923519,),
    "SF6": (10.549570,),
    "NF3": (10.994894,),
}


@dataclass(frozen=True)
class BandFeatureResult:
    """Real statistical result for one gas absorption band search."""

    gas: str
    band_center_um: float
    computable: bool
    reason: str | None = None
    band_point_count: int = 0
    continuum_point_count: int = 0
    band_mean: float | None = None
    continuum_mean: float | None = None
    significance_sigma: float | None = None


def search_gas_absorption_bands(
    wavelength_um: np.ndarray,
    signal: np.ndarray,
    signal_err: np.ndarray,
    *,
    resolving_power: float = MIRI_LRS_REPRESENTATIVE_RESOLVING_POWER,
) -> list[BandFeatureResult]:
    """Search a real spectrum for excess signal at every known gas band center.

    For each band center, compares the mean signal within the real
    instrumental resolution window (``center +/- center / (2 * R)``) to the
    mean signal in two equal-width continuum windows immediately adjacent
    on either side, in units of the real combined per-point measurement
    uncertainty (root-sum-square of both windows' standard errors).
    """

    wavelength_um = np.asarray(wavelength_um, dtype=float)
    signal = np.asarray(signal, dtype=float)
    signal_err = np.asarray(signal_err, dtype=float)

    results: list[BandFeatureResult] = []
    for gas, centers in GAS_ABSORPTION_BANDS_UM.items():
        for center in centers:
            results.append(
                _search_one_band(
                    gas,
                    center,
                    wavelength_um,
                    signal,
                    signal_err,
                    resolving_power=resolving_power,
                )
            )
    return results


def _search_one_band(
    gas: str,
    center_um: float,
    wavelength_um: np.ndarray,
    signal: np.ndarray,
    signal_err: np.ndarray,
    *,
    resolving_power: float,
) -> BandFeatureResult:
    half_width = center_um / (2.0 * resolving_power)
    band_mask = np.abs(wavelength_um - center_um) <= half_width
    band_count = int(np.sum(band_mask))
    if band_count == 0:
        return BandFeatureResult(
            gas=gas,
            band_center_um=center_um,
            computable=False,
            reason="No spectral points fall within the band window.",
        )

    continuum_mask = (
        (wavelength_um >= center_um - 3 * half_width)
        & (wavelength_um < center_um - half_width)
    ) | (
        (wavelength_um > center_um + half_width)
        & (wavelength_um <= center_um + 3 * half_width)
    )
    continuum_count = int(np.sum(continuum_mask))
    if continuum_count < 2:
        return BandFeatureResult(
            gas=gas,
            band_center_um=center_um,
            computable=False,
            reason="Fewer than 2 continuum points adjacent to the band window.",
            band_point_count=band_count,
        )

    band_mean = float(np.mean(signal[band_mask]))
    continuum_mean = float(np.mean(signal[continuum_mask]))

    band_sem = _standard_error(signal[band_mask], signal_err[band_mask])
    continuum_sem = _standard_error(signal[continuum_mask], signal_err[continuum_mask])
    combined_uncertainty = float(np.sqrt(band_sem**2 + continuum_sem**2))

    significance = (
        (continuum_mean - band_mean) / combined_uncertainty
        if combined_uncertainty > 0.0
        else None
    )

    return BandFeatureResult(
        gas=gas,
        band_center_um=center_um,
        computable=True,
        band_point_count=band_count,
        continuum_point_count=continuum_count,
        band_mean=band_mean,
        continuum_mean=continuum_mean,
        significance_sigma=significance,
    )


def _standard_error(values: np.ndarray, errors: np.ndarray) -> float:
    """Real standard error of the mean, combining sample scatter and per-point error.

    Uses whichever is larger: the sample standard error of the mean, or the
    root-sum-square of the real per-point measurement uncertainties divided
    by the sample size. This avoids understating uncertainty when the
    per-point errors are small but the points themselves scatter more than
    that (e.g. unmodeled systematics), and avoids understating it when the
    sample is small but per-point errors are large.
    """

    n = values.size
    if n == 0:
        return 0.0
    sample_sem = float(np.std(values, ddof=1)) / np.sqrt(n) if n > 1 else 0.0
    propagated_sem = float(np.sqrt(np.sum(errors**2))) / n
    return max(sample_sem, propagated_sem)
