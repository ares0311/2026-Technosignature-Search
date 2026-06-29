"""Cleanup planner for ignored real-radio corpus payloads.

This module supports Phase 1 data availability by freeing local storage between
bounded Breakthrough Listen download batches. It is deliberately conservative:
dry-run is the default, it only operates under ``data/extended_corpus``, and it
requires evidence that a file has already been converted or ledgered before it
can become a deletion candidate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RADIO_CORPUS_CLEANUP_SCHEMA_VERSION = "radio_corpus_cleanup_plan_v1"
RADIO_CORPUS_CLEANUP_DISCLAIMER = (
    "Radio corpus cleanup plans are local storage-management aids for ignored "
    "science payloads only. They do not delete committed files, do not alter "
    "candidate scores, and do not constitute detections, discoveries, expert "
    "review, external validation, or authorization for external submission."
)


def default_radio_corpus_dir(project_root: Path | None = None) -> Path:
    root = project_root or Path.cwd()
    return root / "data" / "extended_corpus"


def default_results_dir(project_root: Path | None = None) -> Path:
    root = project_root or Path.cwd()
    return root / "results"


def plan_radio_corpus_cleanup(
    corpus_dir: Path | None = None,
    *,
    results_dir: Path | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Return a non-destructive cleanup plan for local radio payloads."""

    root = (project_root or Path.cwd()).resolve()
    corpus = Path(corpus_dir) if corpus_dir is not None else default_radio_corpus_dir(root)
    results = Path(results_dir) if results_dir is not None else default_results_dir(root)
    resolved_corpus = corpus.resolve() if corpus.exists() else corpus.absolute()
    resolved_results = results.resolve() if results.exists() else results.absolute()

    refusal = _refusal_reason(resolved_corpus, root)
    if refusal is not None:
        return _base_plan(root, resolved_corpus, resolved_results) | {
            "ok": False,
            "refused": True,
            "refusal_reason": refusal,
            "candidate_count": 0,
            "total_size_bytes": 0,
            "candidates": [],
        }

    if not resolved_corpus.exists():
        return _base_plan(root, resolved_corpus, resolved_results) | {
            "ok": True,
            "directory_exists": False,
            "candidate_count": 0,
            "total_size_bytes": 0,
            "candidates": [],
            "limitations": ["Corpus directory does not exist; nothing to clean up."],
        }

    zero_hit_manifests = _zero_hit_manifest_paths(resolved_results)
    candidates: list[dict[str, Any]] = []
    for h5_path in sorted(resolved_corpus.rglob("*.h5")):
        dat_path = h5_path.with_suffix(".dat")
        if dat_path.exists() and dat_path.stat().st_size > 0:
            candidates.append(_candidate(h5_path, root, "hdf5_converted_to_dat", dat_path))

    for dat_path in sorted(resolved_corpus.rglob("*.dat")):
        rel = _relative(dat_path, resolved_corpus)
        manifest_path = zero_hit_manifests.get(rel)
        if manifest_path is not None:
            candidates.append(
                _candidate(dat_path, root, "zero_hit_dat_manifested", manifest_path)
            )

    total_size = sum(int(entry["size_bytes"]) for entry in candidates)
    return _base_plan(root, resolved_corpus, resolved_results) | {
        "ok": True,
        "directory_exists": True,
        "candidate_count": len(candidates),
        "total_size_bytes": total_size,
        "candidates": candidates,
        "limitations": [
            "Dry-run is the default; apply mode requires explicit acknowledgement.",
            "HDF5 files are candidates only after a same-stem non-empty .dat exists.",
            "Zero-hit .dat files are candidates only after a zero-hit manifest records "
            "their relative source_data_path.",
            "Hit-bearing .dat files are never cleanup candidates.",
        ],
    }


def apply_radio_corpus_cleanup(
    corpus_dir: Path | None = None,
    *,
    results_dir: Path | None = None,
    project_root: Path | None = None,
    acknowledge_local_apply: bool = False,
) -> dict[str, Any]:
    """Apply a cleanup plan after explicit acknowledgement."""

    plan = plan_radio_corpus_cleanup(
        corpus_dir,
        results_dir=results_dir,
        project_root=project_root,
    )
    if not plan.get("ok"):
        return plan
    if not acknowledge_local_apply:
        return plan | {
            "applied": False,
            "apply_blocked": True,
            "apply_blocked_reason": (
                "Apply requires --acknowledge-local-apply because it deletes "
                "ignored local science payloads."
            ),
        }

    deleted: list[str] = []
    errors: list[str] = []
    for entry in plan.get("candidates", []):
        if not isinstance(entry, dict):
            continue
        path = Path(str(entry["path"]))
        try:
            path.unlink()
            deleted.append(str(path))
        except OSError as exc:  # pragma: no cover - defensive local filesystem path
            errors.append(f"failed to delete {path}: {exc}")

    return plan | {
        "applied": True,
        "deleted_count": len(deleted),
        "deleted_paths": deleted,
        "errors": errors,
        "ok": not errors,
    }


def _base_plan(root: Path, corpus: Path, results: Path) -> dict[str, Any]:
    return {
        "schema_version": RADIO_CORPUS_CLEANUP_SCHEMA_VERSION,
        "disclaimer": RADIO_CORPUS_CLEANUP_DISCLAIMER,
        "project_root": str(root),
        "corpus_dir": str(corpus),
        "results_dir": str(results),
    }


def _candidate(path: Path, root: Path, reason: str, evidence_path: Path | None) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path),
        "relative_path": _relative(path, root),
        "size_bytes": stat.st_size,
        "reason": reason,
        "evidence_path": str(evidence_path) if evidence_path is not None else None,
        "evidence_relative_path": (
            _relative(evidence_path, root) if evidence_path is not None else None
        ),
    }


def _zero_hit_manifest_paths(results_dir: Path) -> dict[str, Path]:
    if not results_dir.exists():
        return {}
    sources: dict[str, Path] = {}
    for manifest_path in sorted(results_dir.rglob("*.manifest.json")):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("artifact_kind") != "zero_hit_observation_manifest":
            continue
        source_data_path = payload.get("source_data_path")
        if isinstance(source_data_path, str) and source_data_path:
            sources[source_data_path] = manifest_path
    return sources


def _refusal_reason(corpus: Path, root: Path) -> str | None:
    try:
        rel = corpus.relative_to(root)
    except ValueError:
        return "refusing to clean up paths outside the project root"
    parts = rel.parts
    if len(parts) < 2 or parts[:2] != ("data", "extended_corpus"):
        return "radio corpus cleanup only operates under data/extended_corpus"
    return None


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
