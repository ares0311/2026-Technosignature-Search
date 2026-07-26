from __future__ import annotations

import csv
import shutil
from pathlib import Path

from techno_search.hunter_adaptive_discovery import adaptive_discovery_loop
from techno_search.target_priority_queue import TARGET_PRIORITY_QUEUE_FIELDS


def _write_queue(path: Path, rows: list[tuple[str, float, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TARGET_PRIORITY_QUEUE_FIELDS)
        writer.writeheader()
        for target_id, score, status in rows:
            row = dict.fromkeys(TARGET_PRIORITY_QUEUE_FIELDS, "")
            row.update(
                {
                    "target_id": target_id,
                    "target_selection_score": str(score),
                    "total_priority": str(score),
                    "status": status,
                }
            )
            writer.writerow(row)


def test_high_value_candidate_outside_initial_eligible_pool_is_found(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "initial.csv"
    _write_queue(
        queue,
        [
            ("INITIAL", 0.5, "raw_download_approval_required"),
            ("OUTSIDE", 0.9, "queued_metadata_discovery"),
            ("LOWER", 0.4, "queued_metadata_discovery"),
        ],
    )

    def expand(
        current: Path,
        rows: list[dict[str, str]],
        work_dir: Path,
        round_number: int,
    ) -> tuple[Path, dict[str, object]]:
        assert [row["target_id"] for row in rows] == ["OUTSIDE"]
        updated = work_dir / f"round-{round_number}.csv"
        shutil.copy2(current, updated)
        records = list(csv.DictReader(updated.open(newline="", encoding="utf-8")))
        records[0]["status"] = "raw_download_approval_required"
        for record in records:
            if record["target_id"] == "OUTSIDE":
                record["status"] = "raw_download_approval_required"
        _write_queue(
            updated,
            [
                (
                    record["target_id"],
                    float(record["target_selection_score"]),
                    record["status"],
                )
                for record in records
            ],
        )
        return updated, {"found": ["OUTSIDE"]}

    resolved_queue, report = adaptive_discovery_loop(
        queue,
        target_count=1,
        work_dir=tmp_path / "work",
        expand_round=expand,
    )

    rows = list(csv.DictReader(resolved_queue.open(newline="", encoding="utf-8")))
    eligible = [
        row
        for row in rows
        if row["status"] == "raw_download_approval_required"
    ]
    eligible.sort(key=lambda row: -float(row["target_selection_score"]))
    assert eligible[0]["target_id"] == "OUTSIDE"
    assert report["round_count"] == 1
    assert report["sufficient"] is True


def test_weak_absolute_quality_does_not_block_best_available_n(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    _write_queue(
        queue,
        [
            ("WEAK1", 0.01, "raw_download_approval_required"),
            ("WEAK2", 0.001, "raw_download_approval_required"),
        ],
    )

    resolved_queue, report = adaptive_discovery_loop(
        queue,
        target_count=2,
        work_dir=tmp_path / "work",
        expand_round=lambda *_args: (_ for _ in ()).throw(AssertionError()),
    )

    assert resolved_queue == queue
    assert report["eligible_count"] == 2
    assert report["selection_cutoff_score"] == 0.001
    assert report["round_count"] == 0
