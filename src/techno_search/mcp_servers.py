"""Project-scoped MCP servers for conservative local automation."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, BinaryIO, Literal, cast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVER_VERSION = "0.1.0"

ServerKind = Literal["project_files", "git_read", "techno_guard"]

DENIED_PATH_PARTS = frozenset(
    {
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
    }
)

DENIED_RELATIVE_PREFIXES = (
    Path("data/raw"),
    Path("data/interim"),
    Path("data/external"),
    Path("data/processed"),
)

GIT_COMMANDS: dict[str, tuple[str, ...]] = {
    "status_short_branch": ("git", "status", "--short", "--branch"),
    "diff": ("git", "diff"),
    "diff_staged": ("git", "diff", "--staged"),
    "log_recent": ("git", "log", "--oneline", "--decorate", "-n", "20"),
    "branch_current": ("git", "branch", "--show-current"),
}

TECHNO_GUARD_COMMANDS: dict[str, tuple[str, ...]] = {
    "pytest": (".venv/bin/python", "-m", "pytest"),
    "coverage": (
        ".venv/bin/python",
        "-m",
        "pytest",
        "--cov=techno_search",
        "--cov-report=term-missing",
    ),
    "ruff": (".venv/bin/ruff", "check", "."),
    "mypy": (".venv/bin/mypy", "src"),
    "help": (".venv/bin/techno-search", "--help"),
    "validate_all": (".venv/bin/techno-search", "validate-all"),
    "validation_summary": (".venv/bin/techno-search", "validation-summary"),
    "operations_readiness": (
        ".venv/bin/techno-search",
        "operations-readiness-summary",
    ),
    "score_radio_clean": (
        ".venv/bin/techno-search",
        "score",
        "examples/candidates/radio_clean_candidate.json",
    ),
    "score_batch_bootstrap": (
        ".venv/bin/techno-search",
        "score-batch",
        "examples/candidates",
        "artifacts/mcp_bootstrap_batch_reports",
    ),
}


def project_relative_path(path_text: str, *, root: Path = PROJECT_ROOT) -> Path:
    """Resolve a repository-local path while blocking private and bulky paths."""
    if not path_text:
        raise ValueError("path is required")
    requested = Path(path_text)
    if requested.is_absolute():
        raise ValueError("absolute paths are not allowed")
    relative = Path(*requested.parts)
    if ".." in relative.parts:
        raise ValueError("parent-directory traversal is not allowed")
    if any(part in DENIED_PATH_PARTS for part in relative.parts):
        raise ValueError(f"path is denied by MCP bootstrap policy: {relative}")
    if any(
        relative == denied or relative.is_relative_to(denied)
        for denied in DENIED_RELATIVE_PREFIXES
    ):
        raise ValueError(f"bulk data path is denied by MCP bootstrap policy: {relative}")
    resolved = (root / relative).resolve()
    root_resolved = root.resolve()
    if not resolved.is_relative_to(root_resolved):
        raise ValueError("path escapes repository root")
    return resolved


def list_project_files(pattern: str = "*", *, limit: int = 200) -> list[str]:
    if not pattern:
        pattern = "*"
    files: list[str] = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(PROJECT_ROOT)
        try:
            project_relative_path(relative.as_posix())
        except ValueError:
            continue
        if fnmatch.fnmatch(relative.as_posix(), pattern):
            files.append(relative.as_posix())
    return sorted(files)[:limit]


def read_project_file(path_text: str, *, max_bytes: int = 200_000) -> str:
    path = project_relative_path(path_text)
    if not path.is_file():
        raise ValueError(f"not a readable project file: {path_text}")
    data = path.read_bytes()
    if len(data) > max_bytes:
        raise ValueError(f"file exceeds MCP bootstrap read limit: {path_text}")
    return data.decode("utf-8")


def run_fixed_command(command: tuple[str, ...]) -> str:
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return f"exit_code={result.returncode}\n{result.stdout}"


def run_git_command(command_name: str) -> str:
    command = GIT_COMMANDS.get(command_name)
    if command is None:
        allowed = ", ".join(sorted(GIT_COMMANDS))
        raise ValueError(f"unsupported git command {command_name!r}; allowed: {allowed}")
    return run_fixed_command(command)


def run_techno_guard_command(command_name: str) -> str:
    command = TECHNO_GUARD_COMMANDS.get(command_name)
    if command is None:
        allowed = ", ".join(sorted(TECHNO_GUARD_COMMANDS))
        raise ValueError(
            f"unsupported techno_guard command {command_name!r}; allowed: {allowed}"
        )
    if not (PROJECT_ROOT / ".venv" / "bin").is_dir():
        raise ValueError("local .venv is missing; refusing to use system Python")
    return run_fixed_command(command)


def tool_definitions(server_kind: ServerKind) -> list[dict[str, Any]]:
    if server_kind == "project_files":
        return [
            {
                "name": "list_project_files",
                "description": (
                    "List repository-local files excluding denied private, cache, "
                    "log, and bulk data paths."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "default": "*"},
                        "limit": {"type": "integer", "default": 200},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "read_project_file",
                "description": (
                    "Read a small UTF-8 repository file through the MCP bootstrap "
                    "path policy."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                    "additionalProperties": False,
                },
            },
        ]
    if server_kind == "git_read":
        return [
            {
                "name": "git_read",
                "description": (
                    "Run one fixed read-only git inspection command from the "
                    "bootstrap allowlist."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "enum": sorted(GIT_COMMANDS),
                        }
                    },
                    "required": ["command"],
                    "additionalProperties": False,
                },
            }
        ]
    return [
        {
            "name": "techno_guard",
            "description": "Run one fixed local validation command from the bootstrap allowlist.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": sorted(TECHNO_GUARD_COMMANDS),
                    }
                },
                "required": ["command"],
                "additionalProperties": False,
            },
        }
    ]


def call_tool(server_kind: ServerKind, name: str, arguments: dict[str, Any]) -> str:
    if server_kind == "project_files" and name == "list_project_files":
        pattern = str(arguments.get("pattern", "*"))
        limit = int(arguments.get("limit", 200))
        return json.dumps(list_project_files(pattern, limit=limit), indent=2)
    if server_kind == "project_files" and name == "read_project_file":
        return read_project_file(str(arguments.get("path", "")))
    if server_kind == "git_read" and name == "git_read":
        return run_git_command(str(arguments.get("command", "")))
    if server_kind == "techno_guard" and name == "techno_guard":
        return run_techno_guard_command(str(arguments.get("command", "")))
    raise ValueError(f"unsupported tool for {server_kind}: {name}")


def _read_message(stdin: BinaryIO) -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = stdin.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        key, _, value = line.decode("utf-8").partition(":")
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    return cast(dict[str, Any], json.loads(stdin.read(length).decode("utf-8")))


def _write_message(stdout: BinaryIO, message: dict[str, Any]) -> None:
    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    stdout.write(f"Content-Length: {len(body)}\r\n\r\n".encode())
    stdout.write(body)
    stdout.flush()


def _success(request_id: object, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: object, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32603, "message": message},
    }


def serve(server_kind: ServerKind) -> None:
    handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any] | None]] = {
        "initialize": lambda request: _success(
            request.get("id"),
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": f"technosignatures_{server_kind}",
                    "version": SERVER_VERSION,
                },
            },
        ),
        "tools/list": lambda request: _success(
            request.get("id"), {"tools": tool_definitions(server_kind)}
        ),
    }

    while True:
        request = _read_message(sys.stdin.buffer)
        if request is None:
            return
        if "id" not in request:
            continue
        method = str(request.get("method", ""))
        response: dict[str, Any] | None
        try:
            if method == "tools/call":
                params = cast(dict[str, Any], request.get("params", {}))
                name = str(params.get("name", ""))
                arguments = cast(dict[str, Any], params.get("arguments", {}))
                text = call_tool(server_kind, name, arguments)
                response = _success(
                    request.get("id"),
                    {"content": [{"type": "text", "text": text}], "isError": False},
                )
            elif method in handlers:
                response = handlers[method](request)
            else:
                response = _error(request.get("id"), f"unsupported method: {method}")
        except Exception as exc:
            response = _success(
                request.get("id"),
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                },
            )
        if response is not None:
            _write_message(sys.stdout.buffer, response)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a conservative project-scoped MCP server."
    )
    parser.add_argument("server", choices=["project_files", "git_read", "techno_guard"])
    args = parser.parse_args(argv)
    serve(cast(ServerKind, args.server))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
