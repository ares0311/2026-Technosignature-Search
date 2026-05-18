"""Feature importance mapping from baseline rule fire rates to feature names."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FEATURE_IMPORTANCE_SCHEMA_VERSION = "feature_importance_v1"
FEATURE_IMPORTANCE_DISCLAIMER = (
    "Feature importance scores are derived from synthetic baseline rule fire rates only. "
    "They are scheduling and development diagnostics — "
    "not calibrated signal detection metrics or discovery claims."
)


def _default_importance_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests" / "fixtures" / "feature_importance.json"
    )


@dataclass
class FeatureImportanceEntry:
    importance_id: str
    track: str
    feature_name: str
    baseline_rule_name: str
    rule_fire_rate: float
    importance_score: float
    rank: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "importance_id": self.importance_id,
            "track": self.track,
            "feature_name": self.feature_name,
            "baseline_rule_name": self.baseline_rule_name,
            "rule_fire_rate": self.rule_fire_rate,
            "importance_score": self.importance_score,
            "rank": self.rank,
        }


def load_feature_importance_entries(
    fixture_path: Path | None = None,
) -> list[FeatureImportanceEntry]:
    path = fixture_path or _default_importance_path()
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = data.get("feature_importance_entries", [])
    return [
        FeatureImportanceEntry(
            importance_id=e["importance_id"],
            track=e["track"],
            feature_name=e["feature_name"],
            baseline_rule_name=e["baseline_rule_name"],
            rule_fire_rate=float(e["rule_fire_rate"]),
            importance_score=float(e["importance_score"]),
            rank=int(e["rank"]),
        )
        for e in entries
    ]


def feature_importance_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_feature_importance_entries(fixture_path)
    by_track: dict[str, int] = {}
    top_feature_by_track: dict[str, str] = {}
    unique_rules: set[str] = set()

    for e in entries:
        by_track[e.track] = by_track.get(e.track, 0) + 1
        unique_rules.add(e.baseline_rule_name)
        if e.rank == 1:
            top_feature_by_track[e.track] = e.feature_name

    return {
        "schema_version": FEATURE_IMPORTANCE_SCHEMA_VERSION,
        "disclaimer": FEATURE_IMPORTANCE_DISCLAIMER,
        "entry_count": len(entries),
        "by_track": by_track,
        "top_feature_by_track": top_feature_by_track,
        "tracks_covered": sorted(by_track),
        "unique_rule_names": sorted(unique_rules),
    }
