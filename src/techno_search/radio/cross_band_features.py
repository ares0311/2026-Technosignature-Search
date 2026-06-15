"""Cross-band feature normalization for GBT turboSETI hit tables.

Extracts telescope-agnostic, frequency-normalized features so the scoring
model generalizes across GBT bands (L/S/C/X) and future MeerKAT or
Parkes observations.

Scientific guardrail: these features are local triage aids only.  No
feature value constitutes a technosignature detection or authorizes
external submission.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CROSS_BAND_FEATURES_VERSION = "cross_band_features_v1"
CROSS_BAND_FEATURES_DISCLAIMER = (
    "Cross-band feature normalization outputs are local triage aids only. "
    "No normalized feature value constitutes a detection claim or authorizes "
    "external submission."
)

# Earth's sidereal rotation produces a maximum drift of ~0.44 Hz/s/GHz
# (geocentric acceleration on a grounded antenna at the equator).
# Signals drifting faster are inconsistent with a purely terrestrial emitter
# at rest with respect to Earth; they may be satellites, aircraft, or
# genuinely non-terrestrial — all requiring follow-up scrutiny.
EARTH_ACCELERATION_DRIFT_HZ_S_PER_GHZ = 0.44

# SNR window half-width in Hz for local relative SNR computation
RELATIVE_SNR_WINDOW_HZ = 10_000_000.0  # ±10 MHz

CROSS_BAND_FEATURE_NAMES = [
    "normalized_drift_hz_s_per_ghz",
    "is_earth_drift_consistent",
    "relative_snr",
    "on_off_consistency_score",
]


# ---------------------------------------------------------------------------
# Individual feature functions
# ---------------------------------------------------------------------------

def normalize_drift_rate(
    drift_hz_per_s: float,
    center_freq_hz: float,
) -> float:
    """Return drift rate normalized by centre frequency in Hz/s/GHz.

    Dividing by (centre_freq / 1 GHz) makes the value telescope- and
    band-independent.  A Doppler drift from constant line-of-sight
    acceleration scales linearly with observing frequency, so this ratio is
    the physically meaningful quantity.

    Returns 0.0 if centre_freq_hz is zero or negative to avoid division by
    zero.
    """
    if center_freq_hz <= 0.0:
        return 0.0
    freq_ghz = center_freq_hz / 1e9
    return drift_hz_per_s / freq_ghz


def is_earth_drift_consistent(
    normalized_drift: float,
    *,
    threshold: float = EARTH_ACCELERATION_DRIFT_HZ_S_PER_GHZ,
) -> bool:
    """Return True if |normalized_drift| ≤ threshold.

    Signals within the Earth-acceleration drift budget are consistent with
    a fixed terrestrial transmitter.  This is a conservative flag — True
    means consistent with RFI, not proof of RFI.
    """
    return abs(normalized_drift) <= threshold


def relative_snr(
    hit_snr: float,
    all_snrs_in_window: list[float],
) -> float:
    """Return SNR of a hit relative to the local window median.

    Using the local median suppresses band-to-band sensitivity variations.
    A hit at 10× the local median is scored 10.0 regardless of absolute SNR.

    Returns hit_snr if window is empty or median is zero.
    """
    if not all_snrs_in_window:
        return hit_snr
    sorted_snrs = sorted(all_snrs_in_window)
    n = len(sorted_snrs)
    mid = n // 2
    median = (sorted_snrs[mid - 1] + sorted_snrs[mid]) / 2.0 if n % 2 == 0 else sorted_snrs[mid]
    if median <= 0.0:
        return hit_snr
    return hit_snr / median


def compute_relative_snr_from_hits(
    hit_freq_hz: float,
    hit_snr: float,
    all_hits: list[dict[str, Any]],
    *,
    window_hz: float = RELATIVE_SNR_WINDOW_HZ,
) -> float:
    """Compute relative SNR for a hit against nearby hits in the same dataset.

    Looks at hits within ±window_hz of hit_freq_hz and computes the median
    SNR of that neighbourhood, then returns hit_snr / median.

    Args:
        hit_freq_hz: Centre frequency of the target hit in Hz.
        hit_snr: SNR of the target hit.
        all_hits: List of dicts each containing 'frequency_hz' and 'snr'.
        window_hz: Half-width of the frequency window in Hz.

    Returns:
        Relative SNR (float ≥ 0).
    """
    window_snrs: list[float] = []
    for h in all_hits:
        try:
            freq = float(h["frequency_hz"])
            snr = float(h["snr"])
        except (KeyError, TypeError, ValueError):
            continue
        if abs(freq - hit_freq_hz) <= window_hz:
            window_snrs.append(snr)
    return relative_snr(hit_snr, window_snrs)


def on_off_consistency_score(
    target_freq_hz: float,
    all_hits: list[dict[str, Any]],
    *,
    freq_tol_hz: float = 5.0,
) -> float:
    """Return fraction of OFF scans that contain the signal at target_freq_hz.

    A signal present in OFF (non-target) scans is likely RFI.  This score
    is 0.0 if the signal appears in no OFF scans and 1.0 if it appears in
    all OFF scans.

    Args:
        target_freq_hz: Frequency to search for in Hz.
        all_hits: List of dicts with 'frequency_hz' and 'scan_role'.
        freq_tol_hz: Frequency matching tolerance in Hz.

    Returns:
        Float in [0, 1].
    """
    off_scans_with_signal: set[str] = set()
    all_off_scan_ids: set[str] = set()

    for h in all_hits:
        try:
            freq = float(h["frequency_hz"])
            role = str(h.get("scan_role", "")).lower()
            scan_id = str(h.get("target_id", h.get("scan_id", "unknown")))
        except (TypeError, ValueError):
            continue
        if role in ("off", "b", "off_target"):
            all_off_scan_ids.add(scan_id)
            if abs(freq - target_freq_hz) <= freq_tol_hz:
                off_scans_with_signal.add(scan_id)

    if not all_off_scan_ids:
        return 0.0
    return len(off_scans_with_signal) / len(all_off_scan_ids)


# ---------------------------------------------------------------------------
# Batch feature extraction
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CrossBandFeatures:
    """Telescope/band-agnostic features for a single radio hit."""

    normalized_drift_hz_s_per_ghz: float
    is_earth_drift_consistent: bool
    relative_snr: float
    on_off_consistency_score: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "normalized_drift_hz_s_per_ghz": self.normalized_drift_hz_s_per_ghz,
            "is_earth_drift_consistent": self.is_earth_drift_consistent,
            "relative_snr": self.relative_snr,
            "on_off_consistency_score": self.on_off_consistency_score,
        }


def extract_cross_band_features(
    hit: dict[str, Any],
    all_hits: list[dict[str, Any]],
    *,
    drift_threshold: float = EARTH_ACCELERATION_DRIFT_HZ_S_PER_GHZ,
    freq_tol_hz: float = 5.0,
    snr_window_hz: float = RELATIVE_SNR_WINDOW_HZ,
) -> CrossBandFeatures:
    """Extract all cross-band features for a single hit.

    Args:
        hit: Dict with 'frequency_hz', 'drift_rate_hz_per_sec', 'snr'.
        all_hits: Full hit table including the target hit (for context).
        drift_threshold: Earth-drift threshold in Hz/s/GHz.
        freq_tol_hz: Frequency tolerance for ON/OFF matching in Hz.
        snr_window_hz: Half-width of SNR normalization window in Hz.

    Returns:
        CrossBandFeatures dataclass.
    """
    freq_hz = float(hit.get("frequency_hz", 0.0))
    drift = float(hit.get("drift_rate_hz_per_sec", 0.0))
    snr = float(hit.get("snr", 0.0))

    norm_drift = normalize_drift_rate(drift, freq_hz)
    earth_consistent = is_earth_drift_consistent(norm_drift, threshold=drift_threshold)
    rel_snr = compute_relative_snr_from_hits(
        freq_hz, snr, all_hits, window_hz=snr_window_hz
    )
    on_off = on_off_consistency_score(freq_hz, all_hits, freq_tol_hz=freq_tol_hz)

    return CrossBandFeatures(
        normalized_drift_hz_s_per_ghz=norm_drift,
        is_earth_drift_consistent=earth_consistent,
        relative_snr=rel_snr,
        on_off_consistency_score=on_off,
    )


def cross_band_features_summary() -> dict[str, Any]:
    """Return a provenance summary for cross-band feature normalization."""
    return {
        "schema_version": CROSS_BAND_FEATURES_VERSION,
        "disclaimer": CROSS_BAND_FEATURES_DISCLAIMER,
        "feature_names": CROSS_BAND_FEATURE_NAMES,
        "earth_acceleration_drift_hz_s_per_ghz": EARTH_ACCELERATION_DRIFT_HZ_S_PER_GHZ,
        "relative_snr_window_hz": RELATIVE_SNR_WINDOW_HZ,
        "feature_count": len(CROSS_BAND_FEATURE_NAMES),
    }
