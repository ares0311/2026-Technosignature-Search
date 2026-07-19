"""Durable Hunter search lifecycle over the existing radio pipeline.

The immutable search manifest freezes target selection. Append-only events record
execution attempts, failures, and completion without rewriting search history.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import secrets
import subprocess
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from techno_search import __version__
from techno_search.prod_scan_queue import ScanHistoryRecord, append_scan_record, load_scan_history
from techno_search.production_run_outcomes import (
    LEGACY_PRODUCTION_FOLLOW_UPS_SCHEMA_VERSIONS,
    PRODUCTION_FOLLOW_UPS_SCHEMA_VERSION,
    make_production_run_id,
    production_run_file,
)
from techno_search.production_scan import ProductionScanResult, run_production_scan
from techno_search.provenance import git_commit
from techno_search.target_priority_queue import (
    TARGET_PRIORITY_QUEUE_SCHEMA_VERSION,
    build_target_priority_manifest,
    read_target_priority_queue,
)

SEARCH_MANIFEST_SCHEMA_VERSION = "hunter_search_manifest_v2"
LEGACY_SEARCH_MANIFEST_SCHEMA_VERSIONS = frozenset({"hunter_search_manifest_v1"})
SEARCH_EVENT_SCHEMA_VERSION = "hunter_search_event_v2"
LEGACY_SEARCH_EVENT_SCHEMA_VERSIONS = frozenset({"hunter_search_event_v1"})
FOLLOW_UP_REGISTRY_SCHEMA_VERSION = "hunter_follow_up_registry_v1"
SEARCH_DISCLAIMER = (
    "Hunter searches and follow-up records are local scientific workflow artifacts. "
    "They do not constitute a detection, discovery, expert review, external validation, "
    "or authorization for external submission."
)
_HIP_PATTERN = re.compile(r"(?i)hip(\d+)")


class SearchLifecycleError(RuntimeError):
    """Raised when a durable search cannot safely advance."""


class SearchApprovalRequired(SearchLifecycleError):
    """Raised before a pending search would acquire raw archive payloads."""


CommandRunner = Callable[[Sequence[str]], int]
ProductionRunner = Callable[..., ProductionScanResult]


def make_search_id(*, now: datetime | None = None, token: str | None = None) -> str:
    """Return a stable, human-readable search identifier."""
    moment = (now or datetime.now(UTC)).astimezone(UTC)
    clean_token = (token or secrets.token_hex(4)).upper()
    if len(clean_token) != 8 or not clean_token.isalnum():
        raise ValueError("token must be exactly eight alphanumeric characters")
    return f"SEARCH-{moment.strftime('%Y%m%dT%H%M%SZ')}-{clean_token}"


def create_search(
    *,
    target_count: int,
    mode: str,
    queue_path: Path = Path("data_selection/target_priority_queue.csv"),
    scans_dir: Path = Path("results/scans"),
    searches_dir: Path = Path("results/searches"),
    manifest_dir: Path = Path("results/search_manifests"),
    search_id: str | None = None,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Freeze an exact pending search without acquiring or processing data."""
    if target_count <= 0:
        raise ValueError("target_count must be positive")
    if mode not in {"new", "follow-up"}:
        raise ValueError("mode must be 'new' or 'follow-up'")
    if not queue_path.is_file():
        raise SearchLifecycleError(f"candidate catalog not found: {queue_path}")

    queue_rows = _validated_queue_rows(queue_path)
    generated_at = created_at_utc or _utc_now()
    resolved_id = search_id or make_search_id()
    search_dir = searches_dir / resolved_id
    manifest_path = search_dir / "manifest.json"
    events_path = search_dir / "events.ndjson"
    if search_dir.exists():
        raise SearchLifecycleError(f"search already exists: {resolved_id}")

    if mode == "new":
        selected, viable_count = _select_new_targets(queue_path, target_count)
        registry_summary: dict[str, Any] | None = None
    else:
        registry_summary = follow_up_registry(
            scans_dirs=(scans_dir, searches_dir), queue_path=queue_path
        )
        selected = list(registry_summary["eligible_entries"])[:target_count]
        viable_count = int(registry_summary["eligible_count"])

    if not selected:
        raise SearchLifecycleError(f"no eligible {mode} targets are available")
    if len(selected) < target_count:
        raise SearchLifecycleError(
            f"requested {target_count} targets but only {len(selected)} eligible {mode} "
            "targets are available; no partial search was created"
        )
    selected = [_with_execution_contract(target, mode=mode) for target in selected]
    execution_kind_counts: dict[str, int] = {}
    for target in selected:
        kind = str(target["execution_kind"])
        execution_kind_counts[kind] = execution_kind_counts.get(kind, 0) + 1

    queue_sha = _sha256(queue_path)
    projected_gb = round(
        sum(float(target.get("estimated_download_gb") or 0.0) for target in selected), 6
    )
    manifest: dict[str, Any] = {
        "schema_version": SEARCH_MANIFEST_SCHEMA_VERSION,
        "artifact_kind": "hunter_search_manifest",
        "search_id": resolved_id,
        "created_at_utc": generated_at,
        "created_by_project": "Techno-Hunter",
        "app_version": __version__,
        "code_commit": git_commit(),
        "mode": mode,
        "initial_status": "pending",
        "candidate_catalog": {
            "path": str(queue_path),
            "sha256": queue_sha,
            "schema_version": TARGET_PRIORITY_QUEUE_SCHEMA_VERSION,
            "candidate_count": len(queue_rows),
            "viable_candidate_count": viable_count,
        },
        "selection": {
            "requested_count": target_count,
            "selected_count": len(selected),
            "ranking_key": (
                "target_selection_score" if mode == "new" else "follow_up_priority"
            ),
            "deterministic_tie_breaker": "canonical_target_id",
            "projected_download_gb": projected_gb,
            "execution_kind_counts": execution_kind_counts,
            "follow_up_observation_fulfilled_count": sum(
                bool(target["follow_up_observation_fulfilled"])
                for target in selected
            ),
            "partial_selection_allowed": False,
        },
        "pipeline": {
            "acquisition": "scripts/run_stream_process_evict_batch.sh",
            "preprocessing": "scripts/run_turboseti_on_extended_corpus.sh",
            "scoring": "scripts/run_pipeline_on_bl_data.sh",
            "interpretation": "techno_search.production_scan.run_production_scan",
            "raw_retention_policy": "stream_process_evict",
            "turbo_seti_parameters": {
                "max_drift_hz_per_sec": 10.0,
                "min_drift_hz_per_sec": 0.0001,
                "snr_threshold": 10.0,
            },
        },
        "targets": selected,
        "follow_up_registry": (
            {
                "schema_version": registry_summary["schema_version"],
                "source_ledger_count": registry_summary["source_ledger_count"],
                "unresolved_identity_count": registry_summary["unresolved_identity_count"],
            }
            if registry_summary is not None
            else None
        ),
        "disclaimer": SEARCH_DISCLAIMER,
        "detection_claimed": False,
        "external_submission_allowed": False,
    }
    search_dir.mkdir(parents=True, exist_ok=False)
    _write_new_json(manifest_path, manifest)
    _append_event(
        events_path,
        {
            "event": "created",
            "search_id": resolved_id,
            "at_utc": generated_at,
            "target_count": len(selected),
            "mode": mode,
            "manifest_sha256": _sha256(manifest_path),
        },
    )
    if target_count > 100:
        manifest_dir.mkdir(parents=True, exist_ok=True)
        _write_review_csv(manifest_dir / f"{resolved_id}.csv", selected)
    return manifest


