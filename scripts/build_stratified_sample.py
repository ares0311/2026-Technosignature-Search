#!/usr/bin/env python3
"""build_stratified_sample.py — Stratified random sample of BL HPRC targets.

Generates a scientifically defensible target manifest for the extended corpus
download by sampling from the BL High-Priority Candidate (HPRC) target list
(Isaacson et al. 2017, PASP 129, 054501) using stratified random sampling
across stellar distance, spectral type, galactic latitude, and exoplanet-host
status.

Methodology
-----------
Strata are defined by the Cartesian product of:
  - Distance bin: near (≤8 pc), mid (8–20 pc), far (20–50 pc)
  - Spectral class: F, G, K, M  (first letter of MK type)
  - Exoplanet host: yes (1), no (0)

This yields up to 24 cells.  Within each cell, targets are ordered by distance
(nearest first) then sampled without replacement using the specified random
seed.  Cells with fewer targets than the per-cell quota are included in full.

The output manifest records the sampling seed, date, strata definitions,
selected targets, and the seed CSV provenance so the selection is exactly
reproducible.

Usage
-----
    .venv/bin/python scripts/build_stratified_sample.py \\
        [--seed SEED] \\
        [--per-stratum N] \\
        [--max-targets N] \\
        [--seed-csv PATH] \\
        [--output PATH]

Outputs
-------
    data/target_sample_manifest.json   — machine-readable selection manifest
    (stdout)                           — human-readable summary

Scientific guardrail
--------------------
The manifest is a scheduling aid.  No selected target constitutes a detection
claim or authorizes external submission.  All outputs are local reproducibility
records only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SEED_CSV = REPO_ROOT / "data" / "bl_hprc_seed_targets.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "target_sample_manifest.json"

SCHEMA_VERSION = "target_sample_manifest_v1"
DISCLAIMER = (
    "This manifest is a local scheduling aid produced by stratified random "
    "sampling from the BL HPRC target list (Isaacson et al. 2017). "
    "No selected target constitutes a detection claim or authorizes external "
    "submission. Targets with no BL open-data availability will be skipped "
    "silently by the download script."
)

# Strata definitions
DISTANCE_BINS = [
    ("near", 0.0, 8.0),
    ("mid", 8.0, 20.0),
    ("far", 20.0, 50.0),
]
SPEC_CLASSES = ["F", "G", "K", "M"]
EXOPLANET_VALUES = [0, 1]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _parse_spec_class(spec_type: str) -> str:
    """Return the leading letter of the MK spectral type, upper-cased."""
    for ch in spec_type.strip():
        if ch.isalpha():
            return ch.upper()
    return "?"


def _assign_distance_bin(dist_pc: float) -> str | None:
    for label, lo, hi in DISTANCE_BINS:
        if lo <= dist_pc < hi:
            return label
    return None


def load_seed_targets(csv_path: Path) -> list[dict]:
    """Parse the seed CSV, returning one dict per target row."""
    rows = []
    with csv_path.open(encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            rows.append(stripped)

    if not rows:
        raise ValueError(f"No data rows in {csv_path}")

    reader = csv.DictReader(rows)
    targets = []
    for row in reader:
        try:
            dist_pc = float(row["dist_pc"])
            exoplanet = int(row["exoplanet"])
        except (KeyError, ValueError) as exc:
            print(f"[WARN] Skipping malformed row {row}: {exc}", file=sys.stderr)
            continue
        targets.append(
            {
                "hip": row["hip"].strip(),
                "name": row.get("name", "").strip(),
                "ra_deg": float(row.get("ra_deg", 0)),
                "dec_deg": float(row.get("dec_deg", 0)),
                "dist_pc": dist_pc,
                "spec_type": row.get("spec_type", "").strip(),
                "spec_class": _parse_spec_class(row.get("spec_type", "")),
                "bv": float(row.get("bv", 0)),
                "gal_lat": float(row.get("gal_lat", 0)),
                "exoplanet": exoplanet,
                "bl_paper": row.get("bl_paper", "").strip(),
                "distance_bin": _assign_distance_bin(dist_pc),
            }
        )
    return targets


def build_strata(
    targets: list[dict],
    per_stratum: int,
    rng: random.Random,
) -> dict[str, list[dict]]:
    """Partition targets into strata and sample within each."""
    # Build stratum → target list
    cells: dict[str, list[dict]] = {}
    for dist_bin, _, _ in DISTANCE_BINS:
        for sc in SPEC_CLASSES:
            for ep in EXOPLANET_VALUES:
                key = f"{dist_bin}:{sc}:exoplanet={ep}"
                cells[key] = []

    ungrouped = []
    for t in targets:
        dist_bin = t.get("distance_bin")
        sc = t.get("spec_class", "?")
        ep = t.get("exoplanet", 0)
        key = f"{dist_bin}:{sc}:exoplanet={ep}"
        if key in cells:
            cells[key].append(t)
        else:
            ungrouped.append(t)

    if ungrouped:
        print(
            f"[INFO] {len(ungrouped)} targets fell outside defined strata "
            f"(distance ≥50 pc or unknown spec class) — excluded from selection.",
            file=sys.stderr,
        )

    # Sort each cell by distance (nearest first) then sample
    selected: dict[str, list[dict]] = {}
    for key, cell in cells.items():
        cell_sorted = sorted(cell, key=lambda t: t["dist_pc"])
        n = min(per_stratum, len(cell_sorted))
        chosen = rng.sample(cell_sorted, n) if n > 0 else []
        if chosen:
            selected[key] = sorted(chosen, key=lambda t: t["dist_pc"])

    return selected


def build_manifest(
    seed_csv: Path,
    per_stratum: int,
    max_targets: int | None,
    seed: int,
) -> dict:
    """Return the full sampling manifest dict."""
    rng = random.Random(seed)
    targets = load_seed_targets(seed_csv)
    strata = build_strata(targets, per_stratum, rng)

    all_selected: list[dict] = []
    for cell_targets in strata.values():
        all_selected.extend(cell_targets)

    # Deduplicate by HIP (a star might appear in multiple cells if spec_class
    # is ambiguous — shouldn't happen with the current CSV but guard it).
    seen_hips: set[str] = set()
    deduped: list[dict] = []
    for t in all_selected:
        if t["hip"] not in seen_hips:
            seen_hips.add(t["hip"])
            deduped.append(t)

    # Sort final list for deterministic ordering: distance_bin then dist_pc then HIP
    bin_order = {b: i for i, (b, _, _) in enumerate(DISTANCE_BINS)}
    deduped.sort(
        key=lambda t: (
            bin_order.get(t.get("distance_bin", ""), 99),
            t["dist_pc"],
            t["hip"],
        )
    )

    if max_targets is not None and len(deduped) > max_targets:
        deduped = deduped[:max_targets]

    strata_summary = {
        k: [t["hip"] for t in v] for k, v in sorted(strata.items()) if v
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "disclaimer": DISCLAIMER,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "sampling": {
            "random_seed": seed,
            "per_stratum_quota": per_stratum,
            "max_targets": max_targets,
            "distance_bins_pc": [
                {"label": lb, "lo": lo, "hi": hi}
                for lb, lo, hi in DISTANCE_BINS
            ],
            "spectral_classes": SPEC_CLASSES,
            "strata_count": len(
                [k for k, v in strata.items() if v]
            ),
        },
        "seed_csv": {
            "path": str(seed_csv),
            "sha256": _sha256_file(seed_csv),
            "total_targets": len(targets),
        },
        "selection_summary": {
            "selected_count": len(deduped),
            "strata_with_targets": strata_summary,
        },
        "targets": deduped,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build stratified random sample of BL HPRC targets."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42 — document this in any publication).",
    )
    parser.add_argument(
        "--per-stratum",
        type=int,
        default=2,
        help="Targets to select per stratum cell (default: 2).",
    )
    parser.add_argument(
        "--max-targets",
        type=int,
        default=None,
        help="Cap on total selected targets (default: no cap).",
    )
    parser.add_argument(
        "--seed-csv",
        type=Path,
        default=DEFAULT_SEED_CSV,
        help=f"Path to seed target CSV (default: {DEFAULT_SEED_CSV}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output manifest path (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary without writing output file.",
    )
    args = parser.parse_args(argv)

    if not args.seed_csv.exists():
        print(
            f"[ERROR] Seed CSV not found: {args.seed_csv}",
            file=sys.stderr,
        )
        return 1

    manifest = build_manifest(
        seed_csv=args.seed_csv,
        per_stratum=args.per_stratum,
        max_targets=args.max_targets,
        seed=args.seed,
    )

    sel = manifest["selection_summary"]
    print(f"[INFO]  Seed CSV: {args.seed_csv} ({manifest['seed_csv']['total_targets']} targets)")
    print(f"[INFO]  Random seed: {manifest['sampling']['random_seed']}")
    print(f"[INFO]  Per-stratum quota: {manifest['sampling']['per_stratum_quota']}")
    print(f"[INFO]  Strata with targets: {manifest['sampling']['strata_count']}")
    print(f"[INFO]  Selected targets: {sel['selected_count']}")
    print()
    print("Selected targets (ordered by distance bin then distance):")
    for t in manifest["targets"]:
        ep_flag = " [exoplanet host]" if t["exoplanet"] else ""
        print(
            f"  {t['hip']:10s}  {t['name'][:20]:20s}  "
            f"{t['spec_type']:8s}  {t['dist_pc']:6.1f} pc  "
            f"|b|={abs(t['gal_lat']):4.1f}°{ep_flag}"
        )

    print()
    print(f"[INFO]  Disclaimer: {manifest['disclaimer']}")

    if args.dry_run:
        print("[DRY-RUN] Output not written.")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\n[OK]    Manifest written to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
