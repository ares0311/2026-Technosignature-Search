"""Background target-priority and search-ledger helpers."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
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
BACKGROUND_PRIORITY_CONFIG_VERSION = "background_priority_v0"
LOCAL_BACKGROUND_EXECUTION_MODE = "local_non_network_fixture_runner"
LOCAL_BACKGROUND_REVIEW_STATUS = "local_scheduling_only"

DEFAULT_PRIORITY_WEIGHTS = {
    "followup_value": 0.35,
    "novelty_score": 0.25,
    "data_quality_score": 0.20,
    "observability_score": 0.10,
    "false_positive_probability": -0.30,
}
DEFAULT_BLOCKING_ISSUE_PENALTY_PER_ISSUE = 0.05
DEFAULT_MAX_BLOCKING_ISSUE_PENALTY = 0.25


@dataclass(frozen=True)
class BackgroundPriorityConfig:
    """Versioned target-priority and local passive-runner settings."""

    config_version: str
    description: str
    disclaimer: str
    weights: dict[str, float]
    blocking_issue_penalty_per_issue: float
    max_blocking_issue_penalty: float
    passive_runner_requires_opt_in: bool
    network_access_enabled: bool
    local_runner_status: str
    local_runner_pathway: str


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
    execution_mode: str = "unspecified"
    selected_priority_score: float | None = None
    target_selection_rationale: tuple[str, ...] = ()
    candidate_packet_ids: tuple[str, ...] = ()
    negative_result_logged: bool = False
    requires_human_review: bool = False
    reviewed_workflow_status: str = "unreviewed"


def default_background_priority_config_path() -> Path:
    """Return the repository-local v0 background priority config path."""

    return Path(__file__).resolve().parents[2] / "configs" / (
        "background_priority_v0.json"
    )


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


def load_background_priority_config(
    path: Path | None = None,
) -> BackgroundPriorityConfig:
    """Load versioned background target-priority configuration."""

    config_path = path or default_background_priority_config_path()
    with config_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    config_version = str(data.get("config_version", ""))
    if config_version != BACKGROUND_PRIORITY_CONFIG_VERSION:
        msg = (
            f"Unsupported background priority config version {config_version!r}; "
            f"expected {BACKGROUND_PRIORITY_CONFIG_VERSION!r}"
        )
        raise ValueError(msg)

    weights = _float_mapping(data["weights"])
    missing = set(DEFAULT_PRIORITY_WEIGHTS) - set(weights)
    if missing:
        msg = f"Background priority config is missing weights: {sorted(missing)}"
        raise ValueError(msg)

    return BackgroundPriorityConfig(
        config_version=config_version,
        description=str(data.get("description", "")),
        disclaimer=str(data.get("disclaimer", TARGET_PRIORITY_DISCLAIMER)),
        weights=weights,
        blocking_issue_penalty_per_issue=float(
            data.get(
                "blocking_issue_penalty_per_issue",
                DEFAULT_BLOCKING_ISSUE_PENALTY_PER_ISSUE,
            )
        ),
        max_blocking_issue_penalty=float(
            data.get("max_blocking_issue_penalty", DEFAULT_MAX_BLOCKING_ISSUE_PENALTY)
        ),
        passive_runner_requires_opt_in=bool(
            data.get("passive_runner_requires_opt_in", True)
        ),
        network_access_enabled=bool(data.get("network_access_enabled", False)),
        local_runner_status=str(
            data.get("local_runner_status", "local_fixture_search_logged")
        ),
        local_runner_pathway=str(
            data.get("local_runner_pathway", "github_reproducibility_only")
        ),
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
    config: BackgroundPriorityConfig | None = None,
) -> float:
    """Compute an auditable target-priority score."""

    active_config = config or load_background_priority_config()
    active_weights = weights or active_config.weights
    score = (
        active_weights["followup_value"] * target.followup_value
        + active_weights["novelty_score"] * target.novelty_score
        + active_weights["data_quality_score"] * target.data_quality_score
        + active_weights["observability_score"] * target.observability_score
        + active_weights["false_positive_probability"]
        * target.false_positive_probability
    )
    if target.blocking_issue_count:
        score -= min(
            active_config.max_blocking_issue_penalty,
            active_config.blocking_issue_penalty_per_issue
            * target.blocking_issue_count,
        )
    return round(score, 6)


def target_priority_summary(
    path: Path | None = None,
    config_path: Path | None = None,
) -> dict[str, object]:
    """Summarize background target-priority fixture coverage."""

    target_path = path or default_background_targets_path()
    resolved_config_path = config_path or default_background_priority_config_path()
    config = load_background_priority_config(resolved_config_path)
    targets = load_background_targets(target_path)
    scored_targets = [
        {
            "target_id": target.target_id,
            "track": target.track.value,
            "source_id": target.source_id,
            "priority_score": target_priority_score(target, config=config),
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
        "config_path": str(resolved_config_path),
        "schema_version": TARGET_PRIORITY_SCHEMA_VERSION,
        "config_version": config.config_version,
        "disclaimer": TARGET_PRIORITY_DISCLAIMER,
        "target_count": len(targets),
        "by_track": _counter_to_dict(Counter(target.track.value for target in targets)),
        "weights": dict(sorted(config.weights.items())),
        "blocking_issue_penalty_per_issue": config.blocking_issue_penalty_per_issue,
        "max_blocking_issue_penalty": config.max_blocking_issue_penalty,
        "passive_runner_requires_opt_in": config.passive_runner_requires_opt_in,
        "network_access_enabled": config.network_access_enabled,
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
    candidate_packet_ids = [
        candidate_id for entry in entries for candidate_id in entry.candidate_packet_ids
    ]

    return {
        "ledger_path": str(ledger_path),
        "schema_version": BACKGROUND_SEARCH_LEDGER_SCHEMA_VERSION,
        "disclaimer": BACKGROUND_SEARCH_LEDGER_DISCLAIMER,
        "entry_count": len(entries),
        "searched_target_count": len(searched_targets),
        "candidate_count": sum(entry.candidate_count for entry in entries),
        "candidate_packet_id_count": len(candidate_packet_ids),
        "blocking_issue_count": len(all_blocking_issues),
        "negative_result_logged_count": sum(
            1 for entry in entries if entry.negative_result_logged
        ),
        "requires_human_review_count": sum(
            1 for entry in entries if entry.requires_human_review
        ),
        "scheduling_only_count": sum(
            1
            for entry in entries
            if entry.reviewed_workflow_status == LOCAL_BACKGROUND_REVIEW_STATUS
        ),
        "by_track": _counter_to_dict(Counter(entry.track.value for entry in entries)),
        "by_status": _counter_to_dict(Counter(entry.status for entry in entries)),
        "by_execution_mode": _counter_to_dict(
            Counter(entry.execution_mode for entry in entries)
        ),
        "by_reviewed_workflow_status": _counter_to_dict(
            Counter(entry.reviewed_workflow_status for entry in entries)
        ),
        "by_recommended_pathway": _counter_to_dict(Counter(pathways)),
        "run_ids": sorted(entry.run_id for entry in entries),
        "target_ids": sorted(searched_targets),
        "candidate_packet_ids": sorted(candidate_packet_ids),
    }


def background_review_workflow_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize reviewed workflow semantics for passive/background ledger entries."""

    ledger_path = path or default_background_ledger_path()
    entries = load_background_search_ledger(ledger_path)
    rationale_count = sum(len(entry.target_selection_rationale) for entry in entries)
    blocked_entries = [
        entry.run_id
        for entry in entries
        if entry.blocking_issues or entry.reviewed_workflow_status == "review_blocked"
    ]
    local_only_entries = [
        entry.run_id
        for entry in entries
        if entry.execution_mode == LOCAL_BACKGROUND_EXECUTION_MODE
    ]

    return {
        "ledger_path": str(ledger_path),
        "schema_version": BACKGROUND_SEARCH_LEDGER_SCHEMA_VERSION,
        "disclaimer": BACKGROUND_SEARCH_LEDGER_DISCLAIMER,
        "entry_count": len(entries),
        "reviewed_workflow_status_count": len(
            {entry.reviewed_workflow_status for entry in entries}
        ),
        "target_selection_rationale_count": rationale_count,
        "negative_result_logged_count": sum(
            1 for entry in entries if entry.negative_result_logged
        ),
        "requires_human_review_count": sum(
            1 for entry in entries if entry.requires_human_review
        ),
        "local_only_entry_count": len(local_only_entries),
        "scheduling_only_count": sum(
            1
            for entry in entries
            if entry.reviewed_workflow_status == LOCAL_BACKGROUND_REVIEW_STATUS
        ),
        "candidate_packet_id_count": sum(
            len(entry.candidate_packet_ids) for entry in entries
        ),
        "blocked_entry_count": len(blocked_entries),
        "by_execution_mode": _counter_to_dict(
            Counter(entry.execution_mode for entry in entries)
        ),
        "by_reviewed_workflow_status": _counter_to_dict(
            Counter(entry.reviewed_workflow_status for entry in entries)
        ),
        "blocked_run_ids": sorted(blocked_entries),
        "local_only_run_ids": sorted(local_only_entries),
    }


