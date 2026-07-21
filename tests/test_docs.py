import csv
import json
import re
import tomllib
from pathlib import Path


def test_cli_usage_references_existing_example_paths() -> None:
    doc = Path("docs/CLI_USAGE.md").read_text(encoding="utf-8")

    assert ".venv/bin/techno-search score examples/candidates/radio_clean_candidate.json" in doc
    assert ".venv/bin/techno-search score-batch" in doc
    assert Path("examples/candidates/radio_clean_candidate.json").exists()
    assert Path("examples/reports/example-radio-clean.md").exists()
    assert Path("examples/reports/example-radio-clean.json").exists()
    assert Path("examples/reports/example-radio-clean.manifest.json").exists()


def test_readme_references_current_authoritative_docs() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    linked_paths = (
        "AGENTS.md",
        "docs/PRODUCTION_READINESS.md",
        "docs/SYSTEMATIC_SEARCH_PLAN.md",
        "docs/PRODUCTION_SCAN_RUNBOOK.md",
        "docs/VALIDATION.md",
        "docs/CI.md",
        "docs/LOCAL_SYSTEM_PROFILE.md",
        "docs/technosignature_datasets_agent_brief.md",
        "docs/astrometrics_coding_agents_master_guide.md",
        "docs/astrometrics_data_selection_policy.md",
        "docs/astrometrics_external_and_cloud_storage_policy.md",
    )
    for path in linked_paths:
        assert path in readme
        assert Path(path).exists()


def test_readme_is_current_public_entrypoint() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    expected_sections = (
        "## Scientific boundary",
        "## Current status",
        "## Pipeline architecture",
        "## Data and target-selection policy",
        "## Environment",
        "## Quick start",
        "## Real-data workflows",
        "## Validation and release discipline",
        "## Repository layout",
        "## Scientific guardrails",
        "## Disclaimer",
        "## License",
    )
    for section in expected_sections:
        assert section in readme

    required_current_claims = (
        "No confirmed positive technosignature labels exist.",
        "remain unlabeled",
        "ranking diagnostic",
        "fail-closed",
        "Phase 0 is complete",
        "zero independently escalation-ready candidates",
        "100 GB",
        "metadata target queue",
        "scripts/run_parallel_validation.py",
        "six non-overlapping pytest-xdist workers",
        "track-b-candidate-readiness",
        "No result authorizes public disclosure or external submission.",
    )
    for claim in required_current_claims:
        assert claim in readme

    retired_claims = (
        "Citizen-Science Production Deployment Readiness",
        "Learned real-label scoring model",
        "Local citizen-science production promotion is allowed",
        "124 real cadence evidence groups labeled",
        "review labels, consensus, and exports",
        "logs/techno_search.sqlite3",
        "sqlite-operational-log-adapter",
        "candidate-extraction-handoff-summary",
        "benchmark-run-append",
    )
    for claim in retired_claims:
        assert claim not in readme


def test_readme_documents_the_installed_hunter_lifecycle() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    for command in ("Create-New-Search", "Run-New-Search", "Show-Follow-Ups"):
        assert f"{command} =" in pyproject
        assert f".venv/bin/{command}" in readme

    required_contract = (
        "Creation performs selection only. It does not download or process raw data.",
        "executes that exact search without regenerating its targets",
        "exits with status 2 before downloading anything",
        "rerunning the same search ID resumes the same immutable target list",
        "a completed search rejects another execution instead of duplicating history",
        "results/searches/SEARCH-*/manifest.json",
        "results/searches/SEARCH-*/events.ndjson",
        "results/scan_history.ndjson",
        "--approve-acquisition",
        "--json",
    )
    for claim in required_contract:
        assert claim in readme


def test_readme_shell_examples_start_by_syncing_main() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    bash_blocks = re.findall(r"```bash\n(.*?)```", readme, flags=re.DOTALL)

    assert bash_blocks
    assert all(block.startswith("git pull origin main\n") for block in bash_blocks)


