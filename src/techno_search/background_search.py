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
BACKGROUND_REVIEWED_LOG_SCHEMA_VERSION = "background_reviewed_log_v1"
BACKGROUND_REVIEWED_LOG_DISCLAIMER = (
    "Reviewed background-search records document targets that do not currently "
    "require follow-up; they are not external validation or discovery claims."
)
BACKGROUND_NEEDS_FOLLOW_UP_SCHEMA_VERSION = "background_needs_follow_up_log_v1"
BACKGROUND_NEEDS_FOLLOW_UP_DISCLAIMER = (
    "Needs-follow-up background-search records identify local follow-up work for "
    "review; they are not detections, not discovery claims, and not submission "
    "approvals."
)
BACKGROUND_FOLLOW_UP_TEST_SCHEMA_VERSION = "background_follow_up_tests_v1"
BACKGROUND_FOLLOW_UP_TEST_DISCLAIMER = (
    "Background follow-up test records describe deterministic local checks only; "
    "they are not detections, not external validation, and not submission approvals."
)
BACKGROUND_REPORT_READINESS_SCHEMA_VERSION = "background_report_readiness_v1"
BACKGROUND_REPORT_READINESS_DISCLAIMER = (
    "Background report-readiness records gate conservative draft reports and "
    "submission recommendations; they are not discoveries, endorsements, or "
    "authorization to submit externally."
)
BACKGROUND_DRAFT_REPORT_SCHEMA_VERSION = "background_draft_follow_up_reports_v1"
BACKGROUND_DRAFT_REPORT_MANIFEST_SCHEMA_VERSION = (
    "background_draft_report_manifest_v1"
)
BACKGROUND_DRAFT_REPORT_DISCLAIMER = (
    "Background draft follow-up reports are conservative internal summaries for "
    "review-ready records; they are not discoveries, detections, external "
    "validation, or authorization to submit externally."
)
BACKGROUND_USER_DECISION_SCHEMA_VERSION = "background_user_decisions_v1"
BACKGROUND_USER_DECISION_DISCLAIMER = (
    "Background user decision records preserve explicit human choices about "
    "follow-up reports; they do not create external submission approval unless "
    "that approval is recorded directly by the user."
)
BACKGROUND_PRIORITY_CONFIG_VERSION = "background_priority_v0"
LOCAL_BACKGROUND_EXECUTION_MODE = "local_non_network_fixture_runner"
LOCAL_BACKGROUND_REVIEW_STATUS = "local_scheduling_only"
BACKGROUND_REVIEWED_NO_FOLLOW_UP_STATUS = "reviewed_no_follow_up"
BACKGROUND_NEEDS_FOLLOW_UP_STATUS = "needs_follow_up_required"
CANDIDATE_EXTRACTION_HANDOFF_SCHEMA_VERSION = "candidate_extraction_handoff_v1"
CANDIDATE_EXTRACTION_HANDOFF_DISCLAIMER = (
    "Candidate extraction handoff records describe local fixture handoffs from "
    "target selection to possible candidate packet generation; they are not "
    "detections, discoveries, external validation, or calibrated performance claims."
)

DEFAULT_PRIORITY_WEIGHTS = {
    "followup_value": 0.35,
    "novelty_score": 0.25,
    "data_quality_score": 0.20,
    "observability_score": 0.10,
    "false_positive_probability": -0.30,
}
DEFAULT_BLOCKING_ISSUE_PENALTY_PER_ISSUE = 0.05
DEFAULT_MAX_BLOCKING_ISSUE_PENALTY = 0.25
DEFAULT_NEVER_REVIEWED_TARGET_BOOST = 0.08
DEFAULT_PRIOR_REVIEW_PENALTY_PER_ENTRY = 0.04
DEFAULT_MAX_PRIOR_REVIEW_PENALTY = 0.12
DEFAULT_NEEDS_FOLLOW_UP_PRIORITY_THRESHOLD = 0.70
MANDATORY_FOLLOW_UP_TESTS = (
    "provenance_check",
    "false_positive_class_check",
    "cross_source_consistency_check",
    "calibration_confidence_check",
    "reproducibility_check",
    "human_review_checklist",
)


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
    never_reviewed_target_boost: float
    prior_review_penalty_per_entry: float
    max_prior_review_penalty: float
    needs_follow_up_priority_threshold: float


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


@dataclass(frozen=True)
class BackgroundReviewedLogEntry:
    """One reviewed target outcome that does not currently need follow-up."""

    review_id: str
    run_id: str
    target_id: str
    track: Track
    outcome_status: str
    reviewed_at_utc: str
    reason_codes: tuple[str, ...]
    negative_evidence: tuple[str, ...]
    blocking_issues: tuple[str, ...]
    recommended_next_action: str
    network_access_allowed: bool


@dataclass(frozen=True)
class BackgroundNeedsFollowUpEntry:
    """One target outcome requiring additional local follow-up or review."""

    follow_up_id: str
    run_id: str
    target_id: str
    track: Track
    follow_up_status: str
    created_at_utc: str
    trigger_types: tuple[str, ...]
    reason_codes: tuple[str, ...]
    required_tests: tuple[str, ...]
    blocking_issues: tuple[str, ...]
    report_required: bool
    human_review_required: bool
    submission_requires_user_approval: bool
    network_access_allowed: bool


@dataclass(frozen=True)
class BackgroundFollowUpTestResult:
    """One deterministic local follow-up test result."""

    result_id: str
    follow_up_id: str
    run_id: str
    target_id: str
    track: Track
    test_name: str
    status: str
    executed_at_utc: str
    evidence: tuple[str, ...]
    negative_evidence: tuple[str, ...]
    blocking_issues: tuple[str, ...]
    uncertainty_notes: tuple[str, ...]
    network_access_allowed: bool


@dataclass(frozen=True)
class SubmissionRecommendation:
    """One conservative report-routing recommendation."""

    rank: int
    destination: str
    suitability_rationale: str
    risks: tuple[str, ...]
    prerequisites: tuple[str, ...]
    recommended_action: str


@dataclass(frozen=True)
class BackgroundReportReadinessRecord:
    """One report-readiness gate for a needs-follow-up item."""

    readiness_id: str
    follow_up_id: str
    run_id: str
    target_id: str
    track: Track
    readiness_status: str
    evaluated_at_utc: str
    mandatory_tests_complete: bool
    ready_to_draft_report: bool
    report_required: bool
    user_approval_required: bool
    external_submission_allowed: bool
    recommended_action: str
    blocking_issues: tuple[str, ...]
    limitations: tuple[str, ...]
    top_three_recommendations: tuple[SubmissionRecommendation, ...]
    network_access_allowed: bool


@dataclass(frozen=True)
class BackgroundDraftFollowUpReport:
    """One conservative draft follow-up report summary."""

    draft_id: str
    readiness_id: str
    follow_up_id: str
    run_id: str
    target_id: str
    track: Track
    draft_status: str
    generated_at_utc: str
    report_title: str
    abstract: str
    methodology_summary: str
    evidence_supporting_follow_up: tuple[str, ...]
    negative_evidence: tuple[str, ...]
    uncertainty_and_limitations: tuple[str, ...]
    blocking_issues: tuple[str, ...]
    recommended_next_steps: tuple[str, ...]
    user_approval_required: bool
    external_submission_allowed: bool
    network_access_allowed: bool


@dataclass(frozen=True)
class BackgroundUserDecisionRecord:
    """One explicit human decision about a background follow-up item."""

    decision_id: str
    readiness_id: str
    follow_up_id: str
    target_id: str
    track: Track
    decision: str
    decided_at_utc: str
    rationale: str
    required_next_actions: tuple[str, ...]
    external_submission_approved: bool
    request_more_tests: bool
    close_as_reviewed: bool
    submission_destination: str | None
    blocking_issues: tuple[str, ...]
    network_access_allowed: bool