def run_local_background_search_once(
    ledger_path: Path,
    target_path: Path | None = None,
    config_path: Path | None = None,
    run_id: str | None = None,
    code_commit: str = "not-recorded",
    opt_in: bool = False,
) -> dict[str, object]:
    """Append one local-only background search ledger entry for the top target."""

    resolved_target_path = target_path or default_background_targets_path()
    resolved_config_path = config_path or default_background_priority_config_path()
    config = load_background_priority_config(resolved_config_path)
    if config.passive_runner_requires_opt_in and not opt_in:
        msg = "Local background runs require explicit opt-in."
        raise ValueError(msg)
    if config.network_access_enabled:
        msg = "Local background fixture runner must not enable network access."
        raise ValueError(msg)

    targets = load_background_targets(resolved_target_path)
    if not targets:
        msg = "No background targets are available to search."
        raise ValueError(msg)

    selected = sorted(
        targets,
        key=lambda target: (
            -target_priority_score(target, config=config),
            target.target_id,
        ),
    )[0]
    priority_score = target_priority_score(selected, config=config)
    timestamp = datetime.now(UTC).isoformat()
    entry = BackgroundSearchLedgerEntry(
        run_id=run_id or _run_id_from_timestamp(timestamp),
        target_id=selected.target_id,
        track=selected.track,
        status=config.local_runner_status,
        query_parameters={
            "mode": LOCAL_BACKGROUND_EXECUTION_MODE,
            "target_path": str(resolved_target_path),
            "config_path": str(resolved_config_path),
            "selected_priority_score": priority_score,
        },
        started_at_utc=timestamp,
        completed_at_utc=timestamp,
        config_version=config.config_version,
        code_commit=code_commit,
        cache_key=f"local-fixture-{selected.target_id}-{config.config_version}",
        candidate_count=0,
        recommended_pathways=(config.local_runner_pathway,),
        blocking_issues=(
            "local fixture runner records scheduling only; no candidate extraction was performed",
        ),
        execution_mode=LOCAL_BACKGROUND_EXECUTION_MODE,
        selected_priority_score=priority_score,
        target_selection_rationale=(
            "highest configured target-priority score",
            "false-positive probability and blocking issues penalized",
            "local fixture runner does not query live providers",
        ),
        candidate_packet_ids=(),
        negative_result_logged=True,
        requires_human_review=False,
        reviewed_workflow_status=LOCAL_BACKGROUND_REVIEW_STATUS,
    )
    append_background_search_ledger_entry(ledger_path, entry)
    return {
        "ok": True,
        "appended_entry": _ledger_entry_to_mapping(entry),
        "ledger_summary": background_search_ledger_summary(ledger_path),
        "review_workflow_summary": background_review_workflow_summary(ledger_path),
    }


