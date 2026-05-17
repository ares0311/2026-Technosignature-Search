"""Per-track scoring sensitivity configuration summary helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SENSITIVITY_CONFIG_SCHEMA_VERSION = "sensitivity_config_summary_v1"

SENSITIVITY_CONFIG_DISCLAIMER = (
    "Per-track sensitivity weights are local scheduling and calibration parameters only. "
    "They are synthetic v0 development coefficients and do not represent calibrated "
    "survey detection sensitivities or validated performance against real observations."
)

ALLOWED_TRACKS = frozenset({"radio", "infrared", "anomaly"})
ALLOWED_WEIGHT_KEYS = frozenset({"signal_weight", "false_positive_weight", "provenance_weight"})


def _default_scoring_config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "configs" / "scoring_v0.json"


def sensitivity_config_summary(
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Return per-track sensitivity weight summary from the scoring config."""

    path = config_path or _default_scoring_config_path()
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)

    track_sensitivity = config.get("track_sensitivity", {})
    tracks_present = sorted(track_sensitivity.keys())
    missing_tracks = sorted(ALLOWED_TRACKS - set(tracks_present))

    per_track: dict[str, dict[str, float]] = {}
    total_weight_count = 0
    for track, weights in track_sensitivity.items():
        per_track[track] = {
            str(k): float(v) for k, v in weights.items() if k in ALLOWED_WEIGHT_KEYS
        }
        total_weight_count += len(per_track[track])

    all_weights_in_range = all(
        0.0 <= w <= 10.0
        for weights in per_track.values()
        for w in weights.values()
    )

    return {
        "schema_version": SENSITIVITY_CONFIG_SCHEMA_VERSION,
        "disclaimer": SENSITIVITY_CONFIG_DISCLAIMER,
        "config_path": str(path),
        "track_count": len(tracks_present),
        "tracks_present": tracks_present,
        "missing_tracks": missing_tracks,
        "weight_count": total_weight_count,
        "per_track_weights": dict(sorted(per_track.items())),
        "all_weights_in_range": all_weights_in_range,
    }
