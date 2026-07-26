from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.hunter_cross_project_history import (
    CROSS_PROJECT_HISTORY_SCHEMA_VERSION,
    cross_project_alias_counts,
    cross_project_evidence_by_alias,
    export_cross_project_history,
    load_cross_project_history_export,
    write_cross_project_history_export,
)
from techno_search.prod_scan_queue import SCAN_HISTORY_SCHEMA_VERSION


def _write_sibling_export(path: Path, *, canonical_id: str = "HIP 71681") -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "manifest_id": "hunter-prior-search-history-v1",
                "sources": [
                    {
                        "search_id": "historical-discovery-run-001",
                        "started_at": "2026-06-28T09:00:00Z",
                        "completed_at": "2026-06-28T09:10:00Z",
                        "searched_by": "EXO-Hunter",
                        "source_project": "2026 Exoplanet Research",
                        "source_path": "logs/discovery_run_001.json",
                        "source_sha256": "0" * 64,
                        "provenance_uri": "local-artifact:logs/discovery_run_001.json",
                        "entries": [
                            {
                                "target_id": canonical_id.replace(" ", ""),
                                "canonical_id": canonical_id,
                                "mission": "TESS",
                                "status": "no_signal",
                                "searched_at": "2026-06-28T09:05:36Z",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_load_cross_project_history_export_reads_a_real_sibling_export(
    tmp_path: Path,
) -> None:
    path = tmp_path / "sibling_export.json"
    _write_sibling_export(path)

    payload = load_cross_project_history_export(path)

    assert payload["schema_version"] == CROSS_PROJECT_HISTORY_SCHEMA_VERSION
    assert payload["sources"][0]["source_project"] == "2026 Exoplanet Research"
    assert payload["sources"][0]["validity_state"] == "stale-but-usable"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(schema_version=2),
        lambda d: d.update(sources=[]),
        lambda d: d["sources"][0].pop("source_project"),
        lambda d: d["sources"][0].pop("searched_by"),
        lambda d: d["sources"][0].update(entries=[]),
        lambda d: d["sources"][0]["entries"][0].pop("status"),
        lambda d: d["sources"][0]["entries"][0].update(target_id="", canonical_id=""),
    ],
)
def test_load_cross_project_history_export_fails_closed_on_malformed_export(
    tmp_path: Path, mutate: object
) -> None:
    path = tmp_path / "sibling_export.json"
    _write_sibling_export(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutate(payload)  # type: ignore[operator]
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        load_cross_project_history_export(path)


def test_cross_project_alias_counts_normalizes_spaced_canonical_ids(tmp_path: Path) -> None:
    path = tmp_path / "sibling_export.json"
    _write_sibling_export(path, canonical_id="HIP 71681")
    payload = load_cross_project_history_export(path)

    counts = cross_project_alias_counts(payload)

    assert counts["HIP71681"] == 1


def test_cross_project_evidence_by_alias_reports_source_and_status(tmp_path: Path) -> None:
    path = tmp_path / "sibling_export.json"
    _write_sibling_export(path, canonical_id="TIC 281731203")
    payload = load_cross_project_history_export(path)

    evidence = cross_project_evidence_by_alias(payload)

    assert evidence["TIC281731203"] == [
        {
            "source_project": "2026 Exoplanet Research",
            "status": "no_signal",
            "searched_at": "2026-06-28T09:05:36Z",
            "validity_state": "stale-but-usable",
        }
    ]


def test_failed_cross_project_attempt_never_changes_selection_counts(
    tmp_path: Path,
) -> None:
    path = tmp_path / "sibling_export.json"
    _write_sibling_export(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["sources"][0]["entries"][0]["status"] = "failed"
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_cross_project_history_export(path)

    assert loaded["sources"][0]["entries"][0]["validity_state"] == "invalid"
    assert not cross_project_alias_counts(loaded)
    assert not cross_project_evidence_by_alias(loaded)


def test_direct_cross_project_source_hash_mismatch_requires_refresh(
    tmp_path: Path,
) -> None:
    root = tmp_path / "sibling"
    source = root / "logs" / "discovery_run_001.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"real": true}\n', encoding="utf-8")
    export = root / "data_selection" / "hunter_prior_search_history_v1.json"
    export.parent.mkdir(parents=True)
    _write_sibling_export(export)

    with pytest.raises(ValueError, match="refresh-required"):
        load_cross_project_history_export(export)


def _write_scan_history(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "schema_version": SCAN_HISTORY_SCHEMA_VERSION,
                    "target_stem": "capture_HIP71681_0001",
                    "run_id": "RUN-2026-07-25_000000Z-TEST-prod-scan",
                    "scanned_at_utc": "2026-07-25T00:00:00Z",
                    "score": 0.4,
                    "pathway": "known_object_annotation",
                    "dat_file": "data/extended_corpus/HIP71681/capture.dat",
                }
            )
            + "\n"
        )


def test_export_cross_project_history_builds_a_real_schema_v1_manifest(
    tmp_path: Path,
) -> None:
    scan_history_path = tmp_path / "scan_history.ndjson"
    _write_scan_history(scan_history_path)

    payload = export_cross_project_history(
        scan_history_path=scan_history_path,
        known_target_ids={"HIP71681"},
        generated_at_utc="2026-07-25T12:00:00Z",
    )

    assert payload["schema_version"] == 1
    source = payload["sources"][0]
    assert source["searched_by"] == "Techno-Hunter"
    assert source["source_project"] == "2026 Technosignatures"
    entry = source["entries"][0]
    assert entry["target_id"] == "HIP71681"
    assert entry["canonical_id"] == "HIP 71681"
    assert entry["status"] == "known_object_annotation"


def test_export_cross_project_history_rejects_a_history_with_no_known_targets(
    tmp_path: Path,
) -> None:
    scan_history_path = tmp_path / "scan_history.ndjson"
    _write_scan_history(scan_history_path)

    with pytest.raises(ValueError, match="nothing real to export"):
        export_cross_project_history(
            scan_history_path=scan_history_path,
            known_target_ids={"HIP999999"},
        )


def test_write_cross_project_history_export_writes_a_loadable_file(tmp_path: Path) -> None:
    scan_history_path = tmp_path / "scan_history.ndjson"
    _write_scan_history(scan_history_path)
    output_path = tmp_path / "hunter_prior_search_history_v1.json"

    summary = write_cross_project_history_export(
        output_path,
        scan_history_path=scan_history_path,
        known_target_ids={"HIP71681"},
        generated_at_utc="2026-07-25T12:00:00Z",
    )

    assert summary["ok"] is True
    assert summary["entry_count"] == 1
    reloaded = load_cross_project_history_export(output_path)
    assert reloaded["sources"][0]["entries"][0]["target_id"] == "HIP71681"
