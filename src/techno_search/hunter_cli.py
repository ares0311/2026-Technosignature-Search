"""Polished shell entry points for the durable Hunter search lifecycle."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from io import StringIO
from pathlib import Path
from typing import Any, TextIO

from techno_search.hunter_adaptive_discovery import prepare_production_new_target_queue
from techno_search.hunter_follow_up_discovery import (
    FollowUpDiscoveryError,
    discover_follow_up_targets,
)
from techno_search.hunter_search import (
    SearchApprovalRequired,
    SearchLifecycleError,
    create_search,
    follow_up_registry,
    run_search,
)


def create_new_search(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="Create-New-Search")
    parser.add_argument("--targets", type=int, required=True)
    parser.add_argument("--mode", choices=("new", "follow-up"), required=True)
    parser.add_argument(
        "--candidate-catalog",
        type=Path,
        default=Path("data_selection/bl_archive_candidate_catalog.csv"),
    )
    parser.add_argument(
        "--priority-queue",
        type=Path,
        default=Path("data_selection/target_priority_queue.csv"),
    )
    parser.add_argument("--scans-dir", type=Path, default=Path("results/scans"))
    parser.add_argument("--searches-dir", type=Path, default=Path("results/searches"))
    parser.add_argument(
        "--manifest-dir", type=Path, default=Path("results/search_manifests")
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--min-ra-deg", type=float)
    parser.add_argument("--max-ra-deg", type=float)
    parser.add_argument("--min-dec-deg", type=float)
    parser.add_argument("--max-dec-deg", type=float)
    parser.add_argument("--min-abs-galactic-latitude-deg", type=float)
    parser.add_argument("--max-estimated-download-gb", type=float)
    parser.add_argument(
        "--target-prefix",
        action="append",
        dest="target_prefixes",
        help="Restrict selection to one or more catalog-ID prefixes (repeatable).",
    )
    args = parser.parse_args(argv)
    try:
        manifest = create_search(
            target_count=args.targets,
            mode=args.mode,
            candidate_catalog_path=args.candidate_catalog,
            queue_path=args.priority_queue,
            scans_dir=args.scans_dir,
            searches_dir=args.searches_dir,
            manifest_dir=args.manifest_dir,
            adaptive_discovery=(
                lambda queue_path, target_count, search_id, constraints: (
                    prepare_production_new_target_queue(
                        queue_path,
                        target_count=target_count,
                        search_id=search_id,
                        constraints=constraints,
                    )
                )
            )
            if args.mode == "new"
            else None,
            follow_up_discovery=(
                lambda targets, target_count: discover_follow_up_targets(
                    targets, target_count=target_count
                )
            )
            if args.mode == "follow-up"
            else None,
            constraints={
                "min_ra_deg": args.min_ra_deg,
                "max_ra_deg": args.max_ra_deg,
                "min_dec_deg": args.min_dec_deg,
                "max_dec_deg": args.max_dec_deg,
                "min_abs_galactic_latitude_deg": (
                    args.min_abs_galactic_latitude_deg
                ),
                "max_estimated_download_gb": args.max_estimated_download_gb,
                "target_prefixes": args.target_prefixes or (),
            },
        )
    except (FollowUpDiscoveryError, SearchLifecycleError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        _print_created_search(manifest, args.searches_dir, args.manifest_dir, sys.stdout)
    return 0


def run_new_search(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="Run-New-Search")
    parser.add_argument("--search-id")
    parser.add_argument("--searches-dir", type=Path, default=Path("results/searches"))
    parser.add_argument("--history-file", type=Path, default=Path("results/scan_history.ndjson"))
    parser.add_argument("--chunk-size", type=int, default=25)
    parser.add_argument("--pipeline-workers", type=int, default=12)
    parser.add_argument("--no-rich", action="store_true")
    parser.add_argument(
        "--approve-acquisition",
        action="store_true",
        help="Approve the immutable manifest's bounded raw archive acquisition.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run_search(
            searches_dir=args.searches_dir,
            search_id=args.search_id,
            approve_acquisition=args.approve_acquisition,
            chunk_size=args.chunk_size,
            pipeline_workers=args.pipeline_workers,
            history_path=args.history_file,
            stdout=StringIO() if args.json else sys.stdout,
            use_rich=not args.no_rich and not args.json,
            command_runner=_quiet_command_runner if args.json else None,
        )
    except SearchApprovalRequired as exc:
        print(f"APPROVAL REQUIRED: {exc}", file=sys.stderr)
        return 2
    except (SearchLifecycleError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            f"Completed {result['search_id']} as {result['run_id']}: "
            f"{result['target_count']} target(s), "
            f"{result['follow_up_required_count']} follow-up target(s)."
        )
    return 0


def show_follow_ups(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="Show-Follow-Ups")
    parser.add_argument("--scans-dir", type=Path, default=Path("results/scans"))
    parser.add_argument("--searches-dir", type=Path, default=Path("results/searches"))
    parser.add_argument(
        "--priority-queue",
        type=Path,
        default=Path("data_selection/target_priority_queue.csv"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        registry = follow_up_registry(
            scans_dirs=(args.scans_dir, args.searches_dir),
            queue_path=args.priority_queue,
        )
    except SearchLifecycleError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(registry, indent=2, sort_keys=True))
    else:
        _print_follow_ups(registry, sys.stdout)
    return 0


def _print_created_search(
    manifest: dict[str, Any], searches_dir: Path, manifest_dir: Path, out: TextIO
) -> None:
    search_id = str(manifest["search_id"])
    targets = list(manifest["targets"])
    print(
        f"Created pending {manifest['mode']} search {search_id} with {len(targets)} target(s).",
        file=out,
    )
    print(f"Durable manifest: {searches_dir / search_id / 'manifest.json'}", file=out)
    print(
        f"Candidate universe: {manifest['candidate_catalog']['candidate_count']}; "
        f"eligible: {manifest['eligibility_queue']['viable_candidate_count']}; "
        f"projected acquisition: {manifest['selection']['projected_download_gb']:.3f} GB",
        file=out,
    )
    shortfall = manifest["selection"].get("shortfall")
    if shortfall:
        print(
            f"SHORTFALL: returned {shortfall['returned_count']} of "
            f"{shortfall['requested_count']} requested target(s) -- {shortfall['reason']}.",
            file=out,
        )
    if len(targets) > 100:
        print(f"Review CSV: {manifest_dir / f'{search_id}.csv'}", file=out)
        return
    print(
        "Rank | Target | Type | Distance ly | Spectral | Exoplanet | "
        "Prior searches | Prior provenance | Score | GB | Execution | Selection reason",
        file=out,
    )
    for rank, target in enumerate(targets, 1):
        score = (
            target.get("follow_up_priority", 0.0)
            if manifest["mode"] == "follow-up"
            else target.get("target_selection_score", 0.0)
        )
        print(
            " | ".join(
                [
                    str(rank),
                    str(target.get("hip", "")),
                    str(target.get("object_type", "") or "unknown"),
                    (
                        f"{float(target['distance_light_years']):.2f}"
                        if target.get("distance_light_years") is not None
                        else "unknown"
                    ),
                    str(target.get("spectral_type", "") or "unknown"),
                    str(target.get("exoplanet_host", "unknown")),
                    str(target.get("prior_search_count", 0)),
                    "; ".join(
                        value
                        for value in (
                            str(
                                target.get("prior_search_provenance_summary", "")
                            ).strip(),
                            str(target.get("cross_project_prior_search", "")).strip(),
                        )
                        if value
                    )
                    or "none",
                    f"{float(score):.3f}",
                    f"{float(target.get('estimated_download_gb') or 0.0):.3f}",
                    str(target.get("execution_kind", "")),
                    str(target.get("selection_reason", "")),
                ]
            ),
            file=out,
        )


def _print_follow_ups(registry: dict[str, Any], out: TextIO) -> None:
    entries = list(registry["eligible_entries"])
    print(
        f"{len(entries)} actionable follow-up target(s) from "
        f"{registry['source_ledger_count']} durable run ledger(s); "
        f"{registry['unresolved_identity_count']} row(s) excluded for unresolved identity.",
        file=out,
    )
    if not entries:
        print("Follow-up targets: none", file=out)
        return
    print("Target | Priority | Evidence | Prior searches | Recommended next action", file=out)
    for entry in entries:
        evidence = entry["evidence"]
        evidence_text = (
            f"score={evidence['score']:.3f}, snr={evidence['snr']:.2f}, "
            f"rfi={'yes' if evidence['cross_target_rfi_flagged'] else 'no'}"
        )
        print(
            " | ".join(
                [
                    str(entry["hip"]),
                    f"{float(entry['follow_up_priority']):.3f}",
                    evidence_text,
                    str(len(entry["prior_search_provenance"])),
                    str(entry["recommended_next_action"]),
                ]
            ),
            file=out,
        )


def _quiet_command_runner(command: Sequence[str]) -> int:
    """Keep a machine-readable run clean; the batch runner writes its own log."""
    completed = subprocess.run(
        list(command),
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode
