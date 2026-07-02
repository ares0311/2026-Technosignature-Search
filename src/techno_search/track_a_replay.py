"""Track A Phase 3: Small Historical Replay.

Per docs/technosignature_datasets_agent_brief.md Phase 3, before any Track B
work begins, the pipeline must be re-run end-to-end on a small set of known
historical events and confirmed to recover the correct known-source
explanation, plus confirmed to emit `no_known_match`/`low_confidence` rather
than an unsupported claim when there is no explanation.

Rather than hand-picking named objects from memory (a guess this project's
directives explicitly forbid), this replay samples real rows directly from
whichever Track A catalogs the user has already acquired locally via
`track-a-catalog-acquire`, and confirms that cross-matching each sampled
object's own real coordinates recovers that same object's known class. This
is fully self-verifying against real acquired data: every replay case is a
real cataloged source, not a fabricated or remembered one.

A single negative control (a fixed sky position of RA=180.0, Dec=-89.5 --
one arcminute from the south celestial pole) is included; it is chosen to be
astronomically empty of these four catalogs by construction (all four are
transient/AGN/pulsar catalogs with no reason to cluster there), not verified
against any specific historical non-detection, and is used only to confirm
the pipeline reports `no_known_match`/`low_confidence` instead of a false
positive when it should be.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from techno_search.track_a_catalogs import default_normalized_catalog_path
from techno_search.track_a_crossmatch import ALL_CATALOG_NAMES, cross_match_known_sources

TRACK_A_REPLAY_SCHEMA_VERSION = "track_a_historical_replay_v1"

TRACK_A_REPLAY_DISCLAIMER = (
    "Track A historical replay confirms that the acquisition + cross-match "
    "pipeline recovers known explanations for real cataloged sources and "
    "correctly reports no-match for empty sky. It is not a technosignature "
    "detection test and does not authorize Track B unknown_candidate routing "
    "on its own."
)

NEGATIVE_CONTROL_RA_DEG = 180.0
NEGATIVE_CONTROL_DEC_DEG = -89.5


@dataclass(frozen=True)
class ReplayCase:
    """One historical replay case: a real cataloged source or the negative control."""

    case_id: str
    catalog_name: str | None
    source_id: str | None
    ra_deg: float
    dec_deg: float
    expected_classification_prefix: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "catalog_name": self.catalog_name,
            "source_id": self.source_id,
            "ra_deg": self.ra_deg,
            "dec_deg": self.dec_deg,
            "expected_classification_prefix": self.expected_classification_prefix,
        }


def _sample_replay_cases(
    *,
    project_root: Path | None,
    sample_size: int,
) -> list[ReplayCase]:
    import pandas as pd

    cases: list[ReplayCase] = []
    for catalog_name in ALL_CATALOG_NAMES:
        path = default_normalized_catalog_path(project_root, name=catalog_name)
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        for i, row in df.head(sample_size).iterrows():
            cases.append(
                ReplayCase(
                    case_id=f"{catalog_name}-{i}",
                    catalog_name=catalog_name,
                    source_id=str(row["source_id"]),
                    ra_deg=float(row["ra_deg"]),
                    dec_deg=float(row["dec_deg"]),
                    expected_classification_prefix=f"known_{row['object_class']}",
                )
            )

    cases.append(
        ReplayCase(
            case_id="negative-control-south-pole",
            catalog_name=None,
            source_id=None,
            ra_deg=NEGATIVE_CONTROL_RA_DEG,
            dec_deg=NEGATIVE_CONTROL_DEC_DEG,
            expected_classification_prefix="no_known_match",
        )
    )
    return cases


def run_historical_replay(
    *,
    project_root: Path | None = None,
    sample_size: int = 1,
    radius_arcsec: float = 5.0,
) -> dict[str, Any]:
    """Run the Phase 3 Small Historical Replay against locally acquired catalogs.

    Samples `sample_size` real rows from each locally acquired catalog and
    confirms cross-matching each object's own coordinates recovers its known
    class, plus confirms a fixed empty-sky negative control reports
    no_known_match/low_confidence. Returns a report suitable for saving as
    replay evidence per the brief's Phase 3 requirements.
    """

    cases = _sample_replay_cases(project_root=project_root, sample_size=sample_size)
    results: list[dict[str, Any]] = []
    recovered = 0
    for case in cases:
        result = cross_match_known_sources(
            case.ra_deg,
            case.dec_deg,
            radius_arcsec=radius_arcsec,
            project_root=project_root,
        )
        classification = str(result["classification"])
        if case.expected_classification_prefix == "no_known_match":
            case_recovered = classification in {"no_known_match", "low_confidence"}
        else:
            case_recovered = classification == case.expected_classification_prefix
        if case_recovered:
            recovered += 1
        results.append(
            {
                "case": case.as_dict(),
                "classification": classification,
                "recovered": case_recovered,
                "crossmatch_result": result,
            }
        )

    catalogs_available = [
        name
        for name in ALL_CATALOG_NAMES
        if default_normalized_catalog_path(project_root, name=name).exists()
    ]

    return {
        "schema_version": TRACK_A_REPLAY_SCHEMA_VERSION,
        "disclaimer": TRACK_A_REPLAY_DISCLAIMER,
        "ran_at_utc": datetime.now(UTC).isoformat(),
        "catalogs_available": catalogs_available,
        "case_count": len(cases),
        "recovered_count": recovered,
        "all_recovered": recovered == len(cases),
        "results": results,
    }


def save_historical_replay_report(
    report: dict[str, Any],
    *,
    project_root: Path | None = None,
) -> Path:
    """Save a replay report to metrics/track_a/historical_replay.json (local, ignored)."""

    root = project_root or Path(__file__).resolve().parents[2]
    out_path = root / "metrics" / "track_a" / "historical_replay.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return out_path
