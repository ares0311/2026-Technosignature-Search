"""Command-line interface for synthetic candidate scoring."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from techno_search.calibration import load_calibration_fixtures, summarize_calibration_fixtures
from techno_search.reporting import (
    DEFAULT_SCORING_CONFIG_VERSION,
    candidate_packet_json,
    write_candidate_reports,
)
from techno_search.schemas import Candidate, candidate_from_mapping
from techno_search.scoring import score_candidate
from techno_search.validation import validate_candidate_file, validate_report_directory

SCHEMA_FILENAMES = {
    "batch_manifest": "batch_manifest.schema.json",
    "candidate_packet": "candidate_packet.schema.json",
    "report_manifest": "report_manifest.schema.json",
}


def main(argv: list[str] | None = None, stdout: TextIO | None = None) -> int:
    """Run the `techno-search` CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    out = stdout or sys.stdout

    if args.command == "score":
        candidate = load_candidate_json(args.input)
        scored = score_candidate(candidate)
        if args.output_dir is not None:
            paths = write_candidate_reports(scored, args.output_dir, filename_prefix=args.prefix)
            print(str(paths.markdown_path), file=out)
            print(str(paths.json_path), file=out)
            print(str(paths.manifest_path), file=out)
        else:
            print(candidate_packet_json(scored), file=out)
        return 0

    if args.command == "score-batch":
        manifest_path = score_batch(args.input_dir, args.output_dir, prefix=args.prefix)
        print(str(manifest_path), file=out)
        return 0

    if args.command == "calibration-summary":
        fixtures = load_calibration_fixtures(args.fixture_path)
        summary = summarize_calibration_fixtures(fixtures)
        print(json.dumps(summary.as_dict(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "validate-candidate":
        result = validate_candidate_file(args.input)
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if result.ok else 1

    if args.command == "validate-reports":
        result = validate_report_directory(args.report_dir)
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True), file=out)
        return 0 if result.ok else 1

    if args.command == "schema-paths":
        print(json.dumps(schema_paths(), indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "score-regression-summary":
        print(
            json.dumps(score_regression_summary(args.snapshot_path), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def load_candidate_json(path: Path | str) -> Candidate:
    """Load a normalized synthetic candidate JSON file."""

    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    return candidate_from_mapping(data)


def score_batch(input_dir: Path | str, output_dir: Path | str, *, prefix: str = "") -> Path:
    """Score all JSON candidate packets in a directory and write an aggregate manifest."""

    source_dir = Path(input_dir)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, str]] = []
    for candidate_path in sorted(source_dir.glob("*.json")):
        candidate = load_candidate_json(candidate_path)
        scored = score_candidate(candidate)
        report_prefix = f"{prefix}{candidate.candidate_id}" if prefix else candidate.candidate_id
        paths = write_candidate_reports(scored, destination, filename_prefix=report_prefix)
        entries.append(
            {
                "candidate_id": candidate.candidate_id,
                "track": candidate.track.value,
                "recommended_pathway": scored.recommended_pathway.value,
                "config_version": str(
                    candidate.provenance.get("config_version", DEFAULT_SCORING_CONFIG_VERSION)
                ),
                "input_path": str(candidate_path),
                "markdown_path": str(paths.markdown_path),
                "json_path": str(paths.json_path),
                "manifest_path": str(paths.manifest_path),
            }
        )

    batch_manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "input_dir": str(source_dir),
        "output_dir": str(destination),
        "config_version": DEFAULT_SCORING_CONFIG_VERSION,
        "candidate_count": len(entries),
        "reports": entries,
    }
    manifest_path = destination / "batch_manifest.json"
    manifest_path.write_text(json.dumps(batch_manifest, indent=2, sort_keys=True) + "\n")
    return manifest_path


def schema_paths() -> dict[str, str]:
    """Return repository-local schema artifact paths."""

    schema_dir = Path(__file__).resolve().parents[2] / "schemas"
    return {
        schema_name: str(schema_dir / filename)
        for schema_name, filename in sorted(SCHEMA_FILENAMES.items())
    }


def default_score_regression_snapshot_path() -> Path:
    """Return the repository-local score regression snapshot path."""

    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / (
        "score_regressions.json"
    )


def score_regression_summary(snapshot_path: Path | None = None) -> dict[str, object]:
    """Summarize score regression snapshot coverage."""

    path = snapshot_path or default_score_regression_snapshot_path()
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    candidates = data["candidates"]
    return {
        "snapshot_path": str(path),
        "candidate_count": len(candidates),
        "by_track": dict(
            sorted(Counter(candidate["track"] for candidate in candidates.values()).items())
        ),
        "by_recommended_pathway": dict(
            sorted(
                Counter(
                    candidate["recommended_pathway"] for candidate in candidates.values()
                ).items()
            )
        ),
        "candidate_ids": sorted(candidates),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="techno-search",
        description="Score synthetic technosignature-interest candidate packets.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    score_parser = subparsers.add_parser(
        "score",
        help="Score a normalized synthetic candidate JSON file.",
    )
    score_parser.add_argument("input", type=Path, help="Input candidate JSON path.")
    score_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional directory for Markdown and JSON review packets.",
    )
    score_parser.add_argument(
        "--prefix",
        help="Optional safe filename prefix for written reports.",
    )
    batch_parser = subparsers.add_parser(
        "score-batch",
        help="Score all normalized synthetic candidate JSON files in a directory.",
    )
    batch_parser.add_argument("input_dir", type=Path, help="Input candidate JSON directory.")
    batch_parser.add_argument("output_dir", type=Path, help="Output report directory.")
    batch_parser.add_argument(
        "--prefix",
        default="",
        help="Optional filename prefix prepended to each candidate ID.",
    )
    calibration_parser = subparsers.add_parser(
        "calibration-summary",
        help="Summarize synthetic calibration fixture coverage.",
    )
    calibration_parser.add_argument(
        "--fixture-path",
        type=Path,
        help="Optional calibration fixture JSON path.",
    )
    validate_candidate_parser = subparsers.add_parser(
        "validate-candidate",
        help="Validate a normalized synthetic candidate JSON file.",
    )
    validate_candidate_parser.add_argument("input", type=Path, help="Input candidate JSON path.")
    validate_reports_parser = subparsers.add_parser(
        "validate-reports",
        help="Validate generated candidate report packets and manifests in a directory.",
    )
    validate_reports_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing generated candidate reports.",
    )
    subparsers.add_parser(
        "schema-paths",
        help="Print local JSON schema artifact paths.",
    )
    score_regression_parser = subparsers.add_parser(
        "score-regression-summary",
        help="Summarize score regression snapshot coverage.",
    )
    score_regression_parser.add_argument(
        "--snapshot-path",
        type=Path,
        help="Optional score regression snapshot JSON path.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
