#!/usr/bin/env python3
"""acquire_bl_hprc_full_catalog.py -- Real full Isaacson et al. 2017 HPRC target list.

Downloads the real, full 1,709-star Breakthrough Listen HPRC target list
(Isaacson et al. 2017, PASP 129, 054501) from its real, verified VizieR
machine-readable table -- catalog `J/PASP/129/E4501`, table `table1`, NOT
the plausible-looking but real-checked-and-rejected `J/PASP/129/054501`
identifier (confirmed via a real live VizieR query, 2026-07-04; see
`docs/bl_hprc_target_list_research.md` for the full research trail).

This replaces the current `data/bl_hprc_seed_targets.csv` (a hand-picked
48-star subset) as the real sampling frame source for the stratified
target sampler, given real available storage budget to support a much
larger real radio corpus than the current fixed 31-target manifest.

Real column schema (verified via live VizieR retrieval, not guessed):
``Star``, ``RAJ2000``, ``DEJ2000``, ``Ep``, ``Vmag``, ``SpType``, ``Dist``,
``pmRA``, ``pmDE``, ``SimbadName``. Does NOT include B-V color or
exoplanet-host status -- those fields in the current 48-star seed CSV were
supplemented from other sources and are not fabricated here for the
larger real set.

Real archive policy (verified 2026-07-04, not guessed): VizieR/CDS
publishes no documented rate limit for this table endpoint. The
Breakthrough Listen Open Data Archive documents a 500-file per-query
result cap and no published concurrent-request limit -- this script
performs a single VizieR request, so neither limit is relevant here.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
VIZIER_ENDPOINT = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
VIZIER_SOURCE = "J/PASP/129/E4501/table1"
DEFAULT_RAW_OUTPUT = REPO_ROOT / "data" / "bl_hprc_full_targets_vizier_raw.tsv"
DEFAULT_CSV_OUTPUT = REPO_ROOT / "data" / "bl_hprc_full_targets_vizier.csv"

EXPECTED_COLUMNS = [
    "Star",
    "RAJ2000",
    "DEJ2000",
    "Ep",
    "Vmag",
    "SpType",
    "Dist",
    "pmRA",
    "pmDE",
    "SimbadName",
]
# Real row count confirmed via live VizieR retrieval, 2026-07-04 (see
# docs/bl_hprc_target_list_research.md). A different count on a future run
# means the real source catalog changed -- review before accepting, don't
# silently rewrite this constant.
EXPECTED_ROW_COUNT = 1709


def fetch_raw_tsv(*, timeout: float = 60.0) -> str:
    """Fetch the real live VizieR TSV response. Requires real network access."""

    params = {"-source": VIZIER_SOURCE, "-out.max": "unlimited", "-out": "*"}
    url = f"{VIZIER_ENDPOINT}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "TechnosignatureSearch/1.0"})  # noqa: S310
    with urlopen(req, timeout=timeout) as response:  # noqa: S310
        return response.read().decode("utf-8", "replace")


def parse_vizier_tsv(text: str) -> list[dict[str, str]]:
    """Parse a real VizieR ASU-TSV response body into row dicts.

    Raises ``RuntimeError`` if the expected ``Star`` header row or any
    expected column is missing.
    """

    header: list[str] | None = None
    rows: list[dict[str, str]] = []

    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue

        fields = [field.strip() for field in line.split("\t")]

        if fields[0] == "Star":
            header = fields
            missing = [col for col in EXPECTED_COLUMNS if col not in header]
            if missing:
                msg = f"VizieR schema changed; missing columns: {missing}"
                raise RuntimeError(msg)
            continue

        if header is None:
            continue

        first = fields[0].strip()
        if first == "" or set(first) <= {"-"}:
            continue

        row = dict(zip(header, fields, strict=False))
        if row.get("Star"):
            rows.append(row)

    if header is None:
        msg = "No 'Star' header row found in VizieR TSV response."
        raise RuntimeError(msg)

    return rows


def acquire_bl_hprc_full_catalog(
    *,
    raw_output: Path = DEFAULT_RAW_OUTPUT,
    csv_output: Path = DEFAULT_CSV_OUTPUT,
    expected_row_count: int | None = EXPECTED_ROW_COUNT,
) -> dict[str, object]:
    """Fetch, validate, and write the real full HPRC target list.

    Returns a real summary dict (row count, output paths, first/last star)
    suitable for the data-collection status manifest. Raises
    ``RuntimeError`` if the row count doesn't match ``expected_row_count``
    (pass ``None`` to skip that check).
    """

    text = fetch_raw_tsv()
    rows = parse_vizier_tsv(text)

    if expected_row_count is not None and len(rows) != expected_row_count:
        msg = (
            f"VizieR row count changed for {VIZIER_SOURCE}: expected "
            f"{expected_row_count}, observed {len(rows)}. Review the "
            "source before accepting this update."
        )
        raise RuntimeError(msg)

    raw_output.parent.mkdir(parents=True, exist_ok=True)
    raw_output.write_text(text, encoding="utf-8")

    csv_output.parent.mkdir(parents=True, exist_ok=True)
    with csv_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return {
        "row_count": len(rows),
        "raw_output": str(raw_output),
        "csv_output": str(csv_output),
        "first_star": rows[0]["Star"] if rows else None,
        "last_star": rows[-1]["Star"] if rows else None,
        "vizier_source": VIZIER_SOURCE,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_OUTPUT)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV_OUTPUT)
    parser.add_argument(
        "--skip-row-count-check",
        action="store_true",
        help="Skip the expected-row-count validation (use if the real source has changed).",
    )
    args = parser.parse_args(argv)

    try:
        summary = acquire_bl_hprc_full_catalog(
            raw_output=args.raw_output,
            csv_output=args.csv_output,
            expected_row_count=None if args.skip_row_count_check else EXPECTED_ROW_COUNT,
        )
    except (RuntimeError, OSError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        try:
            from techno_search.data_collection_status import (
                record_and_publish_data_collection_status,
            )

            record_and_publish_data_collection_status(
                REPO_ROOT, "acquire_bl_hprc_full_catalog", {"ok": False, "error": str(exc)}
            )
        except Exception:  # noqa: BLE001 - status reporting must not mask the real error
            pass
        return 1

    print(f"[OK]    Fetched {summary['row_count']} real rows from {summary['vizier_source']}")
    print(f"[INFO]  Raw TSV: {summary['raw_output']}")
    print(f"[INFO]  Normalized CSV: {summary['csv_output']}")
    print(f"[INFO]  First: {summary['first_star']}  Last: {summary['last_star']}")

    try:
        from techno_search.data_collection_status import (
            record_and_publish_data_collection_status,
        )

        record_and_publish_data_collection_status(
            REPO_ROOT,
            "acquire_bl_hprc_full_catalog",
            {"ok": True, **{k: v for k, v in summary.items() if k != "vizier_source"}},
        )
    except Exception:  # noqa: BLE001 - status reporting is best-effort
        print("[INFO]  Status manifest update/commit skipped (non-fatal).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
