from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path

from techno_search.cli import main
from techno_search.target_priority_queue import (
    TARGET_PRIORITY_QUEUE_FIELDS,
    build_target_priority_queue,
    target_priority_queue_summary,
    write_target_priority_queue,
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
