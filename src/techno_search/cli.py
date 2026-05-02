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
from techno_search.constants import DEFAULT_SCHEMA_VERSION, DEFAULT_SCORING_CONFIG_VERSION
from techno_search.live_data import live_data_enabled, provider_adapters
from techno_search.reporting import (
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

    if args.command == "validate-all":
        all_result = validate_all()
        print(json.dumps(all_result, indent=2, sort_keys=True), file=out)
        return 0 if all_result["ok"] else 1

    if args.command == "regenerate-examples":
        regeneration_result = regenerate_examples()
        print(json.dumps(regeneration_result, indent=2, sort_keys=True), file=out)
        return 0

    if args.command == "provenance-summary":
        print(
            json.dumps(provenance_summary(args.report_dir), indent=2, sort_keys=True),
            file=out,
        )
        return 0

    if args.command == "live-provider-summary":
        print(json.dumps(live_provider_summary(), indent=2, sort_keys=True), file=out)
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
        "schema_version": DEFAULT_SCHEMA_VERSION,
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


def default_project_root() -> Path:
    """Return the repository root."""

    return Path(__file__).resolve().parents[2]


def regenerate_examples() -> dict[str, object]:
    """Regenerate committed example reports from example candidate JSON files."""

    candidate_dir = Path("examples/candidates")
    reports_dir = Path("examples/reports")
    batch_reports_dir = Path("examples/batch_reports")

    report_paths: list[str] = []
    for candidate_path in sorted(candidate_dir.glob("*.json")):
        candidate = load_candidate_json(candidate_path)
        scored = score_candidate(candidate)
        paths = write_candidate_reports(
            scored,
            reports_dir,
            filename_prefix=candidate.candidate_id,
        )
        report_paths.extend(
            [str(paths.markdown_path), str(paths.json_path), str(paths.manifest_path)]
        )

    batch_manifest_path = score_batch(candidate_dir, batch_reports_dir)
    return {
        "candidate_count": len(list(candidate_dir.glob("*.json"))),
        "reports_dir": str(reports_dir),
        "batch_reports_dir": str(batch_reports_dir),
        "report_paths": sorted(report_paths),
        "batch_manifest_path": str(batch_manifest_path),
    }


def validate_all() -> dict[str, object]:
    """Run local validation summaries that do not require network access."""

    root = default_project_root()
    candidate_results = {
        str(path): validate_candidate_file(path).as_dict()
        for path in sorted((root / "examples" / "candidates").glob("*.json"))
    }
    report_result = validate_report_directory(root / "examples" / "reports").as_dict()
    schemas = schema_paths()
    schema_results = {path: Path(path).exists() for path in schemas.values()}
    calibration = summarize_calibration_fixtures(load_calibration_fixtures()).as_dict()
    regression = score_regression_summary()

    ok = (
        all(result["ok"] for result in candidate_results.values())
        and bool(report_result["ok"])
        and all(schema_results.values())
    )
    return {
        "ok": ok,
        "candidates": candidate_results,
        "reports": report_result,
        "schemas": schemas,
        "schema_paths_exist": schema_results,
        "calibration_summary": calibration,
        "score_regression_summary": regression,
    }


def provenance_summary(report_dir: Path | str) -> dict[str, object]:
    """Summarize provenance across per-candidate report manifests."""

    directory = Path(report_dir)
    manifest_paths = sorted(directory.glob("*.manifest.json"))
    manifests = []
    for path in manifest_paths:
        with path.open(encoding="utf-8") as handle:
            manifests.append(json.load(handle))

    return {
        "report_dir": str(directory),
        "manifest_count": len(manifests),
        "candidate_ids": sorted(str(manifest["candidate_id"]) for manifest in manifests),
        "by_track": dict(sorted(Counter(str(manifest["track"]) for manifest in manifests).items())),
        "by_schema_version": dict(
            sorted(Counter(str(manifest["schema_version"]) for manifest in manifests).items())
        ),
        "by_config_version": dict(
            sorted(Counter(str(manifest["config_version"]) for manifest in manifests).items())
        ),
        "by_source_dataset": dict(
            sorted(
                Counter(
                    str(manifest.get("provenance_summary", {}).get("source_dataset", "unknown"))
                    for manifest in manifests
                ).items()
            )
        ),
    }


def live_provider_summary() -> dict[str, object]:
    """Return configured live-provider adapter metadata without network access."""

    adapters = provider_adapters()
    return {
        "live_enabled": live_data_enabled(),
        "provider_count": len(adapters),
        "providers": [
            {
                "provider_name": adapter.provider_name,
                "service_url": adapter.service_url,
            }
            for adapter in adapters
        ],
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
    subparsers.add_parser(
        "validate-all",
        help=(
            "Run local validation summaries for examples, reports, schemas, "
            "calibration, and score snapshots."
        ),
    )
    subparsers.add_parser(
        "regenerate-examples",
        help="Regenerate committed example reports from examples/candidates.",
    )
    provenance_parser = subparsers.add_parser(
        "provenance-summary",
        help="Summarize provenance fields across report manifests in a directory.",
    )
    provenance_parser.add_argument(
        "report_dir",
        type=Path,
        help="Directory containing per-candidate report manifests.",
    )
    subparsers.add_parser(
        "live-provider-summary",
        help="Print configured live-provider adapter names, URLs, and live-enabled status.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
