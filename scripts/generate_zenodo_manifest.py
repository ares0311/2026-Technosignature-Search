#!/usr/bin/env python3
"""
generate_zenodo_manifest.py

Builds a Zenodo-compatible archive manifest (JSON) for the
2026 Technosignature Search citizen-science pipeline.

Outputs:
  results/zenodo_manifest.json   — machine-readable manifest with SHA-256
                                   checksums; suitable for Zenodo deposit

Usage:
  .venv/bin/python scripts/generate_zenodo_manifest.py [OPTIONS]

Options:
  --data-dir PATH   Path to local calibration data (default: ~/technosignature-data)
  --output PATH     Output manifest path (default: results/zenodo_manifest.json)
  --dry-run         Print manifest to stdout; do not write file

Scientific guardrail:
  This manifest is a reproducibility aid only. No entry constitutes a
  detection claim or authorizes external submission. All files listed
  are calibration aids, pipeline source code, or provenance records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files/dirs included from the repository
REPO_INCLUDE_PATTERNS: list[str] = [
    "src/**/*.py",
    "schemas/**/*.json",
    "tests/fixtures/**/*.json",
    "tests/fixtures/**/*.csv",
    "tests/fixtures/**/*.dat",
    "tests/fixtures/**/*.metadata.json",
    "configs/**/*.json",
    "docs/*.md",
    "README.md",
    "CHANGELOG.md",
    "pyproject.toml",
    "results/scans/**/*.json",
]

# Explicit single files always included
REPO_INCLUDE_FILES: list[str] = [
    "docs/EXTERNAL_SUBMISSION_PROTOCOL.md",
    "docs/CALIBRATION_TRANSFER_PROTOCOL.md",
    "docs/PRODUCTION_READINESS.md",
    "docs/PIPELINE_SPEC.md",
    "docs/SCORING_MODEL.md",
    "docs/CITIZEN_SCIENCE_REVIEW.md",
]

# Prefixes never included even if matched by a pattern
EXCLUDE_PREFIXES: list[str] = [
    ".venv/",
    ".git/",
    ".claude/",
    "__pycache__/",
    "node_modules/",
    "*.egg-info/",
]

# Local calibration data filenames that should be included if present
CALIBRATION_DAT_NAMES: list[str] = [
    # HIP99427 ABACAD cadence
    "guppi_59046_HIP99427",
    "guppi_59046_HIP100670",
    "guppi_59046_HIP99560",
    "guppi_59046_HIP99759",
    # Voyager 1 turboSETI test
    "bl_turboSETI_test.dat",
    "voyager1_hits.dat",
]

ZENODO_METADATA = {
    "title": "2026 Technosignature Search — Citizen-Science Pipeline v0.77",
    "description": (
        "Source code, schema artifacts, calibration fixtures, turboSETI hit tables, "
        "labeled candidate dataset, and provenance records for the 2026 "
        "Technosignature Search citizen-science pipeline. "
        "Calibrated against 213 real GBT hits from 5 cadences, 5 targets, 2 epochs. "
        "Scoring model v1 achieves 77.42%% diagnostic agreement on 124 real HIP99427 labels. "
        "Scientific guardrail: this archive is a reproducibility aid. No entry "
        "constitutes a detection claim, confirmed technosignature, or authorization "
        "to submit. No expert or peer review has occurred."
    ),
    "upload_type": "software",
    "access_right": "open",
    "license": "MIT",
    "keywords": [
        "SETI",
        "technosignature",
        "radio astronomy",
        "citizen science",
        "turboSETI",
        "Breakthrough Listen",
        "GBT",
        "pipeline",
        "calibration",
    ],
    "notes": (
        "This deposit corresponds to Milestone 77 (Escalation Gate Hardening + "
        "External Submission Protocol). All Tier 1 and Tier 2 production gaps are closed. "
        "Expert review and peer review remain unclaimed."
    ),
    "scientific_guardrail": (
        "No result in this archive constitutes a confirmed technosignature. "
        "No scoring result authorizes external submission. "
        "Extraordinary claims require extraordinary evidence."
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_excluded(rel: str) -> bool:
    for prefix in EXCLUDE_PREFIXES:
        if prefix.endswith("/"):
            if rel.startswith(prefix.rstrip("/")):
                return True
        elif rel == prefix:
            return True
    return False


def collect_repo_files() -> list[dict]:
    entries: list[dict] = []
    seen: set[Path] = set()

    for pattern in REPO_INCLUDE_PATTERNS:
        for p in sorted(REPO_ROOT.glob(pattern)):
            if not p.is_file():
                continue
            rel = p.relative_to(REPO_ROOT).as_posix()
            if _is_excluded(rel):
                continue
            if p in seen:
                continue
            seen.add(p)
            entries.append({
                "path": rel,
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
                "source": "repository",
            })

    for fname in REPO_INCLUDE_FILES:
        p = REPO_ROOT / fname
        if p.is_file() and p not in seen:
            seen.add(p)
            entries.append({
                "path": fname,
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
                "source": "repository",
            })

    return entries


def collect_data_files(data_dir: Path) -> list[dict]:
    if not data_dir.exists():
        return []
    entries: list[dict] = []
    for dat_pattern in CALIBRATION_DAT_NAMES:
        for p in sorted(data_dir.rglob("*")):
            if not p.is_file():
                continue
            if dat_pattern in p.name:
                entries.append({
                    "path": str(p),
                    "size_bytes": p.stat().st_size,
                    "sha256": sha256_file(p),
                    "source": "local_calibration_data",
                    "note": (
                        "Local calibration data from Breakthrough Listen public archive. "
                        "Not committed to repository. Must be downloaded separately."
                    ),
                })
    return entries


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / "technosignature-data",
        help="Path to local calibration data directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "results" / "zenodo_manifest.json",
        help="Output manifest path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print manifest to stdout; do not write file",
    )
    args = parser.parse_args()

    print("[START] Collecting repository files...")
    t0 = time.time()
    repo_files = collect_repo_files()
    print(f"[INFO]  {len(repo_files)} repository files collected")

    print(f"[INFO]  Scanning calibration data dir: {args.data_dir}")
    data_files = collect_data_files(args.data_dir)
    if data_files:
        print(f"[INFO]  {len(data_files)} local calibration file(s) found")
    else:
        print("[WARN]  No local calibration files found — archive will be incomplete")
        print(f"[WARN]  Expected .dat files in: {args.data_dir}")

    all_files = repo_files + data_files
    total_bytes = sum(f["size_bytes"] for f in all_files)

    manifest = {
        "schema_version": "zenodo_archive_manifest_v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pipeline_milestone": 77,
        "pipeline_version": "v0.77.0",
        "scientific_guardrail": ZENODO_METADATA["scientific_guardrail"],
        "zenodo_metadata": ZENODO_METADATA,
        "summary": {
            "total_files": len(all_files),
            "total_bytes": total_bytes,
            "repository_files": len(repo_files),
            "local_calibration_files": len(data_files),
        },
        "files": all_files,
    }

    elapsed = time.time() - t0
    print(f"[DONE]  Manifest built in {elapsed:.1f}s")
    print(f"[INFO]  Total files: {len(all_files)}, total size: {total_bytes:,} bytes")

    if args.dry_run:
        print(json.dumps(manifest, indent=2))
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK]   Manifest written: {args.output}")
    print("")
    print("Next step (human action — requires Zenodo account):")
    print("  1. Review manifest: cat results/zenodo_manifest.json | jq '.summary'")
    print("  2. Upload to Zenodo via web UI or Zenodo API")
    print("  3. Record the DOI in docs/ZENODO_ARCHIVE_MANIFEST.md")
    print("  4. This satisfies P5 of docs/EXTERNAL_SUBMISSION_PROTOCOL.md")
    print("     (public reproducibility package posted)")


if __name__ == "__main__":
    main()
