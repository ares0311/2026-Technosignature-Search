from pathlib import Path


def test_cli_usage_references_existing_example_paths() -> None:
    doc = Path("docs/CLI_USAGE.md").read_text(encoding="utf-8")

    assert ".venv/bin/techno-search score examples/candidates/radio_clean_candidate.json" in doc
    assert ".venv/bin/techno-search score-batch" in doc
    assert Path("examples/candidates/radio_clean_candidate.json").exists()
    assert Path("examples/reports/example-radio-clean.md").exists()
    assert Path("examples/reports/example-radio-clean.json").exists()
    assert Path("examples/reports/example-radio-clean.manifest.json").exists()


def test_readme_quickstart_references_existing_examples() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "pip install -e \".[dev]\"" in readme
    assert ".venv/bin/techno-search score examples/candidates/radio_clean_candidate.json" in readme
    assert (
        ".venv/bin/techno-search score-batch examples/candidates examples/batch_reports"
        in readme
    )

    linked_paths = (
        "examples/reports/example-radio-clean.md",
        "examples/reports/example-radio-clean.manifest.json",
        "examples/batch_reports/batch_manifest.json",
        "examples/batch_reports/example-radio-clean.md",
        "examples/batch_reports/example-infrared-clean.md",
        "examples/batch_reports/example-anomaly-clean.md",
    )
    for path in linked_paths:
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
        "## 🔎 Search Tracks",
        "## ⚡ Quickstart",
        "## 📦 Example Outputs",
        "## 🧾 Schemas",
        "## 📂 Project Structure",
        "## 🖥 Local System Profile",
        "## ⚠️ Important Disclaimer",
        "## 📜 License",
        "## 🔭 Vision",
    )
    for section in expected_sections:
        assert section in readme

    assert "false positives until shown otherwise" in readme
    assert "No claims of confirmed technosignatures" in readme
    assert "not unsupported claims" in readme


def test_publishing_docs_reference_current_validation_commands() -> None:
    doc = Path("docs/PUBLISHING.md").read_text(encoding="utf-8")

    assert "git push origin main" in doc
    assert ".venv/bin/python -m pytest --cov=techno_search --cov-report=term-missing" in doc
    assert ".venv/bin/python -m ruff check ." in doc
    assert ".venv/bin/python -m mypy src" in doc
    assert "git diff --check" in doc
