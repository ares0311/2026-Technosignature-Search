"""Local policy checks for project-scoped MCP server implementation."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, cast

import techno_search.mcp_servers as mcp_servers

MCP_SERVER_POLICY_SCHEMA_VERSION = "mcp_server_policy_v1"

MCP_SERVER_POLICY_DISCLAIMER = (
    "MCP server policy checks are local implementation drift guards only. "
    "They inspect project-scoped MCP tool names, fixed command allowlists, "
    "repository path-denial rules, read-size limits, and .venv enforcement. "
    "They do not execute MCP commands, authorize live data access, authorize "
    "external submission, change candidate scores, change pathways, create "
    "detections, claim discoveries, or provide external validation."
)

FORBIDDEN_COMMAND_TOKENS = (
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

FORBIDDEN_GIT_MUTATION_COMMANDS = (
    "add",
    "checkout",
    "clean",
    "commit",
    "merge",
    "pull",
    "push",
    "rebase",
    "reset",
    "restore",
    "rm",
    "switch",
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_expected_path() -> Path:
    return _project_root() / "tests" / "fixtures" / "mcp_server_policy.json"


def load_mcp_server_policy_expectations(path: Path | None = None) -> dict[str, Any]:
    expectation_path = path if path is not None else _default_expected_path()
    raw = json.loads(expectation_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_mcp_server_policy"])


def _tool_names(server_kind: mcp_servers.ServerKind) -> list[str]:
    return sorted(str(tool["name"]) for tool in mcp_servers.tool_definitions(server_kind))


def _additional_properties_disabled(server_kind: mcp_servers.ServerKind) -> bool:
    for tool in mcp_servers.tool_definitions(server_kind):
        schema = tool.get("inputSchema", {})
        if not isinstance(schema, dict):
            return False
        if schema.get("additionalProperties") is not False:
            return False
    return True


def _command_map(commands: dict[str, tuple[str, ...]]) -> dict[str, list[str]]:
    return {name: list(command) for name, command in sorted(commands.items())}


def _read_max_bytes() -> int:
    signature = inspect.signature(mcp_servers.read_project_file)
    return int(signature.parameters["max_bytes"].default)


def _venv_enforced() -> bool:
    source = inspect.getsource(mcp_servers.run_techno_guard_command)
    return ".venv" in source and "refusing to use system Python" in source


def _validate_exact_list(
    *,
    label: str,
    actual: list[str],
    expected: list[str],
) -> list[str]:
    issues: list[str] = []
    actual_set = set(actual)
    expected_set = set(expected)
    for missing in sorted(expected_set - actual_set):
        issues.append(f"{label} missing expected item: {missing}")
    for extra in sorted(actual_set - expected_set):
        issues.append(f"{label} has unexpected item: {extra}")
    return issues


def _validate_command_map(
    *,
    label: str,
    actual: dict[str, list[str]],
    expected: dict[str, list[str]],
) -> tuple[list[str], int, int]:
    issues: list[str] = []
    missing_count = 0
    mismatch_count = 0
    actual_names = set(actual)
    expected_names = set(expected)
    for missing in sorted(expected_names - actual_names):
        missing_count += 1
        issues.append(f"{label} missing expected command: {missing}")
    for extra in sorted(actual_names - expected_names):
        issues.append(f"{label} has unexpected command: {extra}")
    for name, expected_command in sorted(expected.items()):
        actual_command = actual.get(name)
        if actual_command is not None and actual_command != expected_command:
            mismatch_count += 1
            issues.append(
                f"{label} command {name} {actual_command!r} "
                f"!= expected {expected_command!r}"
            )
    return issues, missing_count, mismatch_count


def _forbidden_command_tokens(commands: dict[str, list[str]]) -> list[str]:
    combined = "\n".join(" ".join(command).lower() for command in commands.values())
    return sorted(token for token in FORBIDDEN_COMMAND_TOKENS if token in combined)


def _mutating_git_command_names(commands: dict[str, list[str]]) -> list[str]:
    mutating: list[str] = []
    for name, command in commands.items():
        if not command:
            mutating.append(name)
            continue
        if command[0] != "git":
            mutating.append(name)
            continue
        if len(command) > 1 and command[1] in FORBIDDEN_GIT_MUTATION_COMMANDS:
            mutating.append(name)
    return sorted(mutating)


def mcp_server_policy_summary(expected_path: Path | None = None) -> dict[str, Any]:
    expected = load_mcp_server_policy_expectations(expected_path)
    expected_server_kinds = [str(kind) for kind in expected["server_kinds"]]
    server_kinds = ["project_files", "git_read", "techno_guard"]
    project_files_policy = cast(dict[str, Any], expected["project_files"])
    git_read_policy = cast(dict[str, Any], expected["git_read"])
    techno_guard_policy = cast(dict[str, Any], expected["techno_guard"])

    issues: list[str] = []
    issues.extend(
        _validate_exact_list(
            label="MCP server kinds",
            actual=server_kinds,
            expected=expected_server_kinds,
        )
    )

    project_tool_names = _tool_names("project_files")
    git_tool_names = _tool_names("git_read")
    techno_tool_names = _tool_names("techno_guard")
    issues.extend(
        _validate_exact_list(
            label="project_files tools",
            actual=project_tool_names,
            expected=[str(name) for name in project_files_policy["tool_names"]],
        )
    )
    issues.extend(
        _validate_exact_list(
            label="git_read tools",
            actual=git_tool_names,
            expected=[str(name) for name in git_read_policy["tool_names"]],
        )
    )
    issues.extend(
        _validate_exact_list(
            label="techno_guard tools",
            actual=techno_tool_names,
            expected=[str(name) for name in techno_guard_policy["tool_names"]],
        )
    )

    actual_denied_parts = sorted(mcp_servers.DENIED_PATH_PARTS)
    expected_denied_parts = sorted(
        str(part) for part in project_files_policy["denied_path_parts"]
    )
    issues.extend(
        _validate_exact_list(
            label="MCP denied path parts",
            actual=actual_denied_parts,
            expected=expected_denied_parts,
        )
    )
    actual_denied_prefixes = sorted(
        prefix.as_posix() for prefix in mcp_servers.DENIED_RELATIVE_PREFIXES
    )
    expected_denied_prefixes = sorted(
        str(prefix) for prefix in project_files_policy["denied_relative_prefixes"]
    )
    issues.extend(
        _validate_exact_list(
            label="MCP denied relative prefixes",
            actual=actual_denied_prefixes,
            expected=expected_denied_prefixes,
        )
    )
    read_max_bytes = _read_max_bytes()
    expected_read_max_bytes = int(project_files_policy["read_max_bytes"])
    if read_max_bytes != expected_read_max_bytes:
        issues.append(
            f"MCP read max bytes {read_max_bytes} != expected {expected_read_max_bytes}"
        )

    git_commands = _command_map(mcp_servers.GIT_COMMANDS)
    expected_git_commands = cast(dict[str, list[str]], git_read_policy["commands"])
    git_issues, git_missing, git_mismatch = _validate_command_map(
        label="git_read",
        actual=git_commands,
        expected=expected_git_commands,
    )
    issues.extend(git_issues)
    techno_commands = _command_map(mcp_servers.TECHNO_GUARD_COMMANDS)
    expected_techno_commands = cast(
        dict[str, list[str]],
        techno_guard_policy["commands"],
    )
    techno_issues, techno_missing, techno_mismatch = _validate_command_map(
        label="techno_guard",
        actual=techno_commands,
        expected=expected_techno_commands,
    )
    issues.extend(techno_issues)

    command_tokens = sorted(
        set(_forbidden_command_tokens(git_commands))
        | set(_forbidden_command_tokens(techno_commands))
    )
    if command_tokens:
        issues.append(
            "MCP server commands contain forbidden token(s): "
            + ", ".join(command_tokens)
        )
    mutating_git_commands = _mutating_git_command_names(git_commands)
    if mutating_git_commands:
        issues.append(
            "git_read contains mutating command(s): "
            + ", ".join(mutating_git_commands)
        )

    additional_properties_ok = all(
        _additional_properties_disabled(cast(mcp_servers.ServerKind, kind))
        for kind in server_kinds
    )
    if not additional_properties_ok:
        issues.append("one or more MCP tool schemas allow additional properties")
    venv_required = bool(techno_guard_policy["venv_required"])
    venv_enforced = _venv_enforced()
    if venv_required and not venv_enforced:
        issues.append("techno_guard does not enforce local .venv availability")

    return {
        "schema_version": MCP_SERVER_POLICY_SCHEMA_VERSION,
        "disclaimer": MCP_SERVER_POLICY_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "server_kind_count": len(server_kinds),
        "project_file_tool_count": len(project_tool_names),
        "git_read_tool_count": len(git_tool_names),
        "techno_guard_tool_count": len(techno_tool_names),
        "denied_path_part_count": len(actual_denied_parts),
        "denied_relative_prefix_count": len(actual_denied_prefixes),
        "read_max_bytes": read_max_bytes,
        "git_read_command_count": len(git_commands),
        "techno_guard_command_count": len(techno_commands),
        "git_read_missing_command_count": git_missing,
        "techno_guard_missing_command_count": techno_missing,
        "git_read_command_mismatch_count": git_mismatch,
        "techno_guard_command_mismatch_count": techno_mismatch,
        "forbidden_command_token_count": len(command_tokens),
        "forbidden_command_tokens": command_tokens,
        "mutating_git_command_count": len(mutating_git_commands),
        "mutating_git_commands": mutating_git_commands,
        "tool_schema_additional_properties_disabled": additional_properties_ok,
        "venv_enforced": venv_enforced,
        "live_provider_enabled": "live_provider" in command_tokens,
        "external_submission_enabled": "external_submission" in command_tokens,
        "arbitrary_shell_enabled": any(
            token in command_tokens for token in ["bash", "shell", "sh -c", "python -c"]
        ),
    }
