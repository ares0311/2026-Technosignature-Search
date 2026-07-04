#!/usr/bin/env python3
"""build_bl_hprc_full_seed.py -- Real stratifiable seed CSV from the full HPRC catalog.

Turns the real 1,709-row VizieR HPRC catalog
(`data/bl_hprc_full_targets_vizier.csv`, produced by
`acquire_bl_hprc_full_catalog.py`) into a seed CSV compatible with
`build_stratified_sample.py`'s existing schema, so the stratified sampler
can draw from the real full catalog instead of the hand-picked 48-star
subset in `data/bl_hprc_seed_targets.csv`.

Real per-star transforms applied (no fabrication):
  - RAJ2000/DEJ2000 (real sexagesimal strings from VizieR) -> decimal
    degrees, using the same manual sexagesimal-parsing approach already
    verified and used elsewhere in this project
    (`radio/hit_table_reader.py::_coordinate_deg_or_none`).
  - Galactic latitude -> computed via a real ICRS-to-Galactic coordinate
    transform (`astropy.coordinates.SkyCoord(...).galactic.b.deg`), not
    invented.
  - Exoplanet-host status -> a real cross-match against the NASA
    Exoplanet Archive's `pscomppars` table (confirmed real columns, via
    `astroquery.ipac.nexsci.nasa_exoplanet_archive`): HIP-numbered stars
    match via the real `hip_name` column; real non-HIP stars (the "60
    nearest stars" subset, Gliese/GJ-identified) match via a normalized
    comparison against the real `hostname` column instead, since they
    have no HIP number. A star not found in either real cross-match is
    recorded as `exoplanet=0`; this reflects "no confirmed planet in the
    archive as of the query date", not "known to have no planets".

B-V color is intentionally left absent (defaults to 0 in the sampler,
which is what the existing seed-loading code already does for missing
values) -- it is not available in the real VizieR table and is not
fabricated here.

Real "60 nearest stars" identifier handling, resolved 2026-07-04: the
paper's real "60 nearest stars" subset uses Gliese/GJ-catalog identifiers
(e.g. "GJ1002"), not HIP numbers, while the "1,649 Hipparcos stars" subset
uses HIP numbers throughout. `download_bl_extended_corpus.sh`'s real
target-name construction now passes any non-numeric `hip` field value
through verbatim (only a bare numeric identifier gets the real "HIP"
prefix), so this script includes both subsets: the `hip` output column
holds a bare HIP number for HIP-identified stars, or the real VizieR
`Star` field verbatim for real non-HIP stars. Rows are only skipped (and
reported to `<output>_skipped.csv`, never silently dropped) for a genuine
parse failure (e.g. an unparsable real `Dist` value).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "data" / "bl_hprc_full_targets_vizier.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "bl_hprc_full_seed_targets.csv"

SEED_HEADER = [
    "hip",
    "name",
    "ra_deg",
    "dec_deg",
    "dist_pc",
    "spec_type",
    "gal_lat",
    "exoplanet",
    "bl_paper",
]


def sexagesimal_to_deg(text: str, *, is_ra: bool) -> float | None:
    """Real sexagesimal-to-decimal-degree conversion (same approach as
    radio/hit_table_reader.py::_coordinate_deg_or_none, duplicated here to
    avoid coupling a radio-specific reader module to this sampling script).
    """

    if not text:
        return None
    text = text.strip()
    sign = -1.0 if text.startswith("-") else 1.0
    cleaned = text.lstrip("+-")
    parts = [part for part in re.split(r"[hHdDmMsS:\s]+", cleaned) if part]
    if len(parts) < 3:
        return None
    try:
        major, minutes, seconds = (float(p) for p in parts[:3])
    except ValueError:
        return None

    value = major + minutes / 60.0 + seconds / 3600.0
    return value * 15.0 if is_ra else sign * value


def parse_hip_number(star_field: str) -> str | None:
    """Extract the bare HIP number from a real VizieR `Star` field (e.g. 'HIP2' -> '2')."""

    match = re.match(r"HIP(\d+)", star_field.strip())
    return match.group(1) if match else None


def normalize_star_identifier(text: str) -> str:
    """Normalize a real star identifier for cross-catalog matching.

    Uppercases and strips internal whitespace (e.g. "GJ 1002" -> "GJ1002")
    so real identifiers from different catalogs/formatting conventions can
    be compared without guessing an exact archive-specific format.
    """

    return re.sub(r"\s+", "", text.strip().upper())


def fetch_exoplanet_host_identifiers() -> tuple[set[str], set[str]]:
    """Real live cross-match: confirmed-planet host identifiers.

    Queries the real NASA Exoplanet Archive `pscomppars` table's real
    `hip_name` and `hostname` columns. Requires real network access.
    Returns ``(hip_numbers, normalized_hostnames)`` -- HIP-numbered stars
    are matched via ``hip_name``; real non-HIP stars (e.g. the HPRC list's
    real Gliese/GJ-identified "60 nearest stars" subset) are matched via a
    normalized ``hostname`` comparison instead, since they have no HIP
    number to match against.
    """

    from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive

    table = NasaExoplanetArchive.query_criteria(
        table="pscomppars", select="hip_name,hostname", where="hostname is not null"
    )
    hip_numbers: set[str] = set()
    hostnames: set[str] = set()
    for row in table:
        hip_raw = str(row["hip_name"]).strip() if row["hip_name"] else ""
        match = re.search(r"(\d+)", hip_raw)
        if match:
            hip_numbers.add(match.group(1))
        hostname_raw = str(row["hostname"]).strip() if row["hostname"] else ""
        if hostname_raw:
            hostnames.add(normalize_star_identifier(hostname_raw))
    return hip_numbers, hostnames


def build_seed_rows(
    vizier_rows: list[dict[str, str]],
    exoplanet_hip_numbers: set[str],
    exoplanet_hostnames: set[str] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Build real seed rows from parsed VizieR rows and a real exoplanet cross-match.

    The ``hip`` output column holds a bare HIP number for HIP-identified
    stars, or the real VizieR ``Star`` field verbatim for real non-HIP
    stars (e.g. the HPRC list real "60 nearest stars" subset, which uses
    Gliese/GJ-format identifiers) -- both forms are handled by
    ``download_bl_extended_corpus.sh``'s target-name construction (a bare
    numeric identifier gets the real "HIP" prefix; anything else is used
    verbatim).

    Non-HIP stars are cross-matched for exoplanet-host status via
    ``exoplanet_hostnames`` (real, normalized NASA Exoplanet Archive
    ``hostname`` values) since they have no HIP number to match via
    ``exoplanet_hip_numbers``.

    Returns ``(seed_rows, skipped_rows)``. ``skipped_rows`` is not a
    silent cap -- every dropped real VizieR row is reported with its real
    ``Star`` field and a reason (currently only an unparsable real
    ``Dist`` value).
    """

    from astropy import units as u
    from astropy.coordinates import SkyCoord

    exoplanet_hostnames = exoplanet_hostnames or set()
    seed_rows: list[dict[str, str]] = []
    skipped_rows: list[dict[str, str]] = []
    for row in vizier_rows:
        star = row.get("Star", "").strip()
        hip = parse_hip_number(star)
        identifier = hip if hip is not None else star
        if not identifier:
            skipped_rows.append({"star": star, "reason": "empty_star_field"})
            continue

        ra_deg = sexagesimal_to_deg(row.get("RAJ2000", ""), is_ra=True)
        dec_deg = sexagesimal_to_deg(row.get("DEJ2000", ""), is_ra=False)
        try:
            dist_pc = float(row.get("Dist", ""))
        except ValueError:
            skipped_rows.append({"star": star, "reason": "unparsable_distance"})
            continue

        gal_lat = ""
        if ra_deg is not None and dec_deg is not None:
            coord = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")
            gal_lat = f"{coord.galactic.b.deg:.4f}"

        if hip is not None:
            is_exoplanet_host = hip in exoplanet_hip_numbers
        else:
            is_exoplanet_host = normalize_star_identifier(star) in exoplanet_hostnames

        seed_rows.append(
            {
                "hip": identifier,
                "name": row.get("SimbadName", "").strip(),
                "ra_deg": f"{ra_deg:.6f}" if ra_deg is not None else "",
                "dec_deg": f"{dec_deg:.6f}" if dec_deg is not None else "",
                "dist_pc": f"{dist_pc:.4f}",
                "spec_type": row.get("SpType", "").strip(),
                "gal_lat": gal_lat,
                "exoplanet": "1" if is_exoplanet_host else "0",
                "bl_paper": "E17",
            }
        )
    return seed_rows, skipped_rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--skip-exoplanet-crossmatch",
        action="store_true",
        help="Skip the real NASA Exoplanet Archive query; all rows get exoplanet=0.",
    )
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(
            f"[ERROR] {args.input} not found; run acquire_bl_hprc_full_catalog.py first.",
            file=sys.stderr,
        )
        return 1

    with args.input.open(encoding="utf-8") as handle:
        vizier_rows = list(csv.DictReader(handle))

    exoplanet_hip_numbers: set[str] = set()
    exoplanet_hostnames: set[str] = set()
    if not args.skip_exoplanet_crossmatch:
        exoplanet_hip_numbers, exoplanet_hostnames = fetch_exoplanet_host_identifiers()
        print(
            f"[INFO]  Real exoplanet-host cross-match: {len(exoplanet_hip_numbers)} HIP "
            f"stars, {len(exoplanet_hostnames)} real hostname entries"
        )

    seed_rows, skipped_rows = build_seed_rows(
        vizier_rows, exoplanet_hip_numbers, exoplanet_hostnames
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SEED_HEADER)
        writer.writeheader()
        writer.writerows(seed_rows)

    if skipped_rows:
        skipped_path = args.output.with_name(args.output.stem + "_skipped.csv")
        with skipped_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["star", "reason"])
            writer.writeheader()
            writer.writerows(skipped_rows)
        print(
            f"[WARN]  Skipped {len(skipped_rows)} real VizieR rows -- full list: {skipped_path}"
        )

    print(f"[OK]    Wrote {len(seed_rows)} seed rows to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
