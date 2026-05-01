"""Command-line interface for synthetic candidate scoring."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from techno_search.reporting import candidate_packet_json, write_candidate_reports
from techno_search.schemas import Candidate, FeatureValue, Track
from techno_search.scoring import score_candidate


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

    parser.error(f"Unknown command: {args.command}")
    return 2


def load_candidate_json(path: Path | str) -> Candidate:
    """Load a normalized synthetic candidate JSON file."""

    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    return candidate_from_mapping(data)


def candidate_from_mapping(data: dict[str, Any]) -> Candidate:
    """Convert a JSON mapping into a candidate."""

    return Candidate(
        candidate_id=str(data["candidate_id"]),
        track=Track(str(data["track"])),
        features=_feature_mapping(data.get("features", {})),
        source_ids=tuple(str(item) for item in data.get("source_ids", ())),
        provenance=_feature_mapping(data.get("provenance", {})),
    )


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
    return parser


def _feature_mapping(data: dict[str, Any]) -> dict[str, FeatureValue]:
    return {str(key): _feature_value(value) for key, value in data.items()}


def _feature_value(value: Any) -> FeatureValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    msg = f"Unsupported candidate JSON value: {value!r}"
    raise TypeError(msg)


if __name__ == "__main__":
    raise SystemExit(main())
