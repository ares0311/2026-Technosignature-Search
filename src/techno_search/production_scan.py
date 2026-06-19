"""Rich-backed production scan orchestration for local operations.

The JSON artifacts remain the source of truth. Terminal output is intentionally
compact: live status while work runs, then one completion row per evaluated
target.
"""

from __future__ import annotations

import json
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
    make_production_run_id,
    production_run_file,
    write_production_outcomes,
)
from techno_search.review_dashboard import review_dashboard_summary
from techno_search.scan_summary import load_candidates_from_batch_dir, scan_summary

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
            producer=dashboard_func or review_dashboard_summary,
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
        dashboard = (dashboard_func or review_dashboard_summary)()
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
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
