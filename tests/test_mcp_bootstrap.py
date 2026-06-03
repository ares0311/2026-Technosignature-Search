from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

from techno_search.mcp_servers import (
    GIT_COMMANDS,
    TECHNO_GUARD_COMMANDS,
    list_project_files,
    project_relative_path,
    tool_definitions,
)

ROOT = Path(__file__).resolve().parents[1]


def test_project_file_policy_allows_docs() -> None:
    path = project_relative_path("docs/Technosignatures_MCP_BOOTSTRAP.md")

    assert path.name == "Technosignatures_MCP_BOOTSTRAP.md"


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt",
        ".venv/bin/python",
        ".git/config",
        "logs/validation.sqlite3",
        "cache/live_providers/example.json",
        "artifacts/mcp_bootstrap_batch_reports/report.json",
        "data/raw/catalog.fits",
    ],
)
def test_project_file_policy_denies_private_cache_log_and_bulk_paths(path: str) -> None:
    with pytest.raises(ValueError):
        project_relative_path(path)


def test_project_file_listing_excludes_denied_paths() -> None:
    files = list_project_files("docs/*.md", limit=200)

    assert "docs/Technosignatures_MCP_BOOTSTRAP.md" in files
    assert all(not file.startswith("logs/") for file in files)
    assert all(".venv/" not in file for file in files)


def test_git_server_exposes_only_read_allowlist() -> None:
    allowed = {command for value in GIT_COMMANDS.values() for command in value}

    assert "push" not in allowed
    assert "reset" not in allowed
    assert "clean" not in allowed
    assert set(GIT_COMMANDS) == {
        "branch_current",
        "diff",
        "diff_staged",
        "log_recent",
        "status_short_branch",
    }


def test_techno_guard_exposes_only_fixed_local_validation_commands() -> None:
    for command in TECHNO_GUARD_COMMANDS.values():
        assert command[0].startswith(".venv/bin/")
        assert "integration_live" not in command

    assert "validate_all" in TECHNO_GUARD_COMMANDS
    assert "validation_summary" in TECHNO_GUARD_COMMANDS
    assert "operations_readiness" in TECHNO_GUARD_COMMANDS


def test_tool_definitions_do_not_offer_arbitrary_shell() -> None:
    serialized = json.dumps(
        {
            "project_files": tool_definitions("project_files"),
            "git_read": tool_definitions("git_read"),
            "techno_guard": tool_definitions("techno_guard"),
        }
    )

    assert "shell" not in serialized.lower()
    assert "exec" not in serialized.lower()


def test_claude_mcp_config_is_project_scoped_and_fixed() -> None:
    config = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    servers = config["mcpServers"]

    assert set(servers) == {
        "technosignatures_git_read",
        "technosignatures_project_files",
        "techno_guard",
    }
    for server in servers.values():
        assert server["command"] == ".venv/bin/python"
        assert server["args"][:2] == ["-m", "techno_search.mcp_servers"]


def test_codex_mcp_config_is_project_scoped_and_fixed() -> None:
    config = tomllib.loads((ROOT / ".codex" / "config.toml").read_text(encoding="utf-8"))
    servers = config["mcp_servers"]

    assert set(servers) == {
        "technosignatures_git_read",
        "technosignatures_project_files",
        "techno_guard",
    }
    for server in servers.values():
        assert server["command"] == ".venv/bin/python"
        assert server["args"][:2] == ["-m", "techno_search.mcp_servers"]


def test_mcp_configs_do_not_store_secrets_or_live_provider_defaults() -> None:
    combined = (
        (ROOT / ".mcp.json").read_text(encoding="utf-8")
        + (ROOT / ".codex" / "config.toml").read_text(encoding="utf-8")
    ).lower()

    for forbidden in ["token", "password", "secret", "api_key", "live_provider"]:
        assert forbidden not in combined
