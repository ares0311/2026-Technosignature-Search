"""Durability checks for the committed public-archive candidate catalog."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data_selection" / "bl_archive_candidate_catalog.csv"
STATUS = ROOT / "docs" / "data_collection_status.json"


def test_committed_archive_catalog_is_large_unique_and_status_bound() -> None:
    rows = list(csv.DictReader(CATALOG.open(encoding="utf-8")))
    assert len(rows) >= 10_000
    assert len({row["candidate_id"] for row in rows}) == len(rows)
    assert len({row["archive_target_label"].casefold() for row in rows}) == len(rows)
    assert {row["schema_version"] for row in rows} == {
        "bl_archive_candidate_catalog_v1"
    }

    status = json.loads(STATUS.read_text(encoding="utf-8"))["runs"]
    successful = [
        value
        for key, value in status.items()
        if key.startswith("acquire_bl_archive_candidate_catalog__") and value.get("ok")
    ]
    latest = max(successful, key=lambda value: value["retrieved_at_utc"])
    assert hashlib.sha256(CATALOG.read_bytes()).hexdigest() == latest["catalog_sha256"]
    assert latest["candidate_count"] == len(rows)
    assert latest["raw_science_payload_downloaded"] is False


def test_unresolved_or_ambiguous_archive_labels_are_never_ranked() -> None:
    rows = list(csv.DictReader(CATALOG.open(encoding="utf-8")))
    unresolved = [row for row in rows if row["identity_status"] != "resolved_existing_queue_alias"]
    assert unresolved
    assert all(row["canonical_target_id"] == "" for row in unresolved)
    assert all(row["ranking_eligible"] == "false" for row in unresolved)
    assert all(row["target_selection_score"] == "" for row in unresolved)

    ranked = [row for row in rows if row["ranking_eligible"] == "true"]
    assert ranked
    assert all(row["identity_status"] == "resolved_existing_queue_alias" for row in ranked)
    assert all(row["queue_status"] == "raw_download_approval_required" for row in ranked)
    assert all(row["target_selection_score"] for row in ranked)
