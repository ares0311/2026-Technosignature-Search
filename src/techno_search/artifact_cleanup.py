"""Local cleanup planner for ignored background ``artifacts/`` directories.

This module is intentionally conservative. It only touches files under the
ignored top-level ``artifacts/`` directory and refuses to operate on committed
project paths (``examples/``, ``schemas/``, ``tests/``, ``docs/``, ``configs/``,
``src/``, ``logs/``, ``cache/``, ``data/``). Cleanup is dry-run by default; the
caller must explicitly request ``apply`` mode.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

ARTIFACT_CLEANUP_SCHEMA_VERSION = "artifact_cleanup_plan_v1"
ARTIFACT_CLEANUP_DISCLAIMER = (
    "Artifact cleanup plans are local maintenance summaries only. They do not "
    "modify committed project paths and never affect candidate evidence, "
    "reports, schemas, or tests."
)
DEFAULT_ARTIFACTS_DIRNAME = "artifacts"
ARTIFACT_CLEANUP_FORBIDDEN_ROOTS: tuple[str, ...] = (
    "examples",
    "schemas",
    "tests",
    "docs",
    "configs",
    "src",
    "logs",
    "cache",
    "data",
    ".git",
    ".github",
    ".venv",
)


def default_artifacts_dir(project_root: Path | None = None) -> Path:
    """Return the default ignored top-level ``artifacts/`` directory."""

    root = project_root or Path.cwd()
    return root / DEFAULT_ARTIFACTS_DIRNAME


def plan_artifact_cleanup(
    artifacts_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> dict[str, object]:
    """Return a non-destructive cleanup plan for the artifacts directory."""

    root = (project_root or Path.cwd()).resolve()
    target = Path(artifacts_dir) if artifacts_dir is not None else default_artifacts_dir(root)
    resolved_target = target.resolve() if target.exists() else target.absolute()

    refusal = _refusal_reason(resolved_target, root)
    if refusal is not None:
        return _refusal_plan(resolved_target, root, refusal)

    if not resolved_target.exists():
        return {
            "schema_version": ARTIFACT_CLEANUP_SCHEMA_VERSION,
            "disclaimer": ARTIFACT_CLEANUP_DISCLAIMER,
            "ok": True,
            "artifacts_dir": str(resolved_target),
            "project_root": str(root),
            "directory_exists": False,
            "candidate_count": 0,
            "total_size_bytes": 0,
            "candidates": [],
            "forbidden_roots": list(ARTIFACT_CLEANUP_FORBIDDEN_ROOTS),
            "uncertainty_and_limitations": [
                "Artifacts directory does not exist; nothing to clean up.",
            ],
        }

    candidates: list[dict[str, object]] = []
    total_size = 0
    for path in sorted(resolved_target.rglob("*")):
        if not path.is_file():
            continue
        size_bytes = path.stat().st_size
        total_size += size_bytes
        candidates.append(
            {
                "path": str(path),
                "relative_path": _relative(path, root),
                "size_bytes": size_bytes,
            }
        )
    return {
        "schema_version": ARTIFACT_CLEANUP_SCHEMA_VERSION,
        "disclaimer": ARTIFACT_CLEANUP_DISCLAIMER,
        "ok": True,
        "artifacts_dir": str(resolved_target),
        "project_root": str(root),
        "directory_exists": True,
        "candidate_count": len(candidates),
        "total_size_bytes": total_size,
        "candidates": candidates,
        "forbidden_roots": list(ARTIFACT_CLEANUP_FORBIDDEN_ROOTS),
        "uncertainty_and_limitations": [
            "Cleanup planning never touches committed project paths.",
            "Apply mode requires explicit opt-in and only deletes files; "
            "directories are kept so logs and run state can resume.",
        ],
    }


def apply_artifact_cleanup(
    artifacts_dir: Path | None = None,
    *,
    project_root: Path | None = None,
    acknowledge_local_apply: bool = False,
) -> dict[str, object]:
    """Apply a cleanup plan, deleting files only under ``artifacts_dir``."""

    plan = plan_artifact_cleanup(artifacts_dir, project_root=project_root)
    if not plan.get("ok"):
        return plan
    if not acknowledge_local_apply:
        return {
            **plan,
            "applied": False,
            "apply_blocked": True,
            "apply_blocked_reason": (
                "Apply requires the explicit acknowledgement flag because it "
                "deletes local files."
            ),
        }
    deleted: list[str] = []
    errors: list[str] = []
    raw_candidates = plan.get("candidates", [])
    if not isinstance(raw_candidates, list):
        raw_candidates = []
    for entry in raw_candidates:
        if not isinstance(entry, dict):
            continue
        path = Path(str(entry["path"]))
        try:
            path.unlink()
            deleted.append(str(path))
        except OSError as exc:  # pragma: no cover - defensive
            errors.append(f"failed to delete {path}: {exc}")
    return {
        **plan,
        "applied": True,
        "deleted_count": len(deleted),
        "deleted_paths": deleted,
        "errors": errors,
        "ok": not errors,
    }


def _refusal_reason(target: Path, root: Path) -> str | None:
    if target == root:
        return "refusing to clean up the project root"
    try:
        rel = target.relative_to(root)
    except ValueError:
        return "refusing to clean up a path outside the project root"
    parts = rel.parts
    if not parts:
        return "refusing to clean up the project root"
    if parts[0] in ARTIFACT_CLEANUP_FORBIDDEN_ROOTS:
        return f"refusing to clean up forbidden committed root: {parts[0]!r}"
    if parts[0] != DEFAULT_ARTIFACTS_DIRNAME:
        return (
            "refusing to clean up a directory outside the ignored "
            f"{DEFAULT_ARTIFACTS_DIRNAME}/ tree"
        )
    return None


def _refusal_plan(target: Path, root: Path, reason: str) -> dict[str, object]:
    return {
        "schema_version": ARTIFACT_CLEANUP_SCHEMA_VERSION,
        "disclaimer": ARTIFACT_CLEANUP_DISCLAIMER,
        "ok": False,
        "artifacts_dir": str(target),
        "project_root": str(root),
        "directory_exists": target.exists(),
        "refused": True,
        "refusal_reason": reason,
        "candidate_count": 0,
        "total_size_bytes": 0,
        "candidates": [],
        "forbidden_roots": list(ARTIFACT_CLEANUP_FORBIDDEN_ROOTS),
    }


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def iter_known_artifact_subpaths(artifacts_dir: Path) -> Iterable[Path]:
    """Iterate predictable background artifact subpaths for documentation/tests."""

    base = Path(artifacts_dir)
    return (
        base / "background_search_ledger.json",
        base / "background_reviewed_log.json",
        base / "background_needs_follow_up_log.json",
        base / "background_draft_reports",
        base / "background_scheduler_dry_run",
        base / "validation_draft_reports",
        base / "validation_sqlite_logs",
    )
