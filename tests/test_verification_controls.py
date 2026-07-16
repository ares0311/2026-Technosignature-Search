"""Adversarial/negative controls for the reliability-verification scripts.

These prove the critical controls (directive parity, no-fake-completion,
verification freshness) actually detect representative failures, not just
that they exist. Every test operates on ``tmp_path`` or the real repository
in read-only fashion; none of them mutate real repository files.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_verification_freshness  # noqa: E402
from check_directive_parity import directive_parity_errors  # noqa: E402
from check_no_fake_completion import fake_completion_errors  # noqa: E402
from check_verification_freshness import verification_freshness_errors  # noqa: E402

GOOD_CLAUDE_MD = (
    "# CLAUDE.md\n\n"
    "**AGENTS.md is the single source of truth for all directives** — "
    "everything.\n\n"
    "Read `AGENTS.md` first, every session; where anything below appears to "
    "conflict, `AGENTS.md` governs.\n"
)

GOOD_AGENTS_MD = (
    "# AGENTS.md\n\n"
    "## LLM MAINTENANCE DIRECTIVES\n\n"
    "### FAIL LOUDLY\n\n"
    "Never silently swallow a material failure.\n\n"
    "### NO FAKE COMPLETION\n\n"
    "Never represent incomplete required work as complete.\n\n"
    "### NO UNSUPPORTED COMPLETION CLAIMS\n\n"
    "Do not claim work is complete without evidence.\n\n"
    "### AGENT INSTRUCTION EXPOSURE\n\n"
    "Codex reads this file directly; Claude Code reads CLAUDE.md.\n"
)


# --- directive parity: known-good, known-bad, malformed ---


def test_directive_parity_passes_on_real_repo() -> None:
    errors = directive_parity_errors(REPO_ROOT)
    assert errors == []


def test_directive_parity_flags_missing_claude_deference_marker(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("# CLAUDE.md\n\nNo deference here.\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(GOOD_AGENTS_MD, encoding="utf-8")

    errors = directive_parity_errors(tmp_path)

    assert errors != []
    assert any("deference marker" in e for e in errors)


def test_directive_parity_flags_missing_agents_md_section(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text(GOOD_CLAUDE_MD, encoding="utf-8")
    broken_agents = GOOD_AGENTS_MD.replace("### FAIL LOUDLY\n\n", "")
    (tmp_path / "AGENTS.md").write_text(broken_agents, encoding="utf-8")

    errors = directive_parity_errors(tmp_path)

    assert errors != []
    assert any("FAIL LOUDLY" in e for e in errors)


def test_directive_parity_fails_loudly_on_missing_files(tmp_path: Path) -> None:
    errors = directive_parity_errors(tmp_path)

    assert len(errors) == 2
    assert any("CLAUDE.md" in e for e in errors)
    assert any("AGENTS.md" in e for e in errors)


# --- no-fake-completion: known-good, known-bad, malformed ---


def test_fake_completion_passes_on_real_repo_src() -> None:
    errors = fake_completion_errors(REPO_ROOT / "src")
    assert errors == []


def test_fake_completion_flags_bare_pass_stub_with_real_signature(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text(
        "def compute_required_score(candidate_id: str, evidence: dict) -> float:\n"
        "    pass\n",
        encoding="utf-8",
    )

    errors = fake_completion_errors(tmp_path)

    assert errors != []
    assert any("compute_required_score" in e for e in errors)


def test_fake_completion_allows_documented_legacy_stub_signature(tmp_path: Path) -> None:
    (tmp_path / "legacy_stub.py").write_text(
        "def legacy_summary(*_a: object, **_k: object) -> dict:\n    pass\n",
        encoding="utf-8",
    )

    errors = fake_completion_errors(tmp_path)

    assert errors == []


def test_fake_completion_flags_unresolved_todo_marker(tmp_path: Path) -> None:
    (tmp_path / "todo.py").write_text(
        "def f() -> int:\n    return 1  # TODO: replace with real computation\n",
        encoding="utf-8",
    )

    errors = fake_completion_errors(tmp_path)

    assert errors != []
    assert any("TODO/FIXME" in e for e in errors)


def test_fake_completion_todo_suppression_marker_is_honored(tmp_path: Path) -> None:
    (tmp_path / "suppressed.py").write_text(
        "def f() -> int:\n"
        "    return 1  # TODO: intentional, tracked elsewhere  # noqa: fake-completion\n",
        encoding="utf-8",
    )

    errors = fake_completion_errors(tmp_path)

    assert errors == []


def test_fake_completion_fails_loudly_on_unparseable_file(tmp_path: Path) -> None:
    (tmp_path / "broken_syntax.py").write_text("def broken(:\n    return\n", encoding="utf-8")

    errors = fake_completion_errors(tmp_path)

    assert errors != []
    assert any("could not parse" in e for e in errors)


# --- verification freshness: known-good, known-bad, malformed ---
#
# This sandbox denies writes to any nested `.git/`-suffixed path (confirmed:
# even `git init` inside a tmp_path under the repo tree fails trying to copy
# hook templates and write `.git/config`), so a real throwaway git repo per
# test is not possible here. Instead these tests mock at the actual external
# boundary — the `_git()` subprocess call — and exercise the real decision
# logic in `verification_freshness_errors()` against controlled git output.
# This is not "a mock reproducing the behavior under test": the git
# subprocess itself is the external dependency being stood in for; the
# branching logic that consumes its output is real and unmocked.


def test_verification_freshness_passes_on_clean_committed_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "src").mkdir()

    def fake_git(repo_root: Path, *args: str) -> str:
        if args[:2] == ("status", "--porcelain"):
            return ""
        if args == ("rev-parse", "HEAD"):
            return "aaaa000000000000000000000000000000000000"
        raise AssertionError(f"unexpected git args in this test: {args}")

    monkeypatch.setattr(check_verification_freshness, "_git", fake_git)

    errors, notes = verification_freshness_errors(tmp_path)

    assert errors == []
    assert any("has not yet recorded" in n for n in notes)


def test_verification_freshness_flags_uncommitted_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "src").mkdir()

    def fake_git(repo_root: Path, *args: str) -> str:
        if args[:2] == ("status", "--porcelain"):
            return " M src/placeholder.py"
        raise AssertionError(f"unexpected git args in this test: {args}")

    monkeypatch.setattr(check_verification_freshness, "_git", fake_git)

    errors, _notes = verification_freshness_errors(tmp_path)

    assert errors != []
    assert any("VERIFICATION STALE" in e and "uncommitted" in e for e in errors)


def test_verification_freshness_marker_matches_head_on_clean_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "verification_last_pass.json").write_text(
        json.dumps({"commit_sha": "aaaa000000000000000000000000000000000000"}),
        encoding="utf-8",
    )

    def fake_git(repo_root: Path, *args: str) -> str:
        if args[:2] == ("status", "--porcelain"):
            return ""
        if args == ("rev-parse", "HEAD"):
            return "aaaa000000000000000000000000000000000000"
        raise AssertionError(f"unexpected git args in this test: {args}")

    monkeypatch.setattr(check_verification_freshness, "_git", fake_git)

    errors, notes = verification_freshness_errors(tmp_path)

    assert errors == []
    assert not any("has not yet recorded" in n for n in notes)


def test_verification_freshness_flags_stale_marker_after_relevant_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "verification_last_pass.json").write_text(
        json.dumps({"commit_sha": "aaaa000000000000000000000000000000000000"}),
        encoding="utf-8",
    )

    def fake_git(repo_root: Path, *args: str) -> str:
        if args[:2] == ("status", "--porcelain"):
            return ""
        if args == ("rev-parse", "HEAD"):
            return "bbbb111111111111111111111111111111111111"
        if args[:2] == ("diff", "--name-only"):
            return "src/placeholder.py"
        raise AssertionError(f"unexpected git args in this test: {args}")

    monkeypatch.setattr(check_verification_freshness, "_git", fake_git)

    errors, _notes = verification_freshness_errors(tmp_path)

    assert errors != []
    assert any("VERIFICATION STALE" in e and "last recorded pass" in e for e in errors)


def test_verification_freshness_fails_loudly_outside_git_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "src").mkdir()

    def fake_git(repo_root: Path, *args: str) -> str:
        raise subprocess.CalledProcessError(128, ["git", *args])

    monkeypatch.setattr(check_verification_freshness, "_git", fake_git)

    errors, _notes = verification_freshness_errors(tmp_path)

    assert errors != []
    assert any("not a usable git repository" in e for e in errors)


def test_verification_freshness_record_pass_writes_current_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_git(repo_root: Path, *args: str) -> str:
        if args == ("rev-parse", "HEAD"):
            return "cccc222222222222222222222222222222222222"
        raise AssertionError(f"unexpected git args in this test: {args}")

    monkeypatch.setattr(check_verification_freshness, "_git", fake_git)

    marker_path = check_verification_freshness.record_verification_pass(tmp_path)

    recorded = json.loads(marker_path.read_text(encoding="utf-8"))
    assert recorded["commit_sha"] == "cccc222222222222222222222222222222222222"


@pytest.fixture(autouse=True)
def _no_real_repo_mutation() -> None:
    """Guard: fail the whole module if a test ever writes into the real repo root.

    This is a belt-and-suspenders check on top of every test above already
    using tmp_path exclusively — it exists so a future edit that accidentally
    points a test at REPO_ROOT instead of tmp_path is caught immediately.
    """
    marker = REPO_ROOT / "artifacts" / "verification_last_pass.json"
    before = marker.read_bytes() if marker.exists() else None
    yield
    after = marker.read_bytes() if marker.exists() else None
    assert before == after, (
        "a test in test_verification_controls.py mutated the real repository's "
        "verification marker — every test here must use tmp_path"
    )
