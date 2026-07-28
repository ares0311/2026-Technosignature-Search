#!/usr/bin/env python3
"""Turn identity-resolved BL archive labels into a real stellar seed CSV.

``data_selection/bl_archive_candidate_catalog.csv`` has, since version 1.2.48,
real SIMBAD-resolved positions for 6,007 archive labels the original
queue-alias path could not resolve, and (since 1.2.49) each resolved row's
real SIMBAD ``object_type`` classification. This script does the one thing
that evidence enables and nothing more: filter to the subset SIMBAD itself
classifies as a stellar object, and write it in
``data/bl_hprc_full_seed_targets.csv``'s compatible schema so
``target_priority_queue.build_target_priority_queue()`` can rank it through
its existing ``extra_seed_csv_paths`` merge -- no scoring logic changes, no
new selection formula, no fabricated distance/spectral-type/exoplanet fields
(those columns are left honestly blank when this project has no real value
for them, matching how ``_prior_significance``/``_data_quality`` already
treat a missing ``dist_pc``/``spec_type`` as "no evidence", not zero).

The stellar/non-stellar split below is an explicit, reviewed allowlist over
every real ``object_type`` value observed in the committed catalog as of
2026-07-24 (56 distinct values), not a regex guess: SIMBAD's own object-type
short codes are used directly, classified by their real, documented meaning
(https://simbad.cds.unistra.fr/guide/otypes.htx). Known pulsars are
deliberately excluded even though they are compact stellar remnants: this
project already has a dedicated ATNF pulsar cross-match
(``track_a_catalogs.py``) as a Track A known-explanation check, and folding
known pulsars into the primary stellar target-selection queue would
conflate that separate, already-solved identification problem with novel
star-target discovery. Extragalactic/AGN/radio-source/galaxy-cluster types
are excluded because they are not the kind of individual star this queue's
schema (``spec_type``, ``exoplanet``, ``dist_pc``) or this project's stellar
technosignature search targets.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import os
import re
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG_PATH = REPO_ROOT / "data_selection" / "bl_archive_candidate_catalog.csv"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "data" / "bl_archive_resolved_stellar_seed_targets.csv"
SEED_FIELDS = (
    "hip",
    "name",
    "ra_deg",
    "dec_deg",
    "dist_pc",
    "spec_type",
    "gal_lat",
    "exoplanet",
    "bl_paper",
    "object_type",
)
RESOLVED_STATUS = "resolved_via_simbad_name_lookup"

# Stellar SIMBAD object_type short codes observed in the real committed
# catalog (2026-07-24). A code ending in "*" is SIMBAD's own convention for
# a stellar object; a "_Candidate" suffix on an otherwise-stellar code is
# still a stellar candidate, not a different category.
_STELLAR_OTYPE_SUFFIXES = ("*",)
_STELLAR_OTYPE_EXACT = frozenset(
    {
        "Star",
        "Planet",
        "YSO",
        "WhiteDwarf",
        "HotSubdwarf",
        "EclBin",
        "RRLyrae",
        "Cepheid",
        "ClassicalCep",
        "Type2Cep",
        "BlueSG",
        "EllipVar",
        "HighMassXBin",
    }
)
# Explicitly excluded even though not every case is caught by the suffix
# rule above, kept as a documented, reviewed negative list rather than
# relying on the allowlist alone to prove intent for the ambiguous ones:
# known pulsars (already a dedicated Track A catalog check, not a novel
# star target) and every extragalactic/AGN/radio-source/cluster code.
_NON_STELLAR_OTYPE_EXACT = frozenset(
    {
        "Pulsar",
        "Galaxy",
        "GtowardsGroup",
        "GtowardsCl",
        "AGN",
        "AGN_Candidate",
        "Seyfert",
        "Seyfert1",
        "Seyfert2",
        "QSO",
        "BLLac",
        "Blazar",
        "RadioG",
        "LINER",
        "GlobCluster",
        "EmissionG",
        "LowSurfBrghtG",
        "HIIG",
        "StarburstG",
        "BrightestCG",
        "PairG",
        "GinPair",
        "MolCld",
        "radioBurst",
    }
)


class SeedBuildError(RuntimeError):
    """Raised when the archive catalog cannot be turned into a seed CSV
    without guessing."""


def is_stellar_object_type(object_type: str) -> bool:
    """Return whether SIMBAD's own object_type marks this a stellar target.

    A trailing "_Candidate" suffix (SIMBAD's own convention for a tentative
    classification) is stripped before every other check, so it can never
    change the verdict for the underlying type.
    """
    value = object_type.strip()
    if not value:
        return False
    base_value = value.removesuffix("_Candidate")
    if base_value in _NON_STELLAR_OTYPE_EXACT:
        return False
    if base_value in _STELLAR_OTYPE_EXACT:
        return True
    return base_value.endswith(_STELLAR_OTYPE_SUFFIXES)


_HIP_LABEL_RE = re.compile(r"^[Hh][Ii][Pp](?P<number>\d+)(?:_[SR])?$")


def _hip_number(archive_target_label: str) -> str:
    match = _HIP_LABEL_RE.match(archive_target_label)
    return match.group("number") if match else ""


def build_stellar_seed_rows(catalog_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Filter resolved archive rows to real stellar targets, deduplicated
    by canonical_target_id so a label's ON/OFF cadence-role suffix variants
    (which resolve to the same real object) do not produce duplicate seed
    rows.

    A HIP-designated label always seeds its row's ``name`` as the bare
    ``HIP<number>`` form, never the raw archive label with its cadence-role
    suffix still attached. ``target_priority_queue.py`` uses ``name`` as the
    row's ``target_id`` and also derives ``HIP<number>`` as a real coverage-
    matching alias for any HIP-numbered row (``_aliases_for_row``) -- a
    ``HIP36817_R`` target_id would still alias-match existing coverage for
    the primary-seed's real ``HIP36817`` entry while remaining a distinct
    row, silently creating a second, duplicate queue row for the same real
    star that inherits its size-preflight/eligibility status without ever
    being deduplicated by the existing same-target_id collision rule.
    """
    seen_ids: set[str] = set()
    rows: list[dict[str, str]] = []
    for row in catalog_rows:
        if row.get("identity_status") != RESOLVED_STATUS:
            continue
        if not is_stellar_object_type(row.get("object_type", "")):
            continue
        canonical_id = row["canonical_target_id"]
        if canonical_id in seen_ids:
            continue
        seen_ids.add(canonical_id)
        hip_number = _hip_number(row["archive_target_label"])
        rows.append(
            {
                "hip": hip_number,
                "name": f"HIP{hip_number}" if hip_number else row["archive_target_label"],
                "ra_deg": row["ra_deg"],
                "dec_deg": row["dec_deg"],
                "dist_pc": "",
                "spec_type": "",
                "gal_lat": "",
                "exoplanet": "",
                "bl_paper": "",
                "object_type": row["object_type"],
            }
        )
    return rows


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary)
        raise


