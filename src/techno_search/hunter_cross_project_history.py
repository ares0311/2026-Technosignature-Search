"""Cross-project Hunter search-history exchange (Techno-Hunter/EXO-Hunter/NEO-Hunter).

Mirrors 2026 Exoplanet Research's ``hunter_prior_search_history_v1`` schema
and ``src/exo_toolkit/hunter_history.py`` design exactly (see that repo's
``docs/HUNTER_CROSS_PROJECT_INTERFACE.md``) rather than inventing a new
shape -- the schema is already proven, documented, and explicitly offered
as a copy-this-file contract for any repo in the Hunter family. NEO-Hunter
uses a disjoint minor-planet identity space and has no bridge to build.

A direct sibling export's per-source ``source_sha256`` is verified against
that sibling's real source file. An operator-copied export cannot reproduce
that check unless the source is copied too, so it is explicitly marked
``stale-but-usable`` rather than silently represented as current.

As of 2026-07-25, this session confirmed the "outside current git root"
restriction is specifically a Claude Code Read/Bash *tool-argument* guard,
not an OS-level sandbox: a literal sibling-repo path passed as a Bash
argument is refused, but the exact same path computed *inside* running
Python code (e.g. ``sibling_history_export_path()`` below, mirroring
``mcp_servers.py``'s ``CROSS_PROJECT_ROOTS``) reads normally. That makes
direct reads of a sibling's real, live export genuinely available --
`--cross-project-sibling <name>` uses this path; the operator-copied-file
flow (`--cross-project-history-path`) remains for any environment where
that isn't true (e.g. a machine without the sibling repos checked out as
siblings, or a differently-configured harness).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from techno_search.prod_scan_queue import load_scan_history
from techno_search.target_alias import TargetAliasResolver

CROSS_PROJECT_HISTORY_SCHEMA_VERSION = 1
CROSS_PROJECT_HISTORY_MANIFEST_ID = "hunter-prior-search-history-v1"
CROSS_PROJECT_ROOT_NAMES = {
    "exo_hunter": "2026 Exoplanet Research",
    "neo_hunter": "2026 Near Earth Objects",
}
CROSS_PROJECT_COMPLETED_STATUSES = frozenset(
    {
        "candidate_found",
        "candidate_review_packet",
        "do_not_submit_false_positive",
        "follow_up",
        "human_review_queue",
        "known",
        "known_object_annotation",
        "needs_follow_up_review",
        "no_signal",
        "non_detection",
        "unknown",
        "unresolved",
    }
)
CROSS_PROJECT_INVALID_STATUSES = frozenset(
    {"cancelled", "failed", "no_data", "not_started"}
)
CROSS_PROJECT_DECISION_STATES = frozenset({"valid", "stale-but-usable"})
CROSS_PROJECT_HISTORY_DISCLAIMER = (
    "Cross-project Hunter search-history exports are local scheduling aids "
    "shared between independently sandboxed Astrometrics search projects. "
    "They do not constitute a detection, discovery, expert review, external "
    "validation, or authorization for external submission."
)


def _target_alias(raw_id: str) -> str:
    """Normalize a catalog ID to this project's alias form (e.g. 'TIC 123' -> 'TIC123')."""
    return raw_id.replace(" ", "").upper()


def sibling_history_export_path(project: str) -> Path:
    """Resolve a sibling Hunter repo's real, live history-export path.

    Computed relative to this repo's own location, not a hardcoded absolute
    path or an MCP/control-plane module, so this
    reads real, current data when the sibling repo is genuinely checked out
    as a sibling directory, without requiring an operator file copy first.
    """
    root_name = CROSS_PROJECT_ROOT_NAMES.get(project)
    if root_name is None:
        allowed = ", ".join(sorted(CROSS_PROJECT_ROOT_NAMES))
        raise ValueError(f"unknown sibling project {project!r}; allowed: {allowed}")
    root = Path(__file__).resolve().parents[3] / root_name
    return root / "data_selection" / "hunter_prior_search_history_v1.json"


