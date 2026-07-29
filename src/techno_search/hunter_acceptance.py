"""Fresh-state controlled acceptance for the canonical Techno-Hunter lifecycle.

The harness replaces only the external archive with a loopback HTTP source.
It still exercises the real persistent slash-command router, CLI parsers,
adaptive selector, immutable search lifecycle, stream/process/evict runner,
turboSETI preprocessing, candidate pipeline, production interpretation,
history/follow-up persistence, fault/resume behavior, and restart reads.
Controlled data are pipeline test evidence only, never training labels or
scientific performance evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import threading
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from pathlib import Path
from typing import Any, TextIO

from techno_search import __version__
from techno_search.hunter_adaptive_discovery import adaptive_discovery_loop
from techno_search.hunter_cli import create_new_search, run_new_search, show_follow_ups
from techno_search.hunter_search import create_search, load_search, run_search
from techno_search.hunter_shell import CommandHandlers, HunterShell
from techno_search.production_scan import run_production_scan
from techno_search.provenance import git_commit
from techno_search.target_priority_queue import (
    TARGET_PRIORITY_QUEUE_FIELDS,
    build_target_priority_manifest,
)

CONTROLLED_ACCEPTANCE_SCHEMA_VERSION = "hunter_controlled_prod_acceptance_v1"
NEW_SEARCH_ID = "SEARCH-20260729T120000Z-ACCEPT01"
FOLLOW_UP_SEARCH_ID = "SEARCH-20260729T120100Z-ACCEPT02"
CONTROLLED_TARGET_ID = "OUTSIDE"
CONTROLLED_FIXTURE_CLASSIFICATION = (
    "controlled pipeline smoke fixture; not training data, a scientific label, "
    "or real-world performance evidence"
)


class ControlledAcceptanceError(RuntimeError):
    """Raised when the controlled production contract is not satisfied."""


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        return


def run_controlled_prod_acceptance(
    *,
    work_dir: Path,
    evidence_path: Path,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Run the controlled acceptance and write a self-contained evidence bundle."""
    try:
        evidence = _portable_value(
            _execute_controlled_acceptance(work_dir=work_dir),
            work_dir,
        )
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (ControlledAcceptanceError, OSError, ValueError) as exc:
        print(f"ERROR: controlled Hunter acceptance failed: {exc}", file=stderr)
        return 1
    print(
        f"Controlled Hunter PROD acceptance passed: {evidence_path}",
        file=stdout,
    )
    return 0


