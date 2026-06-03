from __future__ import annotations

import json
from pathlib import Path

from techno_search.mcp_server_policy import (
    MCP_SERVER_POLICY_SCHEMA_VERSION,
    load_mcp_server_policy_expectations,
    mcp_server_policy_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "mcp_server_policy.json"


def _fixture_payload() -> dict[str, object]:
    return {
        "schema_version": MCP_SERVER_POLICY_SCHEMA_VERSION,
        "expected_mcp_server_policy": {
            "server_kinds": ["project_files", "git_read", "techno_guard"],
            "project_files": {
                "tool_names": ["list_project_files", "read_project_file"],
                "denied_path_parts": [
                    ".claude",
                    ".env",
                    ".git",
                    ".mypy_cache",
                    ".pytest_cache",
                    ".ruff_cache",
                    ".venv",
                    "__pycache__",
                    "artifacts",
                    "cache",
                    "htmlcov",
                    "logs",
                ],
                "denied_relative_prefixes": [
                    "data/raw",
                    "data/interim",
                    "data/external",
                    "data/processed",
                ],
                "read_max_bytes": 200000,
            },
            "git_read": {
                "tool_names": ["git_read"],
                "commands": {
                    "branch_current": ["git", "branch", "--show-current"],
                    "diff": ["git", "diff"],
                    "diff_staged": ["git", "diff", "--staged"],
                    "log_recent": [
                        "git",
                        "log",
                        "--oneline",
                        "--decorate",
                        "-n",
                        "20",
                    ],
                    "status_short_branch": ["git", "status", "--short", "--branch"],
                },
            },
            "techno_guard": {
                "tool_names": ["techno_guard"],
                "venv_required": True,
                "commands": {
                    "coverage": [
                        ".venv/bin/python",
                        "-m",
                        "pytest",
                        "--cov=techno_search",
                        "--cov-report=term-missing",
                    ],
                    "help": [".venv/bin/techno-search", "--help"],
                    "mypy": [".venv/bin/mypy", "src"],
                    "operations_readiness": [
                        ".venv/bin/techno-search",
                        "operations-readiness-summary",
                    ],
                    "pytest": [".venv/bin/python", "-m", "pytest"],
                    "ruff": [".venv/bin/ruff", "check", "."],
                    "score_batch_bootstrap": [
                        ".venv/bin/techno-search",
                        "score-batch",
                        "examples/candidates",
                        "artifacts/mcp_bootstrap_batch_reports",
                    ],
                    "score_radio_clean": [
                        ".venv/bin/techno-search",
                        "score",
                        "examples/candidates/radio_clean_candidate.json",
                    ],
                    "validate_all": [".venv/bin/techno-search", "validate-all"],
                    "validation_summary": [
                        ".venv/bin/techno-search",
                        "validation-summary",
                    ],
                },
            },
        },
    }


def _write_expected(path: Path, payload: dict[str, object]) -> Path:
    expected_path = path / "mcp_server_policy.json"
    expected_path.write_text(json.dumps(payload), encoding="utf-8")
    return expected_path


def test_load_mcp_server_policy_expectations() -> None:
    expected = load_mcp_server_policy_expectations(FIXTURE_PATH)

    assert expected["project_files"]["read_max_bytes"] == 200000
    assert expected["techno_guard"]["venv_required"] is True


def test_default_mcp_server_policy_passes() -> None:
    summary = mcp_server_policy_summary()

    assert summary["schema_version"] == MCP_SERVER_POLICY_SCHEMA_VERSION
    assert summary["ok"] is True
    assert summary["issue_count"] == 0
    assert summary["server_kind_count"] == 3
    assert summary["project_file_tool_count"] == 2
    assert summary["git_read_command_count"] == 5
    assert summary["techno_guard_command_count"] == 10
    assert summary["forbidden_command_token_count"] == 0
    assert summary["mutating_git_command_count"] == 0
    assert summary["tool_schema_additional_properties_disabled"] is True
    assert summary["venv_enforced"] is True
    assert summary["live_provider_enabled"] is False
    assert summary["external_submission_enabled"] is False
    assert summary["arbitrary_shell_enabled"] is False


def test_detects_expected_tool_name_drift(tmp_path: Path) -> None:
    payload = _fixture_payload()
    policy = payload["expected_mcp_server_policy"]
    assert isinstance(policy, dict)
    project_files = policy["project_files"]
    assert isinstance(project_files, dict)
    project_files["tool_names"] = ["read_project_file"]
    expected_path = _write_expected(tmp_path, payload)

    summary = mcp_server_policy_summary(expected_path)

    assert summary["ok"] is False
    assert any("project_files tools has unexpected item" in issue for issue in summary["issues"])


def test_detects_read_size_policy_drift(tmp_path: Path) -> None:
    payload = _fixture_payload()
    policy = payload["expected_mcp_server_policy"]
    assert isinstance(policy, dict)
    project_files = policy["project_files"]
    assert isinstance(project_files, dict)
    project_files["read_max_bytes"] = 1000
    expected_path = _write_expected(tmp_path, payload)

    summary = mcp_server_policy_summary(expected_path)

    assert summary["ok"] is False
    assert any("MCP read max bytes 200000 != expected 1000" in issue for issue in summary["issues"])


def test_detects_git_command_policy_drift(tmp_path: Path) -> None:
    payload = _fixture_payload()
    policy = payload["expected_mcp_server_policy"]
    assert isinstance(policy, dict)
    git_read = policy["git_read"]
    assert isinstance(git_read, dict)
    commands = git_read["commands"]
    assert isinstance(commands, dict)
    commands["status_short_branch"] = ["git", "status"]
    expected_path = _write_expected(tmp_path, payload)

    summary = mcp_server_policy_summary(expected_path)

    assert summary["ok"] is False
    assert summary["git_read_command_mismatch_count"] == 1


def test_detects_missing_techno_guard_command_policy_drift(tmp_path: Path) -> None:
    payload = _fixture_payload()
    policy = payload["expected_mcp_server_policy"]
    assert isinstance(policy, dict)
    techno_guard = policy["techno_guard"]
    assert isinstance(techno_guard, dict)
    commands = techno_guard["commands"]
    assert isinstance(commands, dict)
    commands.pop("validate_all")
    expected_path = _write_expected(tmp_path, payload)

    summary = mcp_server_policy_summary(expected_path)

    assert summary["ok"] is False
    assert any(
        "techno_guard has unexpected command: validate_all" in issue
        for issue in summary["issues"]
    )
