"""Merge multiple citizen-science label JSON files into one combined training dataset.

Closes KNOWN_LIMITATIONS #1: Single-target generalization gap — combines labels
from multiple GBT ABACAD cadences to improve cross-target coverage.

Usage:
    python scripts/combine_citizen_science_labels.py \
        --inputs examples/real_labeled/hip99427_citizen_science_labels_v1.json \
        --output examples/real_labeled/combined_citizen_science_labels_v1.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

COMBINED_SCHEMA_VERSION = "labeled_candidates_citizen_science_combined_v1"

SUPPORTED_SCHEMA_VERSIONS = {
    "labeled_candidates_citizen_science_v1",
    "labeled_candidates_citizen_science_combined_v1",
}

COMBINED_DISCLAIMER = (
    "Combined citizen-science label dataset merged from multiple GBT ABACAD cadences. "
    "Labels are conservative citizen-science operational annotations derived from cadence "
    "behavior. These labels are not expert labels, not external validation, not detections, "
    "not discoveries, and does not constitute authorization for external submission. "
    "not expert labels — cross-target generalization is improved but not independently "
    "validated. External submission is not authorized."
)

DEFAULT_INPUTS = [
    REPO_ROOT / "examples" / "real_labeled" / "hip99427_citizen_science_labels_v1.json"
]
DEFAULT_OUTPUT = (
    REPO_ROOT / "examples" / "real_labeled" / "combined_citizen_science_labels_v1.json"
)


def _file_sha256(path: Path) -> str:
    """Compute sha256 of a file reading in 1 MB chunks."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _load_label_file(path: Path) -> dict[str, Any]:
    """Load and validate a citizen-science label file.

    Raises:
        ValueError: If schema_version is not in SUPPORTED_SCHEMA_VERSIONS.
        ValueError: If entries list is empty.
        FileNotFoundError: If the file does not exist.
    """
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    schema = data.get("schema_version", "")
    if schema not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(
            f"unsupported schema_version: {schema!r} in {path}. "
            f"Supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )
    entries = data.get("entries", [])
    if not entries:
        raise ValueError(f"no entries found in {path}")
    return data


def combine_label_files(
    input_paths: list[Path],
    *,
    deduplicate: bool = True,
) -> dict[str, Any]:
    """Merge citizen-science label files into one combined dataset.

    Args:
        input_paths: List of paths to citizen-science label JSON files.
        deduplicate: If True (default), skip entries with duplicate candidate_id.

    Returns:
        Combined dataset dict with schema_version, entries, and source provenance.
    """
    seen_ids: set[str] = set()
    all_entries: list[dict[str, Any]] = []
    duplicates_skipped = 0
    source_datasets: list[dict[str, Any]] = []
    label_counts: dict[str, int] = {}
    per_source_label_counts: dict[str, dict[str, int]] = {}

    for path in input_paths:
        path = Path(path)
        data = _load_label_file(path)
        sha256 = _file_sha256(path)
        schema = data.get("schema_version", "")
        entries = list(data.get("entries", []))

        source_label_counts: dict[str, int] = defaultdict(int)
        entries_added = 0

        for entry in entries:
            candidate = entry.get("candidate", {})
            cid = str(
                candidate.get("candidate_id")
                or entry.get("candidate_id")
                or id(entry)
            )
            if deduplicate and cid in seen_ids:
                duplicates_skipped += 1
                continue
            seen_ids.add(cid)
            all_entries.append(entry)
            entries_added += 1
            lbl = str(entry.get("label", entry.get("audit_label", "unknown")))
            label_counts[lbl] = label_counts.get(lbl, 0) + 1
            source_label_counts[lbl] += 1

        per_source_label_counts[path.name] = dict(source_label_counts)

        source_datasets.append({
            "filename": path.name,
            "sha256": sha256,
            "schema_version": schema,
            "entry_count": len(entries),
            "entries_added": entries_added,
            "datasets": data.get("dataset_classification", "unknown"),
        })

    return {
        "schema_version": COMBINED_SCHEMA_VERSION,
        "disclaimer": COMBINED_DISCLAIMER,
        "generated_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "total_entries": len(all_entries),
        "label_counts": label_counts,
        "duplicate_entries_skipped": duplicates_skipped,
        "source_datasets": source_datasets,
        "per_source_label_counts": per_source_label_counts,
        "external_submission_authorized": False,
        "entries": all_entries,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for combining citizen-science label files."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Merge multiple citizen-science label JSON files into a combined dataset."
    )
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=False,
        help="Input citizen-science label JSON files (default: HIP99427 labels).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output combined label JSON file path.",
    )
    parser.add_argument(
        "--no-deduplicate",
        action="store_true",
        help="Disable deduplication by candidate_id.",
    )
    args = parser.parse_args(argv)

    input_paths = [Path(p) for p in args.inputs] if args.inputs else DEFAULT_INPUTS

    # Validate all input files exist before processing
    missing = [p for p in input_paths if not Path(p).exists()]
    if missing:
        for p in missing:
            print(f"[ERROR] Input file not found: {p}", file=sys.stderr)
        return 1

    try:
        result = combine_label_files(
            input_paths,
            deduplicate=not args.no_deduplicate,
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    total = result["total_entries"]
    skipped = result["duplicate_entries_skipped"]
    sources = len(result["source_datasets"])
    print(
        f"[OK] Combined {total} entries from {sources} source(s); "
        f"{skipped} duplicates skipped. Output: {out_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
