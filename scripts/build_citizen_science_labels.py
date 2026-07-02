#!/usr/bin/env python3
"""Build the reviewed HIP99427 citizen-science label dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from techno_search.citizen_science_labels import write_citizen_science_dataset
from techno_search.gbt_cadence import load_cadence_manifest

COMMITTED_FIXTURE_OUTPUT = (
    Path("examples")
    / "real_labeled"
    / "hip99427_citizen_science_labels_v1.json"
)
LOCAL_DEFAULT_OUTPUT = (
    Path("tmp_training")
    / "real_labeled"
    / "hip99427_citizen_science_labels_v1.local.json"
)


def resolve_output_path(
    explicit_output: Path | None,
    *,
    update_committed_fixture: bool,
) -> Path:
    if explicit_output is not None:
        return explicit_output
    if update_committed_fixture:
        return COMMITTED_FIXTURE_OUTPUT
    return LOCAL_DEFAULT_OUTPUT


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
        default=None,
        help=(
            "Output path. Defaults to an ignored local file under tmp_training/ "
            "so normal operator runs remain safe under `git add .`."
        ),
    )
    parser.add_argument(
        "--update-committed-fixture",
        action="store_true",
        help=(
            "Deliberately refresh the committed examples/real_labeled fixture. "
            "Use only when the fixture change is intended for GitHub review."
        ),
    )
    parser.add_argument(
        "--semisupervised-model",
        type=Path,
        default=None,
        help=(
            "Optional fitted SemisupervisedScorer joblib model. Defaults to "
            "data/meerkat_hits/semisupervised_scorer.joblib when present."
        ),
    )
    args = parser.parse_args()
    output_path = resolve_output_path(
        args.output,
        update_committed_fixture=args.update_committed_fixture,
    )

    manifest = load_cadence_manifest(args.manifest)
    dataset = write_citizen_science_dataset(
        args.cadence_csv,
        output_path,
        manifest=manifest,
        semisupervised_model_path=args.semisupervised_model,
    )

    anomaly_scores_by_label: dict[str, list[float]] = {}
    for entry in dataset["entries"]:
        score = entry["candidate"]["features"].get("semisupervised_anomaly_score")
        if score is not None:
            anomaly_scores_by_label.setdefault(entry["label"], []).append(float(score))
    anomaly_score_summary = {
        label: {
            "count": len(scores),
            "min": min(scores),
            "max": max(scores),
            "mean": sum(scores) / len(scores),
        }
        for label, scores in sorted(anomaly_scores_by_label.items())
        if scores
    }

    print(
        json.dumps(
            {
                "output": str(output_path),
                "committed_fixture_update": output_path == COMMITTED_FIXTURE_OUTPUT,
                "entry_count": dataset["total_entries"],
                "label_counts": dataset["label_counts"],
                "review_summary": dataset["review_summary"],
                "anomaly_score_summary_by_label": anomaly_score_summary,
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
