"""Scoring configuration summary helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCORING_CONFIG_SCHEMA_VERSION = "scoring_config_summary_v1"

SCORING_CONFIG_DISCLAIMER = (
    "Scoring configuration summary reports local threshold values only. "
    "These thresholds are synthetic development parameters for v0 scoring. "
    "They do not represent calibrated survey performance metrics or validated "
    "detection thresholds against real astronomical data."
)


def _default_scoring_config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "configs" / "scoring_v0.json"


def scoring_config_summary(
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Return a human-readable summary of current scoring thresholds."""

    path = config_path or _default_scoring_config_path()
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)

    thresholds = config.get("pathway_thresholds", {})
    performance = config.get("local_performance_defaults", {})

    return {
        "schema_version": SCORING_CONFIG_SCHEMA_VERSION,
        "disclaimer": SCORING_CONFIG_DISCLAIMER,
        "config_path": str(path),
        "config_description": str(config.get("description", "")),
        "threshold_count": len(thresholds),
        "pathway_thresholds": dict(thresholds),
        "local_performance_defaults": dict(performance),
        "cpu_heavy_workers": int(performance.get("cpu_heavy_workers", 0)),
        "light_io_workers": int(performance.get("light_io_workers", 0)),
        "memory_budget_gb": int(performance.get("memory_budget_gb", 0)),
    }