def test_readme_status_matches_current_version_and_candidate_inventory() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    with Path("data_selection/bl_archive_candidate_catalog.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        catalog = list(csv.DictReader(handle))
    with Path("data_selection/target_priority_queue.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        queue = list(csv.DictReader(handle))

    resolved_count = sum(
        row["identity_status"] == "resolved_existing_queue_alias" for row in catalog
    )
    eligible = [row for row in queue if row["status"] == "raw_download_approval_required"]
    eligible_gb = sum(float(row["estimated_download_gb"]) for row in eligible)

    assert f"version-{pyproject['project']['version']}-blue" in readme
    assert f"{len(catalog):,} unique Breakthrough Listen archive labels" in readme
    assert f"resolves {resolved_count:,} identities" in readme
    assert f"{len(eligible):,} are currently ranking-eligible" in readme
    assert f"approximately {eligible_gb:.3f} GB" in readme


def test_publishing_docs_reference_current_validation_commands() -> None:
    doc = Path("docs/PUBLISHING.md").read_text(encoding="utf-8")

    assert "git push origin main" in doc
    assert "caffeinate -i .venv/bin/python scripts/run_parallel_validation.py" in doc
    assert "git diff --check" in doc


def test_dataset_brief_is_wired_into_authoritative_docs() -> None:
    required_docs = (
        "AGENTS.md",
        "CLAUDE.md",
        "docs/PRODUCTION_READINESS.md",
        "docs/PRODUCTION_SCAN_RUNBOOK.md",
        "docs/PROJECT_STATUS.md",
        "docs/ROADMAP.md",
    )

    assert Path("docs/technosignature_datasets_agent_brief.md").exists()
    for doc_path in required_docs:
        doc = Path(doc_path).read_text(encoding="utf-8")
        assert "docs/technosignature_datasets_agent_brief.md" in doc
        assert "Track A" in doc
        assert "unknown_candidate" in doc


def test_project_status_tracks_track_b_gate_progress() -> None:
    status = Path("docs/PROJECT_STATUS.md").read_text(encoding="utf-8")

    assert "Track B Phase 4 gate exists and has CLI wiring" in status
    assert "fail-closed packet-readiness audit" in status
    assert "hit-bearing real-candidate gate review remain open" in status
    assert "Not started — brief is merged locally" not in status


def test_track_a_htru2_feature_schema_is_committed() -> None:
    schema_path = Path("schemas/track_a_htru2_schema.json")

    assert schema_path.exists()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["schema_version"] == "track_a_htru2_baseline_v1"
    assert schema["label_column"] == "class"
    assert len(schema["feature_columns"]) == 8


def test_background_scheduler_templates_use_ignored_artifact_paths() -> None:
    cron = Path("docs/templates/background-search.cron").read_text(encoding="utf-8")
    launchd = Path("docs/templates/background-search.launchd.plist").read_text(
        encoding="utf-8"
    )

    for template in (cron, launchd):
        assert ".venv/bin/techno-search background-run-once" in template
        assert "artifacts/background_search_ledger.json" in template
        assert "artifacts/background_reviewed_log.json" in template
        assert "artifacts/background_needs_follow_up_log.json" in template
        assert "logs/techno_search.sqlite3" in template
        assert "--sqlite-log-path" in template
        assert "--acknowledge-local-run" in template
        assert "TECHNO_SEARCH_ENABLE_LIVE_DATA" not in template


def test_ci_template_stays_non_networked_and_outside_workflows() -> None:
    ci_doc = Path("docs/CI.md").read_text(encoding="utf-8")
    template = Path("docs/templates/ci.yml").read_text(encoding="utf-8")
    launcher = Path("scripts/run_parallel_validation.py").read_text(encoding="utf-8")

    assert Path("docs/templates/ci.yml").exists()
    _ = Path(".github/workflows/ci.yml").exists()
    assert "workflow` scope" in ci_doc
    assert "TECHNO_SEARCH_ENABLE_LIVE_DATA=0" in ci_doc
    assert 'TECHNO_SEARCH_ENABLE_LIVE_DATA: "0"' in template
    assert 'python scripts/run_parallel_validation.py -- -m "not integration_live"' in template
    assert "git diff --check" in template
    assert '"validate-all"' in launcher
    assert "techno-search health" in template


def test_cli_docs_include_draft_report_and_decision_workflows() -> None:
    doc = Path("docs/CLI_USAGE.md").read_text(encoding="utf-8")

    assert ".venv/bin/techno-search draft-follow-up-report-write" in doc
    assert ".venv/bin/techno-search validate-draft-reports" in doc
    assert ".venv/bin/techno-search user-decision-record" in doc
    assert ".venv/bin/techno-search init-logs" in doc
    assert ".venv/bin/techno-search sqlite-log-bootstrap-summary" in doc
    assert ".venv/bin/techno-search sqlite-log-summary" in doc
    assert ".venv/bin/techno-search sqlite-log-integrity-summary" in doc
    assert ".venv/bin/techno-search sqlite-recent-runs" in doc
    assert ".venv/bin/techno-search sqlite-needs-follow-up" in doc
    assert ".venv/bin/techno-search sqlite-log-export" in doc
    assert ".venv/bin/techno-search sqlite-migration-summary" in doc
    assert ".venv/bin/techno-search sqlite-log-pragmas" in doc
    assert ".venv/bin/techno-search sqlite-log-backup" in doc
    assert ".venv/bin/techno-search sqlite-log-retention-summary" in doc
    assert ".venv/bin/techno-search sqlite-log-vacuum" in doc
    assert ".venv/bin/techno-search sqlite-log-commit-guard" in doc
    assert ".venv/bin/techno-search validate-sqlite-logs" in doc
    assert ".venv/bin/techno-search validate-input" in doc
    assert ".venv/bin/techno-search run-pipeline" in doc
    assert ".venv/bin/techno-search rfi-database-summary" in doc
    assert ".venv/bin/techno-search rfi-database-admission-summary" in doc
    assert ".venv/bin/techno-search curated-dataset-admission-summary" in doc
    assert ".venv/bin/techno-search sqlite-log-consistency-summary" in doc
    assert ".venv/bin/techno-search project-status-consistency-summary" in doc
    assert ".venv/bin/techno-search mcp-server-policy-summary" in doc
    assert ".venv/bin/techno-search scheduler-dry-run" in doc
    assert "--sqlite-log-path" in doc
    assert "--confirm-external-submission-approval" not in doc
    assert "request_more_tests` and `close_as_reviewed` are the only" in doc
