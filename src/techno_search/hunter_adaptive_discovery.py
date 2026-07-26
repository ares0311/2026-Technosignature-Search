"""Adaptive metadata discovery for canonical Hunter new-target selection."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from techno_search.hunter_constraints import (
    normalize_constraints,
    target_matches_constraints,
)
from techno_search.target_priority_queue import (
    TARGET_PRIORITY_MANIFEST_SCHEMA_VERSION,
    default_target_priority_queue_inputs,
    read_target_priority_queue,
    write_target_priority_queue,
    write_target_priority_size_preflight,
)

ELIGIBLE_STATUS = "raw_download_approval_required"
EXPANDABLE_STATUSES = frozenset(
    {"queued_metadata_discovery", "size_preflight_required"}
)
RoundExpander = Callable[
    [Path, Sequence[Mapping[str, str]], Path, int], tuple[Path, dict[str, Any]]
]


class AdaptiveDiscoveryError(ValueError):
    """Raised when current metadata cannot support a safe top-N decision."""


def adaptive_discovery_loop(
    queue_path: Path,
    *,
    target_count: int,
    work_dir: Path,
    expand_round: RoundExpander,
    constraints: Mapping[str, Any] | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Expand until top-N is supported or the accessible universe is exhausted."""
    if target_count <= 0:
        raise ValueError("target_count must be positive")
    work_dir.mkdir(parents=True, exist_ok=True)
    active_constraints = normalize_constraints(constraints)
    rounds: list[dict[str, Any]] = []
    batch_size = max(60, target_count)
    current_queue = queue_path
    previous_signature: tuple[tuple[str, str], ...] | None = None

    while True:
        state = _selection_support_state(
            current_queue, target_count, active_constraints
        )
        if state["sufficient"]:
            public_state = {
                key: value for key, value in state.items() if key != "expandable_rows"
            }
            return current_queue, {
                "strategy": "adaptive_score_bound_v1",
                "sufficient": True,
                "universe_exhausted": bool(state["universe_exhausted"]),
                "round_count": len(rounds),
                "rounds": rounds,
                "constraints": active_constraints,
                **public_state,
            }
        expandable = list(state["expandable_rows"])
        signature = tuple((row["target_id"], row["status"]) for row in expandable)
        if signature == previous_signature:
            raise AdaptiveDiscoveryError(
                "adaptive discovery made no eligibility progress; current metadata "
                "requires refresh before top-N sufficiency can be established"
            )
        previous_signature = signature
        selected_rows = expandable[:batch_size]
        current_queue, evidence = expand_round(
            current_queue, selected_rows, work_dir, len(rounds) + 1
        )
        rounds.append(
            {
                "round": len(rounds) + 1,
                "examined_count": len(selected_rows),
                "minimum_examined_score": min(
                    float(row["target_selection_score"]) for row in selected_rows
                ),
                **evidence,
            }
        )
        batch_size *= 2