def load_search(searches_dir: Path, search_id: str) -> dict[str, Any]:
    """Load and validate an immutable search and its append-only events."""
    search_dir = searches_dir / search_id
    manifest_path = search_dir / "manifest.json"
    events_path = search_dir / "events.ndjson"
    if not manifest_path.is_file():
        raise SearchLifecycleError(f"search manifest not found: {manifest_path}")
    manifest = _load_json(manifest_path)
    if manifest.get("schema_version") not in {
        SEARCH_MANIFEST_SCHEMA_VERSION,
        *LEGACY_SEARCH_MANIFEST_SCHEMA_VERSIONS,
    }:
        raise SearchLifecycleError(f"unsupported search manifest schema: {manifest_path}")
    if manifest.get("search_id") != search_id:
        raise SearchLifecycleError(f"search ID/path mismatch: {manifest_path}")
    events = _load_events(events_path, search_id)
    recorded_hash = str(events[0].get("manifest_sha256", "")) if events else ""
    if not recorded_hash or recorded_hash != _sha256(manifest_path):
        raise SearchLifecycleError(
            f"immutable search manifest hash does not match its creation event: {manifest_path}"
        )
    return {"manifest": manifest, "events": events, "status": _event_status(events)}


def latest_pending_search_id(searches_dir: Path) -> str:
    """Return the newest incomplete search ID, failing if none exists."""
    pending: list[tuple[str, str]] = []
    if searches_dir.is_dir():
        for manifest_path in searches_dir.glob("SEARCH-*/manifest.json"):
            manifest = _load_json(manifest_path)
            search_id = str(manifest.get("search_id", ""))
            if not search_id:
                continue
            loaded = load_search(searches_dir, search_id)
            if loaded["status"] != "completed":
                pending.append((str(manifest.get("created_at_utc", "")), search_id))
    if not pending:
        raise SearchLifecycleError(f"no pending searches found in {searches_dir}")
    return max(pending)[1]


