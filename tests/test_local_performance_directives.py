from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_agents_requires_local_gpu_and_parallel_optimization() -> None:
    agents = _read("AGENTS.md")

    assert "Local Performance Optimization" in agents
    assert "docs/SYSTEM_PROFILE.md" in agents
    assert "40-core Apple GPU" in agents
    assert "AI training" in agents
    assert "Apple Metal/MPS" in agents
    assert "up to 12 workers" in agents
    assert "4 to 6 workers" in agents
    assert "Avoid oversubscription" in agents
    assert "Do not hard-code this workstation into" in agents
    assert "REPO-NATIVE SHARD LAUNCHERS" in agents
    assert "scripts/run_six_shard_downloads.py" in agents
    assert "scripts/run_parallel_validation.py" in agents
    assert "six pytest-xdist workers" in agents
    assert "six non-overlapping `loadfile` test" in agents


def test_committed_system_profile_records_gpu_first_ai_guidance() -> None:
    profile = _read("docs/LOCAL_SYSTEM_PROFILE.md")

    assert "40-core Apple GPU" in profile
    assert "AI training" in profile
    assert "Metal/MPS/MLX" in profile
    assert "up to 12 workers" in profile
    assert "4 to 6 workers" in profile
    assert "Avoid oversubscription" in profile
    assert "Do not hard-code this hardware profile into scientific logic" in profile


def test_decision_137_records_local_optimization_policy() -> None:
    decisions = _read("docs/DECISIONS.md")

    assert "DECISION-137" in decisions
    assert "Optimize Local Execution For M4 Max With GPU-First AI Training" in decisions
    assert "Apple Metal/MPS" in decisions
    assert "MLX" in decisions
    assert "up to 12 workers" in decisions
    assert "4 to 6 workers" in decisions
    assert "fallback paths when GPU support is unavailable" in decisions


def test_all_current_agent_validation_surfaces_use_repo_native_launchers() -> None:
    claude = _read("CLAUDE.md")
    validation = _read("docs/VALIDATION.md")
    readme = _read("README.md")
    ci = _read(".github/workflows/ci.yml")
    ci_template = _read("docs/templates/ci.yml")

    for text in (claude, validation, readme, ci, ci_template):
        assert "scripts/run_parallel_validation.py" in text
    assert "scripts/run_six_shard_downloads.py" in claude
    assert "SHARDED EXECUTION DIRECTIVE" in claude
