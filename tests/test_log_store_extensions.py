"""Tests for SQLite migration plan, weekly digest, and the persisted draft example."""

import json
from io import StringIO
from pathlib import Path

from techno_search.cli import main
from techno_search.log_store import (
    SUPPORTED_SQLITE_LOG_MIGRATIONS,
    TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION,
    append_background_run_to_sqlite,
    init_sqlite_log_db,
    sqlite_log_migration_plan,
    sqlite_log_weekly_digest,
)


def _seed_sqlite_db(db_path: Path) -> None:
    init_sqlite_log_db(db_path, code_commit="test", config_version="scoring_v0")
    ledger_entry = {
        "run_id": "test-run-001",
        "target_id": "target-test-001",
        "track": "radio",
        "status": "scheduled",
        "query_parameters": {},
        "started_at_utc": "2026-05-15T00:00:00+00:00",
        "completed_at_utc": "2026-05-15T00:01:00+00:00",
        "config_version": "scoring_v0",
        "code_commit": "test",
        "cache_key": "cache-test",
        "candidate_count": 0,
        "recommended_pathways": ["github_reproducibility_only"],
        "blocking_issues": ["test blocking issue"],
        "execution_mode": "local_fixture_runner",
        "selected_priority_score": 0.42,
        "target_selection_rationale": ["test"],
        "candidate_packet_ids": [],
        "negative_result_logged": True,
        "requires_human_review": False,
        "reviewed_workflow_status": "local_scheduling_only",
    }
    outcome_entry = {
        "review_id": "review-test-001",
        "run_id": "test-run-001",
        "target_id": "target-test-001",
        "track": "radio",
        "outcome_status": "no_follow_up_required",
        "reviewed_at_utc": "2026-05-15T00:01:30+00:00",
        "reason_codes": ["scheduling_only"],
        "negative_evidence": ["No candidate packet generated"],
        "blocking_issues": [],
        "recommended_next_action": "no_action_required",
        "network_access_allowed": False,
    }
    append_background_run_to_sqlite(
        db_path,
        ledger_entry=ledger_entry,
        outcome_kind="reviewed",
        outcome_entry=outcome_entry,
    )


def test_supported_migrations_includes_current_version() -> None:
    assert SUPPORTED_SQLITE_LOG_MIGRATIONS
    versions = {step["to_version"] for step in SUPPORTED_SQLITE_LOG_MIGRATIONS}
    assert TOP_LEVEL_SQLITE_LOG_SCHEMA_VERSION in versions


def test_migration_plan_is_noop_when_schema_matches(tmp_path: Path) -> None:
    db_path = tmp_path / "logs.sqlite3"
    _seed_sqlite_db(db_path)

    plan = sqlite_log_migration_plan(db_path)

    assert plan["dry_run"] is True
    assert plan["destructive_steps_count"] == 0
    assert plan["migration_required"] is False
    assert plan["steps"][0]["kind"] == "noop"


def test_weekly_digest_returns_review_safe_summary(tmp_path: Path) -> None:
    db_path = tmp_path / "logs.sqlite3"
    _seed_sqlite_db(db_path)

    digest = sqlite_log_weekly_digest(db_path)

    assert digest["ok"] is True
    assert digest["run_count"] >= 1
    assert digest["external_submission_approved_count"] == 0
    assert digest["network_access_allowed_count"] == 0


def test_cli_sqlite_log_migrate_dry_run(tmp_path: Path) -> None:
    db_path = tmp_path / "logs.sqlite3"
    _seed_sqlite_db(db_path)
    stdout = StringIO()

    exit_code = main(
        ["sqlite-log-migrate", "--db-path", str(db_path)],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["dry_run"] is True
    assert result["migration_required"] is False


def test_cli_sqlite_log_migrate_apply_blocked(tmp_path: Path) -> None:
    db_path = tmp_path / "logs.sqlite3"
    _seed_sqlite_db(db_path)
    stdout = StringIO()

    exit_code = main(
        ["sqlite-log-migrate", "--db-path", str(db_path), "--apply"],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert result["apply_blocked"] is True


def test_cli_sqlite_log_weekly_digest(tmp_path: Path) -> None:
    db_path = tmp_path / "logs.sqlite3"
    _seed_sqlite_db(db_path)
    stdout = StringIO()

    exit_code = main(
        ["sqlite-log-weekly-digest", "--db-path", str(db_path)],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["run_count"] >= 1


def test_persisted_example_draft_reports_validate() -> None:
    """The committed example draft report directory must validate clean."""

    stdout = StringIO()

    exit_code = main(
        ["validate-draft-reports", "examples/background_draft_reports"],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["errors"] == []