def _execute_controlled_acceptance(*, work_dir: Path) -> dict[str, Any]:
    if work_dir.exists() and any(work_dir.iterdir()):
        raise ControlledAcceptanceError(
            f"acceptance work directory must be absent or empty: {work_dir}"
        )
    work_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[2]
    source_dir = work_dir / "archive_source"
    data_dir = work_dir / "data"
    searches_dir = work_dir / "searches"
    seed_scans_dir = work_dir / "seed_scans"
    manifest_dir = work_dir / "review_manifests"
    history_path = work_dir / "scan_history.ndjson"
    status_path = work_dir / "data_collection_status.json"
    initial_queue_path = work_dir / "initial_queue.csv"
    catalog_path = work_dir / "candidate_catalog.csv"
    source_dir.mkdir(parents=True)
    source_h5 = source_dir / "capture_outside_0001.h5"

    _run_checked(
        [
            str(repo_root / ".venv/bin/python"),
            str(repo_root / "scripts/bl_fetch.py"),
            "synthetic-h5",
            str(source_h5),
        ],
        cwd=repo_root,
    )

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        partial(_QuietHandler, directory=str(source_dir)),
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    source_url = f"http://127.0.0.1:{server.server_port}/{source_h5.name}"
    try:
        _write_controlled_queue(initial_queue_path, source_url=source_url)
        _write_candidate_catalog(catalog_path)
        cached_h5 = data_dir / CONTROLLED_TARGET_ID / source_h5.name
        cached_h5.parent.mkdir(parents=True)
        shutil.copy2(source_h5, cached_h5)
        transcript = StringIO()
        transcript_err = StringIO()
        expansion_holder: dict[str, Any] = {}
        fault = {"injected": False}

        def adaptive_discovery(
            queue_path: Path,
            *,
            target_count: int,
            search_id: str,
            constraints: Mapping[str, Any] | None = None,
        ) -> tuple[Path, dict[str, Any]]:
            def expand_round(
                current: Path,
                rows: Sequence[Mapping[str, str]],
                round_dir: Path,
                round_number: int,
            ) -> tuple[Path, dict[str, Any]]:
                examined = [str(row["target_id"]) for row in rows]
                if examined != [CONTROLLED_TARGET_ID]:
                    raise ControlledAcceptanceError(
                        f"unexpected adaptive expansion candidates: {examined}"
                    )
                updated = round_dir / f"queue_round_{round_number:03d}.csv"
                records = _read_csv(current)
                for record in records:
                    if record["target_id"] == CONTROLLED_TARGET_ID:
                        record["status"] = "raw_download_approval_required"
                        record["local_coverage_status"] = (
                            "not_searched_size_preflight_ok"
                        )
                _write_csv(updated, TARGET_PRIORITY_QUEUE_FIELDS, records)
                return updated, {
                    "adapter": "loopback_archive_metadata_v1",
                    "validity_state": "valid",
                    "examined_target_ids": examined,
                    "promoted_target_ids": [CONTROLLED_TARGET_ID],
                    "queue_sha256": _sha256(updated),
                }

            resolved, report = adaptive_discovery_loop(
                queue_path,
                target_count=target_count,
                work_dir=work_dir / "adaptive_discovery" / search_id,
                expand_round=expand_round,
                constraints=constraints,
            )
            expansion_holder.update(report)
            return resolved, report

        def follow_up_discovery(
            targets: Sequence[Mapping[str, Any]], *, target_count: int
        ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
            selected = [dict(target) for target in targets[:target_count]]
            return selected, {
                "schema_version": "hunter_follow_up_discovery_report_v2",
                "adapter": "controlled_existing_evidence_v1",
                "validity_state": "valid",
                "examined_count": len(targets),
                "selected_count": len(selected),
                "cadence_discovery_count": 0,
            }

        def controlled_create_search(**kwargs: Any) -> dict[str, Any]:
            mode = str(kwargs["mode"])
            kwargs["search_id"] = (
                NEW_SEARCH_ID if mode == "new" else FOLLOW_UP_SEARCH_ID
            )
            kwargs["created_at_utc"] = (
                "2026-07-29T12:00:00Z"
                if mode == "new"
                else "2026-07-29T12:01:00Z"
            )
            return create_search(**kwargs)

        def production_runner(**kwargs: Any) -> Any:
            return run_production_scan(
                **kwargs,
                validate_func=lambda: {
                    "ok": True,
                    "scope": (
                        "controlled acceptance delegates repository-wide validation "
                        "to scripts/run_parallel_validation.py"
                    ),
                },
            )

        def controlled_run_search(**kwargs: Any) -> dict[str, Any]:
            search_id = str(kwargs.get("search_id") or "")
            original_runner = kwargs.pop("command_runner", None)
            if search_id == FOLLOW_UP_SEARCH_ID and not fault["injected"]:
                fault["injected"] = True

                def command_runner(_command: Sequence[str]) -> int:
                    return 9

            else:
                command_runner = original_runner
            return run_search(
                **kwargs,
                data_dir=data_dir,
                command_runner=command_runner,
                production_runner=production_runner,
            )

        handlers = CommandHandlers(
            create=lambda argv: create_new_search(
                argv,
                create_search_func=controlled_create_search,
                adaptive_discovery_func=adaptive_discovery,
                follow_up_discovery_func=follow_up_discovery,
            ),
            run=lambda argv: run_new_search(
                argv,
                run_search_func=controlled_run_search,
            ),
            show_follow_ups=show_follow_ups,
        )
        shell = HunterShell(
            handlers=handlers,
            stdin=StringIO(),
            stdout=transcript,
            stderr=transcript_err,
            interactive=False,
            no_animation=True,
            no_color=True,
            history_path=work_dir / "shell_history",
        )

        env = {
            "TECHNO_DATA_COLLECTION_STATUS_PATH": str(status_path),
            "TECHNO_LOCAL_STORAGE_USAGE_DIRS": str(data_dir),
            "TECHNO_EXTENDED_CORPUS_FREE_SPACE_RESERVE_GB": "0",
            "TECHNO_DOWNLOAD_PROGRESS_INTERVAL_SECONDS": "1",
            "TECHNO_CONTROLLED_ACCEPTANCE": "1",
            "MPLCONFIGDIR": str(work_dir / "matplotlib"),
        }
        with _temporary_environment(env), redirect_stdout(transcript), redirect_stderr(
            transcript_err
        ):
            new_create = shell.dispatch(
                " ".join(
                    [
                        "/Create-New-Search",
                        "--targets 1",
                        "--mode new",
                        f"--candidate-catalog {catalog_path}",
                        f"--priority-queue {initial_queue_path}",
                        f"--scans-dir {seed_scans_dir}",
                        f"--searches-dir {searches_dir}",
                        f"--manifest-dir {manifest_dir}",
                        "--json",
                    ]
                )
            )
            if new_create.exit_code != 0:
                raise ControlledAcceptanceError(transcript_err.getvalue())
            new_run = shell.dispatch(
                " ".join(
                    [
                        "/Run-New-Search",
                        f"--search-id {NEW_SEARCH_ID}",
                        f"--searches-dir {searches_dir}",
                        f"--history-file {history_path}",
                        "--approve-acquisition",
                        "--pipeline-workers 1",
                        "--chunk-size 1",
                        "--json",
                    ]
                )
            )
            if new_run.exit_code != 0:
                raise ControlledAcceptanceError(transcript_err.getvalue())

            dat_paths = sorted((data_dir / CONTROLLED_TARGET_ID).glob("*.dat"))
            if len(dat_paths) != 1:
                raise ControlledAcceptanceError(
                    f"expected one retained turboSETI table, found {len(dat_paths)}"
                )
            _write_seed_follow_up_ledger(seed_scans_dir, dat_paths[0])
            expanded_queue = Path(
                load_search(searches_dir, NEW_SEARCH_ID)["manifest"][
                    "eligibility_queue"
                ]["path"]
            )
            follow_create = shell.dispatch(
                " ".join(
                    [
                        "/Create-New-Search",
                        "--targets 1",
                        "--mode follow-up",
                        f"--candidate-catalog {catalog_path}",
                        f"--priority-queue {expanded_queue}",
                        f"--scans-dir {seed_scans_dir}",
                        f"--searches-dir {searches_dir}",
                        f"--manifest-dir {manifest_dir}",
                        "--json",
                    ]
                )
            )
            if follow_create.exit_code != 0:
                raise ControlledAcceptanceError(transcript_err.getvalue())

            failed_follow_up = shell.dispatch(
                " ".join(
                    [
                        "/Run-New-Search",
                        f"--search-id {FOLLOW_UP_SEARCH_ID}",
                        f"--searches-dir {searches_dir}",
                        f"--history-file {history_path}",
                        "--pipeline-workers 1",
                        "--chunk-size 1",
                        "--json",
                    ]
                )
            )
            if failed_follow_up.exit_code == 0:
                raise ControlledAcceptanceError(
                    "fault injection unexpectedly reported successful completion"
                )
            resumed_follow_up = shell.dispatch(
                " ".join(
                    [
                        "/Run-New-Search",
                        f"--search-id {FOLLOW_UP_SEARCH_ID}",
                        f"--searches-dir {searches_dir}",
                        f"--history-file {history_path}",
                        "--pipeline-workers 1",
                        "--chunk-size 1",
                        "--json",
                    ]
                )
            )
            if resumed_follow_up.exit_code != 0:
                raise ControlledAcceptanceError(transcript_err.getvalue())

            restarted_shell = HunterShell(
                handlers=handlers,
                stdin=StringIO(),
                stdout=transcript,
                stderr=transcript_err,
                interactive=False,
                no_animation=True,
                no_color=True,
                history_path=work_dir / "shell_history_after_restart",
            )
            show_result = restarted_shell.dispatch(
                " ".join(
                    [
                        "/Show-Follow-Ups",
                        f"--priority-queue {expanded_queue}",
                        f"--scans-dir {seed_scans_dir}",
                        f"--searches-dir {searches_dir}",
                        "--json",
                    ]
                )
            )
            if show_result.exit_code != 0:
                raise ControlledAcceptanceError(transcript_err.getvalue())

        return _build_evidence(
            work_dir=work_dir,
            source_h5=source_h5,
            initial_queue_path=initial_queue_path,
            catalog_path=catalog_path,
            searches_dir=searches_dir,
            history_path=history_path,
            status_path=status_path,
            expansion_report=expansion_holder,
            transcript=transcript.getvalue(),
            transcript_err=transcript_err.getvalue(),
        )
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)


