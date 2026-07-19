#!/usr/bin/env python3
"""Acquire the public BL archive target namespace as a fail-closed catalog.

This makes one metadata-only ``list-targets`` request. Archive labels are not
assumed to be physical-object identities: only exact, case-insensitive aliases
already documented by the target-priority queue are resolved. Everything else
remains ineligible pending real identity and file-metadata enrichment.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import io
import json
import os
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from techno_search.data_collection_status import record_and_publish_data_collection_status

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ENDPOINT = "http://seti.berkeley.edu/opendata/api/list-targets"
SOURCE_DOCUMENTATION = "https://github.com/ggroode/bl-opendata/blob/master/README.md"
SCHEMA_VERSION = "bl_archive_candidate_catalog_v1"
EXPECTED_MIN_NONEMPTY_TARGETS = 10_000
DEFAULT_RAW_OUTPUT = REPO_ROOT / "data" / "bl_archive_target_labels.json"
DEFAULT_CATALOG_OUTPUT = REPO_ROOT / "data_selection" / "bl_archive_candidate_catalog.csv"
DEFAULT_QUEUE_PATH = REPO_ROOT / "data_selection" / "target_priority_queue.csv"

CATALOG_FIELDS = (
    "candidate_id",
    "archive_target_label",
    "canonical_target_id",
    "identity_status",
    "identity_provenance",
    "archive_target_present",
    "queue_status",
    "local_coverage_status",
    "target_selection_score",
    "ranking_eligible",
    "eligibility_reason",
    "ra_deg",
    "dec_deg",
    "source_endpoint",
    "retrieved_at_utc",
    "schema_version",
)


class ArchiveCatalogError(RuntimeError):
    """Raised when public metadata cannot be represented without guessing."""


def fetch_target_labels(*, timeout: float = 60.0) -> str:
    """Return the live public target-label JSON without downloading science data."""
    request = Request(  # noqa: S310 - fixed, documented public metadata endpoint
        SOURCE_ENDPOINT,
        headers={"User-Agent": "Techno-Hunter/1.2 archive-metadata-inventory"},
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read().decode("utf-8", "strict")


def parse_target_labels(text: str) -> tuple[list[str], int]:
    """Validate the endpoint response and return nonempty unique labels."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ArchiveCatalogError("list-targets response is not valid JSON") from exc
    if not isinstance(payload, list):
        raise ArchiveCatalogError("list-targets response must be a JSON list")

    labels: list[str] = []
    blank_count = 0
    seen: dict[str, str] = {}
    for index, value in enumerate(payload):
        if not isinstance(value, str):
            raise ArchiveCatalogError(
                f"list-targets row {index} is {type(value).__name__}, not a string"
            )
        label = value.strip()
        if not label:
            blank_count += 1
            continue
        key = label.casefold()
        if key in seen:
            raise ArchiveCatalogError(
                "list-targets contains a case-insensitive identity collision: "
                f"{seen[key]!r} and {label!r}"
            )
        seen[key] = label
        labels.append(label)
    if len(labels) < EXPECTED_MIN_NONEMPTY_TARGETS:
        raise ArchiveCatalogError(
            "list-targets namespace unexpectedly shrank below the verified floor: "
            f"expected at least {EXPECTED_MIN_NONEMPTY_TARGETS}, observed {len(labels)}"
        )
    return labels, blank_count


