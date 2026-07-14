from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_prime_directives_prohibit_new_labeling() -> None:
    agents = _read("AGENTS.md")
    claude = _read("CLAUDE.md")

    assert "PRE-EXISTING LABELED DATA ONLY — PRIME DIRECTIVE" in agents
    assert "Never ask the user—or any other person" in agents
    assert "There are no confirmed positive technosignature labels" in agents
    assert "A valid learned-model path is a Track A classifier" in agents
    assert "STOP — NEVER ASK ANYONE TO LABEL DATA" in claude
    assert "A Track A CNN/classifier may learn pre-existing labels" in claude


def test_science_directives_propagate_labeled_data_boundary() -> None:
    required_markers = {
        "docs/SYSTEMATIC_SEARCH_PLAN.md": "LABEL ACQUISITION IS NOT A PROJECT STEP",
        "docs/ROADMAP.md": "PRIME CONSTRAINT — NO NEW LABELING",
        "docs/PRODUCTION_SCAN_RUNBOOK.md": "STOP — DO NOT CREATE LABELS",
        "docs/THRESHOLD_CALIBRATION.md": "THIS GUIDE DOES NOT AUTHORIZE NEW LABELING",
        "docs/astrometrics_coding_agents_master_guide.md": (
            "Technosignatures repo override — pre-existing labels only"
        ),
        "docs/astrometrics_data_selection_policy.md": (
            "Technosignatures labeled-data override"
        ),
    }

    for path, marker in required_markers.items():
        assert marker in _read(path), path

    readiness = _read("docs/PRODUCTION_READINESS.md")
    research = _read("docs/seti_labeled_hit_data_research.md")
    assert "Phase 1 labeled-data boundary" in readiness
    assert "No project-owned labeling effort is permitted" in research


def test_retired_review_sampler_cannot_be_invoked() -> None:
    cli = _read("src/techno_search/cli.py")

    assert "radio-review-sample" not in cli
    assert not (REPO_ROOT / "src/techno_search/radio_review_sampling.py").exists()
    assert not (REPO_ROOT / "tests/test_radio_review_sampling.py").exists()
