from pathlib import Path


def test_cli_usage_references_existing_example_paths() -> None:
    doc = Path("docs/CLI_USAGE.md").read_text(encoding="utf-8")

    assert ".venv/bin/techno-search score examples/candidates/radio_clean_candidate.json" in doc
    assert ".venv/bin/techno-search score-batch" in doc
    assert Path("examples/candidates/radio_clean_candidate.json").exists()
    assert Path("examples/reports/example-radio-clean.md").exists()
    assert Path("examples/reports/example-radio-clean.json").exists()
    assert Path("examples/reports/example-radio-clean.manifest.json").exists()


def test_readme_references_existing_project_docs() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    linked_paths = (
        "docs/PROJECT_STATUS.md",
        "docs/ROADMAP.md",
        "docs/PIPELINE_SPEC.md",
        "docs/SCORING_MODEL.md",
        "docs/CLI_USAGE.md",
        "docs/VALIDATION.md",
        "docs/CI.md",
        "docs/SUBMISSION_PATHWAYS.md",
        "docs/LOCAL_SYSTEM_PROFILE.md",
    )
    for path in linked_paths:
        assert path in readme
        assert Path(path).exists()


def test_readme_keeps_public_entrypoint_structure() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    expected_sections = (
        "## 📑 Table of Contents",
        "## 🌌 Introduction",
        "## 🧠 Scientific Motivation",
        "## 📊 Current Status",
        "## 🛣 Project Roadmap",
        "## ⚙️ Pipeline Architecture",
        "## 📐 Methodology and Scoring Equations",
        "## 🔭 Data Sources",
        "## 🚀 Installation",
        "## ⚡ Quick Start",
        "## 🧭 Using and Recalibrating the Model",
        "## 🧪 Quality Control",
        "## 📤 Submission Pathways",
        "## 📂 Repository Layout",
        "## 🖥 Local System Profile",
        "## 🛡 Guardrails",
        "## ⚠️ Important Disclaimer",
        "## 📚 Works Cited",
        "## 📜 License",
        "## 🔭 Vision",
    )
    for section in expected_sections:
        assert section in readme

    assert "[Methodology and Scoring Equations](#-methodology-and-scoring-equations)" in readme
    assert "[Using and Recalibrating the Model](#-using-and-recalibrating-the-model)" in readme
    assert "### Abstract" in readme
    assert "Technosignature searches require an analysis framework" in readme
    assert "calibrated empirical likelihoods are not yet claimed" in readme
    assert "candidate-evaluation and reproducibility system" in readme
    assert "Most apparent technosignature-like signals are false positives." in readme
    assert "### Research Questions" in readme
    assert "### Evidence and Null-Model Matrix" in readme
    assert "### Roadmap-Aligned Methodology" in readme
    assert "\\mathcal{M}_{\\mathrm{roadmap}}" in readme
    assert "Advanced AI research track after calibration" in readme
    assert "\\mathcal{H} =" in readme
    assert "K_{ij} =" in readme
    assert "\\mathrm{Brier} =" in readme
    assert "\\mathrm{ECE} =" in readme
    assert "P(H \\mid D) \\propto P(D \\mid H)P(H)" in readme
    assert "\\sum_k w_{ik}x_k" in readme
    assert "P(\\mathrm{false\\ positive}) =" in readme
    assert "Breakthrough Listen-style radio data" in readme
    assert "### What the Model Does Today" in readme
    assert "### Recalibration Workflow" in readme
    assert "### Target Selection and Background Search Roadmap" in readme
    assert "### Background Logging Requirements" in readme
    assert "T =" in readme
    assert "search ledger" in readme
    assert ".venv/bin/techno-search target-priority-summary" in readme
    assert ".venv/bin/techno-search background-ledger-summary" in readme
    assert ".venv/bin/techno-search background-reviewed-workflow-summary" in readme
    assert ".venv/bin/techno-search reviewed-log-summary" in readme
    assert ".venv/bin/techno-search needs-follow-up-summary" in readme
    assert ".venv/bin/techno-search follow-up-test-summary" in readme
    assert ".venv/bin/techno-search report-readiness-summary" in readme
    assert ".venv/bin/techno-search submission-recommendation-summary" in readme
    assert ".venv/bin/techno-search candidate-extraction-handoff-summary" in readme
    assert ".venv/bin/techno-search background-run-once" in readme
    assert ".venv/bin/techno-search init-logs" in readme
    assert ".venv/bin/techno-search sqlite-log-summary" in readme
    assert ".venv/bin/techno-search sqlite-log-integrity-summary" in readme
    assert ".venv/bin/techno-search sqlite-recent-runs" in readme
    assert ".venv/bin/techno-search sqlite-needs-follow-up" in readme
    assert ".venv/bin/techno-search sqlite-log-export" in readme
    assert ".venv/bin/techno-search sqlite-migration-summary" in readme
    assert ".venv/bin/techno-search sqlite-log-pragmas" in readme
    assert ".venv/bin/techno-search sqlite-log-backup" in readme
    assert ".venv/bin/techno-search sqlite-log-retention-summary" in readme
    assert ".venv/bin/techno-search sqlite-log-vacuum" in readme
    assert ".venv/bin/techno-search sqlite-log-commit-guard" in readme
    assert ".venv/bin/techno-search validate-sqlite-logs" in readme
    assert ".venv/bin/techno-search benchmark-run-append" in readme
    assert ".venv/bin/techno-search benchmark-run-compare" in readme
    assert ".venv/bin/techno-search validation-readiness-summary" in readme
    assert "configs/background_priority_v0.json" in readme
    assert "Readiness status is a gate, not a scientific result." in readme
    assert "The selected target is a scheduling recommendation only." in readme
    assert "reviewed_workflow_status" in readme
    assert "background_reviewed_log.json" in readme
    assert "background_needs_follow_up_log.json" in readme
    assert "background_follow_up_tests.json" in readme
    assert "background_report_readiness.json" in readme
    assert "logs/techno_search.sqlite3" in readme
    assert "top-level SQLite" in readme
    assert "external_submission_allowed" in readme
    assert "T_{\\mathrm{sched}}" in readme
    assert "Candidate-extraction handoff records are the next local contract" in readme
    assert "### Quality-Control Matrix" in readme
    assert ".venv/bin/techno-search score examples/candidates/radio_clean_candidate.json" in readme
    assert ".venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing" in readme
    assert "Works Cited" in readme
    assert "Gaia Data Release 3" in readme
    assert "No claims of confirmed technosignatures" in readme
    assert "not unsupported claims" in readme


