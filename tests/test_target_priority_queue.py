from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path

from techno_search.cli import main
from techno_search.target_priority_queue import (
    TARGET_PRIORITY_QUEUE_FIELDS,
    build_target_priority_manifest,
    build_target_priority_queue,
    build_target_priority_size_preflight,
    target_priority_queue_summary,
    write_target_priority_queue,
    write_target_priority_size_preflight,
)


def _write_seed_csv(path: Path) -> None:
    rows = [
        {
            "hip": "2",
            "name": "HIP2",
            "ra_deg": "0.004167",
            "dec_deg": "-19.498611",
            "dist_pc": "45.6",
            "spec_type": "K3V",
            "gal_lat": "-75.9582",
            "exoplanet": "0",
            "bl_paper": "E17",
        },
        {
            "hip": "99427",
            "name": "GJ99427",
            "ra_deg": "302.7191",
            "dec_deg": "77.2411125",
            "dist_pc": "18.0",
            "spec_type": "G2V",
            "gal_lat": "21.0",
            "exoplanet": "1",
            "bl_paper": "E17",
        },
        {
            "hip": "71681",
            "name": "HIP71681",
            "ra_deg": "219.1",
            "dec_deg": "10.2",
            "dist_pc": "8.0",
            "spec_type": "M1V",
            "gal_lat": "12.0",
            "exoplanet": "0",
            "bl_paper": "E17",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_status_json(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "runs": {
                    "download_bl_extended_corpus": {
                        "reused_targets": ["HIP99427"],
                        "downloaded_targets": [],
                        "skipped_targets": [
                            {
                                "target": "HIP71681",
                                "reason": "no_hdf5_url_discovered",
                            }
                        ],
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def test_build_target_priority_queue_marks_discovered_urls_for_size_preflight(
    tmp_path: Path,
) -> None:
    seed_path = tmp_path / "seed.csv"
    status_path = tmp_path / "status.json"
    _write_seed_csv(seed_path)
    status_path.write_text(
        json.dumps(
            {
                "runs": {
                    "download_bl_extended_corpus": {
                        "reused_targets": ["HIP99427"],
                        "downloaded_targets": [],
                        "skipped_targets": [],
                    },
                    "download_bl_extended_corpus_discovery": {
                        "available_targets": [
                            {
                                "target": "HIP2",
                                "url": "https://bldata.berkeley.edu/example/HIP2.h5",
                            }
                        ],
                        "skipped_targets": [
                            {
                                "target": "HIP71681",
                                "reason": "no_hdf5_url_discovered",
                            }
                        ],
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    rows = build_target_priority_queue(
        seed_csv_path=seed_path,
        data_status_path=status_path,
    )
    rows_by_id = {row["target_id"]: row for row in rows}

    assert rows_by_id["HIP2"]["status"] == "size_preflight_required"
    assert rows_by_id["HIP2"]["data_products_available"] == "hdf5_url_discovered"
    assert rows_by_id["HIP2"]["local_coverage_status"] == (
        "not_searched_hdf5_url_discovered"
    )
    assert rows_by_id["HIP2"]["source_hdf5_url"] == (
        "https://bldata.berkeley.edu/example/HIP2.h5"
    )
    assert "size/checksum/storage preflight" in rows_by_id["HIP2"]["notes"]
    assert rows_by_id["HIP71681"]["status"] == "metadata_discovery_required"


def test_build_target_priority_queue_prefers_unsearched_metadata_targets(
    tmp_path: Path,
) -> None:
    seed_path = tmp_path / "seed.csv"
    status_path = tmp_path / "status.json"
    _write_seed_csv(seed_path)
    _write_status_json(status_path)

    rows = build_target_priority_queue(
        seed_csv_path=seed_path,
        data_status_path=status_path,
    )

    assert [row["target_id"] for row in rows] == ["HIP2", "HIP71681", "GJ99427"]
    assert rows[0]["status"] == "queued_metadata_discovery"
    assert rows[0]["search_category"] == "new_parameter_space"
    assert rows[0]["estimated_download_gb"] == ""
    assert rows[1]["status"] == "metadata_discovery_required"
    assert rows[1]["data_products_available"] == "no_hdf5_url_discovered"
    assert rows[2]["status"] == "already_acquired_local_cache"
    assert rows[2]["local_coverage_status"] == "searched_by_project"
    assert rows[2]["catalog_ids"] == "HIP 99427; GJ99427"
    assert set(TARGET_PRIORITY_QUEUE_FIELDS).issubset(rows[0])
    assert float(rows[0]["total_priority"]) > float(rows[2]["total_priority"])


def test_write_target_priority_queue_summary_counts_statuses(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed.csv"
    status_path = tmp_path / "status.json"
    output_path = tmp_path / "data_selection" / "target_priority_queue.csv"
    _write_seed_csv(seed_path)
    _write_status_json(status_path)

    result = write_target_priority_queue(
        output_path,
        seed_csv_path=seed_path,
        data_status_path=status_path,
    )

    assert output_path.exists()
    assert result["schema_version"] == "target_priority_queue_v1"
    assert result["target_count"] == 3
    assert result["by_status"] == {
        "already_acquired_local_cache": 1,
        "metadata_discovery_required": 1,
        "queued_metadata_discovery": 1,
    }
    assert result["top_targets"][0]["target_id"] == "HIP2"


def test_cli_build_and_summarize_target_priority_queue(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed.csv"
    status_path = tmp_path / "status.json"
    output_path = tmp_path / "target_priority_queue.csv"
    _write_seed_csv(seed_path)
    _write_status_json(status_path)

    build_stdout = StringIO()
    exit_code = main(
        [
            "build-target-priority-queue",
            "--seed-csv-path",
            str(seed_path),
            "--data-status-path",
            str(status_path),
            "--output-path",
            str(output_path),
        ],
        stdout=build_stdout,
    )
    build_result = json.loads(build_stdout.getvalue())

    assert exit_code == 0
    assert build_result["ok"] is True
    assert build_result["queue_path"] == str(output_path)

    summary_stdout = StringIO()
    exit_code = main(
        ["target-priority-queue-summary", "--queue-path", str(output_path)],
        stdout=summary_stdout,
    )
    summary = json.loads(summary_stdout.getvalue())

    assert exit_code == 0
    assert summary == target_priority_queue_summary(output_path)


def test_build_target_priority_manifest_selects_top_unsearched_targets(
    tmp_path: Path,
) -> None:
    seed_path = tmp_path / "seed.csv"
    status_path = tmp_path / "status.json"
    queue_path = tmp_path / "target_priority_queue.csv"
    _write_seed_csv(seed_path)
    _write_status_json(status_path)
    write_target_priority_queue(
        queue_path,
        seed_csv_path=seed_path,
        data_status_path=status_path,
    )

    manifest = build_target_priority_manifest(
        queue_path=queue_path,
        max_targets=1,
        generated_at_utc="2026-07-09T12:00:00+00:00",
    )

    assert manifest["schema_version"] == "target_priority_manifest_v1"
    assert manifest["generated_at_utc"] == "2026-07-09T12:00:00+00:00"
    assert manifest["selection"]["selected_count"] == 1
    assert manifest["selection"]["include_statuses"] == ["queued_metadata_discovery"]
    assert manifest["targets"][0]["hip"] == "HIP2"
    assert manifest["targets"][0]["queue_status"] == "queued_metadata_discovery"
    assert manifest["targets"][0]["ra_deg"] == 0.004167
    assert "sha256" in manifest["source_queue"]


def test_cli_build_target_priority_manifest(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed.csv"
    status_path = tmp_path / "status.json"
    queue_path = tmp_path / "target_priority_queue.csv"
    manifest_path = tmp_path / "batch_manifest.json"
    _write_seed_csv(seed_path)
    _write_status_json(status_path)
    write_target_priority_queue(
        queue_path,
        seed_csv_path=seed_path,
        data_status_path=status_path,
    )

    stdout = StringIO()
    exit_code = main(
        [
            "build-target-priority-manifest",
            "--queue-path",
            str(queue_path),
            "--output-path",
            str(manifest_path),
            "--max-targets",
            "2",
            "--generated-at-utc",
            "2026-07-09T12:00:00+00:00",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert result["ok"] is True
    assert result["selected_count"] == 1
    assert result["output_path"] == str(manifest_path)
    assert manifest["targets"][0]["hip"] == "HIP2"
    assert manifest["selection"]["max_targets"] == 2


def test_cli_build_target_priority_manifest_replaces_default_status_filter(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "target_priority_queue.csv"
    manifest_path = tmp_path / "batch_manifest.json"
    with queue_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TARGET_PRIORITY_QUEUE_FIELDS)
        writer.writeheader()
        base_row = {field: "" for field in TARGET_PRIORITY_QUEUE_FIELDS}
        writer.writerow(
            {
                **base_row,
                "target_id": "HIPQUEUED",
                "ra_deg": "1.0",
                "dec_deg": "2.0",
                "search_category": "new_parameter_space",
                "status": "queued_metadata_discovery",
                "local_coverage_status": "not_searched_by_project",
                "total_priority": "20",
                "background_target_priority_score": "0.5",
                "data_products_available": "requires_product_metadata_discovery",
                "notes": "queued",
            }
        )
        writer.writerow(
            {
                **base_row,
                "target_id": "HIPREADY",
                "ra_deg": "3.0",
                "dec_deg": "4.0",
                "search_category": "new_parameter_space",
                "status": "size_preflight_required",
                "local_coverage_status": "not_searched_hdf5_url_discovered",
                "total_priority": "19.75",
                "background_target_priority_score": "0.5",
                "data_products_available": "hdf5_url_discovered",
                "source_hdf5_url": "https://bldata.berkeley.edu/example/HIPREADY.h5",
                "notes": "preflight",
            }
        )

    stdout = StringIO()
    exit_code = main(
        [
            "build-target-priority-manifest",
            "--queue-path",
            str(queue_path),
            "--output-path",
            str(manifest_path),
            "--include-status",
            "size_preflight_required",
        ],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert result["include_statuses"] == ["size_preflight_required"]
    assert result["selected_count"] == 1
    assert manifest["selection"]["include_statuses"] == ["size_preflight_required"]
    assert [target["hip"] for target in manifest["targets"]] == ["HIPREADY"]
    assert manifest["targets"][0]["source_hdf5_url"].endswith("HIPREADY.h5")


def test_target_priority_size_preflight_records_header_metadata(tmp_path: Path) -> None:
    manifest_path = tmp_path / "size_preflight_manifest.json"
    output_path = tmp_path / "size_preflight_report.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "target_priority_manifest_v1",
                "targets": [
                    {
                        "hip": "HIPREADY",
                        "source_hdf5_url": "https://bldata.berkeley.edu/example/HIPREADY.h5",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    def head_fn(url: str, timeout_seconds: float) -> dict[str, object]:
        assert url == "https://bldata.berkeley.edu/example/HIPREADY.h5"
        assert timeout_seconds == 12.0
        return {
            "ok": True,
            "status_code": 200,
            "headers": {
                "content-length": "123456789",
                "accept-ranges": "bytes",
                "etag": '"opaque-etag"',
                "last-modified": "Thu, 09 Jul 2026 17:45:00 GMT",
                "content-type": "application/x-hdf5",
                "content-md5": "abc123",
            },
            "error": "",
        }

    preflight = build_target_priority_size_preflight(
        manifest_path,
        timeout_seconds=12.0,
        head_fn=head_fn,
        generated_at_utc="2026-07-09T18:00:00+00:00",
    )
    result = write_target_priority_size_preflight(
        output_path,
        manifest_path=manifest_path,
        timeout_seconds=12.0,
        head_fn=head_fn,
        generated_at_utc="2026-07-09T18:00:00+00:00",
    )
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert preflight["schema_version"] == "target_priority_size_preflight_v1"
    assert preflight["target_count"] == 1
    assert preflight["ok_target_count"] == 1
    assert preflight["sized_target_count"] == 1
    assert preflight["checksum_header_count"] == 1
    assert preflight["total_content_length_bytes"] == 123456789
    assert preflight["raw_download_authorized"] is False
    assert preflight["targets"][0]["accept_ranges"] == "bytes"
    assert preflight["targets"][0]["checksum_headers"] == {"content-md5": "abc123"}
    assert result["ok"] is True
    assert result["raw_download_authorized"] is False
    assert written == preflight


def test_build_target_priority_queue_promotes_sized_urls_to_download_approval(
    tmp_path: Path,
) -> None:
    seed_path = tmp_path / "seed.csv"
    status_path = tmp_path / "status.json"
    preflight_path = tmp_path / "size_preflight_report.json"
    _write_seed_csv(seed_path)
    status_path.write_text(
        json.dumps(
            {
                "runs": {
                    "download_bl_extended_corpus": {
                        "reused_targets": [],
                        "downloaded_targets": [],
                        "skipped_targets": [],
                    },
                    "download_bl_extended_corpus_discovery": {
                        "available_targets": [
                            {
                                "target": "HIP2",
                                "url": "https://bldata.berkeley.edu/example/HIP2.h5",
                            }
                        ],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    preflight_path.write_text(
        json.dumps(
            {
                "schema_version": "target_priority_size_preflight_v1",
                "targets": [
                    {
                        "target_id": "HIP2",
                        "url": "https://bldata.berkeley.edu/example/HIP2.h5",
                        "ok": True,
                        "content_length_gb": 0.242659,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rows = build_target_priority_queue(
        seed_csv_path=seed_path,
        data_status_path=status_path,
        size_preflight_report_path=preflight_path,
    )
    hip2 = {row["target_id"]: row for row in rows}["HIP2"]

    assert hip2["status"] == "raw_download_approval_required"
    assert hip2["data_products_available"] == "hdf5_size_preflight_ok"
    assert hip2["estimated_download_gb"] == "0.242659"
    assert hip2["local_coverage_status"] == "not_searched_size_preflight_ok"
    assert hip2["source_hdf5_url"].endswith("HIP2.h5")
    assert "explicit operator approval" in hip2["notes"]


def test_build_target_priority_queue_merges_multiple_size_preflight_reports(
    tmp_path: Path,
) -> None:
    """A later acquisition batch's report must not regress an earlier batch.

    Each committed size-preflight report represents one acquisition batch
    (e.g. top-25, then the next-25). Passing only the newest report must not
    drop an earlier batch's already-promoted raw_download_approval_required
    rows back to an unresolved status.
    """

    seed_path = tmp_path / "seed.csv"
    status_path = tmp_path / "status.json"
    first_preflight_path = tmp_path / "first_size_preflight_report.json"
    second_preflight_path = tmp_path / "second_size_preflight_report.json"
    _write_seed_csv(seed_path)
    status_path.write_text(json.dumps({"runs": {}}), encoding="utf-8")
    first_preflight_path.write_text(
        json.dumps(
            {
                "schema_version": "target_priority_size_preflight_v1",
                "targets": [
                    {
                        "target_id": "HIP2",
                        "url": "https://bldata.berkeley.edu/example/HIP2.h5",
                        "ok": True,
                        "content_length_gb": 0.242659,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    second_preflight_path.write_text(
        json.dumps(
            {
                "schema_version": "target_priority_size_preflight_v1",
                "targets": [
                    {
                        "target_id": "HIP99427",
                        "url": "https://bldata.berkeley.edu/example/HIP99427.h5",
                        "ok": True,
                        "content_length_gb": 0.5,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rows = build_target_priority_queue(
        seed_csv_path=seed_path,
        data_status_path=status_path,
        size_preflight_report_path=first_preflight_path,
        extra_size_preflight_report_paths=[second_preflight_path],
    )
    rows_by_target = {row["target_id"]: row for row in rows}

    assert rows_by_target["HIP2"]["status"] == "raw_download_approval_required"
    assert rows_by_target["GJ99427"]["status"] == "raw_download_approval_required"


def test_build_target_priority_queue_merges_multiple_discovery_results(
    tmp_path: Path,
) -> None:
    """A later discovery round must not lose an earlier round's results.

    docs/data_collection_status.json keeps only the single most recent
    ``download_bl_extended_corpus_discovery`` run. Once a second discovery
    round (e.g. next25) has run, the first round's (top25) "no HDF5 URL
    found" targets are no longer visible there. Committed
    ``*_discovery_result.json`` files preserve each round's real outcome, and
    build_target_priority_queue must merge all of them, or the first round's
    already-checked, still-unavailable targets silently fall back to
    queued_metadata_discovery and get re-selected into a later acquisition
    batch, wasting a repeat discovery check on a target already known to
    have no URL.
    """

    seed_path = tmp_path / "seed.csv"
    status_path = tmp_path / "status.json"
    first_round_result_path = tmp_path / "round1_discovery_result.json"
    _write_seed_csv(seed_path)
    # Simulates the real overwrite bug: the tracked status file only still
    # holds the *second* round's discovery outcome (HIP71681 checked, no
    # URL); the first round's outcome (HIP2 checked, no URL) has already
    # been overwritten there and only survives in the committed result file.
    status_path.write_text(
        json.dumps(
            {
                "runs": {
                    "download_bl_extended_corpus_discovery": {
                        "available_targets": [],
                        "skipped_targets": [
                            {
                                "target": "HIP71681",
                                "reason": "no_hdf5_url_discovered",
                            }
                        ],
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    first_round_result_path.write_text(
        json.dumps(
            {
                "available_targets": [],
                "skipped_targets": [
                    {"target": "HIP2", "reason": "no_hdf5_url_discovered"}
                ],
            }
        ),
        encoding="utf-8",
    )

    rows = build_target_priority_queue(
        seed_csv_path=seed_path,
        data_status_path=status_path,
        extra_discovery_result_paths=[first_round_result_path],
    )
    rows_by_target = {row["target_id"]: row for row in rows}

    assert rows_by_target["HIP2"]["status"] == "metadata_discovery_required"
    assert rows_by_target["HIP71681"]["status"] == "metadata_discovery_required"
