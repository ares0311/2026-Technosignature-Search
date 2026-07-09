"""Rich-backed production scan orchestration for local operations.

The JSON artifacts remain the source of truth. Terminal output is intentionally
compact: live status while work runs, then one completion row per evaluated
target.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any, TextIO, cast

from techno_search.candidate_escalation import escalation_gate_check
from techno_search.cross_target_rfi import cross_target_rfi_summary
from techno_search.production_run_outcomes import (
    PRODUCTION_OUTCOME_DISCLAIMER,
    build_target_status_summary,
    latest_production_run_dir,
    make_production_run_id,
    production_run_file,
    write_production_outcomes,
)
from techno_search.scan_summary import load_candidates_from_batch_dir, scan_summary

REVIEW_DASHBOARD_SCHEMA_VERSION = "operator_review_dashboard_v1"


def review_dashboard_summary(
    *,
    candidates: list[JsonObject] | None = None,
    target_status: Mapping[str, Any] | None = None,
    results_dir: Path | None = None,
    scans_dir: Path | None = None,
    run_dir: Path | None = None,
) -> dict[str, object]:
    """Return a compact operator dashboard from real run or candidate state."""
    source = "no_review_source"
    source_path = ""
    loaded_status: Mapping[str, Any] | None = target_status
    loaded_candidates = candidates
    if loaded_status is None and run_dir is not None:
        loaded_status = production_run_file(run_dir, "target_status")
        source = "target_status"
        source_path = str(run_dir)
    if loaded_status is None and results_dir is not None:
        loaded_candidates = load_candidates_from_batch_dir(results_dir)
        source = "candidate_manifests"
        source_path = str(results_dir)
    if loaded_status is None and loaded_candidates is None and scans_dir is not None:
        latest_run = latest_production_run_dir(scans_dir)
        if latest_run is not None:
            loaded_status = production_run_file(latest_run, "target_status")
            source = "latest_target_status"
            source_path = str(latest_run)
        else:
            source = "no_production_runs"
            source_path = str(scans_dir)
    if loaded_status is None and loaded_candidates is not None:
        loaded_status = build_target_status_summary(
            loaded_candidates,
            run_id="RUN-review-dashboard",
        )
        source = "candidate_manifests" if source == "no_review_source" else source
    if loaded_status is not None and source == "no_review_source":
        source = "target_status"

    entries = _dashboard_entries(loaded_status)
    follow_up_entries = [entry for entry in entries if bool(entry.get("follow_up_required"))]
    rfi_flagged_entries = [
        entry for entry in entries if bool(entry.get("cross_target_rfi_flagged"))
    ]
    candidate_review_entries = [
        entry
        for entry in follow_up_entries
        if entry.get("top_pathway") == "candidate_review_packet"
    ]
    human_review_entries = [
        entry for entry in follow_up_entries if entry.get("top_pathway") == "human_review_queue"
    ]
    action_items = _dashboard_action_items(
        follow_up_count=len(follow_up_entries),
        candidate_review_count=len(candidate_review_entries),
        human_review_count=len(human_review_entries),
        rfi_flagged_count=len(rfi_flagged_entries),
        target_count=len(entries),
    )
    return {
        "schema_version": REVIEW_DASHBOARD_SCHEMA_VERSION,
        "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
        "source": source,
        "source_path": source_path,
        "needs_attention": bool(follow_up_entries),
        "target_count": len(entries),
        "follow_up_required_count": len(follow_up_entries),
        "candidate_review_packet_count": len(candidate_review_entries),
        "human_review_queue_count": len(human_review_entries),
        "cross_target_rfi_flagged_count": len(rfi_flagged_entries),
        "top_follow_up_targets": [
            {
                "index_id": str(entry.get("index_id", "")),
                "target_name": str(entry.get("target_name", "")),
                "target_kind": str(entry.get("target_kind", "")),
                "score": float(entry.get("composite_score", 0.0)),
                "pathway": str(entry.get("top_pathway", "")),
            }
            for entry in sorted(
                follow_up_entries,
                key=lambda item: float(item.get("composite_score", 0.0)),
                reverse=True,
            )[:10]
        ],
        "action_items": action_items,
        "detection_claimed": False,
        "external_submission_allowed": False,
    }

try:  # pragma: no cover - exercised when rich is installed in the runtime env.
    RichConsole: Any | None = import_module("rich.console").Console
    RichTable: Any | None = import_module("rich.table").Table
except ImportError:  # pragma: no cover - deterministic fallback tested instead.
    RichConsole = None
    RichTable = None


PRODUCTION_SCAN_SUMMARY_SCHEMA_VERSION = "production_scan_summary_v1"
PRODUCTION_SCAN_DISCLAIMER = (
    "Production scan terminal summaries are local citizen-science operations "
    "aids only. They do not constitute detections, discoveries, expert review, "
    "external validation, or authorization for external submission."
)

JsonObject = dict[str, Any]
ValidationFunc = Callable[[], JsonObject]
DashboardFunc = Callable[[], JsonObject]


def _dashboard_entries(target_status: Mapping[str, Any] | None) -> list[JsonObject]:
    if not target_status or not bool(target_status.get("ok", True)):
        return []
    entries = target_status.get("entries", [])
    return [dict(entry) for entry in entries if isinstance(entry, Mapping)]


def _dashboard_action_items(
    *,
    follow_up_count: int,
    candidate_review_count: int,
    human_review_count: int,
    rfi_flagged_count: int,
    target_count: int,
) -> list[JsonObject]:
    actions: list[JsonObject] = []
    if candidate_review_count:
        actions.append(
            {
                "action": "review_candidate_packets",
                "count": candidate_review_count,
                "reason": "At least one target entered the candidate review packet pathway.",
            }
        )
    if human_review_count:
        actions.append(
            {
                "action": "review_human_queue",
                "count": human_review_count,
                "reason": "At least one target entered the local human review queue.",
            }
        )
    other_follow_ups = follow_up_count - candidate_review_count - human_review_count
    if other_follow_ups > 0:
        actions.append(
            {
                "action": "review_follow_up_ledger",
                "count": other_follow_ups,
                "reason": "At least one target entered another follow-up pathway.",
            }
        )
    if rfi_flagged_count:
        actions.append(
            {
                "action": "inspect_cross_target_rfi_flags",
                "count": rfi_flagged_count,
                "reason": "Cross-target recurrence was recorded as false-positive evidence.",
            }
        )
    if not actions and target_count:
        actions.append(
            {
                "action": "review_non_detection_ledger",
                "count": target_count,
                "reason": (
                    "No follow-up pathways were recorded; preserve the "
                    "negative-evidence ledger."
                ),
            }
        )
    if not actions:
        actions.append(
            {
                "action": "no_review_items_loaded",
                "count": 0,
                "reason": (
                    "No production targets or candidate manifests were available "
                    "to summarize."
                ),
            }
        )
    return actions


class EmptyProductionScanError(RuntimeError):
    """Raised when a production scan has no candidate manifests to evaluate."""


@dataclass(frozen=True)
class ProductionScanResult:
    """Summary of one local production scan run."""

    run_id: str
    run_dir: Path
    target_count: int
    follow_up_required_count: int
    skipped_step_count: int
    interrupted: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": PRODUCTION_SCAN_SUMMARY_SCHEMA_VERSION,
            "disclaimer": PRODUCTION_SCAN_DISCLAIMER,
            "run_id": self.run_id,
            "run_dir": str(self.run_dir),
            "target_count": self.target_count,
            "follow_up_required_count": self.follow_up_required_count,
            "skipped_step_count": self.skipped_step_count,
            "interrupted": self.interrupted,
            "detection_claimed": False,
            "external_submission_allowed": False,
        }


class ProductionConsole:
    """Small console abstraction with a Rich spinner and no noisy JSON dumps."""

    def __init__(self, stream: TextIO, *, use_rich: bool = True) -> None:
        self.stream = stream
        self._rich_console = (
            RichConsole(file=stream, force_terminal=True, highlight=False)
            if use_rich and RichConsole is not None
            else None
        )

    def print_header(self, run_id: str, run_dir: Path) -> None:
        self.write(f"Production scan {run_id}")
        self.write(f"Artifacts: {run_dir}")
        self.write("Guardrail: local scheduling aid only; no detection or submission claim.")

    @contextmanager
    def step(self, label: str) -> Iterator[None]:
        started = time.monotonic()
        if self._rich_console is not None:
            with self._rich_console.status(label, spinner="dots"):
                yield
        else:
            self.write(f"... {label}")
            yield
        elapsed = time.monotonic() - started
        self.write(f"OK {label} ({elapsed:.1f}s)")

    def skipped(self, label: str) -> None:
        self.write(f"SKIP {label} (existing artifact)")

    def warn(self, message: str) -> None:
        self.write(f"WARN {message}")

    def print_target_rows(self, entries: list[JsonObject]) -> None:
        if not entries:
            self.write("Completed target evaluations: none")
            return
        if self._rich_console is not None and RichTable is not None:
            table = RichTable(title="Completed target evaluations")
            table.add_column("Index")
            table.add_column("Target")
            table.add_column("Kind")
            table.add_column("Follow-up")
            table.add_column("Score", justify="right")
            table.add_column("Pathway")
            for entry in entries:
                table.add_row(
                    str(entry.get("index_id", "")),
                    str(entry.get("target_name", "")),
                    str(entry.get("target_kind", "")),
                    "yes" if entry.get("follow_up_required") else "no",
                    f"{float(entry.get('composite_score', 0.0)):.3f}",
                    str(entry.get("top_pathway", "")),
                )
            self._rich_console.print(table)
            return
        self.write("Completed target evaluations:")
        for entry in entries:
            follow_up = "yes" if entry.get("follow_up_required") else "no"
            score = float(entry.get("composite_score", 0.0))
            self.write(
                f"{entry.get('index_id')} | {entry.get('target_name')} | "
                f"{entry.get('target_kind')} | follow-up={follow_up} | "
                f"score={score:.3f} | {entry.get('top_pathway')}"
            )

    def write(self, message: str) -> None:
        print(message, file=self.stream)


def run_production_scan(
    *,
    results_dir: Path,
    scans_dir: Path,
    stdout: TextIO,
    run_id: str | None = None,
    resume_run_dir: Path | None = None,
    use_rich: bool = True,
    allow_empty: bool = False,
    validate_func: ValidationFunc | None = None,
    dashboard_func: DashboardFunc | None = None,
) -> ProductionScanResult:
    """Run the local production scan workflow with compact terminal output.

    Re-running with ``resume_run_dir`` skips steps whose artifacts already exist.
    A keyboard interrupt leaves completed step artifacts in place and writes an
    interrupted run summary when possible.
    """
    started_at_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    resolved_run_dir, resolved_run_id = _resolve_run(scans_dir, run_id, resume_run_dir)
    console = ProductionConsole(stdout, use_rich=use_rich)
    candidates = load_candidates_from_batch_dir(results_dir)
    if not candidates and not allow_empty:
        console.write(f"ERROR no candidate manifests found in {results_dir}")
        console.write(
            "Run candidate-producing pipeline steps first, or pass --allow-empty "
            "only for diagnostics. No production run artifacts were written."
        )
        raise EmptyProductionScanError(
            f"No candidate manifests found in {results_dir}; production scan aborted."
        )
    resolved_run_dir.mkdir(parents=True, exist_ok=True)
    console.print_header(resolved_run_id, resolved_run_dir)
    skipped_steps = 0
    interrupted = False
    try:
        skipped_steps += _run_json_step(
            console,
            label="validate-all",
            path=resolved_run_dir / "validate_all.json",
            producer=validate_func or _default_validate_all,
        )
        scan_summary_path = resolved_run_dir / f"{resolved_run_id}_scan_summary.json"
        skipped_steps += _run_json_step(
            console,
            label=f"scan-summary ({len(candidates)} candidates)",
            path=scan_summary_path,
            producer=lambda: scan_summary(candidates),
            compatibility_path=resolved_run_dir / "scan_summary.json",
        )
        skipped_steps += _run_json_step(
            console,
            label="cross-target-rfi-summary",
            path=resolved_run_dir / "cross_target_rfi.json",
            producer=lambda: _cross_target_rfi_from_candidates(candidates),
        )
        skipped_steps += _run_escalation_step(
            console,
            results_dir=results_dir,
            run_dir=resolved_run_dir,
        )
        dashboard_path = resolved_run_dir / f"{resolved_run_id}_review_dashboard.json"
        skipped_steps += _run_json_step(
            console,
            label="review-dashboard",
            path=dashboard_path,
            producer=(
                dashboard_func
                if dashboard_func is not None
                else lambda: review_dashboard_summary(candidates=candidates)
            ),
            compatibility_path=resolved_run_dir / "review_dashboard.json",
        )
        target_status = _write_outcomes_and_target_status(
            console,
            results_dir=results_dir,
            run_dir=resolved_run_dir,
            run_id=resolved_run_id,
            started_at_utc=started_at_utc,
            scan_summary_path=scan_summary_path,
            candidates=candidates,
        )
        entries = list(target_status.get("entries", []))
        console.print_target_rows(entries)
    except KeyboardInterrupt:
        interrupted = True
        console.warn(
            "Interrupted by operator. Re-run with "
            f"`prod-scan --resume-run-dir {resolved_run_dir}` to continue."
        )
        target_status = _load_target_status(resolved_run_dir)
        entries = list(target_status.get("entries", []))
    result = ProductionScanResult(
        run_id=resolved_run_id,
        run_dir=resolved_run_dir,
        target_count=len(entries),
        follow_up_required_count=sum(
            1 for entry in entries if bool(entry.get("follow_up_required"))
        ),
        skipped_step_count=skipped_steps,
        interrupted=interrupted,
    )
    _write_json(resolved_run_dir / f"{resolved_run_id}_terminal_summary.json", result.as_dict())
    if interrupted:
        raise KeyboardInterrupt
    console.write(
        f"Done {resolved_run_id}: {result.target_count} target(s), "
        f"{result.follow_up_required_count} follow-up candidate target(s)."
    )
    return result


def production_diagnostics(
    *,
    scans_dir: Path,
    stdout: TextIO,
    use_rich: bool = True,
    validate_func: ValidationFunc | None = None,
    dashboard_func: DashboardFunc | None = None,
) -> JsonObject:
    """Run compact local production diagnostics without dumping large JSON."""
    console = ProductionConsole(stdout, use_rich=use_rich)
    diagnostics: JsonObject = {
        "schema_version": "production_diagnostics_v1",
        "disclaimer": PRODUCTION_SCAN_DISCLAIMER,
        "detection_claimed": False,
        "external_submission_allowed": False,
    }
    with console.step("validate-all"):
        validation = (validate_func or _default_validate_all)()
    diagnostics["validate_all_ok"] = bool(validation.get("ok", False))
    with console.step("review-dashboard"):
        dashboard = (
            dashboard_func()
            if dashboard_func is not None
            else review_dashboard_summary(scans_dir=scans_dir)
        )
    diagnostics["review_dashboard_needs_attention"] = bool(
        dashboard.get("needs_attention", False)
    )
    runs = _production_run_list(scans_dir)
    diagnostics["production_run_count"] = int(runs.get("run_count", 0))
    console.write(
        "Diagnostics: "
        f"validate_all_ok={diagnostics['validate_all_ok']} "
        f"needs_attention={diagnostics['review_dashboard_needs_attention']} "
        f"run_count={diagnostics['production_run_count']}"
    )
    return diagnostics


def _resolve_run(
    scans_dir: Path,
    run_id: str | None,
    resume_run_dir: Path | None,
) -> tuple[Path, str]:
    if resume_run_dir is not None:
        run_dir = Path(resume_run_dir)
        manifest_files = sorted(run_dir.glob("RUN-*_manifest.json"))
        if manifest_files:
            manifest = _load_json(manifest_files[-1])
            resolved_id = str(manifest.get("run_id", run_dir.name))
        else:
            resolved_id = run_dir.name
        return run_dir, resolved_id
    resolved_id = run_id or make_production_run_id()
    return Path(scans_dir) / resolved_id, resolved_id


def _run_json_step(
    console: ProductionConsole,
    *,
    label: str,
    path: Path,
    producer: Callable[[], Mapping[str, Any]],
    compatibility_path: Path | None = None,
) -> int:
    if path.exists():
        console.skipped(label)
        if compatibility_path is not None and not compatibility_path.exists():
            _write_json(compatibility_path, _load_json(path))
        return 1
    with console.step(label):
        data = producer()
        _write_json(path, dict(data))
        if compatibility_path is not None:
            _write_json(compatibility_path, dict(data))
    return 0


def _run_escalation_step(
    console: ProductionConsole,
    *,
    results_dir: Path,
    run_dir: Path,
) -> int:
    summary_path = run_dir / "escalations" / "summary.json"
    if summary_path.exists():
        console.skipped("escalation-gate-check")
        return 1
    with console.step("escalation-gate-check"):
        escalation_dir = run_dir / "escalations"
        escalation_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for manifest_file in sorted(Path(results_dir).glob("**/*.manifest.json")):
            manifest = _load_json(manifest_file)
            if manifest.get("artifact_kind") == "production_run_manifest":
                continue
            pathway = str(manifest.get("recommended_pathway", ""))
            if pathway != "candidate_review_packet":
                continue
            candidate_json = manifest_file.with_suffix("").with_suffix(".json")
            if not candidate_json.exists():
                continue
            candidate_data = _load_json(candidate_json)
            gate = escalation_gate_check(candidate_data)
            _write_json(
                escalation_dir / f"{candidate_json.stem}_escalation.json",
                {
                    "escalation_required": bool(gate["passes"]),
                    "passes": bool(gate["passes"]),
                    "reason": str(gate["reason"]),
                    "pathway": str(gate["pathway"]),
                    "snr": float(gate["snr"]),
                    "multi_epoch_persistence_score": float(
                        gate["multi_epoch_persistence_score"]
                    ),
                    "detection_claimed": False,
                    "external_submission_allowed": False,
                },
            )
            count += 1
        _write_json(
            summary_path,
            {
                "escalation_count": count,
                "disclaimer": PRODUCTION_OUTCOME_DISCLAIMER,
                "detection_claimed": False,
                "external_submission_allowed": False,
            },
        )
    return 0


def _write_outcomes_and_target_status(
    console: ProductionConsole,
    *,
    results_dir: Path,
    run_dir: Path,
    run_id: str,
    started_at_utc: str,
    scan_summary_path: Path,
    candidates: list[JsonObject],
) -> JsonObject:
    target_status_path = run_dir / f"{run_id}_target_status.json"
    if target_status_path.exists():
        console.skipped("prod-write-outcomes")
        return _load_json(target_status_path)
    with console.step("prod-write-outcomes"):
        completed_at_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        write_production_outcomes(
            results_dir=results_dir,
            run_dir=run_dir,
            run_id=run_id,
            started_at_utc=started_at_utc,
            completed_at_utc=completed_at_utc,
            scan_summary_path=scan_summary_path,
        )
        return _load_json(target_status_path)


def _cross_target_rfi_from_candidates(candidates: list[JsonObject]) -> JsonObject:
    by_target: dict[str, list[JsonObject]] = {}
    for candidate in candidates:
        by_target.setdefault(str(candidate.get("target_name", "")), []).append(candidate)
    return cross_target_rfi_summary(list(by_target.values()))


def _production_run_list(scans_dir: Path) -> JsonObject:
    from techno_search.production_run_outcomes import production_run_list

    return production_run_list(scans_dir)


def _default_validate_all() -> JsonObject:
    from techno_search.cli import validate_all

    return cast(JsonObject, validate_all())


def _load_target_status(run_dir: Path) -> JsonObject:
    target_status = production_run_file(run_dir, "target_status")
    return target_status if target_status.get("ok") else {"entries": []}


def _load_json(path: Path) -> JsonObject:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_data = _review_safe_json(data)
    path.write_text(json.dumps(safe_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _review_safe_json(value: Any, *, project_root: Path | None = None) -> Any:
    """Remove local absolute project paths from production scan artifacts."""
    root = project_root or Path.cwd()
    if isinstance(value, Mapping):
        return {
            str(_review_safe_json(key, project_root=root)): _review_safe_json(
                item, project_root=root
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_review_safe_json(item, project_root=root) for item in value]
    if isinstance(value, tuple):
        return [_review_safe_json(item, project_root=root) for item in value]
    if isinstance(value, str):
        return _sanitize_local_path_string(value, root)
    return value


def _sanitize_local_path_string(value: str, project_root: Path) -> str:
    root = project_root.resolve()
    root_variants = {str(root), root.as_posix()}
    sanitized = value
    for root_text in root_variants:
        if sanitized == root_text:
            return "."
        prefix = root_text + os.sep
        posix_prefix = root_text + "/"
        for candidate_prefix in {prefix, posix_prefix}:
            if sanitized.startswith(candidate_prefix):
                return sanitized[len(candidate_prefix):]
        sanitized = sanitized.replace(root_text, "$PROJECT_ROOT")
    return sanitized