def run_search(
    *,
    searches_dir: Path = Path("results/searches"),
    search_id: str | None = None,
    approve_acquisition: bool = False,
    chunk_size: int = 25,
    pipeline_workers: int = 12,
    history_path: Path = Path("results/scan_history.ndjson"),
    stdout: TextIO,
    use_rich: bool = True,
    command_runner: CommandRunner | None = None,
    production_runner: ProductionRunner = run_production_scan,
) -> dict[str, Any]:
    """Execute the exact frozen target list and durably record its outcome."""
    if chunk_size <= 0 or pipeline_workers <= 0:
        raise ValueError("chunk_size and pipeline_workers must be positive")
    resolved_id = search_id or latest_pending_search_id(searches_dir)
    loaded = load_search(searches_dir, resolved_id)
    manifest = dict(loaded["manifest"])
    manifest_app_version = str(manifest.get("app_version", ""))
    if manifest_app_version != __version__:
        raise SearchLifecycleError(
            f"search {resolved_id} was created by app version {manifest_app_version}; "
            f"current version is {__version__}. Create a new immutable search so changed "
            "release logic cannot be substituted silently"
        )
    if loaded["status"] == "completed":
        raise SearchLifecycleError(f"search is already complete: {resolved_id}")
    targets = list(manifest.get("targets", []))
    raw_required = [
        target
        for target in targets
        if target.get("source_hdf5_url")
        and not _target_has_local_dat(Path("data/extended_corpus"), str(target["hip"]))
    ]
    if raw_required and not approve_acquisition:
        projected_gb = sum(
            float(target.get("estimated_download_gb") or 0.0) for target in raw_required
        )
        raise SearchApprovalRequired(
            f"search {resolved_id} requires approval-gated acquisition for "
            f"{len(raw_required)} target(s), projected {projected_gb:.3f} GB; "
            "re-run with --approve-acquisition after reviewing the immutable manifest"
        )

    search_dir = searches_dir / resolved_id
    events_path = search_dir / "events.ndjson"
    results_dir = search_dir / "pipeline_results"
    scans_dir = search_dir / "runs"
    out_dir = Path("data/extended_corpus")
    previous_attempt = _latest_attempt_event(list(loaded["events"]))
    run_id = (
        str(previous_attempt["run_id"])
        if previous_attempt is not None
        else make_production_run_id(run_type="hunter-search")
    )
    _append_event(
        events_path,
        {
            "event": "run_resumed" if previous_attempt else "run_started",
            "search_id": resolved_id,
            "run_id": run_id,
            "at_utc": _utc_now(),
            "manifest_sha256": _sha256(search_dir / "manifest.json"),
            "app_version": __version__,
            "code_commit": git_commit(),
            "pipeline_workers": pipeline_workers,
            "chunk_size": chunk_size,
            "execution_kind_counts": manifest["selection"]["execution_kind_counts"],
            "follow_up_observation_fulfilled_count": manifest["selection"][
                "follow_up_observation_fulfilled_count"
            ],
        },
    )
    command = [
        "bash",
        "scripts/run_stream_process_evict_batch.sh",
        "--manifest",
        str(search_dir / "manifest.json"),
        "--out-dir",
        str(out_dir),
        "--results-dir",
        str(results_dir),
        "--status-key",
        f"hunter_search__{resolved_id}",
        "--chunk-size",
        str(chunk_size),
        "--pipeline-workers",
        str(pipeline_workers),
        "--log-file",
        str(search_dir / "acquisition.log"),
    ]
    runner = command_runner or _run_command
    try:
        exit_code = runner(command)
    except Exception as exc:
        _append_event(
            events_path,
            {
                "event": "run_failed",
                "search_id": resolved_id,
                "run_id": run_id,
                "at_utc": _utc_now(),
                "stage": "runner_launch",
                "error": f"{type(exc).__name__}: {exc}",
                "resumable": True,
            },
        )
        raise SearchLifecycleError(
            f"search {resolved_id} runner could not start; the exact search remains resumable"
        ) from exc
    if exit_code != 0:
        _append_event(
            events_path,
            {
                "event": "run_failed",
                "search_id": resolved_id,
                "run_id": run_id,
                "at_utc": _utc_now(),
                "stage": "acquisition_preprocessing_scoring",
                "exit_code": exit_code,
                "resumable": True,
            },
        )
        raise SearchLifecycleError(
            f"search {resolved_id} failed during acquisition/processing with exit "
            f"code {exit_code}; the exact search remains resumable"
        )
    try:
        production_result = production_runner(
            results_dir=results_dir,
            scans_dir=scans_dir,
            stdout=stdout,
            run_id=run_id,
            resume_run_dir=(scans_dir / run_id) if (scans_dir / run_id).exists() else None,
            use_rich=use_rich,
        )
        history_records = _record_run_history(
            manifest=manifest,
            result=production_result,
            history_path=history_path,
            search_id=resolved_id,
        )
        config_versions = _candidate_report_config_versions(results_dir)
    except Exception as exc:
        _append_event(
            events_path,
            {
                "event": "run_failed",
                "search_id": resolved_id,
                "run_id": run_id,
                "at_utc": _utc_now(),
                "stage": "composite_interpretation_and_provenance",
                "error": f"{type(exc).__name__}: {exc}",
                "resumable": True,
            },
        )
        raise

    completed_at = _utc_now()
    completion = {
        "event": "run_completed",
        "search_id": resolved_id,
        "run_id": production_result.run_id,
        "run_dir": str(production_result.run_dir),
        "at_utc": completed_at,
        "target_count": production_result.target_count,
        "follow_up_required_count": production_result.follow_up_required_count,
        "history_records_appended": history_records,
        "app_version": __version__,
        "candidate_report_config_versions": config_versions,
        "execution_kind_counts": manifest["selection"]["execution_kind_counts"],
        "follow_up_observation_fulfilled_count": manifest["selection"][
            "follow_up_observation_fulfilled_count"
        ],
    }
    _append_event(events_path, completion)
    return completion


