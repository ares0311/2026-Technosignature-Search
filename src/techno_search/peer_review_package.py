"""Public reproducibility review package generator.

Generates a structured package of pipeline methodology documentation,
scoring logic summaries, real-label evidence, and example candidate reports
suitable for independent citizen-science reproduction.

The package is a local review artifact only.  Generating a package does
not authorize external submission, constitute a detection claim, or claim
expert review or external validation.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from techno_search.labeled_dataset import labeled_dataset_summary

PEER_REVIEW_PACKAGE_DISCLAIMER = (
    "This public reproducibility package is a local documentation artifact. "
    "It includes synthetic examples and a summary of citizen-science labels "
    "derived from one real cadence. Generating it does not constitute a "
    "detection claim, does not authorize external submission, does not claim "
    "expert review, and does not claim external validation."
)

PEER_REVIEW_ITEMS_REQUIRED = [
    "Pipeline scoring logic (src/techno_search/scoring.py)",
    "Baseline model logic (src/techno_search/baseline_model.py)",
    "False-positive class descriptions (docs/CALIBRATION_FIXTURES.md)",
    "Scoring threshold description (configs/scoring_v0.json)",
    "Example candidate reports (examples/batch_reports/)",
    "Validation gate descriptions (docs/VALIDATION.md)",
    "Production readiness assessment (docs/PRODUCTION_READINESS.md)",
    "Citizen-science review protocol (docs/CITIZEN_SCIENCE_REVIEW.md)",
    "Real cadence label summary (examples/real_labeled/)",
]


def generate_peer_review_package(
    output_dir: Path,
    *,
    include_scoring_config: bool = True,
    include_example_reports: bool = True,
    include_calibration_info: bool = True,
) -> dict[str, Any]:
    """Generate a structured peer review package in output_dir.

    Creates:
      - PEER_REVIEW_README.md — overview and instructions for reviewer
      - methodology_summary.json — pipeline methodology description
      - scoring_config_snapshot.json — current scoring thresholds (read-only copy)
      - example_candidates/ — symlinks or copies of example candidate reports
      - review_checklist.md — checklist of items for reviewer to verify

    Returns a summary dict with the generated file paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(tz=UTC).isoformat()
    files_written: list[str] = []

    # 1. README for the reviewer
    readme_path = output_dir / "PEER_REVIEW_README.md"
    readme_path.write_text(
        _render_readme(generated_at), encoding="utf-8"
    )
    files_written.append(str(readme_path))

    # 2. Methodology summary JSON
    methodology_path = output_dir / "methodology_summary.json"
    methodology_path.write_text(
        json.dumps(_methodology_summary(generated_at), indent=2),
        encoding="utf-8",
    )
    files_written.append(str(methodology_path))

    # 3. Scoring config snapshot
    if include_scoring_config:
        config_path = _find_scoring_config()
        if config_path and config_path.exists():
            snapshot_path = output_dir / "scoring_config_snapshot.json"
            snapshot_path.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
            files_written.append(str(snapshot_path))

    # 4. Calibration info
    if include_calibration_info:
        calib_path = _find_calibration_fixtures()
        if calib_path and calib_path.exists():
            calib_dest = output_dir / "calibration_fixtures_snapshot.json"
            calib_dest.write_text(calib_path.read_text(encoding="utf-8"), encoding="utf-8")
            files_written.append(str(calib_dest))

    # 5. Example reports (copy a summary)
    if include_example_reports:
        examples_summary = _collect_example_report_summaries()
        examples_path = output_dir / "example_candidate_summaries.json"
        examples_path.write_text(
            json.dumps(examples_summary, indent=2), encoding="utf-8"
        )
        files_written.append(str(examples_path))

    # 6. Review checklist
    checklist_path = output_dir / "review_checklist.md"
    checklist_path.write_text(_render_checklist(), encoding="utf-8")
    files_written.append(str(checklist_path))

    # 7. Real citizen-science label summary
    label_path = _find_real_labeled_dataset()
    if label_path is not None:
        label_summary_path = output_dir / "real_labeled_dataset_summary.json"
        label_summary_path.write_text(
            json.dumps(labeled_dataset_summary(label_path), indent=2),
            encoding="utf-8",
        )
        files_written.append(str(label_summary_path))

    return {
        "disclaimer": PEER_REVIEW_PACKAGE_DISCLAIMER,
        "ok": True,
        "output_dir": str(output_dir),
        "generated_at": generated_at,
        "files_written": files_written,
        "file_count": len(files_written),
        "reviewer_instructions": (
            "See PEER_REVIEW_README.md in the output directory for instructions."
        ),
        "items_for_review": PEER_REVIEW_ITEMS_REQUIRED,
    }


