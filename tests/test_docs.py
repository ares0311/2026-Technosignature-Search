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
        "docs/LOCAL_SYSTEM_PROFILE.md",
    )
    for path in linked_paths:
        assert path in readme
        assert Path(path).exists()


def test_readme_keeps_public_entrypoint_structure() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    expected_sections = (
        "## 🌌 Overview",
        "## 🧠 Key Idea",
        "## 📊 Current Status",
        "## 🛣 Roadmap",
        "## ⚙️ Architecture",
        "## 📐 Scoring Model",
        "## 📂 Project Structure",
        "## 🖥 Local System Profile",
        "## ⚠️ Important Disclaimer",
        "## 📜 License",
        "## 🔭 Vision",
    )
    for section in expected_sections:
        assert section in readme

    assert "Most signals are **not technosignatures**." in readme
    assert "P(H | D) ∝ P(D | H) P(H)" in readme
    assert "log_score_i = log_prior_i + weighted_evidence_i" in readme
    assert "No claims of confirmed technosignatures" in readme
    assert "not just interesting anomalies" in readme


def test_publishing_docs_reference_current_validation_commands() -> None:
    doc = Path("docs/PUBLISHING.md").read_text(encoding="utf-8")

    assert "git push origin main" in doc
    assert ".venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing" in doc
    assert ".venv/bin/python -m ruff check ." in doc
    assert ".venv/bin/python -m mypy src" in doc
    assert "git diff --check" in doc