@dataclass(frozen=True)
class BackgroundDraftReportWriteResult:
    """Paths and manifest for persisted conservative draft reports."""

    output_dir: Path
    manifest_path: Path
    markdown_paths: tuple[Path, ...]
    manifest: dict[str, object]


@dataclass(frozen=True)
class CandidateExtractionHandoffRecord:
    """One local-only handoff from background target selection to extraction work."""

    handoff_id: str
    target_id: str
    track: Track
    source_id: str
    extraction_status: str
    execution_mode: str
    ledger_run_id: str
    reviewed_workflow_status: str
    required_inputs: tuple[str, ...]
    available_inputs: tuple[str, ...]
    expected_candidate_packet_ids: tuple[str, ...]
    candidate_fixture_path: str | None
    blocking_issues: tuple[str, ...]
    negative_result_required: bool
    requires_human_review: bool
    network_access_allowed: bool


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


def default_background_reviewed_log_path() -> Path:
    """Return the repository-local reviewed background outcome fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "background_reviewed_log.json"
    )


def default_background_needs_follow_up_log_path() -> Path:
    """Return the repository-local needs-follow-up background fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "background_needs_follow_up_log.json"
    )


def default_background_follow_up_tests_path() -> Path:
    """Return the repository-local background follow-up test fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "background_follow_up_tests.json"
    )


def default_background_report_readiness_path() -> Path:
    """Return the repository-local background report-readiness fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "background_report_readiness.json"
    )


def default_background_draft_reports_path() -> Path:
    """Return the repository-local background draft follow-up report fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "background_draft_follow_up_reports.json"
    )


def default_background_user_decisions_path() -> Path:
    """Return the repository-local background user decision fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "background_user_decisions.json"
    )


def default_candidate_extraction_handoff_path() -> Path:
    """Return the repository-local candidate extraction handoff fixture path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "candidate_extraction_handoffs.json"
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
        never_reviewed_target_boost=float(
            data.get("never_reviewed_target_boost", DEFAULT_NEVER_REVIEWED_TARGET_BOOST)
        ),
        prior_review_penalty_per_entry=float(
            data.get(
                "prior_review_penalty_per_entry",
                DEFAULT_PRIOR_REVIEW_PENALTY_PER_ENTRY,
            )
        ),
        max_prior_review_penalty=float(
            data.get("max_prior_review_penalty", DEFAULT_MAX_PRIOR_REVIEW_PENALTY)
        ),
        needs_follow_up_priority_threshold=float(
            data.get(
                "needs_follow_up_priority_threshold",
                DEFAULT_NEEDS_FOLLOW_UP_PRIORITY_THRESHOLD,
            )
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


def load_candidate_extraction_handoffs(
    path: Path | None = None,
) -> tuple[CandidateExtractionHandoffRecord, ...]:
    """Load local-only candidate extraction handoff records."""

    handoff_path = path or default_candidate_extraction_handoff_path()
    with handoff_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != CANDIDATE_EXTRACTION_HANDOFF_SCHEMA_VERSION:
        msg = (
            f"Unsupported candidate extraction handoff schema version "
            f"{schema_version!r}; expected "
            f"{CANDIDATE_EXTRACTION_HANDOFF_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(
        _candidate_extraction_handoff_from_mapping(record)
        for record in data["handoffs"]
    )


def load_background_reviewed_log(
    path: Path | None = None,
) -> tuple[BackgroundReviewedLogEntry, ...]:
    """Load reviewed background outcome records."""

    reviewed_path = path or default_background_reviewed_log_path()
    with reviewed_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != BACKGROUND_REVIEWED_LOG_SCHEMA_VERSION:
        msg = (
            f"Unsupported background reviewed log schema version "
            f"{schema_version!r}; expected {BACKGROUND_REVIEWED_LOG_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(
        _reviewed_log_entry_from_mapping(entry)
        for entry in data["reviewed_entries"]
    )


def load_background_needs_follow_up_log(
    path: Path | None = None,
) -> tuple[BackgroundNeedsFollowUpEntry, ...]:
    """Load needs-follow-up background outcome records."""

    follow_up_path = path or default_background_needs_follow_up_log_path()
    with follow_up_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != BACKGROUND_NEEDS_FOLLOW_UP_SCHEMA_VERSION:
        msg = (
            f"Unsupported background needs-follow-up log schema version "
            f"{schema_version!r}; expected "
            f"{BACKGROUND_NEEDS_FOLLOW_UP_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(
        _needs_follow_up_entry_from_mapping(entry)
        for entry in data["needs_follow_up_entries"]
    )


def load_background_follow_up_tests(
    path: Path | None = None,
) -> tuple[BackgroundFollowUpTestResult, ...]:
    """Load deterministic local follow-up test results."""

    tests_path = path or default_background_follow_up_tests_path()
    with tests_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != BACKGROUND_FOLLOW_UP_TEST_SCHEMA_VERSION:
        msg = (
            f"Unsupported background follow-up test schema version "
            f"{schema_version!r}; expected {BACKGROUND_FOLLOW_UP_TEST_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(
        _follow_up_test_result_from_mapping(record)
        for record in data["test_results"]
    )


def load_background_report_readiness(
    path: Path | None = None,
) -> tuple[BackgroundReportReadinessRecord, ...]:
    """Load background report-readiness records."""

    readiness_path = path or default_background_report_readiness_path()
    with readiness_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != BACKGROUND_REPORT_READINESS_SCHEMA_VERSION:
        msg = (
            f"Unsupported background report-readiness schema version "
            f"{schema_version!r}; expected {BACKGROUND_REPORT_READINESS_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(
        _report_readiness_record_from_mapping(record)
        for record in data["readiness_records"]
    )


def load_background_draft_reports(
    path: Path | None = None,
) -> tuple[BackgroundDraftFollowUpReport, ...]:
    """Load conservative draft follow-up report records."""

    draft_path = path or default_background_draft_reports_path()
    with draft_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != BACKGROUND_DRAFT_REPORT_SCHEMA_VERSION:
        msg = (
            f"Unsupported background draft report schema version "
            f"{schema_version!r}; expected {BACKGROUND_DRAFT_REPORT_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(
        _draft_follow_up_report_from_mapping(record)
        for record in data["draft_reports"]
    )


def load_background_user_decisions(
    path: Path | None = None,
) -> tuple[BackgroundUserDecisionRecord, ...]:
    """Load explicit user decision records for background follow-up reports."""

    decisions_path = path or default_background_user_decisions_path()
    with decisions_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    schema_version = str(data.get("schema_version", ""))
    if schema_version != BACKGROUND_USER_DECISION_SCHEMA_VERSION:
        msg = (
            f"Unsupported background user decision schema version "
            f"{schema_version!r}; expected {BACKGROUND_USER_DECISION_SCHEMA_VERSION!r}"
        )
        raise ValueError(msg)

    return tuple(
        _user_decision_record_from_mapping(record) for record in data["decisions"]
    )


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


def target_selection_score(
    target: BackgroundTarget,
    *,
    config: BackgroundPriorityConfig | None = None,
    prior_review_count: int = 0,
) -> float:
    """Compute scheduler-oriented target score with review-history adjustments."""

    active_config = config or load_background_priority_config()
    score = target_priority_score(target, config=active_config)
    if prior_review_count == 0:
        score += active_config.never_reviewed_target_boost
    else:
        score -= min(
            active_config.max_prior_review_penalty,
            active_config.prior_review_penalty_per_entry * prior_review_count,
        )
    return round(score, 6)


def target_priority_summary(
    path: Path | None = None,
    config_path: Path | None = None,
    ledger_path: Path | None = None,
) -> dict[str, object]:
    """Summarize background target-priority fixture coverage."""

    target_path = path or default_background_targets_path()
    resolved_config_path = config_path or default_background_priority_config_path()
    config = load_background_priority_config(resolved_config_path)
    targets = load_background_targets(target_path)
    prior_review_counts: Counter[str] = Counter()
    if ledger_path is not None:
        prior_review_counts.update(
            entry.target_id for entry in load_background_search_ledger(ledger_path)
        )
    scored_targets = [
        {
            "target_id": target.target_id,
            "track": target.track.value,
            "source_id": target.source_id,
            "priority_score": target_priority_score(target, config=config),
            "prior_review_count": prior_review_counts[target.target_id],
            "selection_score": target_selection_score(
                target,
                config=config,
                prior_review_count=prior_review_counts[target.target_id],
            ),
            "blocking_issue_count": target.blocking_issue_count,
        }
        for target in targets
    ]
    ranked = sorted(
        scored_targets,
        key=lambda item: (-float(item["selection_score"]), str(item["target_id"])),
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
        "never_reviewed_target_boost": config.never_reviewed_target_boost,
        "prior_review_penalty_per_entry": config.prior_review_penalty_per_entry,
        "max_prior_review_penalty": config.max_prior_review_penalty,
        "needs_follow_up_priority_threshold": (
            config.needs_follow_up_priority_threshold
        ),
        "passive_runner_requires_opt_in": config.passive_runner_requires_opt_in,
        "network_access_enabled": config.network_access_enabled,
        "selected_target_id": selected["target_id"] if selected else None,
        "selected_priority_score": selected["priority_score"] if selected else None,
        "selected_selection_score": selected["selection_score"] if selected else None,
        "ledger_path": str(ledger_path) if ledger_path is not None else None,
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


def candidate_extraction_handoff_summary(
    path: Path | None = None,
) -> dict[str, object]:
    """Summarize local-only candidate extraction handoff readiness."""

    handoff_path = path or default_candidate_extraction_handoff_path()
    records = load_candidate_extraction_handoffs(handoff_path)
    expected_candidate_ids = [
        candidate_id
        for record in records
        for candidate_id in record.expected_candidate_packet_ids
    ]
    blocking_issues = [
        issue for record in records for issue in record.blocking_issues
    ]
    required_inputs = [
        item for record in records for item in record.required_inputs
    ]
    available_inputs = [
        item for record in records for item in record.available_inputs
    ]

    return {
        "handoff_path": str(handoff_path),
        "schema_version": CANDIDATE_EXTRACTION_HANDOFF_SCHEMA_VERSION,
        "disclaimer": CANDIDATE_EXTRACTION_HANDOFF_DISCLAIMER,
        "record_count": len(records),
        "ready_count": sum(
            1 for record in records if record.extraction_status == "ready_for_extraction"
        ),
        "blocked_count": sum(
            1 for record in records if record.extraction_status == "blocked"
        ),
        "no_candidate_expected_count": sum(
            1
            for record in records
            if record.extraction_status == "no_candidate_expected"
        ),
        "scheduling_only_count": sum(
            1
            for record in records
            if record.extraction_status == "scheduling_only"
        ),
        "expected_candidate_packet_count": len(expected_candidate_ids),
        "candidate_fixture_count": sum(
            1 for record in records if record.candidate_fixture_path is not None
        ),
        "blocking_issue_count": len(blocking_issues),
        "negative_result_required_count": sum(
            1 for record in records if record.negative_result_required
        ),
        "requires_human_review_count": sum(
            1 for record in records if record.requires_human_review
        ),
        "network_access_allowed_count": sum(
            1 for record in records if record.network_access_allowed
        ),
        "required_input_count": len(required_inputs),
        "available_input_count": len(available_inputs),
        "by_track": _counter_to_dict(Counter(record.track.value for record in records)),
        "by_extraction_status": _counter_to_dict(
            Counter(record.extraction_status for record in records)
        ),
        "by_reviewed_workflow_status": _counter_to_dict(
            Counter(record.reviewed_workflow_status for record in records)
        ),
        "handoff_ids": sorted(record.handoff_id for record in records),
        "target_ids": sorted({record.target_id for record in records}),
        "expected_candidate_packet_ids": sorted(expected_candidate_ids),
    }


def background_reviewed_log_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize reviewed background outcome records."""

    reviewed_path = path or default_background_reviewed_log_path()
    entries = load_background_reviewed_log(reviewed_path)
    reason_codes = [code for entry in entries for code in entry.reason_codes]
    negative_evidence = [
        evidence for entry in entries for evidence in entry.negative_evidence
    ]
    blocking_issues = [issue for entry in entries for issue in entry.blocking_issues]

    return {
        "reviewed_log_path": str(reviewed_path),
        "schema_version": BACKGROUND_REVIEWED_LOG_SCHEMA_VERSION,
        "disclaimer": BACKGROUND_REVIEWED_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "negative_evidence_count": len(negative_evidence),
        "blocking_issue_count": len(blocking_issues),
        "network_access_allowed_count": sum(
            1 for entry in entries if entry.network_access_allowed
        ),
        "by_track": _counter_to_dict(Counter(entry.track.value for entry in entries)),
        "by_outcome_status": _counter_to_dict(
            Counter(entry.outcome_status for entry in entries)
        ),
        "by_recommended_next_action": _counter_to_dict(
            Counter(entry.recommended_next_action for entry in entries)
        ),
        "reason_codes": sorted(set(reason_codes)),
        "run_ids": sorted(entry.run_id for entry in entries),
        "target_ids": sorted({entry.target_id for entry in entries}),
    }


