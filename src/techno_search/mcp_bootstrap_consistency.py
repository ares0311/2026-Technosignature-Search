"""Consistency checks for project-scoped MCP bootstrap configuration."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any, cast

MCP_BOOTSTRAP_CONSISTENCY_SCHEMA_VERSION = "mcp_bootstrap_consistency_v1"

MCP_BOOTSTRAP_CONSISTENCY_DISCLAIMER = (
    "MCP bootstrap consistency checks are local configuration drift guards only. "
    "They verify project-scoped MCP server names, fixed .venv commands, denied "
    "arbitrary-shell patterns, and disabled live-provider/external-submission "
    "defaults. They do not authorize live data access, external submission, "
    "candidate score changes, pathway changes, detections, discoveries, or "
    "external validation."
)

FORBIDDEN_CONFIG_TOKENS = (
    "api_key",
    "authorization",
    "bash",
    "bearer",
    "credential",
    "curl",
    "external_submission",
    "live_provider",
    "password",
    "python -c",
    "secret",
    "shell",
    "sh -c",
    "token",
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_expected_path() -> Path:
    return _project_root() / "tests" / "fixtures" / "mcp_bootstrap_consistency.json"


def load_mcp_bootstrap_expectations(path: Path | None = None) -> dict[str, Any]:
    expectation_path = path if path is not None else _default_expected_path()
    raw = json.loads(expectation_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_mcp_bootstrap"])


def _read_claude_servers(root: Path) -> dict[str, Any]:
    config_path = root / ".mcp.json"
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw.get("mcpServers", {}))


def _read_codex_servers(root: Path) -> dict[str, Any]:
    config_path = root / ".codex" / "config.toml"
    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw.get("mcp_servers", {}))


def _server_kind(server: dict[str, Any], expected_prefix: list[str]) -> str:
    args = server.get("args", [])
    if not isinstance(args, list):
        return ""
    if args[: len(expected_prefix)] != expected_prefix:
        return ""
    if len(args) <= len(expected_prefix):
        return ""
    return str(args[len(expected_prefix)])


def _collect_forbidden_tokens(root: Path) -> list[str]:
    combined = "\n".join(
        [
            (root / ".mcp.json").read_text(encoding="utf-8").lower(),
            (root / ".codex" / "config.toml").read_text(encoding="utf-8").lower(),
        ]
    )
    return [token for token in FORBIDDEN_CONFIG_TOKENS if token in combined]


def _validate_server_set(
    servers: dict[str, Any],
    *,
    expected_servers: dict[str, str],
    expected_command: str,
    expected_args_prefix: list[str],
    label: str,
) -> tuple[list[str], int, int, int]:
    issues: list[str] = []
    missing_count = 0
    command_mismatch_count = 0
    kind_mismatch_count = 0
    actual_names = set(servers)
    expected_names = set(expected_servers)
    for missing in sorted(expected_names - actual_names):
        missing_count += 1
        issues.append(f"{label} MCP server missing: {missing}")
    for extra in sorted(actual_names - expected_names):
        issues.append(f"{label} MCP server is not expected: {extra}")
    for name, expected_kind in sorted(expected_servers.items()):
        raw_server = servers.get(name)
        if not isinstance(raw_server, dict):
            continue
        command = str(raw_server.get("command", ""))
        if command != expected_command:
            command_mismatch_count += 1
            issues.append(
                f"{label} MCP server {name} command {command!r} "
                f"!= expected {expected_command!r}"
            )
        actual_kind = _server_kind(raw_server, expected_args_prefix)
        if actual_kind != expected_kind:
            kind_mismatch_count += 1
            issues.append(
                f"{label} MCP server {name} kind {actual_kind!r} "
                f"!= expected {expected_kind!r}"
            )
    return issues, missing_count, command_mismatch_count, kind_mismatch_count


def mcp_bootstrap_consistency_summary(
    expected_path: Path | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    root = project_root if project_root is not None else _project_root()
    expected = load_mcp_bootstrap_expectations(expected_path)
    expected_servers = cast(dict[str, str], expected["servers"])
    expected_command = str(expected["command"])
    expected_args_prefix = [str(item) for item in expected["args_prefix"]]

    claude_servers = _read_claude_servers(root)
    codex_servers = _read_codex_servers(root)
    claude_issues, claude_missing, claude_command_mismatch, claude_kind_mismatch = (
        _validate_server_set(
            claude_servers,
            expected_servers=expected_servers,
            expected_command=expected_command,
            expected_args_prefix=expected_args_prefix,
            label="Claude",
        )
    )
    codex_issues, codex_missing, codex_command_mismatch, codex_kind_mismatch = (
        _validate_server_set(
            codex_servers,
            expected_servers=expected_servers,
            expected_command=expected_command,
            expected_args_prefix=expected_args_prefix,
            label="Codex",
        )
    )
    forbidden_tokens = _collect_forbidden_tokens(root)
    issues = [*claude_issues, *codex_issues]
    if forbidden_tokens:
        issues.append(
            "MCP config contains forbidden token(s): "
            + ", ".join(sorted(forbidden_tokens))
        )

    return {
        "schema_version": MCP_BOOTSTRAP_CONSISTENCY_SCHEMA_VERSION,
        "disclaimer": MCP_BOOTSTRAP_CONSISTENCY_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "claude_server_count": len(claude_servers),
        "codex_server_count": len(codex_servers),
        "expected_server_count": len(expected_servers),
        "claude_missing_server_count": claude_missing,
        "codex_missing_server_count": codex_missing,
        "claude_command_mismatch_count": claude_command_mismatch,
        "codex_command_mismatch_count": codex_command_mismatch,
        "claude_kind_mismatch_count": claude_kind_mismatch,
        "codex_kind_mismatch_count": codex_kind_mismatch,
        "forbidden_token_count": len(forbidden_tokens),
        "forbidden_tokens": sorted(forbidden_tokens),
        "live_provider_enabled": "live_provider" in forbidden_tokens,
        "external_submission_enabled": "external_submission" in forbidden_tokens,
        "arbitrary_shell_enabled": any(
            token in forbidden_tokens
            for token in ["bash", "shell", "sh -c", "python -c"]
        ),
    }