def test_publishing_docs_reference_current_validation_commands() -> None:
    doc = Path("docs/PUBLISHING.md").read_text(encoding="utf-8")

    assert "git push origin main" in doc
    assert ".venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing" in doc
    assert ".venv/bin/python -m ruff check ." in doc
    assert ".venv/bin/python -m mypy src" in doc
    assert "git diff --check" in doc


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

    assert Path("docs/templates/ci.yml").exists()
    assert not Path(".github/workflows/ci.yml").exists()
    assert "workflow` scope" in ci_doc
    assert "TECHNO_SEARCH_ENABLE_LIVE_DATA=0" in ci_doc
    assert 'TECHNO_SEARCH_ENABLE_LIVE_DATA: "0"' in template
    assert 'python -m pytest -m "not integration_live"' in template
    assert "python -m ruff check ." in template
    assert "python -m mypy src" in template
    assert "git diff --check" in template
    assert "techno-search validate-all" in template
    assert "techno-search health" in template
    assert "techno-search operations-readiness-summary" in template
    assert "techno-search operations-action-plan-summary" in template
    assert "techno-search operations-action-resolution-summary" in template
    assert "techno-search operations-blocker-detail-summary" in template
    assert "techno-search operations-blocker-review-summary" in template
    assert "techno-search operations-blocker-followup-summary" in template
    assert "techno-search operations-blocker-followup-progress-summary" in template
    assert "techno-search operations-readiness-summary" in ci_doc
    assert "techno-search operations-action-plan-summary" in ci_doc
    assert "techno-search operations-action-resolution-summary" in ci_doc
    assert "techno-search operations-blocker-detail-summary" in ci_doc
    assert "techno-search operations-blocker-review-summary" in ci_doc
    assert "techno-search operations-blocker-followup-summary" in ci_doc
    assert "techno-search operations-blocker-followup-progress-summary" in ci_doc


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
    assert ".venv/bin/techno-search scheduler-dry-run" in doc
    assert "techno-search operations-readiness-summary" in doc
    assert "techno-search operations-action-plan-summary" in doc
    assert "techno-search operations-action-resolution-summary" in doc
    assert "techno-search operations-blocker-detail-summary" in doc
    assert "techno-search operations-blocker-review-summary" in doc
    assert "techno-search operations-blocker-followup-summary" in doc
    assert "techno-search operations-blocker-followup-progress-summary" in doc
    assert "techno-search operations-readiness-digest" in doc
    assert "--sqlite-log-path" in doc
    assert "--confirm-external-submission-approval" in doc
    assert "request_more_tests` and `close_as_reviewed` never imply" in doc