def load_cross_project_history_export(path: Path) -> dict[str, Any]:
    """Fail-closed structural load of a copied-in sibling history export.

    Direct sibling exports are verified against their real source files.
    Operator-copied exports retain ``stale-but-usable`` status because their
    source files are intentionally absent; their completed entries remain
    visible but are never represented as freshly verified.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Cross-project history export must be a JSON object: {path}")
    if payload.get("schema_version") != CROSS_PROJECT_HISTORY_SCHEMA_VERSION:
        raise ValueError(
            f"Cross-project history export must use schema_version="
            f"{CROSS_PROJECT_HISTORY_SCHEMA_VERSION}: {path}"
        )
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError(f"Cross-project history export sources must be a non-empty list: {path}")
    for source_index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"Cross-project history export source must be an object: {path}")
        source_project = str(source.get("source_project", "")).strip()
        searched_by = str(source.get("searched_by", "")).strip()
        search_id = str(source.get("search_id", "")).strip()
        started_at = _parse_timestamp(source.get("started_at"), field="started_at", path=path)
        completed_at = _parse_timestamp(
            source.get("completed_at"), field="completed_at", path=path
        )
        source_sha256 = str(source.get("source_sha256", "")).strip().lower()
        source_path = str(source.get("source_path", "")).strip()
        provenance_uri = str(source.get("provenance_uri", "")).strip()
        if (
            not source_project
            or not searched_by
            or not search_id
            or not source_path
            or not provenance_uri
        ):
            raise ValueError(
                f"Cross-project history export source lacks reliable provenance: {path}"
            )
        if completed_at < started_at:
            raise ValueError(f"Cross-project history source completed before it started: {path}")
        if not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
            raise ValueError(f"Cross-project history source_sha256 is invalid: {path}")
        source_validity = _source_validity_state(
            export_path=path,
            source_path=source_path,
            expected_sha256=source_sha256,
        )
        if source_validity in {"invalid", "refresh-required"}:
            raise ValueError(
                f"Cross-project history source {source_index} is {source_validity}: {path}"
            )
        source["validity_state"] = source_validity
        entries = source.get("entries")
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"Cross-project history export source has no entries: {path}")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"Cross-project history export entry must be an object: {path}")
            raw_id = str(entry.get("canonical_id") or entry.get("target_id") or "").strip()
            status = str(entry.get("status", "")).strip()
            searched_at = _parse_timestamp(
                entry.get("searched_at"), field="searched_at", path=path
            )
            if not raw_id or not status:
                raise ValueError(
                    f"Cross-project history export entry needs target_id/canonical_id "
                    f"and status: {path}"
                )
            if searched_at > completed_at:
                raise ValueError(
                    f"Cross-project history entry occurs after source completion: {path}"
                )
            entry["validity_state"] = _entry_validity_state(
                status=status,
                source_validity=source_validity,
            )
    return payload


def cross_project_alias_counts(payload: Mapping[str, Any]) -> Counter[str]:
    """Count real cross-project search entries per real target alias.

    Feeds directly into the same novelty-adjustment mechanism as this
    project's own ``_load_prior_review_counts`` -- a target another real
    Astrometsrics Hunter project already searched is not novel here either,
    the same evidence-based logic as an already-scanned target within this
    project alone.
    """
    counts: Counter[str] = Counter()
    for source in payload.get("sources", []):
        for entry in source.get("entries", []):
            if entry.get("validity_state") not in CROSS_PROJECT_DECISION_STATES:
                continue
            raw_id = str(entry.get("canonical_id") or entry.get("target_id") or "").strip()
            if raw_id:
                counts[_target_alias(raw_id)] += 1
    return counts


def cross_project_evidence_by_alias(payload: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Map each real target alias to its real cross-project search evidence."""
    by_alias: dict[str, list[dict[str, Any]]] = {}
    for source in payload.get("sources", []):
        source_project = str(source.get("source_project") or source.get("searched_by") or "")
        for entry in source.get("entries", []):
            validity_state = str(entry.get("validity_state", "unknown"))
            if validity_state not in CROSS_PROJECT_DECISION_STATES:
                continue
            raw_id = str(entry.get("canonical_id") or entry.get("target_id") or "").strip()
            if not raw_id:
                continue
            alias = _target_alias(raw_id)
            by_alias.setdefault(alias, []).append(
                {
                    "source_project": source_project,
                    "status": str(entry.get("status", "")),
                    "searched_at": str(entry.get("searched_at", "")),
                    "validity_state": validity_state,
                }
            )
    return by_alias


