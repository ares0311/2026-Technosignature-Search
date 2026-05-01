"""Runtime configuration helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.pathway import PathwayThresholds
from techno_search.schemas import Track


@dataclass(frozen=True)
class LocalPerformanceDefaults:
    """Local defaults informed by docs/LOCAL_SYSTEM_PROFILE.md."""

    cpu_heavy_workers: int
    light_io_workers: int
    memory_budget_gb: int


@dataclass(frozen=True)
class ScoringConfig:
    """Versioned scoring configuration."""

    pathway_thresholds: PathwayThresholds
    local_performance_defaults: LocalPerformanceDefaults


@dataclass(frozen=True)
class TrackConfig:
    """Versioned track-specific search configuration."""

    track: Track
    config_version: str
    thresholds: dict[str, float]
    feature_defaults: dict[str, float]
    assumptions: tuple[str, ...]
    raw: dict[str, Any]


def default_scoring_config_path() -> Path:
    """Return the repository-local v0 scoring config path."""

    return Path(__file__).resolve().parents[2] / "configs" / "scoring_v0.json"


def default_track_config_path(track: Track) -> Path:
    """Return the repository-local v0 config path for a search track."""

    return Path(__file__).resolve().parents[2] / "configs" / f"{track.value}_search_v0.json"


def load_scoring_config(path: Path | None = None) -> ScoringConfig:
    """Load the v0 scoring configuration."""

    config_path = path or default_scoring_config_path()
    with config_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    return ScoringConfig(
        pathway_thresholds=_pathway_thresholds(data["pathway_thresholds"]),
        local_performance_defaults=_local_performance_defaults(
            data["local_performance_defaults"]
        ),
    )


def load_track_config(track: Track, path: Path | None = None) -> TrackConfig:
    """Load a track-specific v0 configuration."""

    config_path = path or default_track_config_path(track)
    with config_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    configured_track = Track(str(data["track"]))
    if configured_track != track:
        msg = f"Config track {configured_track.value!r} does not match requested {track.value!r}."
        raise ValueError(msg)

    return TrackConfig(
        track=configured_track,
        config_version=str(data["config_version"]),
        thresholds=_float_mapping(data["thresholds"]),
        feature_defaults=_float_mapping(data["feature_defaults"]),
        assumptions=tuple(str(item) for item in data.get("assumptions", ())),
        raw=data,
    )


def _pathway_thresholds(data: dict[str, Any]) -> PathwayThresholds:
    return PathwayThresholds(
        known_object_probability=float(data["known_object_probability"]),
        false_positive_probability=float(data["false_positive_probability"]),
        minimum_signal_reality_for_review=float(
            data["minimum_signal_reality_for_review"]
        ),
        candidate_interest_probability=float(data["candidate_interest_probability"]),
        candidate_max_false_positive_probability=float(
            data["candidate_max_false_positive_probability"]
        ),
        candidate_signal_reality=float(data["candidate_signal_reality"]),
        candidate_review_readiness=float(data["candidate_review_readiness"]),
    )


def _local_performance_defaults(data: dict[str, Any]) -> LocalPerformanceDefaults:
    return LocalPerformanceDefaults(
        cpu_heavy_workers=int(data["cpu_heavy_workers"]),
        light_io_workers=int(data["light_io_workers"]),
        memory_budget_gb=int(data["memory_budget_gb"]),
    )


def _float_mapping(data: dict[str, Any]) -> dict[str, float]:
    return {key: float(value) for key, value in data.items()}