def follow_up_registry(
    *,
    scans_dirs: Sequence[Path] = (Path("results/scans"), Path("results/searches")),
    queue_path: Path = Path("data_selection/target_priority_queue.csv"),
) -> dict[str, Any]:
    """Aggregate immutable run ledgers into an actionable follow-up view."""
    queue = {row["target_id"]: row for row in _validated_queue_rows(queue_path)}
    ledger_paths: set[Path] = set()
    for scans_dir in scans_dirs:
        if scans_dir.is_dir():
            ledger_paths.update(scans_dir.glob("**/*_follow_ups.json"))
    by_target: dict[str, dict[str, Any]] = {}
    unresolved = 0
    source_entries = 0
    for path in sorted(ledger_paths):
        ledger = _load_json(path)
        if ledger.get("schema_version") not in {
            PRODUCTION_FOLLOW_UPS_SCHEMA_VERSION,
            *LEGACY_PRODUCTION_FOLLOW_UPS_SCHEMA_VERSIONS,
        }:
            raise SearchLifecycleError(f"unsupported follow-up ledger schema: {path}")
        run_id = str(ledger.get("run_id", path.parent.name))
        source_project = str(ledger.get("source_project", "Techno-Hunter")).strip()
        if not source_project or not run_id:
            raise SearchLifecycleError(f"follow-up ledger lacks reliable provenance: {path}")
        for raw_entry in ledger.get("entries", []):
            if not isinstance(raw_entry, Mapping):
                raise SearchLifecycleError(f"invalid follow-up entry in {path}")
            source_entries += 1
            target_id = _canonical_target_id(str(raw_entry.get("target_name", "")))
            if target_id is None or target_id not in queue:
                unresolved += 1
                continue
            priority = _follow_up_priority(raw_entry)
            provenance = {
                "project": source_project,
                "relationship": (
                    "this_project_search"
                    if source_project == "Techno-Hunter"
                    else "imported_reliable_search_provenance"
                ),
                "run_id": run_id,
                "follow_up_id": str(raw_entry.get("follow_up_id", "")),
                "candidate_id": str(raw_entry.get("candidate_id", "")),
                "ledger_path": str(path),
                "score": float(raw_entry.get("score", 0.0)),
                "pathway": str(raw_entry.get("pathway", "")),
            }
            existing = by_target.get(target_id)
            if existing is None:
                row = queue[target_id]
                by_target[target_id] = {
                    "hip": target_id,
                    "name": target_id,
                    "mode": "follow-up",
                    "ra_deg": _optional_float(row.get("ra_deg")),
                    "dec_deg": _optional_float(row.get("dec_deg")),
                    "estimated_download_gb": _optional_float(
                        row.get("estimated_download_gb")
                    ),
                    "source_hdf5_url": row.get("source_hdf5_url", ""),
                    "queue_status": row.get("status", ""),
                    "target_selection_score": float(row["target_selection_score"]),
                    "follow_up_priority": priority,
                    "selection_reason": _follow_up_action(raw_entry),
                    "recommended_next_action": _follow_up_action(raw_entry),
                    "evidence": _follow_up_evidence(raw_entry),
                    "prior_search_provenance": [provenance],
                }
            else:
                if priority > float(existing["follow_up_priority"]):
                    existing["follow_up_priority"] = priority
                    existing["selection_reason"] = _follow_up_action(raw_entry)
                    existing["recommended_next_action"] = _follow_up_action(raw_entry)
                    existing["evidence"] = _follow_up_evidence(raw_entry)
                existing["prior_search_provenance"].append(provenance)
    eligible = sorted(
        by_target.values(),
        key=lambda entry: (-float(entry["follow_up_priority"]), str(entry["hip"])),
    )
    return {
        "schema_version": FOLLOW_UP_REGISTRY_SCHEMA_VERSION,
        "disclaimer": SEARCH_DISCLAIMER,
        "source_ledger_count": len(ledger_paths),
        "source_entry_count": source_entries,
        "eligible_count": len(eligible),
        "unresolved_identity_count": unresolved,
        "eligible_entries": eligible,
        "detection_claimed": False,
        "external_submission_allowed": False,
    }