def _build_evidence(
    *,
    work_dir: Path,
    source_h5: Path,
    initial_queue_path: Path,
    catalog_path: Path,
    searches_dir: Path,
    history_path: Path,
    status_path: Path,
    expansion_report: Mapping[str, Any],
    transcript: str,
    transcript_err: str,
) -> dict[str, Any]:
    new = load_search(searches_dir, NEW_SEARCH_ID)
    follow = load_search(searches_dir, FOLLOW_UP_SEARCH_ID)
    new_manifest = dict(new["manifest"])
    follow_manifest = dict(follow["manifest"])
    new_status = _load_single(searches_dir / NEW_SEARCH_ID, "*_target_status.json")
    follow_status = _load_single(
        searches_dir / FOLLOW_UP_SEARCH_ID, "*_target_status.json"
    )
    new_candidate = _load_single(
        searches_dir / NEW_SEARCH_ID / "pipeline_results", "*.json",
        exclude_suffixes=(".manifest.json", ".known-explanation.json"),
    )
    follow_candidate = _load_single(
        searches_dir / FOLLOW_UP_SEARCH_ID / "pipeline_results", "*.json",
        exclude_suffixes=(".manifest.json", ".known-explanation.json"),
    )
    new_candidate_manifest = _load_single(
        searches_dir / NEW_SEARCH_ID / "pipeline_results", "*.manifest.json"
    )
    follow_candidate_manifest = _load_single(
        searches_dir / FOLLOW_UP_SEARCH_ID / "pipeline_results", "*.manifest.json"
    )
    observation_provenance = _load_single(
        work_dir / "data", "*.dat.provenance.json"
    )
    data_collection_status = _load_single(work_dir, "data_collection_status.json")
    history = [
        json.loads(line)
        for line in history_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    new_events = list(new["events"])
    follow_events = list(follow["events"])
    selected_new = [str(item["hip"]) for item in new_manifest["targets"]]
    selected_follow = [str(item["hip"]) for item in follow_manifest["targets"]]
    executed_new = sorted(
        {
            CONTROLLED_TARGET_ID
            for entry in new_status["entries"]
            if CONTROLLED_TARGET_ID.casefold()
            in str(entry["target_name"]).casefold()
        }
    )
    executed_follow = sorted(
        {
            CONTROLLED_TARGET_ID
            for entry in follow_status["entries"]
            if CONTROLLED_TARGET_ID.casefold()
            in str(entry["target_name"]).casefold()
        }
    )
    repeated_rankings = [
        build_target_priority_manifest(
            queue_path=Path(new_manifest["eligibility_queue"]["path"]),
            max_targets=1,
            include_statuses=("raw_download_approval_required",),
            generated_at_utc="2026-07-29T12:00:00Z",
        )
        for _ in range(2)
    ]
    assertions = {
        "real_persistent_cli_routing": all(
            command in transcript
            for command in (NEW_SEARCH_ID, FOLLOW_UP_SEARCH_ID)
        ),
        "adaptive_expansion_found_displacing_target": (
            expansion_report.get("round_count") == 1
            and selected_new == [CONTROLLED_TARGET_ID]
        ),
        "weak_best_available_not_threshold_blocked": (
            float(new_manifest["selection"]["quality"]["minimum"]) < 0.01
        ),
        "invalid_and_stale_candidates_excluded": selected_new == [CONTROLLED_TARGET_ID],
        "prior_search_excluded_from_new": "PRIOR" not in selected_new,
        "alias_resolved_to_one_physical_target": (
            str(new_status["entries"][0]["target_name"]).casefold()
            == "capture_outside_0001"
        ),
        "manifested_targets_exactly_executed": (
            selected_new == executed_new and selected_follow == executed_follow
        ),
        "real_preprocessing_and_scoring_executed": (
            new_candidate.get("track") == "radio"
            and new_candidate.get("known_explanation_resolution", {}).get(
                "classification_state"
            )
            in {"known", "unknown", "unresolved"}
            and follow_candidate.get("track") == "radio"
        ),
        "controlled_fixture_provenance_is_explicit": (
            observation_provenance.get("classification")
            == "controlled_acceptance_fixture"
            and observation_provenance.get("controlled_acceptance_only") is True
            and observation_provenance.get("approved_for_local_real_data") is False
            and observation_provenance.get("external_submission_authorized") is False
        ),
        "identical_versioned_inputs_reproduce_ranking": (
            repeated_rankings[0] == repeated_rankings[1]
            and repeated_rankings[0]["targets"][0]["hip"]
            == CONTROLLED_TARGET_ID
        ),
        "partial_failure_resumed_same_run": (
            [event["event"] for event in follow_events]
            == [
                "created",
                "run_started",
                "run_failed",
                "run_resumed",
                "run_completed",
            ]
            and follow_events[1]["run_id"] == follow_events[3]["run_id"]
        ),
        "history_exactly_once_per_completed_search": (
            len(history) == 2
            and {item["parent_run_id"] for item in history}
            == {NEW_SEARCH_ID, FOLLOW_UP_SEARCH_ID}
        ),
        "restart_reloaded_durable_state": (
            new["status"] == "completed" and follow["status"] == "completed"
        ),
        "no_detection_or_external_action_claim": (
            not new_manifest["detection_claimed"]
            and not new_manifest["external_submission_allowed"]
            and not follow_manifest["detection_claimed"]
            and not follow_manifest["external_submission_allowed"]
        ),
    }
    failed = sorted(name for name, passed in assertions.items() if not passed)
    if failed:
        raise ControlledAcceptanceError(
            "controlled acceptance assertions failed: " + ", ".join(failed)
        )

    embedded = {
        "new_search_manifest": new_manifest,
        "new_search_events": new_events,
        "new_target_status": new_status,
        "follow_up_search_manifest": follow_manifest,
        "follow_up_search_events": follow_events,
        "follow_up_target_status": follow_status,
        "new_candidate_interpretation": new_candidate,
        "new_candidate_manifest": new_candidate_manifest,
        "follow_up_candidate_interpretation": follow_candidate,
        "follow_up_candidate_manifest": follow_candidate_manifest,
        "observation_provenance": observation_provenance,
        "data_collection_status": data_collection_status,
        "history": history,
    }
    return {
        "schema_version": CONTROLLED_ACCEPTANCE_SCHEMA_VERSION,
        "release": {
            "app_version": __version__,
            "code_commit": git_commit(),
            "installed_entry_point": "Techno-Hunter",
            "fixture_classification": CONTROLLED_FIXTURE_CLASSIFICATION,
        },
        "request": {
            "new": {"target_count": 1, "mode": "new"},
            "follow_up": {"target_count": 1, "mode": "follow-up"},
        },
        "discovery_coverage": {
            "initial_candidate_count": len(_read_csv(initial_queue_path)),
            "initial_eligible_target_ids": ["WEAK"],
            "expansion_report": dict(expansion_report),
            "accessible_universe_exhausted": bool(
                expansion_report.get("universe_exhausted")
            ),
        },
        "validity_report": {
            "valid_selected_target_ids": [CONTROLLED_TARGET_ID],
            "excluded": {
                "INVALID": "invalid",
                "STALE": "refresh-required",
                "PRIOR": "ineligible_new_due_to_prior_search",
            },
        },
        "ranking_evidence": {
            "selected_target_id": CONTROLLED_TARGET_ID,
            "selected_score": new_manifest["targets"][0][
                "target_selection_score"
            ],
            "initial_cutoff_target_id": "WEAK",
            "initial_cutoff_score": 0.001,
            "absolute_probability_interpretation_allowed": False,
        },
        "selected_targets": {
            "new": selected_new,
            "follow_up": selected_follow,
        },
        "search_runs": {
            "new": {
                "search_id": NEW_SEARCH_ID,
                "event_sequence": [item["event"] for item in new_events],
                "executed_target_ids": executed_new,
            },
            "follow_up": {
                "search_id": FOLLOW_UP_SEARCH_ID,
                "event_sequence": [item["event"] for item in follow_events],
                "executed_target_ids": executed_follow,
                "fault_injected_exit_code": 9,
                "resumed_run_id": follow_events[3]["run_id"],
            },
        },
        "follow_up_state": {
            "source_evidence_consumed": True,
            "final_disposition": follow_events[-1]["follow_up_dispositions"],
            "history_record_count": len(history),
        },
        "provenance_trace": {
            "source_fixture_sha256": _sha256(source_h5),
            "candidate_catalog_sha256": _sha256(catalog_path),
            "initial_queue_sha256": _sha256(initial_queue_path),
            "new_manifest_sha256": _sha256(
                searches_dir / NEW_SEARCH_ID / "manifest.json"
            ),
            "follow_up_manifest_sha256": _sha256(
                searches_dir / FOLLOW_UP_SEARCH_ID / "manifest.json"
            ),
            "data_collection_status_sha256": _sha256(status_path),
            "observation_artifact_sha256": observation_provenance["sha256"],
            "new_candidate_manifest_sha256": _sha256(
                next(
                    (
                        searches_dir
                        / NEW_SEARCH_ID
                        / "pipeline_results"
                    ).glob("**/*.manifest.json")
                )
            ),
            "follow_up_candidate_manifest_sha256": _sha256(
                next(
                    (
                        searches_dir
                        / FOLLOW_UP_SEARCH_ID
                        / "pipeline_results"
                    ).glob("**/*.manifest.json")
                )
            ),
            "selected_target_trace": {
                "target_id": CONTROLLED_TARGET_ID,
                "candidate_catalog_source": new_manifest["candidate_catalog"],
                "eligibility_queue_source": new_manifest["eligibility_queue"],
                "identity_resolution": "resolved_existing_queue_alias",
                "validity_state": "valid",
                "ranking_contribution": new_manifest["targets"][0][
                    "target_selection_score"
                ],
                "selection_reason": new_manifest["targets"][0]["selection_reason"],
                "execution_target_name": new_status["entries"][0]["target_name"],
                "observation_provenance_classification": observation_provenance[
                    "classification"
                ],
                "new_interpretation_candidate_id": new_candidate["candidate_id"],
                "follow_up_interpretation_candidate_id": follow_candidate[
                    "candidate_id"
                ],
                "history_parent_searches": [
                    item["parent_run_id"] for item in history
                ],
            },
            "transformations": [
                "loopback HTTP archive adapter",
                "real stream_process_evict runner",
                "real turboSETI 2.3.2 preprocessing",
                "real radio candidate pipeline and known-explanation resolution",
                "real production composite interpretation",
            ],
        },
        "assertion_results": [
            {"assertion": name, "passed": passed}
            for name, passed in assertions.items()
        ],
        "embedded_artifacts": embedded,
        "transcript": {
            "stdout": _portable_text(transcript, work_dir),
            "stderr": _portable_text(transcript_err, work_dir),
        },
        "limitations": [
            CONTROLLED_FIXTURE_CLASSIFICATION,
            "External archive transport is replaced by a loopback HTTP source.",
            "Repository-wide validation is executed separately by the canonical validator.",
            "The bounded live-source smoke remains the immutable v1.2.69 evidence.",
        ],
        "detection_claimed": False,
        "discovery_claimed": False,
        "expert_review_claimed": False,
        "external_validation_claimed": False,
        "external_submission_allowed": False,
    }


def _write_controlled_queue(path: Path, *, source_url: str) -> None:
    specs = [
        (CONTROLLED_TARGET_ID, 0.009, "queued_metadata_discovery", source_url),
        ("WEAK", 0.001, "raw_download_approval_required", source_url),
        ("INVALID", 0.999, "invalid", source_url),
        ("STALE", 0.998, "metadata_refresh_required", source_url),
        ("PRIOR", 0.5, "already_acquired_local_cache", source_url),
    ]
    rows: list[dict[str, str]] = []
    for target_id, score, status, url in specs:
        row = dict.fromkeys(TARGET_PRIORITY_QUEUE_FIELDS, "")
        row.update(
            {
                "target_id": target_id,
                "project": "controlled_acceptance",
                "source": "controlled_versioned_candidate_universe",
                "catalog_ids": target_id,
                "ra_deg": "10.0",
                "dec_deg": "20.0",
                "object_type": "Star",
                "data_products_available": "hdf5_size_preflight_ok",
                "estimated_download_gb": "0.004",
                "search_category": "controlled_pipeline_acceptance",
                "total_priority": f"{score:.6f}",
                "target_selection_score": f"{score:.6f}",
                "background_target_priority_score": f"{score:.6f}",
                "priority_config_version": "background_priority_v0",
                "status": status,
                "local_coverage_status": (
                    "searched_by_project"
                    if status == "already_acquired_local_cache"
                    else "not_searched_size_preflight_ok"
                ),
                "source_hdf5_url": url,
                "notes": CONTROLLED_FIXTURE_CLASSIFICATION,
            }
        )
        rows.append(row)
    _write_csv(path, TARGET_PRIORITY_QUEUE_FIELDS, rows)


def _write_candidate_catalog(path: Path) -> None:
    fields = [
        "schema_version",
        "candidate_id",
        "archive_target_label",
        "identity_status",
        "ranking_eligible",
    ]
    rows = [
        {
            "schema_version": "bl_archive_candidate_catalog_v1",
            "candidate_id": f"CONTROLLED-{index:03d}",
            "archive_target_label": target_id,
            "identity_status": "resolved_existing_queue_alias",
            "ranking_eligible": "true" if target_id in {"OUTSIDE", "WEAK"} else "false",
        }
        for index, target_id in enumerate(
            ("OUTSIDE", "WEAK", "INVALID", "STALE", "PRIOR"), 1
        )
    ]
    _write_csv(path, fields, rows)


def _write_seed_follow_up_ledger(scans_dir: Path, dat_path: Path) -> None:
    run_id = "RUN-2026-07-29_115900Z-SEED-hunter-search"
    run_dir = scans_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "production_follow_ups_v2",
        "artifact_kind": "production_follow_ups",
        "source_project": "Techno-Hunter",
        "run_id": run_id,
        "entries": [
            {
                "follow_up_id": "FU-CONTROLLED-001",
                "candidate_id": "capture_outside_0001",
                "target_name": "capture_outside_0001",
                "pathway": "human_review_queue",
                "score": 0.8,
                "snr": 20.0,
                "frequency_hz": 8.421e9,
                "drift_rate_hz_per_sec": 0.38,
                "drift_evidence_available": True,
                "cross_target_rfi_flagged": False,
                "source_data_path": str(dat_path),
                "recommended_next_action": (
                    "reanalyze retained controlled evidence to verify durable "
                    "follow-up consumption"
                ),
            }
        ],
        "detection_claimed": False,
        "external_submission_allowed": False,
    }
    path = run_dir / f"{run_id}_follow_ups.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_single(
    root: Path,
    pattern: str,
    *,
    exclude_suffixes: Sequence[str] = (),
) -> dict[str, Any]:
    paths = [
        path
        for path in root.glob(f"**/{pattern}")
        if not any(path.name.endswith(suffix) for suffix in exclude_suffixes)
    ]
    if len(paths) != 1:
        raise ControlledAcceptanceError(
            f"expected one {pattern} artifact under {root}, found {len(paths)}"
        )
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ControlledAcceptanceError(f"expected JSON object in {paths[0]}")
    return payload


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path, fieldnames: Sequence[str], rows: Sequence[Mapping[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _portable_text(value: str, work_dir: Path) -> str:
    return value.replace(str(work_dir), "$ACCEPTANCE_WORK_DIR")


def _portable_value(value: Any, work_dir: Path) -> Any:
    if isinstance(value, str):
        return _portable_text(value, work_dir)
    if isinstance(value, list):
        return [_portable_value(item, work_dir) for item in value]
    if isinstance(value, dict):
        return {
            key: _portable_value(item, work_dir)
            for key, item in value.items()
        }
    return value


def _run_checked(command: Sequence[str], *, cwd: Path) -> None:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ControlledAcceptanceError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )


@contextmanager
def _temporary_environment(values: Mapping[str, str]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, old_value in previous.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value