def background_needs_follow_up_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize needs-follow-up background outcome records."""

    follow_up_path = path or default_background_needs_follow_up_log_path()
    entries = load_background_needs_follow_up_log(follow_up_path)
    reason_codes = [code for entry in entries for code in entry.reason_codes]
    trigger_types = [kind for entry in entries for kind in entry.trigger_types]
    required_tests = [test for entry in entries for test in entry.required_tests]
    blocking_issues = [issue for entry in entries for issue in entry.blocking_issues]

    return {
        "needs_follow_up_log_path": str(follow_up_path),
        "schema_version": BACKGROUND_NEEDS_FOLLOW_UP_SCHEMA_VERSION,
        "disclaimer": BACKGROUND_NEEDS_FOLLOW_UP_DISCLAIMER,
        "entry_count": len(entries),
        "required_test_count": len(required_tests),
        "mandatory_test_coverage_count": len(set(required_tests)),
        "blocking_issue_count": len(blocking_issues),
        "report_required_count": sum(1 for entry in entries if entry.report_required),
        "human_review_required_count": sum(
            1 for entry in entries if entry.human_review_required
        ),
        "submission_requires_user_approval_count": sum(
            1 for entry in entries if entry.submission_requires_user_approval
        ),
        "network_access_allowed_count": sum(
            1 for entry in entries if entry.network_access_allowed
        ),
        "by_track": _counter_to_dict(Counter(entry.track.value for entry in entries)),
        "by_follow_up_status": _counter_to_dict(
            Counter(entry.follow_up_status for entry in entries)
        ),
        "by_trigger_type": _counter_to_dict(Counter(trigger_types)),
        "reason_codes": sorted(set(reason_codes)),
        "required_tests": sorted(set(required_tests)),
        "run_ids": sorted(entry.run_id for entry in entries),
        "target_ids": sorted({entry.target_id for entry in entries}),
    }


def background_follow_up_test_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize deterministic local follow-up test results."""

    tests_path = path or default_background_follow_up_tests_path()
    records = load_background_follow_up_tests(tests_path)
    evidence = [item for record in records for item in record.evidence]
    negative_evidence = [
        item for record in records for item in record.negative_evidence
    ]
    blocking_issues = [issue for record in records for issue in record.blocking_issues]
    uncertainty_notes = [
        note for record in records for note in record.uncertainty_notes
    ]
    mandatory_by_follow_up = {
        follow_up_id: {
            record.test_name
            for record in records
            if record.follow_up_id == follow_up_id
        }
        for follow_up_id in {record.follow_up_id for record in records}
    }
    complete_follow_up_ids = sorted(
        follow_up_id
        for follow_up_id, test_names in mandatory_by_follow_up.items()
        if set(MANDATORY_FOLLOW_UP_TESTS) <= test_names
    )

    return {
        "follow_up_tests_path": str(tests_path),
        "schema_version": BACKGROUND_FOLLOW_UP_TEST_SCHEMA_VERSION,
        "disclaimer": BACKGROUND_FOLLOW_UP_TEST_DISCLAIMER,
        "result_count": len(records),
        "follow_up_count": len(mandatory_by_follow_up),
        "complete_follow_up_test_set_count": len(complete_follow_up_ids),
        "mandatory_test_count": len(MANDATORY_FOLLOW_UP_TESTS),
        "evidence_count": len(evidence),
        "negative_evidence_count": len(negative_evidence),
        "blocking_issue_count": len(blocking_issues),
        "uncertainty_note_count": len(uncertainty_notes),
        "network_access_allowed_count": sum(
            1 for record in records if record.network_access_allowed
        ),
        "by_track": _counter_to_dict(Counter(record.track.value for record in records)),
        "by_test_name": _counter_to_dict(Counter(record.test_name for record in records)),
        "by_status": _counter_to_dict(Counter(record.status for record in records)),
        "complete_follow_up_ids": complete_follow_up_ids,
        "follow_up_ids": sorted(mandatory_by_follow_up),
        "target_ids": sorted({record.target_id for record in records}),
        "required_tests": sorted(MANDATORY_FOLLOW_UP_TESTS),
    }


