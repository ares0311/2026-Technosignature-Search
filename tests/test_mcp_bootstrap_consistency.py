from __future__ import annotations

import json
from pathlib import Path

from techno_search.mcp_bootstrap_consistency import (
    MCP_BOOTSTRAP_CONSISTENCY_SCHEMA_VERSION,
    load_mcp_bootstrap_expectations,
    mcp_bootstrap_consistency_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "mcp_bootstrap_consistency.json"


def _write_expected(path: Path) -> Path:
    expected_path = path / "mcp_expected.json"
    expected_path.write_text(
        json.dumps(
            {
                "schema_version": MCP_BOOTSTRAP_CONSISTENCY_SCHEMA_VERSION,
                "expected_mcp_bootstrap": {
                    "command": ".venv/bin/python",
                    "args_prefix": ["-m", "techno_search.mcp_servers"],
                    "servers": {
                        "technosignatures_project_files": "project_files",
                        "technosignatures_git_read": "git_read",
                        "techno_guard": "techno_guard",
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    return expected_path


def _write_configs(
    path: Path,
    *,
    command: str = ".venv/bin/python",
    include_extra_shell_server: bool = False,
    project_files_kind: str = "project_files",
) -> None:
    (path / ".codex").mkdir()
    servers = {
        "technosignatures_project_files": project_files_kind,
        "technosignatures_git_read": "git_read",
        "techno_guard": "techno_guard",
    }
    mcp_servers: dict[str, dict[str, object]] = {
        name: {
            "command": command,
            "args": ["-m", "techno_search.mcp_servers", kind],
        }
        for name, kind in servers.items()
    }
    if include_extra_shell_server:
        mcp_servers["unsafe_shell"] = {
            "command": "bash",
            "args": ["-lc", "echo unsafe"],
        }
    (path / ".mcp.json").write_text(
        json.dumps({"mcpServers": mcp_servers}),
        encoding="utf-8",
    )
    (path / ".codex" / "config.toml").write_text(
        "\n".join(
            [
                f"[mcp_servers.{name}]\n"
                f'command = "{server["command"]}"\n'
                f"args = {json.dumps(server['args'])}\n"
                for name, server in mcp_servers.items()
            ]
        ),
        encoding="utf-8",
    )


def test_load_fixture_expectations() -> None:
    expected = load_mcp_bootstrap_expectations(FIXTURE_PATH)

    assert expected["command"] == ".venv/bin/python"
    assert expected["servers"]["techno_guard"] == "techno_guard"


def test_default_project_mcp_bootstrap_consistency_passes() -> None:
    summary = mcp_bootstrap_consistency_summary()

    assert summary["schema_version"] == MCP_BOOTSTRAP_CONSISTENCY_SCHEMA_VERSION
    assert summary["ok"] is True
    assert summary["claude_server_count"] == 3
    assert summary["codex_server_count"] == 3
    assert summary["forbidden_token_count"] == 0
    assert summary["live_provider_enabled"] is False
    assert summary["external_submission_enabled"] is False
    assert summary["arbitrary_shell_enabled"] is False


def test_custom_project_mcp_bootstrap_consistency_passes(tmp_path: Path) -> None:
    expected_path = _write_expected(tmp_path)
    _write_configs(tmp_path)

    summary = mcp_bootstrap_consistency_summary(expected_path, tmp_path)

    assert summary["ok"] is True
    assert summary["issue_count"] == 0


def test_detects_command_mismatch(tmp_path: Path) -> None:
    expected_path = _write_expected(tmp_path)
    _write_configs(tmp_path, command="python")

    summary = mcp_bootstrap_consistency_summary(expected_path, tmp_path)

    assert summary["ok"] is False
    assert summary["claude_command_mismatch_count"] == 3
    assert summary["codex_command_mismatch_count"] == 3


def test_detects_kind_mismatch(tmp_path: Path) -> None:
    expected_path = _write_expected(tmp_path)
    _write_configs(tmp_path, project_files_kind="techno_guard")

    summary = mcp_bootstrap_consistency_summary(expected_path, tmp_path)

    assert summary["ok"] is False
    assert summary["claude_kind_mismatch_count"] == 1
    assert summary["codex_kind_mismatch_count"] == 1


def test_detects_extra_shell_and_forbidden_tokens(tmp_path: Path) -> None:
    expected_path = _write_expected(tmp_path)
    _write_configs(tmp_path, include_extra_shell_server=True)

    summary = mcp_bootstrap_consistency_summary(expected_path, tmp_path)

    assert summary["ok"] is False
    assert summary["forbidden_token_count"] >= 2
    assert summary["arbitrary_shell_enabled"] is True
    assert any("unsafe_shell" in issue for issue in summary["issues"])