def build_seed_file(
    catalog_path: Path = DEFAULT_CATALOG_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict[str, Any]:
    if not catalog_path.is_file():
        raise SeedBuildError(f"catalog not found: {catalog_path}")
    with catalog_path.open(newline="", encoding="utf-8") as handle:
        catalog_rows = list(csv.DictReader(handle))

    resolved_count = sum(1 for row in catalog_rows if row.get("identity_status") == RESOLVED_STATUS)
    seed_rows = build_stellar_seed_rows(catalog_rows)

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=SEED_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(seed_rows)
    _atomic_write(output_path, buffer.getvalue())

    return {
        "ok": True,
        "resolved_candidate_count": resolved_count,
        "stellar_seed_row_count": len(seed_rows),
        "excluded_non_stellar_or_duplicate_count": resolved_count - len(seed_rows),
        "output_path": str(output_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog-path", type=Path, default=DEFAULT_CATALOG_PATH)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args(argv)
    try:
        summary = build_seed_file(args.catalog_path, args.output_path)
    except SeedBuildError as exc:
        print(f"[ERROR] {exc}")
        return 1
    print(
        f"[OK] {summary['stellar_seed_row_count']} stellar seed row(s) written "
        f"from {summary['resolved_candidate_count']} resolved candidate(s) "
        f"({summary['excluded_non_stellar_or_duplicate_count']} excluded as "
        "non-stellar or a duplicate cadence-role variant)"
    )
    print(f"[INFO] Output: {summary['output_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
