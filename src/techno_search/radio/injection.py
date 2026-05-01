"""Synthetic radio injection helpers."""

from __future__ import annotations

from dataclasses import dataclass

from techno_search.schemas import FeatureValue


@dataclass(frozen=True)
class SyntheticRadioInjection:
    """A small synthetic narrowband radio hit used for v0 tests."""

    frequency_hz: float
    drift_rate_hz_per_sec: float
    snr: float
    bandwidth_hz: float = 1.5
    target_id: str = "synthetic-target"
    scan_role: str = "on"

    def as_hit_row(self, *, recovered_score: float = 1.0) -> dict[str, FeatureValue]:
        return {
            "frequency_hz": self.frequency_hz,
            "drift_rate_hz_per_sec": self.drift_rate_hz_per_sec,
            "snr": self.snr,
            "bandwidth_hz": self.bandwidth_hz,
            "scan_role": self.scan_role,
            "target_id": self.target_id,
            "injection_recovery_score": _clamp(recovered_score),
        }


def injection_recovery_score(
    injection: SyntheticRadioInjection,
    *,
    recovered_frequency_hz: float | None,
    recovered_drift_rate_hz_per_sec: float | None,
    frequency_tolerance_hz: float = 5.0,
    drift_tolerance_hz_per_sec: float = 0.5,
) -> float:
    """Score whether a synthetic injection was recovered near the expected values."""

    if recovered_frequency_hz is None or recovered_drift_rate_hz_per_sec is None:
        return 0.0

    frequency_error = abs(recovered_frequency_hz - injection.frequency_hz)
    drift_error = abs(recovered_drift_rate_hz_per_sec - injection.drift_rate_hz_per_sec)
    frequency_score = 1.0 - (frequency_error / frequency_tolerance_hz)
    drift_score = 1.0 - (drift_error / drift_tolerance_hz_per_sec)
    return _clamp((0.65 * frequency_score) + (0.35 * drift_score))


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))
