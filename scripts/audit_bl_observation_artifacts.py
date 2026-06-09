#!/usr/bin/env python3
"""Audit local BL hit tables before production-path pipeline execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from techno_search.observation_artifact import assess_observation_directory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--require-approved",
        action="store_true",
        help="Exit nonzero unless at least one approved real observation is present.",
    )
    args = parser.parse_args()

    assessments = assess_observation_directory(args.directory)
    approved = [item for item in assessments if item.approved_for_pipeline]
    payload = {
        "directory": str(args.directory),
        "artifact_count": len(assessments),
        "approved_real_observation_count": len(approved),
        "artifacts": [item.as_dict() for item in assessments],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.require_approved and not approved:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