def append_background_search_ledger_entry(
    path: Path,
    entry: BackgroundSearchLedgerEntry,
) -> None:
    """Append a background-search ledger entry, creating the ledger if needed."""

    ledger_path = Path(path)
    if ledger_path.exists():
        with ledger_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        schema_version = str(data.get("schema_version", ""))
        if schema_version != BACKGROUND_SEARCH_LEDGER_SCHEMA_VERSION:
            msg = (
                f"Unsupported background search ledger schema version "
                f"{schema_version!r}; expected "
                f"{BACKGROUND_SEARCH_LEDGER_SCHEMA_VERSION!r}"
            )
            raise ValueError(msg)
        entries = list(data.get("ledger_entries", []))
    else:
        data = {
            "schema_version": BACKGROUND_SEARCH_LEDGER_SCHEMA_VERSION,
            "description": (
                "Local passive/background search ledger. Entries record searched "
                "targets, not discoveries."
            ),
            "disclaimer": BACKGROUND_SEARCH_LEDGER_DISCLAIMER,
        }
        entries = []

    entries.append(_ledger_entry_to_mapping(entry))
    data["ledger_entries"] = entries
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
        execution_mode=str(
            data.get(
                "execution_mode",
                data.get("query_parameters", {}).get("mode", "unspecified"),
            )
        ),
        selected_priority_score=_optional_float(data.get("selected_priority_score")),
        target_selection_rationale=tuple(
            str(reason) for reason in data.get("target_selection_rationale", ())
        ),
        candidate_packet_ids=tuple(
            str(candidate_id) for candidate_id in data.get("candidate_packet_ids", ())
        ),
        negative_result_logged=bool(data.get("negative_result_logged", False)),
        requires_human_review=bool(data.get("requires_human_review", False)),
        reviewed_workflow_status=str(
            data.get("reviewed_workflow_status", "unreviewed")
        ),
    )


