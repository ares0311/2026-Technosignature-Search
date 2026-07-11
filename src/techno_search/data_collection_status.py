"""Tracked data-collection status manifest (compact progress reporting).

Real data acquisition scripts (BL extended-corpus downloads, JWST/MAST
searches, photometry light-curve searches, satellite/catalog acquisitions)
each produce a real local result -- counts of items found/downloaded/
skipped/failed. Historically the only record of that result was console
output the user had to paste back for review.

This module writes a single small, tracked JSON manifest
(``docs/data_collection_status.json``) that each acquisition entrypoint
updates in place (keyed by script/command name) after a real run, and
optionally commits + pushes just that one file directly to ``main`` --
mirroring how a PR merge is a compact, poll-free signal, this manifest lets
review happen via ``git pull`` instead of console-output paste. This is a
provenance/status record only; it does not itself constitute a detection,
discovery, or external-submission claim.

Committing here pushes directly to ``main`` (not through the agent's PR
flow) because this runs on the user's own machine under the user's own git
identity, the same as the user's own manual commits -- it is not the
agent's branch. Git failures (nothing to commit, no network, etc.) are
reported in the returned result rather than raised, so a real acquisition
run's exit status is never blocked by a status-reporting side effect.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DATA_COLLECTION_STATUS_SCHEMA_VERSION = "data_collection_status_v1"
DATA_COLLECTION_STATUS_RELATIVE_PATH = Path("docs/data_collection_status.json")
DATA_COLLECTION_STATUS_DISCLAIMER = (
    "This manifest records real local data-collection run outcomes "
    "(counts of items found/downloaded/skipped/failed) for compact "
    "progress review. It is not a detection, discovery, external "
    "validation, or external-submission claim."
)


def update_data_collection_status(
    project_root: Path,
    script: str,
    summary: dict[str, Any],
    *,
    status_path: Path | None = None,
) -> dict[str, Any]:
    """Update one script's entry in the tracked status manifest and write it back.

    Pure file I/O, no git side effects -- safe to call from tests. Returns
    the full manifest dict after the update.
    """

    path = status_path or (project_root / DATA_COLLECTION_STATUS_RELATIVE_PATH)
    manifest: dict[str, Any]
    if path.exists():
        manifest = json.loads(path.read_text())
    else:
        manifest = {
            "schema_version": DATA_COLLECTION_STATUS_SCHEMA_VERSION,
            "disclaimer": DATA_COLLECTION_STATUS_DISCLAIMER,
            "runs": {},
        }

    manifest["schema_version"] = DATA_COLLECTION_STATUS_SCHEMA_VERSION
    manifest["disclaimer"] = DATA_COLLECTION_STATUS_DISCLAIMER
    manifest.setdefault("runs", {})
    manifest["runs"][script] = {
        "last_run_utc": datetime.now(UTC).isoformat(),
        **summary,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def commit_and_push_status(
    project_root: Path,
    *,
    status_path: Path | None = None,
    message: str,
) -> dict[str, Any]:
    """Best-effort ``git add``/``commit``/``push`` of just the status manifest.

    Never raises -- returns a result dict describing what happened, since a
    status-reporting side effect must not block or fail a real acquisition
    run's own exit status.
    """

    path = status_path or (project_root / DATA_COLLECTION_STATUS_RELATIVE_PATH)
    result: dict[str, Any] = {"committed": False, "pushed": False, "error": None}

    canonical_path = project_root / DATA_COLLECTION_STATUS_RELATIVE_PATH
    try:
        is_canonical_path = path.resolve() == canonical_path.resolve()
    except OSError:
        is_canonical_path = False
    if not is_canonical_path:
        result["error"] = (
            "auto-commit skipped: status_path "
            f"{path!s} is not the canonical {canonical_path!s} (this guards "
            "against a redirected/manual/test status path -- e.g. "
            "TECHNO_DATA_COLLECTION_STATUS_PATH pointed inside the repo for "
            "local testing -- getting auto-committed and pushed to main; "
            "this happened for real twice before this guard existed)"
        )
        return result

    def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    try:
        branch_proc = _run(["git", "branch", "--show-current"])
        current_branch = branch_proc.stdout.strip()
        if branch_proc.returncode != 0 or current_branch != "main":
            result["error"] = (
                "auto-commit skipped: current branch is "
                f"{current_branch!r}, not 'main' (real acquisition runs always "
                "happen on the user's own main branch; this guards against "
                "test/CI/agent-branch invocations auto-committing)"
            )
            return result

        add_proc = _run(["git", "add", str(path)])
        if add_proc.returncode != 0:
            result["error"] = f"git add failed: {add_proc.stderr.strip()}"
            return result

        commit_proc = _run(["git", "commit", "-m", message, "--", str(path)])
        if commit_proc.returncode != 0:
            if "nothing to commit" in (commit_proc.stdout + commit_proc.stderr).lower():
                result["error"] = "nothing to commit (manifest unchanged)"
            else:
                result["error"] = f"git commit failed: {commit_proc.stderr.strip()}"
            return result
        result["committed"] = True

        push_proc = _run(["git", "push", "origin", "HEAD"])
        if push_proc.returncode != 0:
            result["error"] = f"git push failed: {push_proc.stderr.strip()}"
            return result
        result["pushed"] = True
    except (OSError, subprocess.SubprocessError) as exc:
        result["error"] = f"git operation raised: {exc}"

    return result


def record_and_publish_data_collection_status(
    project_root: Path,
    script: str,
    summary: dict[str, Any],
    *,
    status_path: Path | None = None,
    auto_commit: bool = True,
) -> dict[str, Any]:
    """Update the manifest and (by default) commit + push it. Main entrypoint."""

    manifest = update_data_collection_status(
        project_root, script, summary, status_path=status_path
    )
    git_result: dict[str, Any] | None = None
    if auto_commit:
        git_result = commit_and_push_status(
            project_root,
            status_path=status_path,
            message=f"Update data collection status: {script}",
        )
    return {"manifest": manifest, "git": git_result}
