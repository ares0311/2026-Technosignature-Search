#!/usr/bin/env python3
"""Build the reviewed HIP99427 citizen-science label dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from techno_search.citizen_science_labels import write_citizen_science_dataset
from techno_search.gbt_cadence import load_cadence_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("configs/gbt_hip99427_cadence_v1.json"),
    )
    parser.add_argument(
        "--cadence-csv",
        type=Path,
        default=(
            Path.home()
            / "technosignature-data"
            / "bl_hits"
            / "GBT_HIP99427_2016-12-30_ABACAD.csv"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            Path("examples")
            / "real_labeled"
            / "hip99427_citizen_science_labels_v1.json"
        ),
    )
    args = parser.parse_args()

    manifest = load_cadence_manifest(args.manifest)
    dataset = write_citizen_science_dataset(
        args.cadence_csv,
        args.output,
        manifest=manifest,
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "entry_count": dataset["total_entries"],
                "label_counts": dataset["label_counts"],
                "review_summary": dataset["review_summary"],
                "external_validation_claimed": False,
                "external_submission_authorized": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