def background_report_readiness_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize report-readiness gates and submission recommendations."""

    readiness_path = path or default_background_report_readiness_path()
    records = load_background_report_readiness(readiness_path)
    recommendations = [
        recommendation
        for record in records
        for recommendation in record.top_three_recommendations
    ]
    blocking_issues = [issue for record in records for issue in record.blocking_issues]
    limitations = [item for record in records for item in record.limitations]

    return {
        "report_readiness_path": str(readiness_path),
        "schema_version": BACKGROUND_REPORT_READINESS_SCHEMA_VERSION,
        "disclaimer": BACKGROUND_REPORT_READINESS_DISCLAIMER,
        "record_count": len(records),
        "ready_to_draft_report_count": sum(
            1 for record in records if record.ready_to_draft_report
        ),
        "blocked_count": sum(
            1
            for record in records
            if record.readiness_status == "blocked_pending_tests"
        ),
        "report_required_count": sum(1 for record in records if record.report_required),
        "user_approval_required_count": sum(
            1 for record in records if record.user_approval_required
        ),
        "external_submission_allowed_count": sum(
            1 for record in records if record.external_submission_allowed
        ),
        "network_access_allowed_count": sum(
            1 for record in records if record.network_access_allowed
        ),
        "top_three_recommendation_count": len(recommendations),
        "blocking_issue_count": len(blocking_issues),
        "limitation_count": len(limitations),
        "by_track": _counter_to_dict(Counter(record.track.value for record in records)),
        "by_readiness_status": _counter_to_dict(
            Counter(record.readiness_status for record in records)
        ),
        "by_recommended_action": _counter_to_dict(
            Counter(record.recommended_action for record in records)
        ),
        "by_destination_action": _counter_to_dict(
            Counter(recommendation.recommended_action for recommendation in recommendations)
        ),
        "readiness_ids": sorted(record.readiness_id for record in records),
        "follow_up_ids": sorted(record.follow_up_id for record in records),
        "target_ids": sorted({record.target_id for record in records}),
    }


def draft_follow_up_reports_from_readiness(
    path: Path | None = None,
) -> tuple[BackgroundDraftFollowUpReport, ...]:
    """Create conservative draft report summaries from report-readiness records."""

    records = load_background_report_readiness(path)
    return tuple(_draft_report_from_readiness(record) for record in records)


def background_draft_follow_up_report_summary(
    path: Path | None = None,
    *,
    from_readiness: bool = False,
) -> dict[str, object]:
    """Summarize conservative draft follow-up report records."""

    if from_readiness:
        source_path = path or default_background_report_readiness_path()
        records = draft_follow_up_reports_from_readiness(source_path)
        source_key = "report_readiness_path"
    else:
        source_path = path or default_background_draft_reports_path()
        records = load_background_draft_reports(source_path)
        source_key = "draft_report_path"
    blocking_issues = [issue for record in records for issue in record.blocking_issues]
    negative_evidence = [
        evidence for record in records for evidence in record.negative_evidence
    ]
    limitations = [
        item for record in records for item in record.uncertainty_and_limitations
    ]
    next_steps = [step for record in records for step in record.recommended_next_steps]

    return {
        source_key: str(source_path),
        "schema_version": BACKGROUND_DRAFT_REPORT_SCHEMA_VERSION,
        "disclaimer": BACKGROUND_DRAFT_REPORT_DISCLAIMER,
        "draft_report_count": len(records),
        "draft_ready_count": sum(
            1 for record in records if record.draft_status == "draft_ready"
        ),
        "blocked_count": sum(
            1 for record in records if record.draft_status == "blocked_not_ready"
        ),
        "negative_evidence_count": len(negative_evidence),
        "limitation_count": len(limitations),
        "blocking_issue_count": len(blocking_issues),
        "recommended_next_step_count": len(next_steps),
        "user_approval_required_count": sum(
            1 for record in records if record.user_approval_required
        ),
        "external_submission_allowed_count": sum(
            1 for record in records if record.external_submission_allowed
        ),
        "network_access_allowed_count": sum(
            1 for record in records if record.network_access_allowed
        ),
        "by_track": _counter_to_dict(Counter(record.track.value for record in records)),
        "by_draft_status": _counter_to_dict(
            Counter(record.draft_status for record in records)
        ),
        "draft_ids": sorted(record.draft_id for record in records),
        "readiness_ids": sorted(record.readiness_id for record in records),
        "target_ids": sorted({record.target_id for record in records}),
    }


def write_background_draft_follow_up_reports(
    output_dir: Path,
    readiness_path: Path | None = None,
) -> BackgroundDraftReportWriteResult:
    """Persist conservative draft follow-up reports as Markdown plus manifest."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    source_path = readiness_path or default_background_report_readiness_path()
    records = draft_follow_up_reports_from_readiness(source_path)
    markdown_paths: list[Path] = []
    manifest_entries: list[dict[str, object]] = []
    generated_at = datetime.now(UTC).isoformat()
    for record in records:
        markdown_path = destination / f"{_safe_filename(record.draft_id)}.md"
        markdown_path.write_text(_draft_report_markdown(record), encoding="utf-8")
        markdown_paths.append(markdown_path)
        manifest_entries.append(
            {
                "draft_id": record.draft_id,
                "readiness_id": record.readiness_id,
                "follow_up_id": record.follow_up_id,
                "run_id": record.run_id,
                "target_id": record.target_id,
                "track": record.track.value,
                "draft_status": record.draft_status,
                "markdown_path": str(markdown_path),
                "user_approval_required": record.user_approval_required,
                "external_submission_allowed": record.external_submission_allowed,
                "network_access_allowed": record.network_access_allowed,
                "blocking_issue_count": len(record.blocking_issues),
                "negative_evidence_count": len(record.negative_evidence),
                "limitation_count": len(record.uncertainty_and_limitations),
            }
        )
    manifest = {
        "schema_version": BACKGROUND_DRAFT_REPORT_MANIFEST_SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "source_readiness_path": str(source_path),
        "output_dir": str(destination),
        "draft_report_count": len(records),
        "disclaimer": BACKGROUND_DRAFT_REPORT_DISCLAIMER,
        "reports": manifest_entries,
    }
    manifest_path = destination / "background_draft_report_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return BackgroundDraftReportWriteResult(
        output_dir=destination,
        manifest_path=manifest_path,
        markdown_paths=tuple(markdown_paths),
        manifest=manifest,
    )


