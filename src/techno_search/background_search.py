"""Background target-priority and search-ledger helpers."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.schemas import Track

TARGET_PRIORITY_SCHEMA_VERSION = "background_target_priority_v1"
TARGET_PRIORITY_DISCLAIMER = (
    "Target priority scores are scheduling aids only; they are not evidence of a "
    "technosignature or a discovery claim."
)
BACKGROUND_SEARCH_LEDGER_SCHEMA_VERSION = "background_search_ledger_v1"
BACKGROUND_SEARCH_LEDGER_DISCLAIMER = (
    "Background search ledger entries record searched targets and outcomes for "
    "reproducibility; they are not discovery claims."
)

DEFAULT_PRIORITY_WEIGHTS = {
    "followup_value": 0.35,
    "novelty_score": 0.25,
    "data_quality_score": 0.20,
    "observability_score": 0.10,
    "false_positive_probability": -0.30,
}


@dataclass(frozen=True)
class BackgroundTarget:
    """One candidate target for future passive/background search."""

    target_id: str
    track: Track
    source_id: str
    followup_value: float
    novelty_score: float
    data_quality_score: float
    observability_score: float
    false_positive_probability: float
    blocking_issue_count: int


@dataclass(frozen=True)
class BackgroundSearchLedgerEntry:
    """One audited background-search ledger entry."""

    run_id: str
    target_id: str
    track: Track
    status: str
    query_parameters: dict[str, object]
    started_at_utc: str
    completed_at_utc: str
    config_version: str
    code_commit: str
    cache_key: str
    candidate_count: int
    recommended_pathways: tuple[str, ...]
    blocking_issues: tuple[str, ...]


def default_background_targets_path() -> Path:
    """Return the repository-local background target fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "background_targets.json"
    )


def default_background_ledger_path() -> Path:
    """Return the repository-local background search ledger fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "background_search_ledger.json"
    )


def load_background_targets(path: Path | None = None) -> tuple[BackgroundTarget, ...]:
    """Load background target-priority fixture entries."""

    target_path = path or default_background_targets_path()
    with target_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != TARGET_PRIORITY_SCHEMA_VERSION:
        msg = (
            f"Unsupported target priority schema version {schema_version!r}; "
            f"expected {TARGET_PRIORITY_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(_target_from_mapping(target) for target in data["targets"])


def load_background_search_ledger(
    path: Path | None = None,
) -> tuple[BackgroundSearchLedgerEntry, ...]:
    """Load background-search ledger fixture entries."""

    ledger_path = path or default_background_ledger_path()
    with ledger_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != BACKGROUND_SEARCH_LEDGER_SCHEMA_VERSION:
        msg = (
            f"Unsupported background search ledger schema version {schema_version!r}; "
            f"expected {BACKGROUND_SEARCH_LEDGER_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(_ledger_entry_from_mapping(entry) for entry in data["ledger_entries"])


def target_priority_score(
    target: BackgroundTarget,
    weights: dict[str, float] | None = None,
) -> float:
    """Compute an auditable target-priority score."""

    active_weights = weights or DEFAULT_PRIORITY_WEIGHTS
    score = (
        active_weights["followup_value"] * target.followup_value
        + active_weights["novelty_score"] * target.novelty_score
        + active_weights["data_quality_score"] * target.data_quality_score
        + active_weights["observability_score"] * target.observability_score
        + active_weights["false_positive_probability"]
        * target.false_positive_probability
    )
    if target.blocking_issue_count:
        score -= min(0.25, 0.05 * target.blocking_issue_count)
    return round(score, 6)


def target_priority_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize background target-priority fixture coverage."""

    target_path = path or default_background_targets_path()
    targets = load_background_targets(target_path)
    scored_targets = [
        {
            "target_id": target.target_id,
            "track": target.track.value,
            "source_id": target.source_id,
            "priority_score": target_priority_score(target),
            "blocking_issue_count": target.blocking_issue_count,
        }
        for target in targets
    ]
    ranked = sorted(
        scored_targets,
        key=lambda item: (-float(item["priority_score"]), str(item["target_id"])),
    )
    selected = ranked[0] if ranked else None

    return {
        "target_path": str(target_path),
        "schema_version": TARGET_PRIORITY_SCHEMA_VERSION,
        "disclaimer": TARGET_PRIORITY_DISCLAIMER,
        "target_count": len(targets),
        "by_track": _counter_to_dict(Counter(target.track.value for target in targets)),
        "weights": dict(sorted(DEFAULT_PRIORITY_WEIGHTS.items())),
        "selected_target_id": selected["target_id"] if selected else None,
        "selected_priority_score": selected["priority_score"] if selected else None,
        "ranked_targets": ranked,
    }


def background_search_ledger_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize passive/background search ledger fixture entries."""

    ledger_path = path or default_background_ledger_path()
    entries = load_background_search_ledger(ledger_path)
    searched_targets = {entry.target_id for entry in entries}
    all_blocking_issues = [
        issue for entry in entries for issue in entry.blocking_issues
    ]
    pathways = [
        pathway for entry in entries for pathway in entry.recommended_pathways
    ]

    return {
        "ledger_path": str(ledger_path),
        "schema_version": BACKGROUND_SEARCH_LEDGER_SCHEMA_VERSION,
        "disclaimer": BACKGROUND_SEARCH_LEDGER_DISCLAIMER,
        "entry_count": len(entries),
        "searched_target_count": len(searched_targets),
        "candidate_count": sum(entry.candidate_count for entry in entries),
        "blocking_issue_count": len(all_blocking_issues),
        "by_track": _counter_to_dict(Counter(entry.track.value for entry in entries)),
        "by_status": _counter_to_dict(Counter(entry.status for entry in entries)),
        "by_recommended_pathway": _counter_to_dict(Counter(pathways)),
        "run_ids": sorted(entry.run_id for entry in entries),
        "target_ids": sorted(searched_targets),
    }


def _target_from_mapping(data: dict[str, Any]) -> BackgroundTarget:
    return BackgroundTarget(
        target_id=str(data["target_id"]),
        track=Track(str(data["track"])),
        source_id=str(data["source_id"]),
        followup_value=float(data["followup_value"]),
        novelty_score=float(data["novelty_score"]),
        data_quality_score=float(data["data_quality_score"]),
        observability_score=float(data["observability_score"]),
        false_positive_probability=float(data["false_positive_probability"]),
        blocking_issue_count=int(data.get("blocking_issue_count", 0)),
    )


def _ledger_entry_from_mapping(data: dict[str, Any]) -> BackgroundSearchLedgerEntry:
    return BackgroundSearchLedgerEntry(
        run_id=str(data["run_id"]),
        target_id=str(data["target_id"]),
        track=Track(str(data["track"])),
        status=str(data["status"]),
        query_parameters=dict(data.get("query_parameters", {})),
        started_at_utc=str(data["started_at_utc"]),
        completed_at_utc=str(data["completed_at_utc"]),
        config_version=str(data["config_version"]),
        code_commit=str(data["code_commit"]),
        cache_key=str(data["cache_key"]),
        candidate_count=int(data["candidate_count"]),
        recommended_pathways=tuple(
            str(pathway) for pathway in data.get("recommended_pathways", ())
        ),
        blocking_issues=tuple(
            str(issue) for issue in data.get("blocking_issues", ())
        ),
    )


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
