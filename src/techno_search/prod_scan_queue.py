"""Scan history tracking and target queue for production scans.

Scientific guardrail: all records here are local scheduling aids only.
No record constitutes a detection claim or authorizes external submission.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

SCAN_HISTORY_SCHEMA_VERSION = "prod_scan_history_v1"
SCAN_HISTORY_DISCLAIMER = (
    "Scan history records are local scheduling aids only. "
    "No record constitutes a detection claim or authorizes external submission."
)

# Selection-score constants (mirrors background_priority_v0.json)
_BASE_SCORE = 0.50
_NEVER_REVIEWED_BOOST = 0.08
_PRIOR_REVIEW_PENALTY = 0.04
_MAX_PRIOR_REVIEW_PENALTY = 0.12


@dataclass
class ScanHistoryRecord:
    """A single completed production scan record (one per target per run)."""

    target_stem: str
    run_id: str
    scanned_at_utc: str
    score: float
    pathway: str
    dat_file: str
    parent_run_id: str | None = None


@dataclass
class QueueEntry:
    """A candidate target entry in the scan queue, ranked by selection score."""

    dat_file: Path
    target_stem: str
    is_first_scan: bool
    prior_scan_count: int
    last_scanned_at_utc: str | None
    last_score: float | None
    last_pathway: str | None
    selection_score: float
    rationale: str


def discover_dat_files(dat_dir: Path) -> list[Path]:
    """Return sorted .dat files in dat_dir (non-recursive)."""
    if not dat_dir.is_dir():
        return []
    return sorted(f for f in dat_dir.iterdir() if f.is_file() and f.suffix.lower() == ".dat")


def load_scan_history(history_path: Path) -> dict[str, list[ScanHistoryRecord]]:
    """Load NDJSON scan history. Returns {target_stem: [records oldest-first]}."""
    history: dict[str, list[ScanHistoryRecord]] = {}
    if not history_path.exists():
        return history
    for raw in history_path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            d = json.loads(raw)
        except json.JSONDecodeError:
            continue
        stem = d.get("target_stem", "")
        if not stem:
            continue
        history.setdefault(stem, []).append(
            ScanHistoryRecord(
                target_stem=stem,
                run_id=d.get("run_id", ""),
                scanned_at_utc=d.get("scanned_at_utc", ""),
                score=float(d.get("score", 0.0)),
                pathway=d.get("pathway", ""),
                dat_file=d.get("dat_file", ""),
                parent_run_id=d.get("parent_run_id"),
            )
        )
    return history


def append_scan_record(history_path: Path, record: ScanHistoryRecord) -> None:
    """Atomically append a ScanHistoryRecord to the NDJSON history file."""
    history_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            "schema_version": SCAN_HISTORY_SCHEMA_VERSION,
            "target_stem": record.target_stem,
            "run_id": record.run_id,
            "scanned_at_utc": record.scanned_at_utc,
            "score": record.score,
            "pathway": record.pathway,
            "dat_file": record.dat_file,
            "parent_run_id": record.parent_run_id,
        }
    )
    # Use O_APPEND for atomic single-writer safety; advisory lock for multi-process.
    fd = os.open(str(history_path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        try:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
        except ImportError:
            pass
        os.write(fd, (line + "\n").encode("utf-8"))
    finally:
        try:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)
        except ImportError:
            pass
        os.close(fd)


def _selection_score(prior_scan_count: int) -> tuple[float, str]:
    """Return (score, human-readable rationale) for a target with given scan count."""
    if prior_scan_count == 0:
        score = _BASE_SCORE + _NEVER_REVIEWED_BOOST
        rationale = f"never scanned (+{_NEVER_REVIEWED_BOOST:.2f} boost)"
    else:
        penalty = min(_MAX_PRIOR_REVIEW_PENALTY, prior_scan_count * _PRIOR_REVIEW_PENALTY)
        score = _BASE_SCORE - penalty
        times = "time" if prior_scan_count == 1 else "times"
        rationale = f"scanned {prior_scan_count} {times} (-{penalty:.2f} penalty)"
    return round(score, 6), rationale


def build_target_queue(
    dat_dir: Path,
    history_path: Path | None = None,
    *,
    force_rescan: bool = False,
) -> list[QueueEntry]:
    """Return ranked queue of targets for the next scan session.

    Unscanned targets are always included. Previously scanned targets are
    excluded unless force_rescan=True, in which case they rank lower than
    fresh targets (penalty applied per prior scan count).

    Returns list sorted descending by selection_score, then alphabetically
    by target_stem to break ties deterministically.
    """
    dat_files = discover_dat_files(dat_dir)
    history: dict[str, list[ScanHistoryRecord]] = {}
    if history_path is not None:
        history = load_scan_history(history_path)

    entries: list[QueueEntry] = []
    for dat_file in dat_files:
        stem = dat_file.stem
        prior = history.get(stem, [])
        count = len(prior)

        if count > 0 and not force_rescan:
            continue

        last = prior[-1] if prior else None
        score, rationale = _selection_score(count)
        entries.append(
            QueueEntry(
                dat_file=dat_file,
                target_stem=stem,
                is_first_scan=(count == 0),
                prior_scan_count=count,
                last_scanned_at_utc=last.scanned_at_utc if last else None,
                last_score=last.score if last else None,
                last_pathway=last.pathway if last else None,
                selection_score=score,
                rationale=rationale,
            )
        )

    entries.sort(key=lambda e: (-e.selection_score, e.target_stem))
    return entries


def scan_history_summary(
    history_path: Path | None = None,
    dat_dir: Path | None = None,
) -> dict[str, object]:
    """Return a summary dict suitable for CLI JSON output."""
    history: dict[str, list[ScanHistoryRecord]] = {}
    if history_path is not None and history_path.exists():
        history = load_scan_history(history_path)

    total_scans = sum(len(v) for v in history.values())
    unique_targets = len(history)
    re_scanned = sum(1 for v in history.values() if len(v) > 1)

    targets_detail = [
        {
            "target_stem": stem,
            "scan_count": len(records),
            "last_scanned_at_utc": records[-1].scanned_at_utc,
            "last_score": records[-1].score,
            "last_pathway": records[-1].pathway,
        }
        for stem, records in sorted(history.items())
    ]

    pending_count: int | None = None
    if dat_dir is not None:
        dat_files = discover_dat_files(dat_dir)
        pending_count = sum(1 for f in dat_files if f.stem not in history)

    return {
        "schema_version": SCAN_HISTORY_SCHEMA_VERSION,
        "disclaimer": SCAN_HISTORY_DISCLAIMER,
        "history_path": str(history_path) if history_path else None,
        "dat_dir": str(dat_dir) if dat_dir else None,
        "total_scans": total_scans,
        "unique_targets_scanned": unique_targets,
        "re_scanned_targets": re_scanned,
        "pending_targets": pending_count,
        "targets": targets_detail,
    }