def background_user_decision_summary(path: Path | None = None) -> dict[str, object]:
    """Summarize explicit user decision records."""

    decisions_path = path or default_background_user_decisions_path()
    records = load_background_user_decisions(decisions_path)
    blocking_issues = [issue for record in records for issue in record.blocking_issues]
    next_actions = [action for record in records for action in record.required_next_actions]

    return {
        "user_decision_path": str(decisions_path),
        "schema_version": BACKGROUND_USER_DECISION_SCHEMA_VERSION,
        "disclaimer": BACKGROUND_USER_DECISION_DISCLAIMER,
        "decision_count": len(records),
        "external_submission_approved_count": sum(
            1 for record in records if record.external_submission_approved
        ),
        "request_more_tests_count": sum(
            1 for record in records if record.request_more_tests
        ),
        "close_as_reviewed_count": sum(
            1 for record in records if record.close_as_reviewed
        ),
        "blocking_issue_count": len(blocking_issues),
        "required_next_action_count": len(next_actions),
        "network_access_allowed_count": sum(
            1 for record in records if record.network_access_allowed
        ),
        "by_track": _counter_to_dict(Counter(record.track.value for record in records)),
        "by_decision": _counter_to_dict(Counter(record.decision for record in records)),
        "decision_ids": sorted(record.decision_id for record in records),
        "readiness_ids": sorted(record.readiness_id for record in records),
        "target_ids": sorted({record.target_id for record in records}),
    }


def append_background_user_decision_record(
    path: Path,
    record: BackgroundUserDecisionRecord,
) -> dict[str, object]:
    """Append one explicit user decision record, creating the file if needed."""

    if record.decision == "approve_submission":
        if not record.external_submission_approved:
            msg = "approve_submission requires explicit external submission approval."
            raise ValueError(msg)
        if not record.submission_destination:
            msg = "approve_submission requires a submission destination."
            raise ValueError(msg)
        if not record.rationale:
            msg = "approve_submission requires a rationale."
            raise ValueError(msg)
    elif record.external_submission_approved:
        msg = (
            "Only approve_submission decisions may set external submission "
            "approval."
        )
        raise ValueError(msg)

    decision_path = Path(path)
    if decision_path.exists():
        with decision_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        schema_version = str(data.get("schema_version", ""))
        if schema_version != BACKGROUND_USER_DECISION_SCHEMA_VERSION:
            msg = (
                f"Unsupported background user decision schema version "
                f"{schema_version!r}; expected "
                f"{BACKGROUND_USER_DECISION_SCHEMA_VERSION!r}"
            )
            raise ValueError(msg)
        decisions = list(data.get("decisions", []))
    else:
        data = {
            "schema_version": BACKGROUND_USER_DECISION_SCHEMA_VERSION,
            "description": (
                "Explicit user decision records for conservative background "
                "follow-up reports."
            ),
            "disclaimer": BACKGROUND_USER_DECISION_DISCLAIMER,
        }
        decisions = []

    decisions.append(_user_decision_record_to_mapping(record))
    data["decisions"] = decisions
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "appended_decision": _user_decision_record_to_mapping(record),
        "summary": background_user_decision_summary(decision_path),
    }


def scheduler_dry_run(
    artifact_dir: Path,
    *,
    run_id: str = "scheduler-dry-run",
    code_commit: str = "dry-run",
    sqlite_log_path: Path | None = None,
) -> dict[str, object]:
    """Run the local background scheduler path against temporary artifacts."""

    destination = Path(artifact_dir)
    ledger_path = destination / "background_search_ledger.json"
    reviewed_log_path = destination / "background_reviewed_log.json"
    needs_follow_up_log_path = destination / "background_needs_follow_up_log.json"
    resolved_sqlite_log_path = sqlite_log_path or destination / "background_logs.sqlite3"
    result = run_local_background_search_once(
        ledger_path,
        reviewed_log_path=reviewed_log_path,
        needs_follow_up_log_path=needs_follow_up_log_path,
        sqlite_log_path=resolved_sqlite_log_path,
        run_id=run_id,
        code_commit=code_commit,
        opt_in=True,
    )
    return {
        "ok": bool(result["ok"]),
        "artifact_dir": str(destination),
        "ledger_path": str(ledger_path),
        "reviewed_log_path": str(reviewed_log_path),
        "needs_follow_up_log_path": str(needs_follow_up_log_path),
        "sqlite_log_path": str(resolved_sqlite_log_path),
        "network_access_enabled": False,
        "external_submission_allowed": False,
        "result": result,
    }