def _select_new_targets(queue_path: Path, target_count: int) -> tuple[list[dict[str, Any]], int]:
    manifest = build_target_priority_manifest(
        queue_path=queue_path,
        max_targets=target_count,
        include_statuses=("raw_download_approval_required",),
    )
    all_rows = read_target_priority_queue(queue_path)
    viable_count = sum(
        row.get("status") == "raw_download_approval_required" for row in all_rows
    )
    selected = []
    for target in manifest["targets"]:
        selected.append(
            {
                **target,
                "mode": "new",
                "selection_reason": (
                    "highest deterministic target_selection_score among eligible, "
                    "size-preflighted targets not previously searched by this project"
                ),
                "prior_search_provenance": [],
            }
        )
    return selected, viable_count


def _with_execution_contract(target: Mapping[str, Any], *, mode: str) -> dict[str, Any]:
    """State what data this search can process without overstating follow-up work."""
    if mode == "new":
        execution_kind = "novel_target_archive_processing"
    elif str(target.get("source_hdf5_url", "")).strip():
        execution_kind = "follow_up_archive_data_processing"
    else:
        execution_kind = "existing_data_reanalysis"
    return {
        **target,
        "execution_kind": execution_kind,
        # The current catalog does not prove that any archive URL is a later-epoch
        # observation satisfying the recommended follow-up. Never infer that it is.
        "follow_up_observation_fulfilled": False,
    }