def load_queue_aliases(path: Path) -> tuple[dict[str, list[dict[str, str]]], int]:
    """Index only aliases explicitly present in the durable priority queue."""
    if not path.is_file():
        raise ArchiveCatalogError(f"target-priority queue not found: {path}")
    aliases: dict[str, list[dict[str, str]]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ArchiveCatalogError(f"target-priority queue is empty: {path}")
    required = {
        "target_id",
        "catalog_ids",
        "status",
        "local_coverage_status",
        "target_selection_score",
        "ra_deg",
        "dec_deg",
    }
    missing = required - set(rows[0])
    if missing:
        raise ArchiveCatalogError(
            f"target-priority queue lacks required columns: {', '.join(sorted(missing))}"
        )
    for row in rows:
        target_id = row["target_id"].strip()
        if not target_id:
            raise ArchiveCatalogError("target-priority queue contains an empty target_id")
        documented = {target_id}
        documented.update(
            alias.strip() for alias in row["catalog_ids"].split(";") if alias.strip()
        )
        for alias in documented:
            aliases.setdefault(alias.casefold(), []).append(row)
    return aliases, len(rows)


def build_catalog_rows(
    labels: Sequence[str],
    aliases: Mapping[str, Sequence[Mapping[str, str]]],
    *,
    retrieved_at_utc: str,
) -> list[dict[str, str]]:
    """Build stable candidates without inferring identity from label shape."""
    rows: list[dict[str, str]] = []
    candidate_ids: set[str] = set()
    for label in labels:
        matches = list(aliases.get(label.casefold(), ()))
        digest = hashlib.sha256(label.casefold().encode()).hexdigest()[:20].upper()
        candidate_id = f"BLARCHIVE-{digest}"
        if candidate_id in candidate_ids:
            raise ArchiveCatalogError(f"stable candidate ID collision for label {label!r}")
        candidate_ids.add(candidate_id)

        if len(matches) == 1:
            queue_row = matches[0]
            identity_status = "resolved_existing_queue_alias"
            canonical_target_id = queue_row["target_id"].strip()
            identity_provenance = "target_priority_queue_exact_casefold_alias"
            queue_status = queue_row["status"].strip()
            local_coverage_status = queue_row["local_coverage_status"].strip()
            selection_score = queue_row["target_selection_score"].strip()
            ranking_eligible = str(queue_status == "raw_download_approval_required").lower()
            eligibility_reason = (
                "delegate_to_target_priority_queue"
                if ranking_eligible == "true"
                else f"existing_queue_status:{queue_status}"
            )
            ra_deg = queue_row["ra_deg"].strip()
            dec_deg = queue_row["dec_deg"].strip()
        elif len(matches) > 1:
            identity_status = "ambiguous_existing_queue_alias"
            canonical_target_id = ""
            identity_provenance = "multiple_target_priority_queue_alias_matches"
            queue_status = ""
            local_coverage_status = ""
            selection_score = ""
            ranking_eligible = "false"
            eligibility_reason = "ambiguous_identity"
            ra_deg = ""
            dec_deg = ""
        else:
            identity_status = "unresolved_archive_label"
            canonical_target_id = ""
            identity_provenance = "no_exact_target_priority_queue_alias"
            queue_status = ""
            local_coverage_status = ""
            selection_score = ""
            ranking_eligible = "false"
            eligibility_reason = "identity_and_file_metadata_enrichment_required"
            ra_deg = ""
            dec_deg = ""

        rows.append(
            {
                "candidate_id": candidate_id,
                "archive_target_label": label,
                "canonical_target_id": canonical_target_id,
                "identity_status": identity_status,
                "identity_provenance": identity_provenance,
                "archive_target_present": "true",
                "queue_status": queue_status,
                "local_coverage_status": local_coverage_status,
                "target_selection_score": selection_score,
                "ranking_eligible": ranking_eligible,
                "eligibility_reason": eligibility_reason,
                "ra_deg": ra_deg,
                "dec_deg": dec_deg,
                "source_endpoint": SOURCE_ENDPOINT,
                "retrieved_at_utc": retrieved_at_utc,
                "schema_version": SCHEMA_VERSION,
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


def _record_path(path: Path) -> str:
    """Keep committed status portable while allowing external test outputs."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except (OSError, ValueError):
        return str(path)


def acquire_catalog(
    *,
    queue_path: Path = DEFAULT_QUEUE_PATH,
    raw_output: Path = DEFAULT_RAW_OUTPUT,
    catalog_output: Path = DEFAULT_CATALOG_OUTPUT,
    retrieved_at_utc: str | None = None,
    fetcher: Callable[..., str] = fetch_target_labels,
) -> dict[str, Any]:
    """Fetch, validate, resolve, and durably write the metadata catalog."""
    text = fetcher()
    labels, blank_count = parse_target_labels(text)
    aliases, queue_count = load_queue_aliases(queue_path)
    retrieved = retrieved_at_utc or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    rows = build_catalog_rows(labels, aliases, retrieved_at_utc=retrieved)

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CATALOG_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    catalog_text = buffer.getvalue()
    _atomic_write(raw_output, text)
    _atomic_write(catalog_output, catalog_text)

    counts: dict[str, int] = {}
    for row in rows:
        status = row["identity_status"]
        counts[status] = counts.get(status, 0) + 1
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "source_endpoint": SOURCE_ENDPOINT,
        "source_documentation": SOURCE_DOCUMENTATION,
        "retrieved_at_utc": retrieved,
        "raw_response_count": len(labels) + blank_count,
        "blank_label_count": blank_count,
        "candidate_count": len(rows),
        "queue_candidate_count": queue_count,
        "identity_counts": counts,
        "ranking_eligible_count": sum(row["ranking_eligible"] == "true" for row in rows),
        "raw_output": _record_path(raw_output),
        "catalog_output": _record_path(catalog_output),
        "catalog_sha256": hashlib.sha256(catalog_text.encode()).hexdigest(),
        "per_item_detail": {
            "path": _record_path(catalog_output),
            "schema_version": SCHEMA_VERSION,
            "row_count": len(rows),
        },
        "raw_science_payload_downloaded": False,
    }


def main(
    argv: list[str] | None = None,
    *,
    fetcher: Callable[..., str] = fetch_target_labels,
    status_recorder: Callable[..., dict[str, Any]] = record_and_publish_data_collection_status,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-path", type=Path, default=DEFAULT_QUEUE_PATH)
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_OUTPUT)
    parser.add_argument("--catalog-output", type=Path, default=DEFAULT_CATALOG_OUTPUT)
    parser.add_argument("--status-path", type=Path)
    args = parser.parse_args(argv)
    attempt_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    status_key = f"acquire_bl_archive_candidate_catalog__{attempt_id}"

    try:
        summary = acquire_catalog(
            queue_path=args.queue_path,
            raw_output=args.raw_output,
            catalog_output=args.catalog_output,
            fetcher=fetcher,
        )
    except (ArchiveCatalogError, OSError, UnicodeError) as exc:
        failure = {
            "ok": False,
            "schema_version": SCHEMA_VERSION,
            "source_endpoint": SOURCE_ENDPOINT,
            "error": f"{type(exc).__name__}: {exc}",
            "raw_science_payload_downloaded": False,
        }
        try:
            status_recorder(
                REPO_ROOT,
                status_key,
                failure,
                status_path=args.status_path,
            )
        except Exception as status_exc:  # noqa: BLE001 - report both failures loudly
            print(f"[ERROR] Status recording failed: {status_exc}", file=sys.stderr)
        print(f"[ERROR] {failure['error']}", file=sys.stderr)
        return 1

    try:
        status_recorder(
            REPO_ROOT,
            status_key,
            summary,
            status_path=args.status_path,
        )
    except Exception as exc:  # noqa: BLE001 - required acquisition provenance
        print(f"[ERROR] Acquisition succeeded but status recording failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"[OK] {summary['candidate_count']} public archive labels; "
        f"{summary['identity_counts'].get('resolved_existing_queue_alias', 0)} exact "
        f"queue identities; {summary['ranking_eligible_count']} ranking-eligible"
    )
    print(f"[INFO] Catalog: {summary['catalog_output']}")
    print("[INFO] Raw science payload downloaded: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
