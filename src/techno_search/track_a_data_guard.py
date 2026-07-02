"""Disk-usage guardrails and acquisition manifest for Track A dataset ingestion.

Per docs/technosignature_datasets_agent_brief.md, every Track A data acquisition
step must check total raw/temp/cache usage before downloading and must record a
manifest entry for every acquired file. This module implements those two hard
constraints so acquisition scripts cannot silently exceed the ~100 GB cap or
lose provenance for a downloaded file.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TRACK_A_DISK_GUARD_SCHEMA_VERSION = "track_a_disk_guard_v1"


def log_progress(message: str) -> None:
    """Print a timestamped progress line to stderr.

    Acquisition functions call this around network operations so a slow
    download proves it is alive without polluting the JSON emitted on stdout
    by the `techno-search` CLI, matching the [INFO]/[OK] convention used by
    scripts/ingest_meerkat_hits.py and scripts/download_bl_extended_corpus.sh.
    """

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{timestamp}] {message}", file=sys.stderr, flush=True)
DEFAULT_DISK_BUDGET_BYTES = 100 * 1024**3

DEFAULT_GUARDED_DIRS: tuple[str, ...] = ("data_cache", "tmp_training", "tmp_features")


@dataclass(frozen=True)
class DiskUsageReport:
    """Total size of the guarded disposable Track A directories."""

    schema_version: str
    guarded_dirs: tuple[str, ...]
    dir_sizes_bytes: dict[str, int]
    total_bytes: int
    budget_bytes: int
    within_budget: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "guarded_dirs": list(self.guarded_dirs),
            "dir_sizes_bytes": self.dir_sizes_bytes,
            "total_bytes": self.total_bytes,
            "budget_bytes": self.budget_bytes,
            "within_budget": self.within_budget,
        }


def _dir_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def track_a_disk_usage(
    *,
    project_root: Path | None = None,
    guarded_dirs: Iterable[str] = DEFAULT_GUARDED_DIRS,
    budget_bytes: int = DEFAULT_DISK_BUDGET_BYTES,
) -> DiskUsageReport:
    """Report current disk usage of the Track A disposable data directories."""

    root = project_root or Path.cwd()
    dirs = tuple(guarded_dirs)
    dir_sizes = {name: _dir_size_bytes(root / name) for name in dirs}
    total = sum(dir_sizes.values())
    return DiskUsageReport(
        schema_version=TRACK_A_DISK_GUARD_SCHEMA_VERSION,
        guarded_dirs=dirs,
        dir_sizes_bytes=dir_sizes,
        total_bytes=total,
        budget_bytes=budget_bytes,
        within_budget=total <= budget_bytes,
    )


def check_disk_budget_or_raise(
    *,
    project_root: Path | None = None,
    guarded_dirs: Iterable[str] = DEFAULT_GUARDED_DIRS,
    budget_bytes: int = DEFAULT_DISK_BUDGET_BYTES,
    additional_expected_bytes: int = 0,
) -> DiskUsageReport:
    """Raise RuntimeError if current + expected usage would exceed the budget.

    Acquisition scripts must call this before writing any new file so a
    download is never started once it would push local raw/temp/cache usage
    over the ~100 GB operational constraint from the dataset brief.
    """

    report = track_a_disk_usage(
        project_root=project_root,
        guarded_dirs=guarded_dirs,
        budget_bytes=budget_bytes,
    )
    projected_total = report.total_bytes + additional_expected_bytes
    if projected_total > report.budget_bytes:
        msg = (
            "Track A disk budget would be exceeded: current="
            f"{report.total_bytes} bytes, additional_expected={additional_expected_bytes} "
            f"bytes, projected_total={projected_total} bytes, budget={report.budget_bytes} "
            "bytes. Stop and ask the user before downloading."
        )
        raise RuntimeError(msg)
    return report


@dataclass(frozen=True)
class AcquisitionManifestRecord:
    """One manifest record for an acquired or normalized Track A data file."""

    source_name: str
    source_url: str
    access_method: str
    downloaded_at_utc: str
    local_path: str
    file_size_bytes: int
    row_count: int | None
    auth_required: bool
    license_or_terms: str
    sha256: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "source_url": self.source_url,
            "access_method": self.access_method,
            "downloaded_at_utc": self.downloaded_at_utc,
            "local_path": self.local_path,
            "file_size_bytes": self.file_size_bytes,
            "row_count": self.row_count,
            "auth_required": self.auth_required,
            "license_or_terms": self.license_or_terms,
            "sha256": self.sha256,
            "notes": self.notes,
        }


def append_acquisition_manifest(
    record: AcquisitionManifestRecord,
    manifest_path: Path,
) -> None:
    """Append one manifest record as a JSONL line, creating parent dirs as needed."""

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.as_dict(), sort_keys=True))
        handle.write("\n")


def load_acquisition_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    """Load all manifest records from a JSONL manifest file."""

    if not manifest_path.exists():
        return []
    records = []
    with manifest_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
