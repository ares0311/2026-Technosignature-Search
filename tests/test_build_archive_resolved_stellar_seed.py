"""Tests for building a real stellar seed CSV from resolved archive labels."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

MODULE_NAME = "build_archive_resolved_stellar_seed"
MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / f"{MODULE_NAME}.py"
_spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
assert _spec is not None and _spec.loader is not None
build_seed = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = build_seed
_spec.loader.exec_module(build_seed)


def _catalog_row(label: str, **overrides: str) -> dict[str, str]:
    base = {
        "candidate_id": f"BLARCHIVE-{label}",
        "archive_target_label": label,
        "canonical_target_id": f"CID-{label}",
        "identity_status": "resolved_via_simbad_name_lookup",
        "identity_provenance": "simbad_direct_name_match;direct_label",
        "archive_target_present": "true",
        "queue_status": "",
        "local_coverage_status": "",
        "target_selection_score": "",
        "ranking_eligible": "false",
        "eligibility_reason": "identity_resolved_pending_file_metadata_enrichment",
        "ra_deg": "10.0",
        "dec_deg": "20.0",
        "object_type": "Star",
        "source_endpoint": "http://seti.berkeley.edu/opendata/api/list-targets",
        "retrieved_at_utc": "2026-07-24T00:00:00Z",
        "schema_version": "bl_archive_candidate_catalog_v1",
    }
    base.update(overrides)
    return base


def test_is_stellar_object_type_matches_real_observed_categories() -> None:
    stellar = ["Star", "HighPM*", "**", "SB*", "PulsV*", "Planet", "YSO", "WhiteDwarf"]
    non_stellar = [
        "Pulsar",
        "Galaxy",
        "AGN_Candidate",
        "Seyfert2",
        "QSO",
        "Blazar",
        "GtowardsGroup",
        "GlobCluster",
        "radioBurst",
    ]
    for otype in stellar:
        assert build_seed.is_stellar_object_type(otype), otype
    for otype in non_stellar:
        assert not build_seed.is_stellar_object_type(otype), otype
    assert not build_seed.is_stellar_object_type("")


def test_is_stellar_object_type_handles_candidate_suffix() -> None:
    assert build_seed.is_stellar_object_type("BYDraV*_Candidate")
    assert build_seed.is_stellar_object_type("EclBin_Candidate")
    assert build_seed.is_stellar_object_type("RRLyrae_Candidate")


def test_build_stellar_seed_rows_excludes_unresolved_ambiguous_and_non_stellar() -> None:
    rows = [
        _catalog_row("HIP1", canonical_target_id="HD 1", object_type="Star"),
        _catalog_row(
            "3C123",
            canonical_target_id="3C 123",
            object_type="RadioG",
        ),
        _catalog_row(
            "STILLUNRESOLVED",
            identity_status="unresolved_archive_label",
            canonical_target_id="",
            object_type="",
        ),
        _catalog_row(
            "QUEUEROW",
            identity_status="resolved_existing_queue_alias",
            canonical_target_id="HD 2",
            object_type="Star",
        ),
    ]

    seed_rows = build_seed.build_stellar_seed_rows(rows)

    assert len(seed_rows) == 1
    assert seed_rows[0]["name"] == "HIP1"
    assert seed_rows[0]["ra_deg"] == "10.0"
    assert seed_rows[0]["dec_deg"] == "20.0"
    assert seed_rows[0]["hip"] == "1"
    assert seed_rows[0]["dist_pc"] == ""
    assert seed_rows[0]["spec_type"] == ""


def test_build_stellar_seed_rows_deduplicates_cadence_role_suffix_variants() -> None:
    rows = [
        _catalog_row("0407-658", canonical_target_id="ICRF J040820.3-654509", object_type="Star"),
        _catalog_row(
            "0407-658_S", canonical_target_id="ICRF J040820.3-654509", object_type="Star"
        ),
        _catalog_row(
            "0407-658_R", canonical_target_id="ICRF J040820.3-654509", object_type="Star"
        ),
    ]

    seed_rows = build_seed.build_stellar_seed_rows(rows)

    assert len(seed_rows) == 1


def test_build_stellar_seed_rows_extracts_hip_number_from_suffixed_label() -> None:
    rows = [_catalog_row("HIP12345_S", canonical_target_id="HD 99999", object_type="Star")]

    seed_rows = build_seed.build_stellar_seed_rows(rows)

    assert seed_rows[0]["hip"] == "12345"
    # name must be the bare canonical HIP form, not the raw suffixed label:
    # target_priority_queue.py uses name as target_id, and a suffixed
    # target_id would still alias-match an existing HIP<number> row's real
    # coverage state while remaining a separate, undeduplicated queue row
    # for the same physical star (verified live, HIP36817 vs HIP36817_R).
    assert seed_rows[0]["name"] == "HIP12345"


def test_build_seed_file_writes_real_schema_and_summary(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.csv"
    output_path = tmp_path / "seed.csv"
    rows = [
        _catalog_row("HIP1", canonical_target_id="HD 1", object_type="Star"),
        _catalog_row("QSO1", canonical_target_id="QSO B0001", object_type="QSO"),
    ]
    with catalog_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    summary = build_seed.build_seed_file(catalog_path, output_path)

    assert summary["ok"] is True
    assert summary["resolved_candidate_count"] == 2
    assert summary["stellar_seed_row_count"] == 1
    assert summary["excluded_non_stellar_or_duplicate_count"] == 1

    with output_path.open(newline="", encoding="utf-8") as handle:
        out_rows = list(csv.DictReader(handle))
    assert list(out_rows[0]) == list(build_seed.SEED_FIELDS)
    assert out_rows[0]["name"] == "HIP1"
