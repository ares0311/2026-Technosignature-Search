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
    assert ".venv/bin/techno-search candidate-extraction-handoff-summary" in readme
    assert ".venv/bin/techno-search background-run-once" in readme
    assert ".venv/bin/techno-search benchmark-run-append" in readme
    assert ".venv/bin/techno-search benchmark-run-compare" in readme
    assert ".venv/bin/techno-search validation-readiness-summary" in readme
    assert "configs/background_priority_v0.json" in readme
    assert "Readiness status is a gate, not a scientific result." in readme
    assert "The selected target is a scheduling recommendation only." in readme
    assert "reviewed_workflow_status" in readme
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