def _validated_queue_rows(path: Path) -> list[dict[str, str]]:
    rows = read_target_priority_queue(path)
    required = {
        "target_id",
        "target_selection_score",
        "status",
        "priority_config_version",
        "local_coverage_status",
    }
    if not rows:
        raise SearchLifecycleError(f"candidate catalog is empty: {path}")
    missing = required - set(rows[0])
    if missing:
        raise SearchLifecycleError(
            f"candidate catalog is missing required columns: {', '.join(sorted(missing))}"
        )
    seen: set[str] = set()
    for row in rows:
        target_id = row["target_id"].strip()
        if not target_id or target_id in seen:
            raise SearchLifecycleError(f"candidate catalog has missing/duplicate ID: {target_id}")
        seen.add(target_id)
        float(row["target_selection_score"])
    return rows


def _record_run_history(
    *,
    manifest: Mapping[str, Any],
    result: ProductionScanResult,
    history_path: Path,
    search_id: str,
) -> int:
    target_status = production_run_file(result.run_dir, "target_status")
    if not target_status.get("ok"):
        raise SearchLifecycleError(
            f"completed run has no valid target-status ledger: {result.run_dir}"
        )
    entries = list(target_status.get("entries", []))
    selected = {str(target["hip"]) for target in manifest.get("targets", [])}
    resolved_entries: list[tuple[Mapping[str, Any], str, str]] = []
    resolved_targets: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise SearchLifecycleError("target-status ledger contains a non-object entry")
        target_name = str(entry.get("target_name", ""))
        target_id = _canonical_target_id(target_name)
        if target_id is None or target_id not in selected:
            raise SearchLifecycleError(
                f"run output target is not in immutable search manifest: {target_name}"
            )
        resolved_targets.add(target_id)
        resolved_entries.append((entry, target_name, target_id))
    if resolved_targets != selected:
        missing = sorted(selected - resolved_targets)
        raise SearchLifecycleError(
            "run output does not cover every immutable search target; missing: "
            + ", ".join(missing)
        )

    existing = load_scan_history(history_path)
    appended = 0
    for entry, target_name, _target_id in resolved_entries:
        if any(record.run_id == result.run_id for record in existing.get(target_name, [])):
            continue
        append_scan_record(
            history_path,
            ScanHistoryRecord(
                target_stem=target_name,
                run_id=result.run_id,
                scanned_at_utc=_utc_now(),
                score=float(entry.get("composite_score", 0.0)),
                pathway=str(entry.get("top_pathway", "")),
                dat_file=str(entry.get("source_data_path", "")),
                parent_run_id=search_id,
            ),
        )
        appended += 1
    return appended


def _candidate_report_config_versions(results_dir: Path) -> list[str]:
    versions: set[str] = set()
    for path in sorted(results_dir.glob("**/*.manifest.json")):
        manifest = _load_json(path)
        value = str(manifest.get("config_version", "")).strip()
        if value:
            versions.add(value)
    return sorted(versions)


def _follow_up_priority(entry: Mapping[str, Any]) -> float:
    score = float(entry.get("score", 0.0))
    if bool(entry.get("cross_target_rfi_flagged")):
        score *= 0.5
    if not bool(entry.get("drift_evidence_available", False)):
        score *= 0.75
    return round(score, 6)


