"""Synthetic radio hit-table prototype.

This module deliberately handles only small, in-memory synthetic hit tables. It
extracts conservative v0 features for the shared scorer without claiming signal
confirmation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from techno_search.config import TrackConfig, load_track_config
from techno_search.schemas import Candidate, FeatureValue, Track


@dataclass(frozen=True)
class RfiBand:
    """Known or suspected local interference frequency interval."""

    name: str
    low_hz: float
    high_hz: float

    def contains(self, frequency_hz: float) -> bool:
        return self.low_hz <= frequency_hz <= self.high_hz


@dataclass(frozen=True)
class RadioHit:
    """Normalized synthetic radio hit row."""

    frequency_hz: float
    drift_rate_hz_per_sec: float
    snr: float
    bandwidth_hz: float
    scan_role: str
    target_id: str
    metadata_complete: bool = True
    instrumental_artifact_score: float = 0.0
    injection_recovery_score: float = 0.5
    repeat_observation_score: float = 0.0


@dataclass(frozen=True)
class RadioDiagnosticPaths:
    """Optional diagnostic artifacts for a radio candidate."""

    waterfall_plot_path: str | None = None
    hit_table_path: str | None = None
    diagnostic_placeholder: str = "waterfall_not_generated_v0"

    def as_features(self) -> dict[str, FeatureValue]:
        return {
            "waterfall_plot_path": self.waterfall_plot_path,
            "hit_table_path": self.hit_table_path,
            "diagnostic_placeholder": self.diagnostic_placeholder,
        }


DEFAULT_RFI_BANDS_HZ: tuple[RfiBand, ...] = (
    RfiBand("gps_l1", 1_575_000_000.0, 1_576_000_000.0),
    RfiBand("gps_l2", 1_227_000_000.0, 1_228_000_000.0),
    RfiBand("aircraft_ads_b", 1_089_500_000.0, 1_090_500_000.0),
)


def parse_hit_table(
    rows: Sequence[Mapping[str, FeatureValue]],
    *,
    track_config: TrackConfig | None = None,
) -> tuple[RadioHit, ...]:
    """Parse synthetic hit-table rows into normalized radio hits."""

    defaults = _feature_defaults(track_config)
    return tuple(_parse_hit(row, defaults) for row in rows)


def rfi_band_overlap_score(
    frequency_hz: float,
    bands: Sequence[RfiBand] = DEFAULT_RFI_BANDS_HZ,
) -> float:
    """Return 1.0 when the frequency overlaps a known RFI band, else 0.0."""

    return 1.0 if any(band.contains(frequency_hz) for band in bands) else 0.0


def build_radio_candidate(
    candidate_id: str,
    rows: Sequence[Mapping[str, FeatureValue]],
    *,
    source_ids: Sequence[str] = (),
    provenance: Mapping[str, FeatureValue] | None = None,
    rfi_bands: Sequence[RfiBand] = DEFAULT_RFI_BANDS_HZ,
    rfi_database_path: Path | None = None,
    diagnostics: RadioDiagnosticPaths | None = None,
    track_config: TrackConfig | None = None,
) -> Candidate:
    """Build a shared candidate from synthetic radio hit rows."""

    defaults = _feature_defaults(track_config)
    hits = parse_hit_table(rows, track_config=track_config)
    best_hit = _best_hit(hits)
    on_hits = [hit for hit in hits if hit.scan_role == "on"]
    off_hits = [hit for hit in hits if hit.scan_role == "off"]

    max_on_snr = max((hit.snr for hit in on_hits), default=0.0)
    max_off_snr = max((hit.snr for hit in off_hits), default=0.0)
    recurrence_targets = {
        hit.target_id for hit in hits if hit.target_id != best_hit.target_id and hit.snr >= 8.0
    }
    rfi_database_features = _rfi_database_features(
        best_hit.frequency_hz,
        path=rfi_database_path,
    )
    configured_rfi_overlap = rfi_band_overlap_score(best_hit.frequency_hz, rfi_bands)
    database_rfi_overlap = _float(rfi_database_features["rfi_database_overlap_score"])

    features: dict[str, FeatureValue] = {
        "frequency_hz": best_hit.frequency_hz,
        "drift_rate_hz_per_sec": best_hit.drift_rate_hz_per_sec,
        "snr": best_hit.snr,
        "bandwidth_hz": best_hit.bandwidth_hz,
        "on_target_presence_score": _presence_score(max_on_snr),
        "off_target_presence_score": _presence_score(max_off_snr),
        "rfi_band_overlap_score": max(configured_rfi_overlap, database_rfi_overlap),
        "frequency_persistence_score": _frequency_persistence_score(hits, best_hit),
        "nearby_target_recurrence_score": _clamp(len(recurrence_targets) / 3.0),
        "instrumental_artifact_score": max(
            (hit.instrumental_artifact_score for hit in hits), default=0.0
        ),
        "injection_recovery_score": max(
            (hit.injection_recovery_score for hit in hits), default=0.5
        ),
        "repeat_observation_score": max(
            (hit.repeat_observation_score for hit in hits), default=0.0
        ),
        "metadata_completeness_score": _metadata_completeness_score(hits),
        "data_quality_score": _data_quality_score(hits),
        "provenance_completeness_score": (
            1.0 if provenance else defaults.get("provenance_completeness_score", 0.4)
        ),
        "hit_count": len(hits),
        "on_hit_count": len(on_hits),
        "off_hit_count": len(off_hits),
    }
    features.update(rfi_database_features)
    if diagnostics is not None:
        features.update(diagnostics.as_features())

    return Candidate(
        candidate_id=candidate_id,
        track=Track.RADIO,
        features=features,
        source_ids=tuple(source_ids),
        provenance=provenance or {},
    )


def _parse_hit(row: Mapping[str, FeatureValue], defaults: Mapping[str, float]) -> RadioHit:
    scan_role = str(row.get("scan_role", "on")).lower()
    if scan_role not in {"on", "off"}:
        msg = f"scan_role must be 'on' or 'off', got {scan_role!r}"
        raise ValueError(msg)

    return RadioHit(
        frequency_hz=_required_float(row, "frequency_hz"),
        drift_rate_hz_per_sec=_required_float(row, "drift_rate_hz_per_sec"),
        snr=_required_float(row, "snr"),
        bandwidth_hz=_required_float(row, "bandwidth_hz"),
        scan_role=scan_role,
        target_id=str(row.get("target_id", "unknown")),
        metadata_complete=_bool(row.get("metadata_complete", True)),
        instrumental_artifact_score=_clamp(_float(row.get("instrumental_artifact_score", 0.0))),
        injection_recovery_score=_clamp(
            _float(row.get("injection_recovery_score", defaults["injection_recovery_score"]))
        ),
        repeat_observation_score=_clamp(
            _float(row.get("repeat_observation_score", defaults["repeat_observation_score"]))
        ),
    )


def _best_hit(hits: Sequence[RadioHit]) -> RadioHit:
    if not hits:
        raise ValueError("At least one radio hit is required.")
    return max(hits, key=lambda hit: hit.snr)


def _frequency_persistence_score(hits: Sequence[RadioHit], best_hit: RadioHit) -> float:
    near_frequency_hits = [
        hit for hit in hits if abs(hit.frequency_hz - best_hit.frequency_hz) <= 5.0
    ]
    if len(hits) <= 1:
        return 0.0
    return _clamp((len(near_frequency_hits) - 1) / max(len(hits) - 1, 1))


def _metadata_completeness_score(hits: Sequence[RadioHit]) -> float:
    if not hits:
        return 0.0
    complete = sum(1 for hit in hits if hit.metadata_complete)
    return complete / len(hits)


def _data_quality_score(hits: Sequence[RadioHit]) -> float:
    if not hits:
        return 0.0
    artifact_penalty = max((hit.instrumental_artifact_score for hit in hits), default=0.0)
    metadata_score = _metadata_completeness_score(hits)
    return _clamp((0.7 * metadata_score) + (0.3 * (1.0 - artifact_penalty)))


def _rfi_database_features(
    frequency_hz: float,
    *,
    path: Path | None = None,
) -> dict[str, FeatureValue]:
    from techno_search.rfi_database import (
        RFI_DATABASE_SCHEMA_VERSION,
        rfi_database_matches,
        rfi_database_summary,
    )

    matches = rfi_database_matches(frequency_hz, path)
    summary = rfi_database_summary(path)
    match_names = ",".join(match.entry_id for match in matches)
    source_classes = ",".join(sorted({match.source_class for match in matches}))
    return {
        "rfi_database_schema_version": RFI_DATABASE_SCHEMA_VERSION,
        "rfi_database_record_count": int(summary["record_count"]),
        "rfi_database_reviewed_count": int(summary["reviewed_count"]),
        "rfi_database_validation_ok": bool(summary["validation_ok"]),
        "rfi_database_match_count": len(matches),
        "rfi_database_match_ids": match_names,
        "rfi_database_source_classes": source_classes,
        "rfi_database_overlap_score": 1.0 if matches else 0.0,
    }


def _presence_score(snr: float) -> float:
    return _clamp(snr / 30.0)


def _required_float(row: Mapping[str, FeatureValue], key: str) -> float:
    if key not in row:
        msg = f"Missing required radio hit field: {key}"
        raise ValueError(msg)
    return _float(row[key])


def _float(value: FeatureValue) -> float:
    if isinstance(value, bool) or value is None:
        msg = f"Expected numeric value, got {value!r}"
        raise TypeError(msg)
    if isinstance(value, int | float):
        return float(value)
    return float(value)


def _bool(value: FeatureValue) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes"}
    return bool(value)


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _feature_defaults(track_config: TrackConfig | None) -> dict[str, float]:
    config = track_config or load_track_config(Track.RADIO)
    defaults = dict(config.feature_defaults)
    defaults.setdefault("injection_recovery_score", 0.5)
    defaults.setdefault("repeat_observation_score", 0.0)
    defaults.setdefault("provenance_completeness_score", 0.4)
    return defaults