def _ledger_entry_to_mapping(entry: BackgroundSearchLedgerEntry) -> dict[str, object]:
    return {
        "run_id": entry.run_id,
        "target_id": entry.target_id,
        "track": entry.track.value,
        "status": entry.status,
        "query_parameters": entry.query_parameters,
        "started_at_utc": entry.started_at_utc,
        "completed_at_utc": entry.completed_at_utc,
        "config_version": entry.config_version,
        "code_commit": entry.code_commit,
        "cache_key": entry.cache_key,
        "candidate_count": entry.candidate_count,
        "recommended_pathways": list(entry.recommended_pathways),
        "blocking_issues": list(entry.blocking_issues),
        "execution_mode": entry.execution_mode,
        "selected_priority_score": entry.selected_priority_score,
        "target_selection_rationale": list(entry.target_selection_rationale),
        "candidate_packet_ids": list(entry.candidate_packet_ids),
        "negative_result_logged": entry.negative_result_logged,
        "requires_human_review": entry.requires_human_review,
        "reviewed_workflow_status": entry.reviewed_workflow_status,
    }


def _float_mapping(data: dict[str, Any]) -> dict[str, float]:
    return {str(key): float(value) for key, value in data.items()}


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, str | int | float):
        return float(value)
    msg = f"Expected a numeric or string priority score, got {type(value).__name__}"
    raise TypeError(msg)


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def _run_id_from_timestamp(timestamp: str) -> str:
    return "background-local-" + (
        timestamp.replace("+00:00", "Z")
        .replace("-", "")
        .replace(":", "")
        .replace(".", "")
    )