def _methodology_summary(generated_at: str) -> dict[str, Any]:
    return {
        "disclaimer": PEER_REVIEW_PACKAGE_DISCLAIMER,
        "generated_at": generated_at,
        "pipeline_description": (
            "Three-track technosignature candidate scoring pipeline: "
            "(1) radio narrowband drift-rate search via turboSETI hit tables, "
            "(2) infrared excess analysis via Gaia+WISE cross-match, "
            "(3) archival anomaly detection via historical catalog comparison."
        ),
        "scoring_model": (
            "Rule-based v0 scoring model. Features extracted per track; "
            "composite scores computed for signal reality, false-positive "
            "probability, and provenance completeness. "
            "Pathway assignment: known_object_annotation, "
            "do_not_submit_false_positive, human_review_queue, "
            "follow_up_target, github_reproducibility_only."
        ),
        "false_positive_classes": [
            "rfi_band_overlap",
            "satellite_recurrence",
            "instrumental_artifact",
            "agn_blend",
            "dust_yso",
            "extragalactic_contamination",
            "archival_image_artifact",
            "proper_motion",
            "survey_depth_mismatch",
            "variable_star",
        ],
        "data_status": (
            "one checksum-verified GBT ABACAD cadence ingested; 124 exact "
            "frequency/drift groups carry deterministic citizen-science labels"
        ),
        "thresholds_status": "synthetic v0 defaults — not calibrated against real noise",
        "labeled_dataset_status": (
            "124 real-observation operational labels admitted for local evaluation; "
            "not expert labels"
        ),
        "external_validation_status": (
            "none claimed; citizen-science reproducibility review complete"
        ),
        "production_readiness": "~45-50% (see docs/PRODUCTION_READINESS.md)",
        "tier_1_gaps": [
            "Scoring thresholds not calibrated against real noise",
            "Real RFI database not approved",
        ],
    }


def _render_readme(generated_at: str) -> str:
    return f"""\
# Public Reproducibility Review Package

**Generated:** {generated_at}
**Status:** DEVELOPMENT SCAFFOLD — NOT FOR EXTERNAL SUBMISSION

## Disclaimer

{PEER_REVIEW_PACKAGE_DISCLAIMER}

## What Is This?

This package contains documentation and evidence from the
2026-Technosignature-Search pipeline for independent reproduction.

## Items for Review

{chr(10).join(f'- {item}' for item in PEER_REVIEW_ITEMS_REQUIRED)}

## Files in This Package

| File | Description |
|---|---|
| `methodology_summary.json` | Pipeline methodology, scoring model description, and current gaps |
| `scoring_config_snapshot.json` | Current scoring thresholds (v0 synthetic defaults) |
| `calibration_fixtures_snapshot.json` | False-positive class calibration fixtures |
| `example_candidate_summaries.json` | Example scored candidate outputs |
| `review_checklist.md` | Items for the reviewer to verify |
| `real_labeled_dataset_summary.json` | Conservative summary of the admitted real cadence labels |

## Important Notes for Reviewer

1. **One real cadence is included as summarized label evidence.** It is not a
   detection claim or expert-labeled benchmark.
2. **Thresholds are synthetic v0 defaults.** They have not been calibrated
   against real GBT noise distributions.
3. **The real labels are operational citizen-science labels.** They are
   deterministic and independently audited by a second method, not expert labels.
4. **This is not a detection claim.** No technosignature candidates are being
   reported. This package is for review of pipeline methodology only.

## Questions for Reviewer

- Are the false-positive classes comprehensive for L-band GBT observations?
- Are the scoring feature definitions scientifically justified?
- Are the pathway assignment thresholds conservative enough?
- What additional validation steps are needed before processing real data?
- Can another person reproduce all 124 labels from the documented rules?
"""


def _render_checklist() -> str:
    return """\
# Public Reproducibility Review Checklist

For each item below, a reproducer should mark: OK / ISSUE / NOT_APPLICABLE

## Pipeline Methodology
- [ ] Scoring feature definitions are scientifically justified
- [ ] Feature extraction is correct for each track (radio/infrared/anomaly)
- [ ] False-positive class definitions are comprehensive
- [ ] Pathway assignment logic is conservative (false-positive-first)

## Scoring Thresholds
- [ ] Current synthetic v0 thresholds are clearly marked as preliminary
- [ ] Threshold calibration procedure (docs/THRESHOLD_CALIBRATION.md) is sound
- [ ] Plan for real noise distribution analysis is reasonable

## Data Quality
- [ ] Input validation checks are appropriate for the data format
- [ ] RFI database admission gates are appropriate
- [ ] Labeled dataset structure is appropriate for the intended use

## Scientific Language
- [ ] No premature detection claims
- [ ] Conservative language throughout
- [ ] Uncertainty and negative evidence preserved
- [ ] No external submission authorized

## Reproducibility
- [ ] Pipeline outputs are deterministic
- [ ] Provenance tracking is complete
- [ ] Schema versioning is in place
- [ ] All 124 real cadence labels reproduce from the documented rules
- [ ] Primary and audit methods remain independently implemented

## Comments
(Reviewer adds comments here)
"""


def _find_scoring_config() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    path = root / "configs" / "scoring_v0.json"
    return path if path.exists() else None


def _find_calibration_fixtures() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    path = root / "tests" / "fixtures" / "calibration_false_positives.json"
    return path if path.exists() else None


def _find_real_labeled_dataset() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    path = (
        root
        / "examples"
        / "real_labeled"
        / "hip99427_citizen_science_labels_v1.json"
    )
    return path if path.exists() else None


def _collect_example_report_summaries() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    batch_manifest_path = root / "examples" / "batch_reports" / "batch_manifest.json"
    if batch_manifest_path.exists():
        try:
            data: dict[str, Any] = json.loads(batch_manifest_path.read_text(encoding="utf-8"))
            return data
        except Exception:  # noqa: BLE001
            pass
    return {"note": "No example batch reports found."}