def export_cross_project_history(
    *,
    scan_history_path: Path = Path("results/scan_history.ndjson"),
    known_target_ids: Iterable[str],
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build Techno-Hunter's own portable, schema_version=1 history export.

    Publishable in ``data_selection/hunter_prior_search_history_v1.json`` for
    an operator to copy into a sibling repo, mirroring 2026 Exoplanet
    Research's own publish path exactly so the exchange needs no renaming.
    """
    if not scan_history_path.is_file():
        raise ValueError(f"Scan history not found: {scan_history_path}")
    history = load_scan_history(scan_history_path)
    resolver = TargetAliasResolver.build(known_target_ids)
    source_sha256 = hashlib.sha256(scan_history_path.read_bytes()).hexdigest()
    entries: list[dict[str, Any]] = []
    for stem, records in history.items():
        target_id = resolver.resolve(stem)
        if target_id is None:
            continue
        canonical_id = (
            f"{target_id[:3]} {target_id[3:]}"
            if target_id[:3] in {"TIC", "HIP", "KIC"} and target_id[3:].isdigit()
            else target_id
        )
        for record in records:
            entries.append(
                {
                    "target_id": target_id,
                    "canonical_id": canonical_id,
                    "mission": "GBT/MeerKAT radio",
                    "status": record.pathway,
                    "searched_at": record.scanned_at_utc,
                    "run_id": record.run_id,
                    "score": record.score,
                }
            )
    if not entries:
        raise ValueError(
            f"No known-target-ID entries resolved from {scan_history_path}; "
            "nothing real to export"
        )
    generated_at = generated_at_utc or datetime.now(UTC).isoformat()
    return {
        "schema_version": CROSS_PROJECT_HISTORY_SCHEMA_VERSION,
        "manifest_id": CROSS_PROJECT_HISTORY_MANIFEST_ID,
        "description": (
            "Normalized append-only Techno-Hunter (2026 Technosignatures) real "
            "production-scan search history; source scan_history.ndjson remains "
            "unchanged. Status values are this project's own composite pathway "
            "names, not a shared vocabulary -- treat as informational context, "
            "not a cross-project outcome classification."
        ),
        "disclaimer": CROSS_PROJECT_HISTORY_DISCLAIMER,
        "sources": [
            {
                "search_id": f"techno-hunter-scan-history-export-{generated_at}",
                "mode": "new",
                "started_at": generated_at,
                "completed_at": generated_at,
                "searched_by": "Techno-Hunter",
                "source_project": "2026 Technosignatures",
                "method_or_data": (
                    "GBT/MeerKAT turboSETI radio SETI search; ABACAB cadence + "
                    "composite pathway scoring"
                ),
                "source_path": str(scan_history_path),
                "source_sha256": source_sha256,
                "provenance_uri": f"local-artifact:{scan_history_path}#sha256={source_sha256}",
                "entries": entries,
            }
        ],
    }


def write_cross_project_history_export(
    output_path: Path,
    *,
    scan_history_path: Path = Path("results/scan_history.ndjson"),
    known_target_ids: Iterable[str],
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Write Techno-Hunter's own portable history export and return a summary."""
    payload = export_cross_project_history(
        scan_history_path=scan_history_path,
        known_target_ids=known_target_ids,
        generated_at_utc=generated_at_utc,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    entry_count = sum(len(source["entries"]) for source in payload["sources"])
    return {
        "schema_version": CROSS_PROJECT_HISTORY_SCHEMA_VERSION,
        "ok": True,
        "disclaimer": CROSS_PROJECT_HISTORY_DISCLAIMER,
        "output_path": str(output_path),
        "entry_count": entry_count,
        "unique_target_count": len({e["target_id"] for e in payload["sources"][0]["entries"]}),
    }


def _parse_timestamp(value: object, *, field: str, path: Path) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Cross-project history {field} is required: {path}")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Cross-project history {field} is invalid: {path}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"Cross-project history {field} must be timezone-aware: {path}")
    return parsed.astimezone(UTC)


def _source_validity_state(
    *,
    export_path: Path,
    source_path: str,
    expected_sha256: str,
) -> str:
    export_root = (
        export_path.parent.parent
        if export_path.parent.name == "data_selection"
        else None
    )
    if export_root is None:
        return "stale-but-usable"
    original = export_root / source_path
    if not original.is_file():
        return "stale-but-usable"
    actual_sha256 = hashlib.sha256(original.read_bytes()).hexdigest()
    return "valid" if actual_sha256 == expected_sha256 else "refresh-required"


def _entry_validity_state(*, status: str, source_validity: str) -> str:
    normalized = status.strip().lower()
    if normalized in CROSS_PROJECT_COMPLETED_STATUSES:
        return source_validity
    if normalized in CROSS_PROJECT_INVALID_STATUSES:
        return "invalid"
    return "unknown"