def run_local_background_search_once(
    ledger_path: Path,
    reviewed_log_path: Path | None = None,
    needs_follow_up_log_path: Path | None = None,
    sqlite_log_path: Path | None = None,
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

    existing_entries = (
        load_background_search_ledger(ledger_path) if Path(ledger_path).exists() else ()
    )
    prior_review_counts = Counter(entry.target_id for entry in existing_entries)
    selected = sorted(
        targets,
        key=lambda target: (
            -target_selection_score(
                target,
                config=config,
                prior_review_count=prior_review_counts[target.target_id],
            ),
            target.target_id,
        ),
    )[0]
    priority_score = target_priority_score(selected, config=config)
    selection_score = target_selection_score(
        selected,
        config=config,
        prior_review_count=prior_review_counts[selected.target_id],
    )
    timestamp = datetime.now(UTC).isoformat()
    needs_follow_up = _target_requires_follow_up(
        selected,
        selection_score=selection_score,
        config=config,
    )
    status = (
        "needs_follow_up_logged"
        if needs_follow_up
        else BACKGROUND_REVIEWED_NO_FOLLOW_UP_STATUS
    )
    reviewed_status = (
        BACKGROUND_NEEDS_FOLLOW_UP_STATUS
        if needs_follow_up
        else BACKGROUND_REVIEWED_NO_FOLLOW_UP_STATUS
    )
    recommended_pathways = (
        ("human_review_queue", "local_follow_up_tests")
        if needs_follow_up
        else (config.local_runner_pathway,)
    )
    blocking_issues = (
        _follow_up_blocking_issues(selected)
        if needs_follow_up
        else (
            "local fixture runner found no follow-up trigger under current thresholds",
        )
    )
    entry = BackgroundSearchLedgerEntry(
        run_id=run_id or _run_id_from_timestamp(timestamp),
        target_id=selected.target_id,
        track=selected.track,
        status=status,
        query_parameters={
            "mode": LOCAL_BACKGROUND_EXECUTION_MODE,
            "target_path": str(resolved_target_path),
            "config_path": str(resolved_config_path),
            "selected_priority_score": priority_score,
            "selected_selection_score": selection_score,
            "prior_review_count": prior_review_counts[selected.target_id],
            "outcome_log_mode": "reviewed_or_needs_follow_up",
        },
        started_at_utc=timestamp,
        completed_at_utc=timestamp,
        config_version=config.config_version,
        code_commit=code_commit,
        cache_key=f"local-fixture-{selected.target_id}-{config.config_version}",
        candidate_count=0,
        recommended_pathways=recommended_pathways,
        blocking_issues=blocking_issues,
        execution_mode=LOCAL_BACKGROUND_EXECUTION_MODE,
        selected_priority_score=priority_score,
        target_selection_rationale=(
            "highest configured scheduler selection score",
            "false-positive probability and blocking issues penalized",
            "never-reviewed targets receive an explicit scheduling boost",
            "previously reviewed targets receive a bounded review-history penalty",
            "local fixture runner does not query live providers",
        ),
        candidate_packet_ids=(),
        negative_result_logged=not needs_follow_up,
        requires_human_review=needs_follow_up,
        reviewed_workflow_status=reviewed_status,
    )
    append_background_search_ledger_entry(ledger_path, entry)
    resolved_reviewed_log_path = reviewed_log_path or Path(ledger_path).with_name(
        "background_reviewed_log.json"
    )
    resolved_follow_up_log_path = needs_follow_up_log_path or Path(ledger_path).with_name(
        "background_needs_follow_up_log.json"
    )
    if needs_follow_up:
        needs_follow_up_entry = _needs_follow_up_entry_from_run(entry, selected, config)
        append_background_needs_follow_up_entry(
            resolved_follow_up_log_path,
            needs_follow_up_entry,
        )
        if sqlite_log_path is not None:
            _append_background_run_sqlite_log(
                sqlite_log_path,
                entry=entry,
                outcome_kind="needs_follow_up",
                outcome_entry=needs_follow_up_entry,
            )
        outcome_log = {
            "outcome": "needs_follow_up",
            "path": str(resolved_follow_up_log_path),
            "summary": background_needs_follow_up_summary(resolved_follow_up_log_path),
        }
    else:
        reviewed_entry = _reviewed_log_entry_from_run(entry)
        append_background_reviewed_log_entry(
            resolved_reviewed_log_path,
            reviewed_entry,
        )
        if sqlite_log_path is not None:
            _append_background_run_sqlite_log(
                sqlite_log_path,
                entry=entry,
                outcome_kind="reviewed",
                outcome_entry=reviewed_entry,
            )
        outcome_log = {
            "outcome": "reviewed",
            "path": str(resolved_reviewed_log_path),
            "summary": background_reviewed_log_summary(resolved_reviewed_log_path),
        }
    return {
        "ok": True,
        "appended_entry": _ledger_entry_to_mapping(entry),
        "sqlite_log_path": str(sqlite_log_path) if sqlite_log_path is not None else None,
        "ledger_summary": background_search_ledger_summary(ledger_path),
        "review_workflow_summary": background_review_workflow_summary(ledger_path),
        "outcome_log": outcome_log,
    }


def _append_background_run_sqlite_log(
    sqlite_log_path: Path,
    *,
    entry: BackgroundSearchLedgerEntry,
    outcome_kind: str,
    outcome_entry: BackgroundReviewedLogEntry | BackgroundNeedsFollowUpEntry,
) -> None:
    """Mirror one local background run into the top-level SQLite log store."""

    from techno_search.log_store import append_background_run_to_sqlite

    if isinstance(outcome_entry, BackgroundReviewedLogEntry):
        outcome_mapping = _reviewed_log_entry_to_mapping(outcome_entry)
    else:
        outcome_mapping = _needs_follow_up_entry_to_mapping(outcome_entry)
    append_background_run_to_sqlite(
        sqlite_log_path,
        ledger_entry=_ledger_entry_to_mapping(entry),
        outcome_kind=outcome_kind,
        outcome_entry=outcome_mapping,
    )


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


def append_background_reviewed_log_entry(
    path: Path,
    entry: BackgroundReviewedLogEntry,
) -> None:
    """Append one reviewed outcome entry, creating the log if needed."""

    reviewed_path = Path(path)
    if reviewed_path.exists():
        with reviewed_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        schema_version = str(data.get("schema_version", ""))
        if schema_version != BACKGROUND_REVIEWED_LOG_SCHEMA_VERSION:
            msg = (
                f"Unsupported background reviewed log schema version "
                f"{schema_version!r}; expected {BACKGROUND_REVIEWED_LOG_SCHEMA_VERSION!r}"
            )
            raise ValueError(msg)
        entries = list(data.get("reviewed_entries", []))
    else:
        data = {
            "schema_version": BACKGROUND_REVIEWED_LOG_SCHEMA_VERSION,
            "description": (
                "Reviewed local background-search outcomes that do not currently "
                "require follow-up."
            ),
            "disclaimer": BACKGROUND_REVIEWED_LOG_DISCLAIMER,
        }
        entries = []

    entries.append(_reviewed_log_entry_to_mapping(entry))
    data["reviewed_entries"] = entries
    reviewed_path.parent.mkdir(parents=True, exist_ok=True)
    reviewed_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def append_background_needs_follow_up_entry(
    path: Path,
    entry: BackgroundNeedsFollowUpEntry,
) -> None:
    """Append one needs-follow-up outcome entry, creating the log if needed."""

    follow_up_path = Path(path)
    if follow_up_path.exists():
        with follow_up_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        schema_version = str(data.get("schema_version", ""))
        if schema_version != BACKGROUND_NEEDS_FOLLOW_UP_SCHEMA_VERSION:
            msg = (
                f"Unsupported background needs-follow-up log schema version "
                f"{schema_version!r}; expected "
                f"{BACKGROUND_NEEDS_FOLLOW_UP_SCHEMA_VERSION!r}"
            )
            raise ValueError(msg)
        entries = list(data.get("needs_follow_up_entries", []))
    else:
        data = {
            "schema_version": BACKGROUND_NEEDS_FOLLOW_UP_SCHEMA_VERSION,
            "description": (
                "Local background-search outcomes requiring follow-up tests or "
                "human review."
            ),
            "disclaimer": BACKGROUND_NEEDS_FOLLOW_UP_DISCLAIMER,
        }
        entries = []

    entries.append(_needs_follow_up_entry_to_mapping(entry))
    data["needs_follow_up_entries"] = entries
    follow_up_path.parent.mkdir(parents=True, exist_ok=True)
    follow_up_path.write_text(
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


def _candidate_extraction_handoff_from_mapping(
    data: dict[str, Any],
) -> CandidateExtractionHandoffRecord:
    return CandidateExtractionHandoffRecord(
        handoff_id=str(data["handoff_id"]),
        target_id=str(data["target_id"]),
        track=Track(str(data["track"])),
        source_id=str(data["source_id"]),
        extraction_status=str(data["extraction_status"]),
        execution_mode=str(data["execution_mode"]),
        ledger_run_id=str(data["ledger_run_id"]),
        reviewed_workflow_status=str(data["reviewed_workflow_status"]),
        required_inputs=tuple(str(item) for item in data.get("required_inputs", ())),
        available_inputs=tuple(str(item) for item in data.get("available_inputs", ())),
        expected_candidate_packet_ids=tuple(
            str(item) for item in data.get("expected_candidate_packet_ids", ())
        ),
        candidate_fixture_path=_optional_string(data.get("candidate_fixture_path")),
        blocking_issues=tuple(str(item) for item in data.get("blocking_issues", ())),
        negative_result_required=bool(data["negative_result_required"]),
        requires_human_review=bool(data["requires_human_review"]),
        network_access_allowed=bool(data["network_access_allowed"]),
    )


def _reviewed_log_entry_from_mapping(
    data: dict[str, Any],
) -> BackgroundReviewedLogEntry:
    return BackgroundReviewedLogEntry(
        review_id=str(data["review_id"]),
        run_id=str(data["run_id"]),
        target_id=str(data["target_id"]),
        track=Track(str(data["track"])),
        outcome_status=str(data["outcome_status"]),
        reviewed_at_utc=str(data["reviewed_at_utc"]),
        reason_codes=tuple(str(item) for item in data.get("reason_codes", ())),
        negative_evidence=tuple(
            str(item) for item in data.get("negative_evidence", ())
        ),
        blocking_issues=tuple(str(item) for item in data.get("blocking_issues", ())),
        recommended_next_action=str(data["recommended_next_action"]),
        network_access_allowed=bool(data["network_access_allowed"]),
    )


def _needs_follow_up_entry_from_mapping(
    data: dict[str, Any],
) -> BackgroundNeedsFollowUpEntry:
    return BackgroundNeedsFollowUpEntry(
        follow_up_id=str(data["follow_up_id"]),
        run_id=str(data["run_id"]),
        target_id=str(data["target_id"]),
        track=Track(str(data["track"])),
        follow_up_status=str(data["follow_up_status"]),
        created_at_utc=str(data["created_at_utc"]),
        trigger_types=tuple(str(item) for item in data.get("trigger_types", ())),
        reason_codes=tuple(str(item) for item in data.get("reason_codes", ())),
        required_tests=tuple(str(item) for item in data.get("required_tests", ())),
        blocking_issues=tuple(str(item) for item in data.get("blocking_issues", ())),
        report_required=bool(data["report_required"]),
        human_review_required=bool(data["human_review_required"]),
        submission_requires_user_approval=bool(
            data["submission_requires_user_approval"]
        ),
        network_access_allowed=bool(data["network_access_allowed"]),
    )


def _follow_up_test_result_from_mapping(
    data: dict[str, Any],
) -> BackgroundFollowUpTestResult:
    return BackgroundFollowUpTestResult(
        result_id=str(data["result_id"]),
        follow_up_id=str(data["follow_up_id"]),
        run_id=str(data["run_id"]),
        target_id=str(data["target_id"]),
        track=Track(str(data["track"])),
        test_name=str(data["test_name"]),
        status=str(data["status"]),
        executed_at_utc=str(data["executed_at_utc"]),
        evidence=tuple(str(item) for item in data.get("evidence", ())),
        negative_evidence=tuple(
            str(item) for item in data.get("negative_evidence", ())
        ),
        blocking_issues=tuple(str(item) for item in data.get("blocking_issues", ())),
        uncertainty_notes=tuple(
            str(item) for item in data.get("uncertainty_notes", ())
        ),
        network_access_allowed=bool(data["network_access_allowed"]),
    )


def _submission_recommendation_from_mapping(
    data: dict[str, Any],
) -> SubmissionRecommendation:
    return SubmissionRecommendation(
        rank=int(data["rank"]),
        destination=str(data["destination"]),
        suitability_rationale=str(data["suitability_rationale"]),
        risks=tuple(str(item) for item in data.get("risks", ())),
        prerequisites=tuple(str(item) for item in data.get("prerequisites", ())),
        recommended_action=str(data["recommended_action"]),
    )


def _report_readiness_record_from_mapping(
    data: dict[str, Any],
) -> BackgroundReportReadinessRecord:
    return BackgroundReportReadinessRecord(
        readiness_id=str(data["readiness_id"]),
        follow_up_id=str(data["follow_up_id"]),
        run_id=str(data["run_id"]),
        target_id=str(data["target_id"]),
        track=Track(str(data["track"])),
        readiness_status=str(data["readiness_status"]),
        evaluated_at_utc=str(data["evaluated_at_utc"]),
        mandatory_tests_complete=bool(data["mandatory_tests_complete"]),
        ready_to_draft_report=bool(data["ready_to_draft_report"]),
        report_required=bool(data["report_required"]),
        user_approval_required=bool(data["user_approval_required"]),
        external_submission_allowed=bool(data["external_submission_allowed"]),
        recommended_action=str(data["recommended_action"]),
        blocking_issues=tuple(str(item) for item in data.get("blocking_issues", ())),
        limitations=tuple(str(item) for item in data.get("limitations", ())),
        top_three_recommendations=tuple(
            _submission_recommendation_from_mapping(item)
            for item in data.get("top_three_recommendations", ())
        ),
        network_access_allowed=bool(data["network_access_allowed"]),
    )


def _draft_follow_up_report_from_mapping(
    data: dict[str, Any],
) -> BackgroundDraftFollowUpReport:
    return BackgroundDraftFollowUpReport(
        draft_id=str(data["draft_id"]),
        readiness_id=str(data["readiness_id"]),
        follow_up_id=str(data["follow_up_id"]),
        run_id=str(data["run_id"]),
        target_id=str(data["target_id"]),
        track=Track(str(data["track"])),
        draft_status=str(data["draft_status"]),
        generated_at_utc=str(data["generated_at_utc"]),
        report_title=str(data["report_title"]),
        abstract=str(data["abstract"]),
        methodology_summary=str(data["methodology_summary"]),
        evidence_supporting_follow_up=tuple(
            str(item) for item in data.get("evidence_supporting_follow_up", ())
        ),
        negative_evidence=tuple(
            str(item) for item in data.get("negative_evidence", ())
        ),
        uncertainty_and_limitations=tuple(
            str(item) for item in data.get("uncertainty_and_limitations", ())
        ),
        blocking_issues=tuple(str(item) for item in data.get("blocking_issues", ())),
        recommended_next_steps=tuple(
            str(item) for item in data.get("recommended_next_steps", ())
        ),
        user_approval_required=bool(data["user_approval_required"]),
        external_submission_allowed=bool(data["external_submission_allowed"]),
        network_access_allowed=bool(data["network_access_allowed"]),
    )


def _user_decision_record_from_mapping(
    data: dict[str, Any],
) -> BackgroundUserDecisionRecord:
    return BackgroundUserDecisionRecord(
        decision_id=str(data["decision_id"]),
        readiness_id=str(data["readiness_id"]),
        follow_up_id=str(data["follow_up_id"]),
        target_id=str(data["target_id"]),
        track=Track(str(data["track"])),
        decision=str(data["decision"]),
        decided_at_utc=str(data["decided_at_utc"]),
        rationale=str(data["rationale"]),
        required_next_actions=tuple(
            str(item) for item in data.get("required_next_actions", ())
        ),
        external_submission_approved=bool(data["external_submission_approved"]),
        request_more_tests=bool(data["request_more_tests"]),
        close_as_reviewed=bool(data["close_as_reviewed"]),
        submission_destination=_optional_string(data.get("submission_destination")),
        blocking_issues=tuple(str(item) for item in data.get("blocking_issues", ())),
        network_access_allowed=bool(data["network_access_allowed"]),
    )


def _user_decision_record_to_mapping(
    record: BackgroundUserDecisionRecord,
) -> dict[str, object]:
    return {
        "decision_id": record.decision_id,
        "readiness_id": record.readiness_id,
        "follow_up_id": record.follow_up_id,
        "target_id": record.target_id,
        "track": record.track.value,
        "decision": record.decision,
        "decided_at_utc": record.decided_at_utc,
        "rationale": record.rationale,
        "required_next_actions": list(record.required_next_actions),
        "external_submission_approved": record.external_submission_approved,
        "request_more_tests": record.request_more_tests,
        "close_as_reviewed": record.close_as_reviewed,
        "submission_destination": record.submission_destination,
        "blocking_issues": list(record.blocking_issues),
        "network_access_allowed": record.network_access_allowed,
    }


def _draft_report_from_readiness(
    record: BackgroundReportReadinessRecord,
) -> BackgroundDraftFollowUpReport:
    ready = record.ready_to_draft_report and record.mandatory_tests_complete
    draft_status = "draft_ready" if ready else "blocked_not_ready"
    evidence: tuple[str, ...]
    next_steps: tuple[str, ...]
    if ready:
        title = f"Conservative follow-up report draft for {record.target_id}"
        abstract = (
            f"{record.target_id} is a local, fixture-backed follow-up target "
            "with completed mandatory checks. This draft preserves uncertainty "
            "and does not claim a confirmed technosignature."
        )
        next_steps = (
            "human reviewer inspects the draft report",
            "decide whether to request more tests or close as reviewed",
            "keep external submission disabled unless the user explicitly approves",
        )
        evidence = (
            "report-readiness gate is ready for draft preparation",
            "mandatory local follow-up tests are complete",
            "top-three conservative recommendations are available",
        )
    else:
        title = f"Blocked follow-up report note for {record.target_id}"
        abstract = (
            f"{record.target_id} is not ready for a follow-up report because "
            "mandatory local checks or review gates remain unresolved."
        )
        next_steps = (
            "resolve blocking issues before drafting a report",
            "repeat report-readiness review after more tests",
            "do not submit externally",
        )
        evidence = (
            "report-readiness gate requested more tests",
            "blocked tests or limitations remain visible",
        )
    negative_evidence = (
        "external submission is not allowed by the readiness gate",
        "no external validation has been recorded",
        "false positives remain the default hypothesis",
    )
    return BackgroundDraftFollowUpReport(
        draft_id=f"draft-{record.readiness_id}",
        readiness_id=record.readiness_id,
        follow_up_id=record.follow_up_id,
        run_id=record.run_id,
        target_id=record.target_id,
        track=record.track,
        draft_status=draft_status,
        generated_at_utc=record.evaluated_at_utc,
        report_title=title,
        abstract=abstract,
        methodology_summary=(
            "Summary generated from the background report-readiness fixture; "
            "it uses local records only and preserves conservative pathway gates."
        ),
        evidence_supporting_follow_up=evidence,
        negative_evidence=negative_evidence,
        uncertainty_and_limitations=record.limitations,
        blocking_issues=record.blocking_issues,
        recommended_next_steps=next_steps,
        user_approval_required=record.user_approval_required,
        external_submission_allowed=record.external_submission_allowed,
        network_access_allowed=record.network_access_allowed,
    )


def _draft_report_markdown(record: BackgroundDraftFollowUpReport) -> str:
    lines = [
        f"# {record.report_title}",
        "",
        BACKGROUND_DRAFT_REPORT_DISCLAIMER,
        "",
        "## Summary",
        "",
        record.abstract,
        "",
        "## Methodology",
        "",
        record.methodology_summary,
        "",
        "## Evidence Supporting Follow-Up",
        "",
        *_markdown_list(record.evidence_supporting_follow_up),
        "",
        "## Negative Evidence",
        "",
        *_markdown_list(record.negative_evidence),
        "",
        "## Uncertainty And Limitations",
        "",
        *_markdown_list(record.uncertainty_and_limitations),
        "",
        "## Blocking Issues",
        "",
        *_markdown_list(record.blocking_issues or ("None recorded.",)),
        "",
        "## Recommended Next Steps",
        "",
        *_markdown_list(record.recommended_next_steps),
        "",
        "## Gates",
        "",
        f"- Draft status: `{record.draft_status}`",
        f"- User approval required: `{record.user_approval_required}`",
        f"- External submission allowed: `{record.external_submission_allowed}`",
        f"- Network access allowed: `{record.network_access_allowed}`",
        "",
    ]
    return "\n".join(lines)


def _markdown_list(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items]


def _safe_filename(value: str) -> str:
    safe = "".join(
        character if character.isalnum() or character in ("-", "_") else "-"
        for character in value.lower()
    ).strip("-")
    return safe or "draft-report"


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


def _reviewed_log_entry_to_mapping(
    entry: BackgroundReviewedLogEntry,
) -> dict[str, object]:
    return {
        "review_id": entry.review_id,
        "run_id": entry.run_id,
        "target_id": entry.target_id,
        "track": entry.track.value,
        "outcome_status": entry.outcome_status,
        "reviewed_at_utc": entry.reviewed_at_utc,
        "reason_codes": list(entry.reason_codes),
        "negative_evidence": list(entry.negative_evidence),
        "blocking_issues": list(entry.blocking_issues),
        "recommended_next_action": entry.recommended_next_action,
        "network_access_allowed": entry.network_access_allowed,
    }


def _needs_follow_up_entry_to_mapping(
    entry: BackgroundNeedsFollowUpEntry,
) -> dict[str, object]:
    return {
        "follow_up_id": entry.follow_up_id,
        "run_id": entry.run_id,
        "target_id": entry.target_id,
        "track": entry.track.value,
        "follow_up_status": entry.follow_up_status,
        "created_at_utc": entry.created_at_utc,
        "trigger_types": list(entry.trigger_types),
        "reason_codes": list(entry.reason_codes),
        "required_tests": list(entry.required_tests),
        "blocking_issues": list(entry.blocking_issues),
        "report_required": entry.report_required,
        "human_review_required": entry.human_review_required,
        "submission_requires_user_approval": (
            entry.submission_requires_user_approval
        ),
        "network_access_allowed": entry.network_access_allowed,
    }


def _target_requires_follow_up(
    target: BackgroundTarget,
    *,
    selection_score: float,
    config: BackgroundPriorityConfig,
) -> bool:
    return (
        selection_score >= config.needs_follow_up_priority_threshold
        or target.blocking_issue_count > 0
    )


def _follow_up_trigger_types(
    target: BackgroundTarget,
    *,
    selection_score: float,
    config: BackgroundPriorityConfig,
) -> tuple[str, ...]:
    trigger_types: list[str] = []
    if selection_score >= config.needs_follow_up_priority_threshold:
        trigger_types.append("quantitative_threshold")
    if target.blocking_issue_count > 0:
        trigger_types.append("rule_based_blocking_issue")
    return tuple(trigger_types)


def _follow_up_reason_codes(
    target: BackgroundTarget,
    *,
    selection_score: float,
    config: BackgroundPriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if selection_score >= config.needs_follow_up_priority_threshold:
        reason_codes.append("selection_score_above_follow_up_threshold")
    if target.blocking_issue_count > 0:
        reason_codes.append("blocking_issue_requires_review")
    if target.false_positive_probability >= 0.30:
        reason_codes.append("false_positive_probability_requires_context")
    return tuple(reason_codes)


def _follow_up_blocking_issues(target: BackgroundTarget) -> tuple[str, ...]:
    issues = [
        "local fixture runner has not performed mandatory follow-up tests",
        "human review is required before report preparation or submission",
    ]
    if target.blocking_issue_count > 0:
        issues.append(
            "target-priority fixture reports unresolved blocking issues"
        )
    return tuple(issues)


def _needs_follow_up_entry_from_run(
    entry: BackgroundSearchLedgerEntry,
    target: BackgroundTarget,
    config: BackgroundPriorityConfig,
) -> BackgroundNeedsFollowUpEntry:
    selection_score = _optional_float(entry.query_parameters["selected_selection_score"])
    if selection_score is None:
        msg = "Needs-follow-up entries require a selected selection score."
        raise ValueError(msg)
    return BackgroundNeedsFollowUpEntry(
        follow_up_id=f"follow-up-{entry.run_id}",
        run_id=entry.run_id,
        target_id=entry.target_id,
        track=entry.track,
        follow_up_status=BACKGROUND_NEEDS_FOLLOW_UP_STATUS,
        created_at_utc=entry.completed_at_utc,
        trigger_types=_follow_up_trigger_types(
            target,
            selection_score=selection_score,
            config=config,
        ),
        reason_codes=_follow_up_reason_codes(
            target,
            selection_score=selection_score,
            config=config,
        ),
        required_tests=MANDATORY_FOLLOW_UP_TESTS,
        blocking_issues=entry.blocking_issues,
        report_required=True,
        human_review_required=True,
        submission_requires_user_approval=True,
        network_access_allowed=False,
    )


def _reviewed_log_entry_from_run(
    entry: BackgroundSearchLedgerEntry,
) -> BackgroundReviewedLogEntry:
    return BackgroundReviewedLogEntry(
        review_id=f"reviewed-{entry.run_id}",
        run_id=entry.run_id,
        target_id=entry.target_id,
        track=entry.track,
        outcome_status=BACKGROUND_REVIEWED_NO_FOLLOW_UP_STATUS,
        reviewed_at_utc=entry.completed_at_utc,
        reason_codes=("no_follow_up_trigger_met",),
        negative_evidence=(
            "selection score did not meet the configured follow-up threshold",
            "local fixture runner did not produce a candidate packet",
        ),
        blocking_issues=entry.blocking_issues,
        recommended_next_action="retain_in_reviewed_log",
        network_access_allowed=False,
    )


def _float_mapping(data: dict[str, Any]) -> dict[str, float]:
    return {str(key): float(value) for key, value in data.items()}


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, str | int | float):
        return float(value)
    msg = f"Expected a numeric or string priority score, got {type(value).__name__}"
    raise TypeError(msg)


def _optional_string(value: object) -> str | None:
    return None if value is None else str(value)


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def _run_id_from_timestamp(timestamp: str) -> str:
    return "background-local-" + (
        timestamp.replace("+00:00", "Z")
        .replace("-", "")
        .replace(":", "")
        .replace(".", "")
    )
