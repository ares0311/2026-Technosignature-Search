#!/usr/bin/env python3
"""Detect suspicious incomplete-implementation patterns in production code.

This supplements behavioral testing; it does not replace it. Presence of
concerning text/structure is a signal to investigate, not proof that
behavior is broken (see AGENTS.md's NO FAKE COMPLETION section).

Flags, in ``src/`` production code only (tests are exempt — a test double is
explicitly not what this rule targets):

- A function whose entire body is a bare ``pass`` (or docstring + ``pass``),
  UNLESS it matches the repository's documented Phase 0 legacy-stub
  signature: a generic catch-all parameter list (``*_a, **_k`` or similarly
  underscore-prefixed vararg/kwarg names, no other named parameters). That
  signature is this repo's own established, labeled convention for an
  intentionally deleted module's stand-in (see AGENTS.md's NO FAKE
  COMPLETION section) — a real production function with meaningful named
  parameters that does nothing is a genuine red flag and is NOT allowlisted
  by this rule.
- ``TODO`` / ``FIXME`` markers in comments, case-insensitive. Suppress a
  specific line with a trailing ``# noqa: fake-completion`` comment,
  matching this repo's existing Ruff ``# noqa`` suppression convention.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN_ROOT = "src"

_TODO_FIXME_PATTERN = re.compile(r"#.*\b(TODO|FIXME)\b", re.IGNORECASE)
_SUPPRESS_MARKER = "noqa: fake-completion"


def _is_legacy_stub_signature(args: ast.arguments) -> bool:
    """True if the function's params are a generic underscore-prefixed catch-all."""
    if args.args or args.posonlyargs or args.kwonlyargs:
        return False
    vararg_ok = args.vararg is not None and args.vararg.arg.startswith("_")
    kwarg_ok = args.kwarg is not None and args.kwarg.arg.startswith("_")
    return vararg_ok and kwarg_ok


def _strip_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[1:]
    return body


def _bare_pass_errors(path: Path, tree: ast.Module) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = _strip_docstring(node.body)
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            if _is_legacy_stub_signature(node.args):
                continue
            errors.append(
                f"{path}:{node.lineno}: function {node.name!r} has an empty "
                "(bare `pass`) body outside the documented legacy-stub "
                "signature — looks like unfinished required behavior"
            )
    return errors


def _todo_fixme_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _SUPPRESS_MARKER in line:
            continue
        if _TODO_FIXME_PATTERN.search(line):
            errors.append(
                f"{path}:{lineno}: unresolved TODO/FIXME marker in production code "
                f"(suppress with a trailing '# {_SUPPRESS_MARKER}' comment if intentional)"
            )
    return errors


def fake_completion_errors(scan_root: Path) -> list[str]:
    """Return violation strings for every .py file under scan_root; empty means clean."""
    errors: list[str] = []
    for path in sorted(scan_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        errors.extend(_todo_fixme_errors(path, text))
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            errors.append(f"{path}: could not parse for stub analysis: {exc}")
            continue
        errors.extend(_bare_pass_errors(path, tree))
    return errors


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scan-root",
        type=Path,
        default=REPO_ROOT / DEFAULT_SCAN_ROOT,
        help=f"Directory to scan for .py files (default: {DEFAULT_SCAN_ROOT}/).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    errors = fake_completion_errors(args.scan_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"No-fake-completion gate passed: no suspicious stubs or "
        f"TODO/FIXME under {args.scan_root}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
