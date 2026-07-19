"""Fidelity tests for the public BL archive target-namespace catalog."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pytest
import scripts.acquire_bl_archive_candidate_catalog as module
from scripts.acquire_bl_archive_candidate_catalog import (
    ArchiveCatalogError,
    acquire_catalog,
    build_catalog_rows,
    load_queue_aliases,
    parse_target_labels,
)


def _write_queue(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "target_id",
        "catalog_ids",
        "status",
        "local_coverage_status",
        "target_selection_score",
        "ra_deg",
        "dec_deg",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "target_id": "HIP103096",
                "catalog_ids": "HIP 103096; HIP103096",
                "status": "already_acquired_local_cache",
                "local_coverage_status": "searched_by_project",
                "target_selection_score": "0.268",
                "ra_deg": "313.3325",
                "dec_deg": "62.154167",
            }
        )


def test_parse_target_labels_rejects_non_list_and_identity_collisions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(module, "EXPECTED_MIN_NONEMPTY_TARGETS", 1)
    with pytest.raises(ArchiveCatalogError, match="JSON list"):
        parse_target_labels('{"target": "HIP103096"}')
    with pytest.raises(ArchiveCatalogError, match="identity collision"):
        parse_target_labels('["HIP103096", "hip103096"]')


def test_build_catalog_resolves_only_documented_exact_aliases(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    _write_queue(queue)
    aliases, count = load_queue_aliases(queue)

    rows = build_catalog_rows(
        ["HIP103096", "HIP103096_R", "3C286"],
        aliases,
        retrieved_at_utc="2026-07-19T14:00:00Z",
    )

    assert count == 1
    assert rows[0]["canonical_target_id"] == "HIP103096"
    assert rows[0]["identity_status"] == "resolved_existing_queue_alias"
    assert rows[0]["ranking_eligible"] == "false"
    assert rows[1]["identity_status"] == "unresolved_archive_label"
    assert rows[1]["canonical_target_id"] == ""
    assert rows[2]["eligibility_reason"] == (
        "identity_and_file_metadata_enrichment_required"
    )
    assert len({row["candidate_id"] for row in rows}) == 3


def test_acquire_catalog_writes_raw_and_row_level_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "EXPECTED_MIN_NONEMPTY_TARGETS", 2)
    queue = tmp_path / "queue.csv"
    raw = tmp_path / "raw.json"
    catalog = tmp_path / "catalog.csv"
    _write_queue(queue)
    response = json.dumps(["", "HIP103096", "3C286"])

    summary = acquire_catalog(
        queue_path=queue,
        raw_output=raw,
        catalog_output=catalog,
        retrieved_at_utc="2026-07-19T14:00:00Z",
        fetcher=lambda: response,
    )

    assert raw.read_text(encoding="utf-8") == response
    rows = list(csv.DictReader(catalog.open(encoding="utf-8")))
    assert len(rows) == 2
    assert summary["raw_response_count"] == 3
    assert summary["blank_label_count"] == 1
    assert summary["identity_counts"] == {
        "resolved_existing_queue_alias": 1,
        "unresolved_archive_label": 1,
    }
    assert summary["per_item_detail"]["row_count"] == 2
    assert summary["raw_science_payload_downloaded"] is False


def test_main_dispatch_records_success_and_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "EXPECTED_MIN_NONEMPTY_TARGETS", 1)
    queue = tmp_path / "queue.csv"
    _write_queue(queue)
    recorded: list[dict[str, Any]] = []

    status_keys: list[str] = []

    def record(_root: Path, script: str, summary: dict[str, Any], **_kwargs: Any):
        status_keys.append(script)
        recorded.append(summary)
        return {"manifest": {}, "git": None}

    exit_code = module.main(
        [
            "--queue-path",
            str(queue),
            "--raw-output",
            str(tmp_path / "raw.json"),
            "--catalog-output",
            str(tmp_path / "catalog.csv"),
        ],
        fetcher=lambda: '["HIP103096"]',
        status_recorder=record,
    )
    assert exit_code == 0
    assert recorded[-1]["ok"] is True
    assert status_keys[-1].startswith("acquire_bl_archive_candidate_catalog__")

    exit_code = module.main(
        [
            "--queue-path",
            str(queue),
            "--raw-output",
            str(tmp_path / "failed.json"),
            "--catalog-output",
            str(tmp_path / "failed.csv"),
        ],
        fetcher=lambda: "not-json",
        status_recorder=record,
    )
    assert exit_code == 1
    assert recorded[-1]["ok"] is False
    assert status_keys[-1].startswith("acquire_bl_archive_candidate_catalog__")
    assert "not valid JSON" in recorded[-1]["error"]