def _follow_up_action(entry: Mapping[str, Any]) -> str:
    recorded = str(entry.get("recommended_next_action", "")).strip()
    if recorded:
        return recorded
    if bool(entry.get("cross_target_rfi_flagged")):
        return "reject or resolve cross-target RFI recurrence before any repeat observation"
    if not bool(entry.get("drift_evidence_available", False)):
        return "recover drift-rate evidence before follow-up selection"
    return "repeat an ON/OFF cadence at a later epoch and compare persistence"


def _follow_up_evidence(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": str(entry.get("candidate_id", "")),
        "pathway": str(entry.get("pathway", "")),
        "score": float(entry.get("score", 0.0)),
        "snr": float(entry.get("snr", 0.0)),
        "frequency_hz": float(entry.get("frequency_hz", 0.0)),
        "drift_rate_hz_per_sec": float(entry.get("drift_rate_hz_per_sec", 0.0)),
        "cross_target_rfi_flagged": bool(entry.get("cross_target_rfi_flagged", False)),
        "drift_evidence_available": bool(entry.get("drift_evidence_available", False)),
    }


def _canonical_target_id(value: str) -> str | None:
    match = _HIP_PATTERN.search(value)
    return f"HIP{match.group(1)}" if match else None


def _target_has_local_dat(out_dir: Path, target_id: str) -> bool:
    target_dir = out_dir / target_id
    return target_dir.is_dir() and any(target_dir.glob("*.dat"))


def _latest_attempt_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("event") in {"run_started", "run_resumed", "run_failed"}:
            return event
    return None


def _event_status(events: list[dict[str, Any]]) -> str:
    if not events or events[0].get("event") != "created":
        raise SearchLifecycleError("search event history must begin with created")
    event = str(events[-1].get("event", ""))
    if event == "run_completed":
        return "completed"
    if event == "run_failed":
        return "failed_resumable"
    if event in {"run_started", "run_resumed"}:
        return "running_or_interrupted"
    return "pending"


def _append_event(path: Path, event: Mapping[str, Any]) -> None:
    payload = {"schema_version": SEARCH_EVENT_SCHEMA_VERSION, **event}
    data = (json.dumps(payload, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        try:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX)
        except ImportError:  # pragma: no cover - non-POSIX fallback
            pass
        os.write(fd, data)
    finally:
        try:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_UN)
        except ImportError:  # pragma: no cover - non-POSIX fallback
            pass
        os.close(fd)


def _load_events(path: Path, search_id: str) -> list[dict[str, Any]]:
    if not path.is_file():
        raise SearchLifecycleError(f"search event history not found: {path}")
    events: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SearchLifecycleError(f"invalid search event at {path}:{line_number}") from exc
        if event.get("schema_version") not in {
            SEARCH_EVENT_SCHEMA_VERSION,
            *LEGACY_SEARCH_EVENT_SCHEMA_VERSIONS,
        }:
            raise SearchLifecycleError(f"unsupported search event at {path}:{line_number}")
        if event.get("search_id") != search_id:
            raise SearchLifecycleError(f"search event ID mismatch at {path}:{line_number}")
        events.append(event)
    return events


def _write_review_csv(path: Path, targets: list[dict[str, Any]]) -> None:
    fields = [
        "hip",
        "name",
        "mode",
        "ra_deg",
        "dec_deg",
        "estimated_download_gb",
        "target_selection_score",
        "follow_up_priority",
        "execution_kind",
        "follow_up_observation_fulfilled",
        "selection_reason",
        "recommended_next_action",
    ]
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(targets)


def _write_new_json(path: Path, payload: Mapping[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SearchLifecycleError(f"could not load JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise SearchLifecycleError(f"JSON artifact must contain an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    if not isinstance(value, (str, int, float)):
        raise TypeError(f"expected a numeric value, got {type(value).__name__}")
    return float(value)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _run_command(command: Sequence[str]) -> int:
    return subprocess.run(list(command), check=False).returncode