def prepare_production_new_target_queue(
    queue_path: Path,
    *,
    target_count: int,
    search_id: str,
    constraints: Mapping[str, Any] | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Run the installed product's real adaptive discovery implementation."""
    work_dir = Path("results/adaptive_discovery") / search_id
    work_queue = work_dir / "target_priority_queue.csv"
    work_dir.mkdir(parents=True, exist_ok=True)
    default_queue = Path("data_selection/target_priority_queue.csv")
    if queue_path.resolve() == default_queue.resolve():
        inputs = default_target_priority_queue_inputs(
            cross_project_siblings=("exo_hunter",)
        )
        write_target_priority_queue(work_queue, **inputs)
    else:
        shutil.copy2(queue_path, work_queue)

    return adaptive_discovery_loop(
        work_queue,
        target_count=target_count,
        work_dir=work_dir,
        expand_round=_production_expand_round,
        constraints=constraints,
    )


def _selection_support_state(
    queue_path: Path,
    target_count: int,
    constraints: Mapping[str, Any],
) -> dict[str, Any]:
    rows = read_target_priority_queue(queue_path)
    eligible = sorted(
        (
            row
            for row in rows
            if row.get("status") == ELIGIBLE_STATUS
            and target_matches_constraints(row, constraints)
        ),
        key=_ranking_key,
    )
    expandable = sorted(
        (
            row
            for row in rows
            if row.get("status") in EXPANDABLE_STATUSES
            and target_matches_constraints(
                row, constraints, allow_unknown_download_size=True
            )
        ),
        key=_ranking_key,
    )
    cutoff = (
        float(eligible[target_count - 1]["target_selection_score"])
        if len(eligible) >= target_count
        else None
    )
    relevant = [
        row
        for row in expandable
        if cutoff is None or float(row["target_selection_score"]) > cutoff
    ]
    sufficient = not relevant and (len(eligible) >= target_count or not expandable)
    return {
        "candidate_count": len(rows),
        "eligible_count": len(eligible),
        "requested_count": target_count,
        "selection_cutoff_score": cutoff,
        "highest_unresolved_score": (
            float(expandable[0]["target_selection_score"]) if expandable else None
        ),
        "expandable_count": len(expandable),
        "universe_exhausted": not expandable,
        "sufficient": sufficient,
        "expandable_rows": relevant if relevant else expandable,
    }


def _production_expand_round(
    queue_path: Path,
    rows: Sequence[Mapping[str, str]],
    work_dir: Path,
    round_number: int,
) -> tuple[Path, dict[str, Any]]:
    default_seed = Path("data/bl_hprc_full_seed_targets.csv")
    known_ids = {
        row["target_id"]
        for row in read_target_priority_queue(queue_path)
    }
    default_ids = {
        row.get("target_id") or row.get("hip") or ""
        for row in read_target_priority_queue(Path("data_selection/target_priority_queue.csv"))
    }
    if known_ids != default_ids:
        raise AdaptiveDiscoveryError(
            "adaptive expansion of a custom queue requires a complete source-evidence "
            "configuration; provide a fully resolved queue or use the canonical queue"
        )

    prefix = work_dir / f"round_{round_number:03d}"
    discovery_manifest_path = Path(f"{prefix}_discovery_manifest.json")
    discovery_result_path = Path(f"{prefix}_discovery_result.json")
    discovery_stdout_path = Path(f"{prefix}_discovery_stdout.log")
    discovery_stderr_path = Path(f"{prefix}_discovery_stderr.log")
    size_manifest_path = Path(f"{prefix}_size_preflight_manifest.json")
    size_report_path = Path(f"{prefix}_size_preflight_report.json")
    discovery_rows = [
        row for row in rows if row.get("status") == "queued_metadata_discovery"
    ]
    size_rows = [
        row for row in rows if row.get("status") == "size_preflight_required"
    ]

    if discovery_rows:
        _write_json(
            discovery_manifest_path,
            {
                "schema_version": TARGET_PRIORITY_MANIFEST_SCHEMA_VERSION,
                "targets": [_manifest_target(row) for row in discovery_rows],
            },
        )
        command = [
            "bash",
            "scripts/download_bl_extended_corpus.sh",
            "--discover-only",
            "--manifest",
            str(discovery_manifest_path),
            "--discovery-result-output",
            str(discovery_result_path),
        ]
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        discovery_stdout_path.write_text(completed.stdout, encoding="utf-8")
        discovery_stderr_path.write_text(completed.stderr, encoding="utf-8")
        if completed.returncode != 0:
            raise AdaptiveDiscoveryError(
                f"adaptive metadata discovery round {round_number} failed with "
                f"exit code {completed.returncode}; see {discovery_stderr_path}"
            )
        discovery = json.loads(discovery_result_path.read_text(encoding="utf-8"))
        size_rows.extend(
            {
                "target_id": str(item["target"]),
                "source_hdf5_url": str(item["url"]),
            }
            for item in discovery.get("available_targets", [])
        )

    if size_rows:
        _write_json(
            size_manifest_path,
            {
                "schema_version": TARGET_PRIORITY_MANIFEST_SCHEMA_VERSION,
                "targets": [_manifest_target(row) for row in size_rows],
            },
        )
        write_target_priority_size_preflight(
            size_report_path,
            manifest_path=size_manifest_path,
            workers=4,
        )

    next_queue = work_dir / f"target_priority_queue_round_{round_number:03d}.csv"
    inputs = default_target_priority_queue_inputs(
        extra_discovery_result_paths=(
            (discovery_result_path,) if discovery_result_path.is_file() else ()
        ),
        extra_size_preflight_report_paths=(
            (size_report_path,) if size_report_path.is_file() else ()
        ),
        cross_project_siblings=("exo_hunter",),
    )
    inputs["seed_csv_path"] = default_seed
    write_target_priority_queue(next_queue, **inputs)
    artifacts = [
        path
        for path in (
            discovery_manifest_path,
            discovery_result_path,
            discovery_stdout_path,
            discovery_stderr_path,
            size_manifest_path,
            size_report_path,
        )
        if path.is_file()
    ]
    return next_queue, {
        "artifacts": [
            {"path": str(path), "sha256": _sha256(path)} for path in artifacts
        ],
        "queue_path": str(next_queue),
        "queue_sha256": _sha256(next_queue),
    }


def _manifest_target(row: Mapping[str, str]) -> dict[str, Any]:
    return {
        "hip": row.get("target_id") or row.get("hip"),
        "source_hdf5_url": row.get("source_hdf5_url", ""),
        "target_selection_score": float(row.get("target_selection_score") or 0),
    }


def _ranking_key(row: Mapping[str, str]) -> tuple[float, float, str]:
    return (
        -float(row["target_selection_score"]),
        -float(row.get("total_priority") or 0),
        str(row["target_id"]),
    )


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
