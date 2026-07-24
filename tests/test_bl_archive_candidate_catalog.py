"""Durability checks for the committed public-archive candidate catalog."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data_selection" / "bl_archive_candidate_catalog.csv"
STATUS = ROOT / "docs" / "data_collection_status.json"


_ACQUISITION_SCRIPT_PREFIXES = (
    "acquire_bl_archive_candidate_catalog__",
    "enrich_bl_archive_candidate_identity__",
)


def test_committed_archive_catalog_is_large_unique_and_status_bound() -> None:
    rows = list(csv.DictReader(CATALOG.open(encoding="utf-8")))
    assert len(rows) >= 10_000
    assert len({row["candidate_id"] for row in rows}) == len(rows)
    assert len({row["archive_target_label"].casefold() for row in rows}) == len(rows)
    assert {row["schema_version"] for row in rows} == {
        "bl_archive_candidate_catalog_v1"
    }

    # Either the original list-targets acquisition or a later identity-
    # enrichment pass (e.g. SIMBAD name resolution) may be the most recent
    # writer of the committed catalog; whichever ran last must match exactly.
    status = json.loads(STATUS.read_text(encoding="utf-8"))["runs"]
    successful = [
        value
        for key, value in status.items()
        if key.startswith(_ACQUISITION_SCRIPT_PREFIXES) and value.get("ok")
    ]
    latest = max(successful, key=lambda value: value["retrieved_at_utc"])
    assert hashlib.sha256(CATALOG.read_bytes()).hexdigest() == latest["catalog_sha256"]
    assert latest["candidate_count"] == len(rows)
    assert latest["raw_science_payload_downloaded"] is False


def test_unresolved_or_ambiguous_archive_labels_are_never_ranked() -> None:
    rows = list(csv.DictReader(CATALOG.open(encoding="utf-8")))
    non_queue_resolved = [
        row for row in rows if row["identity_status"] != "resolved_existing_queue_alias"
    ]
    assert non_queue_resolved
    # No identity source populates ranking_eligible/target_selection_score
    # directly: even a real SIMBAD-resolved identity still requires the
    # separate archive file-metadata (HDF5 URL/size preflight) enrichment
    # step before it can become viable for acquisition.
    assert all(row["ranking_eligible"] == "false" for row in non_queue_resolved)
    assert all(row["target_selection_score"] == "" for row in non_queue_resolved)

    still_unidentified = [
        row
        for row in non_queue_resolved
        if row["identity_status"] in {"unresolved_archive_label", "ambiguous_existing_queue_alias"}
    ]
    assert still_unidentified
    assert all(row["canonical_target_id"] == "" for row in still_unidentified)

    simbad_resolved = [
        row
        for row in non_queue_resolved
        if row["identity_status"] == "resolved_via_simbad_name_lookup"
    ]
    assert simbad_resolved
    assert all(row["canonical_target_id"] != "" for row in simbad_resolved)
    assert all(row["ra_deg"] and row["dec_deg"] for row in simbad_resolved)
    assert all(row["identity_provenance"].split(";")[0] for row in simbad_resolved)
    # object_type is real evidence (SIMBAD's own classification), never a
    # guess about whether a resolved label belongs in a stellar pipeline.
    assert all(row["object_type"] for row in simbad_resolved)

    ranked = [row for row in rows if row["ranking_eligible"] == "true"]
    assert ranked
    assert all(row["identity_status"] == "resolved_existing_queue_alias" for row in ranked)
    assert all(row["queue_status"] == "raw_download_approval_required" for row in ranked)
    assert all(row["target_selection_score"] for row in ranked)


def test_queue_alias_resolved_rows_also_have_real_object_type() -> None:
    # The same conservative SIMBAD object_type backfill applies uniformly to
    # every row with a resolved canonical_target_id, not just newly-SIMBAD-
    # resolved ones -- it adds real evidence, never re-derives identity.
    rows = list(csv.DictReader(CATALOG.open(encoding="utf-8")))
    queue_resolved = [
        row for row in rows if row["identity_status"] == "resolved_existing_queue_alias"
    ]
    assert queue_resolved
    assert all(row["object_type"] for row in queue_resolved)
