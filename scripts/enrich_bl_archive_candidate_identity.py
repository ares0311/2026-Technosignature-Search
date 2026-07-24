#!/usr/bin/env python3
"""Resolve real sky positions for unresolved BL archive candidate labels.

``acquire_bl_archive_candidate_catalog.py`` only resolves an archive label's
identity against exact aliases already documented in the target-priority
queue; everything else is left ``unresolved_archive_label`` with no
coordinates. This script adds a second, independent real-identity source:
SIMBAD name resolution via its public batch script interface
(https://simbad.cds.unistra.fr/simbad/sim-script), used the same
conservative way as the queue-alias path -- a positive match sets real
``ra_deg``/``dec_deg``/``canonical_target_id``/``object_type`` from SIMBAD's
own response; anything SIMBAD does not resolve is left exactly as it was.
``object_type`` (SIMBAD's short-form classification, e.g. ``Star``, ``QSO``,
``PM*``) is also backfilled for rows resolved by an earlier run of this
script or by the queue-alias path, since it is real independent evidence
about what an identity-resolved label actually is -- not a guess about
whether it belongs in a stellar target-selection pipeline.

Two query strategies, both with documented provenance, no guessing:

1. Direct name query for the archive label, or for the label with a
   trailing ``_S`` or ``_R`` suffix stripped. Lebofsky et al. 2019
   (arXiv:1906.07391, Breakthrough Listen public data/archiving paper)
   documents that Parkes cadence targets use exactly this convention:
   ``_S`` = source/ON target, ``_R`` = reference/OFF target for the same
   physical object. Any other suffix (``_B1``..``_B17``, compound forms
   like ``_N1_R``) is left untouched -- this project has no documented
   source for what those denote, and AGENTS.md forbids guessing.
2. For labels matching the PKS catalog's own B1950 ``HHMM+-DD[.D]``
   naming format that SIMBAD does not resolve directly, retry once with a
   ``PKS `` prefix. This recognizes a standard, documented catalog naming
   convention -- not an identity guess.

Batch alignment: SIMBAD's ``form1`` script output omits failed lookups from
the ``::data::`` block, but its ``::error::`` block reports the exact
1-indexed script line of every failed query (verified live: interleaved
failing/succeeding queries produced ``[2]``/``[4]``/``[6]`` error lines
matching their script line numbers, with surviving ``::data::`` rows in the
same relative order as their surviving queries). This script uses that
explicit index instead of guessing alignment from row order alone, and
fails loudly if the error+data row counts do not exactly account for every
query in the batch.

A resolved label never becomes ``ranking_eligible``: that still requires
real archive file-metadata enrichment (HDF5 URL discovery, size preflight)
via the existing ``download_bl_extended_corpus.sh --discover-only`` /
``target-priority-size-preflight`` pipeline, a separate step.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import http.client
import io
import os
import re
import ssl
import sys
import tempfile
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from techno_search.data_collection_status import record_and_publish_data_collection_status

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG_PATH = REPO_ROOT / "data_selection" / "bl_archive_candidate_catalog.csv"
SIMBAD_SCRIPT_URL = "https://simbad.cds.unistra.fr/simbad/sim-script"
SIMBAD_SOURCE_DOCUMENTATION = "https://simbad.cds.unistra.fr/guide/sim-url.htx"
CADENCE_SUFFIX_SOURCE = "arxiv:1906.07391"
SCHEMA_VERSION = "bl_archive_candidate_catalog_v1"
RESOLVED_STATUS = "resolved_via_simbad_name_lookup"
BATCH_SIZE = 200
REQUEST_DELAY_SECONDS = 1.0
FORMAT_LINE = 'format object form1 "%IDLIST(1) | %COO(d;A) | %COO(d;D) | %OTYPE(S)"'
_FIELD_SEP = " | "
_ERROR_INDEX_RE = re.compile(r"^\[(\d+)\]")
_SECTION_DECORATION_RE = re.compile(r"^:+$")
_SUFFIX_RE = re.compile(r"^(?P<base>.+)(?P<suffix>_[SR])$")
_PKS_STYLE_RE = re.compile(r"^\d{4}[+-]\d{2,3}(\.\d+)?$")

BatchFetcher = Callable[[str], str]


class IdentityEnrichmentError(RuntimeError):
    """Raised when SIMBAD cannot be queried, or its output cannot be trusted,
    without guessing."""


def query_name(label: str) -> tuple[str, str]:
    """Return the (query_name, provenance_basis) to resolve for a label."""
    match = _SUFFIX_RE.match(label)
    if match:
        suffix = match.group("suffix")
        return match.group("base"), f"suffix_stripped:{suffix}:{CADENCE_SUFFIX_SOURCE}"
    return label, "direct_label"


def _content_lines(section: str) -> list[str]:
    """Strip blank lines and ``::marker::`` colon-decoration from a section."""
    return [
        line
        for raw in section.splitlines()
        if (line := raw.strip()) and not _SECTION_DECORATION_RE.match(line)
    ]


def fetch_simbad_script(script: str, *, timeout: float = 60.0) -> str:
    context: ssl.SSLContext
    try:
        import certifi

        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    request = Request(  # noqa: S310 - fixed, documented public SIMBAD endpoint
        f"{SIMBAD_SCRIPT_URL}?{urlencode({'script': script})}",
        headers={"User-Agent": "Techno-Hunter/1.2 archive-identity-enrichment"},
    )
    with urlopen(request, timeout=timeout, context=context) as response:  # noqa: S310
        body: bytes = response.read()
        return body.decode("utf-8", "replace")


def resolve_batch(
    names: list[str],
    *,
    fetcher: BatchFetcher = fetch_simbad_script,
    max_attempts: int = 3,
    retry_delay_seconds: float = 2.0,
) -> dict[str, tuple[str, float, float, str]]:
    """Resolve many SIMBAD names in one request, aligned by explicit error index.

    ``::console::`` (the script-execution confirmation, e.g. "simbatch done")
    is the real completion signal -- it is present on every well-formed
    response. ``::error::`` and ``::data::`` are each omitted entirely when
    empty (verified live: a 200-name batch where every query failed returned
    no ``::data::`` section at all, not an empty one), so neither may be
    required to be present.

    Real live queries against this shared service also occasionally return a
    genuinely truncated/incomplete response missing ``::console::`` itself
    (the same transient-truncation class seen with large HDF5 downloads over
    this network path, not a content bug). That case is retried a bounded
    number of times before failing loudly.
    """
    if not names:
        return {}
    script = "\n".join([FORMAT_LINE, *(f"query id {name}" for name in names)])
    text = ""
    last_error: IdentityEnrichmentError | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            text = fetcher(script)
        except (OSError, http.client.HTTPException) as exc:
            last_error = IdentityEnrichmentError(
                f"SIMBAD request failed (attempt {attempt}/{max_attempts}): "
                f"{type(exc).__name__}: {exc}"
            )
            if attempt < max_attempts:
                time.sleep(retry_delay_seconds)
            continue
        if "::console::" in text:
            last_error = None
            break
        last_error = IdentityEnrichmentError(
            f"Unexpected SIMBAD response shape (attempt {attempt}/{max_attempts}): "
            f"{text[:200]!r}"
        )
        if attempt < max_attempts:
            time.sleep(retry_delay_seconds)
    if last_error is not None:
        raise last_error

    error_positions: set[int] = set()
    if "::error::" in text:
        error_section = text.split("::error::", 1)[1].split("::data::", 1)[0]
        for line in error_section.splitlines():
            line = line.strip()
            match = _ERROR_INDEX_RE.match(line)
            if not match:
                # Section-boundary decoration (":::::...") and blank lines are
                # expected noise around the real "[N] '...'" error entries.
                continue
            script_line = int(match.group(1))
            # ``query id <name>`` for names[i] sits at script line i + 2
            # (script line 1 is the ``format`` directive).
            position = script_line - 2
            if not 0 <= position < len(names):
                raise IdentityEnrichmentError(
                    f"SIMBAD error line references out-of-range position {position}: {line!r}"
                )
            error_positions.add(position)

    data_rows = _content_lines(text.split("::data::", 1)[1]) if "::data::" in text else []
    surviving_positions = [i for i in range(len(names)) if i not in error_positions]
    if len(data_rows) != len(surviving_positions):
        raise IdentityEnrichmentError(
            f"SIMBAD returned {len(data_rows)} data row(s) but "
            f"{len(surviving_positions)} quer(ies) were not reported as errors; "
            "refusing to guess alignment."
        )

    resolved: dict[str, tuple[str, float, float, str]] = {}
    for position, row in zip(surviving_positions, data_rows, strict=True):
        parts = row.split(_FIELD_SEP)
        if len(parts) != 4:
            raise IdentityEnrichmentError(f"Unparseable SIMBAD data row: {row!r}")
        main_id, ra_text, dec_text, otype = (part.strip() for part in parts)
        try:
            ra_deg, dec_deg = float(ra_text), float(dec_text)
        except ValueError as exc:
            raise IdentityEnrichmentError(f"Non-numeric SIMBAD coordinates: {row!r}") from exc
        resolved[names[position]] = (main_id, ra_deg, dec_deg, otype)
    return resolved


def resolve_unresolved_rows(
    rows: list[dict[str, str]],
    *,
    fetcher: BatchFetcher = fetch_simbad_script,
    request_delay_seconds: float = REQUEST_DELAY_SECONDS,
    log: Callable[[str], None] = lambda _msg: None,
) -> dict[str, int]:
    """Resolve real identities for ``unresolved_archive_label`` rows, in place."""
    targets = [row for row in rows if row["identity_status"] == "unresolved_archive_label"]
    query_by_label = {
        row["archive_target_label"]: query_name(row["archive_target_label"]) for row in targets
    }
    unique_names = sorted({name for name, _provenance in query_by_label.values()})

    resolved_by_name: dict[str, tuple[str, float, float, str, str]] = {}
    for start in range(0, len(unique_names), BATCH_SIZE):
        batch = unique_names[start : start + BATCH_SIZE]
        log(f"[SIMBAD] direct query batch {start // BATCH_SIZE + 1}: {len(batch)} name(s)")
        for name, (main_id, ra_deg, dec_deg, otype) in resolve_batch(
            batch, fetcher=fetcher
        ).items():
            resolved_by_name[name] = (main_id, ra_deg, dec_deg, otype, "simbad_direct_name_match")
        if start + BATCH_SIZE < len(unique_names):
            time.sleep(request_delay_seconds)

    pks_candidates = sorted(
        name for name in unique_names if name not in resolved_by_name and _PKS_STYLE_RE.match(name)
    )
    if pks_candidates:
        log(f"[SIMBAD] PKS-prefix retry: {len(pks_candidates)} unresolved PKS-format name(s)")
        prefixed_names = [f"PKS {name}" for name in pks_candidates]
        matches = resolve_batch(prefixed_names, fetcher=fetcher)
        for prefixed_name, original in zip(prefixed_names, pks_candidates, strict=True):
            pks_match = matches.get(prefixed_name)
            if pks_match is not None:
                main_id, ra_deg, dec_deg, otype = pks_match
                resolved_by_name[original] = (
                    main_id,
                    ra_deg,
                    dec_deg,
                    otype,
                    "simbad_pks_prefix_match",
                )

    counts = {"resolved": 0, "unresolved": 0}
    for row in targets:
        name, suffix_provenance = query_by_label[row["archive_target_label"]]
        match = resolved_by_name.get(name)
        if match is None:
            counts["unresolved"] += 1
            continue
        main_id, ra_deg, dec_deg, otype, method = match
        row["canonical_target_id"] = main_id
        row["identity_status"] = RESOLVED_STATUS
        row["identity_provenance"] = f"{method};{suffix_provenance}"
        row["ra_deg"] = repr(ra_deg)
        row["dec_deg"] = repr(dec_deg)
        row["object_type"] = otype
        row["eligibility_reason"] = "identity_resolved_pending_file_metadata_enrichment"
        counts["resolved"] += 1
    return counts


def backfill_object_types(
    rows: list[dict[str, str]],
    *,
    fetcher: BatchFetcher = fetch_simbad_script,
    request_delay_seconds: float = REQUEST_DELAY_SECONDS,
    log: Callable[[str], None] = lambda _msg: None,
) -> int:
    """Fill in ``object_type`` for already-resolved rows that predate it.

    Re-queries by each row's own ``canonical_target_id`` (SIMBAD's real main
    identifier from the earlier resolution), not the original archive label,
    so this never re-derives or second-guesses an existing identity match --
    it only adds the one new field.
    """
    targets = [
        row
        for row in rows
        if row.get("canonical_target_id") and not row.get("object_type")
    ]
    if not targets:
        return 0
    unique_ids = sorted({row["canonical_target_id"] for row in targets})
    otype_by_id: dict[str, str] = {}
    for start in range(0, len(unique_ids), BATCH_SIZE):
        batch = unique_ids[start : start + BATCH_SIZE]
        log(f"[SIMBAD] object-type backfill batch {start // BATCH_SIZE + 1}: {len(batch)} name(s)")
        for name, (_main_id, _ra, _dec, otype) in resolve_batch(batch, fetcher=fetcher).items():
            otype_by_id[name] = otype
        if start + BATCH_SIZE < len(unique_ids):
            time.sleep(request_delay_seconds)

    filled = 0
    for row in targets:
        found_otype = otype_by_id.get(row["canonical_target_id"])
        if found_otype:
            row["object_type"] = found_otype
            filled += 1
    return filled


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


def enrich_catalog(
    catalog_path: Path,
    *,
    fetcher: BatchFetcher = fetch_simbad_script,
    log: Callable[[str], None] = lambda _msg: None,
) -> dict[str, Any]:
    if not catalog_path.is_file():
        raise IdentityEnrichmentError(f"catalog not found: {catalog_path}")
    with catalog_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or ())
        rows = list(reader)
    if "canonical_target_id" not in fieldnames:
        raise IdentityEnrichmentError(f"catalog is missing expected columns: {catalog_path}")
    if "object_type" not in fieldnames:
        # Schema migration for a catalog written before object_type existed:
        # insert it right after dec_deg to match acquire_bl_archive_candidate_
        # catalog.py's CATALOG_FIELDS ordering, and backfill "" for every row.
        insert_at = (
            fieldnames.index("dec_deg") + 1 if "dec_deg" in fieldnames else len(fieldnames)
        )
        fieldnames = fieldnames[:insert_at] + ["object_type"] + fieldnames[insert_at:]
        for row in rows:
            row["object_type"] = ""

    counts = resolve_unresolved_rows(rows, fetcher=fetcher, log=log)
    backfilled = backfill_object_types(rows, fetcher=fetcher, log=log)

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    catalog_text = buffer.getvalue()
    _atomic_write(catalog_path, catalog_text)

    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "retrieved_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "candidate_count": len(rows),
        "resolved_count": counts["resolved"],
        "still_unresolved_count": counts["unresolved"],
        "object_type_backfilled_count": backfilled,
        "source_endpoint": SIMBAD_SCRIPT_URL,
        "source_documentation": SIMBAD_SOURCE_DOCUMENTATION,
        "cadence_suffix_source": CADENCE_SUFFIX_SOURCE,
        "catalog_sha256": hashlib.sha256(catalog_text.encode()).hexdigest(),
        "raw_science_payload_downloaded": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog-path", type=Path, default=DEFAULT_CATALOG_PATH)
    parser.add_argument("--status-path", type=Path)
    args = parser.parse_args(argv)
    attempt_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    status_key = f"enrich_bl_archive_candidate_identity__{attempt_id}"

    def log(message: str) -> None:
        print(message, file=sys.stderr)

    try:
        summary = enrich_catalog(args.catalog_path, log=log)
    except (IdentityEnrichmentError, OSError, UnicodeError) as exc:
        failure = {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "error": f"{type(exc).__name__}: {exc}",
            "raw_science_payload_downloaded": False,
        }
        try:
            record_and_publish_data_collection_status(
                REPO_ROOT, status_key, failure, status_path=args.status_path
            )
        except Exception as status_exc:  # noqa: BLE001 - report both failures loudly
            print(f"[ERROR] Status recording failed: {status_exc}", file=sys.stderr)
        print(f"[ERROR] {failure['error']}", file=sys.stderr)
        return 1

    try:
        record_and_publish_data_collection_status(
            REPO_ROOT, status_key, summary, status_path=args.status_path
        )
    except Exception as exc:  # noqa: BLE001 - required acquisition provenance
        print(f"[ERROR] Enrichment succeeded but status recording failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"[OK] resolved {summary['resolved_count']} new identities; "
        f"{summary['still_unresolved_count']} remain unresolved; "
        f"backfilled object_type for {summary['object_type_backfilled_count']} row(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
