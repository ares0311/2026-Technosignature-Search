from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any

import pytest

import techno_search.hunter_search as hunter_search_module
from techno_search.hunter_cli import create_new_search, show_follow_ups
from techno_search.hunter_search import (
    SearchApprovalRequired,
    SearchLifecycleError,
    create_search,
    follow_up_registry,
    load_search,
    make_search_id,
    run_search,
)
from techno_search.production_run_outcomes import (
    PRODUCTION_FOLLOW_UPS_SCHEMA_VERSION,
    PRODUCTION_TARGET_STATUS_SCHEMA_VERSION,
)
from techno_search.production_scan import ProductionScanResult
from techno_search.target_priority_queue import TARGET_PRIORITY_QUEUE_FIELDS


def _write_queue(path: Path, count: int, *, status: str = "raw_download_approval_required") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TARGET_PRIORITY_QUEUE_FIELDS)
        writer.writeheader()
        for index in range(count):
            target_id = f"HIP{990000 + index}"
            row = dict.fromkeys(TARGET_PRIORITY_QUEUE_FIELDS, "")
            row.update(
                {
                    "target_id": target_id,
                    "project": "test",
                    "source": "pre-existing test catalog",
                    "catalog_ids": target_id,
                    "ra_deg": str(index),
                    "dec_deg": str(-index),
                    "data_products_available": "hdf5_size_preflight_ok",
                    "estimated_download_gb": "0.25",
                    "search_category": "new_parameter_space",
                    "total_priority": "16.5",
                    "target_selection_score": f"{0.9 - index / 10000:.6f}",
                    "priority_config_version": "background_priority_v0",
                    "status": status,
                    "local_coverage_status": (
                        "not_searched_size_preflight_ok"
                        if status == "raw_download_approval_required"
                        else "searched_by_project"
                    ),
                    "background_target_priority_score": "0.5",
                    "source_hdf5_url": f"https://example.test/{target_id}.h5",
                    "notes": "test row",
                }
            )
            writer.writerow(row)


def _write_follow_up_ledger(
    scans_dir: Path,
    target_name: str,
    *,
    rfi: bool = False,
    schema_version: str = PRODUCTION_FOLLOW_UPS_SCHEMA_VERSION,
    run_id: str = "RUN-2026-07-19_120000Z-ABCD-prod-scan",
    score: float = 0.9,
) -> None:
    run_dir = scans_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / f"{run_id}_follow_ups.json").write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "run_id": run_id,
                "entries": [
                    {
                        "follow_up_id": "FU-1",
                        "candidate_id": target_name,
                        "target_name": target_name,
                        "pathway": "candidate_review_packet",
                        "score": score,
                        "snr": 42.0,
                        "frequency_hz": 1.42e9,
                        "drift_rate_hz_per_sec": 0.2,
                        "drift_evidence_available": True,
                        "cross_target_rfi_flagged": rfi,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_make_search_id_is_stable_and_human_readable() -> None:
    assert make_search_id(
        now=datetime(2026, 7, 19, 12, 30, tzinfo=UTC), token="A1B2C3D4"
    ) == "SEARCH-20260719T123000Z-A1B2C3D4"


def test_create_new_search_freezes_exact_ranked_targets(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    _write_queue(queue, 3)

    manifest = create_search(
        target_count=2,
        mode="new",
        queue_path=queue,
        searches_dir=tmp_path / "searches",
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
        created_at_utc="2026-07-19T12:30:00Z",
    )

    assert [target["hip"] for target in manifest["targets"]] == ["HIP990000", "HIP990001"]
    assert manifest["candidate_catalog"]["candidate_count"] == 3
    assert manifest["candidate_catalog"]["viable_candidate_count"] == 3
    assert manifest["selection"]["projected_download_gb"] == 0.5
    loaded = load_search(tmp_path / "searches", manifest["search_id"])
    assert loaded["status"] == "pending"
    assert [event["event"] for event in loaded["events"]] == ["created"]


def test_create_search_refuses_partial_selection(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    _write_queue(queue, 1)

    with pytest.raises(SearchLifecycleError, match="no partial search was created"):
        create_search(
            target_count=2,
            mode="new",
            queue_path=queue,
            searches_dir=searches,
        )

    assert not searches.exists()


def test_create_large_search_writes_review_csv_but_json_is_system_of_record(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    review_dir = tmp_path / "review"
    _write_queue(queue, 101)

    manifest = create_search(
        target_count=101,
        mode="new",
        queue_path=queue,
        searches_dir=searches,
        manifest_dir=review_dir,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
    )

    assert (searches / manifest["search_id"] / "manifest.json").is_file()
    assert (review_dir / f"{manifest['search_id']}.csv").is_file()


def test_run_search_fails_closed_before_unapproved_acquisition(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    _write_queue(queue, 1)
    manifest = create_search(
        target_count=1,
        mode="new",
        queue_path=queue,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
    )

    with pytest.raises(SearchApprovalRequired, match="projected 0.250 GB"):
        run_search(
            searches_dir=searches,
            search_id=manifest["search_id"],
            stdout=StringIO(),
        )

    assert load_search(searches, manifest["search_id"])["status"] == "pending"


def test_load_search_rejects_manifest_tampering(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    _write_queue(queue, 1)
    manifest = create_search(
        target_count=1,
        mode="new",
        queue_path=queue,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
    )
    manifest_path = searches / manifest["search_id"] / "manifest.json"
    manifest_path.write_text(manifest_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(SearchLifecycleError, match="manifest hash"):
        load_search(searches, manifest["search_id"])


def test_run_search_refuses_changed_app_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    _write_queue(queue, 1)
    manifest = create_search(
        target_count=1,
        mode="new",
        queue_path=queue,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
    )
    monkeypatch.setattr(hunter_search_module, "__version__", "9.0.0")

    with pytest.raises(SearchLifecycleError, match="changed release logic"):
        run_search(
            searches_dir=searches,
            search_id=manifest["search_id"],
            stdout=StringIO(),
        )


def test_run_search_replays_manifest_and_appends_completion_history(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    history = tmp_path / "history.ndjson"
    _write_queue(queue, 1)
    manifest = create_search(
        target_count=1,
        mode="new",
        queue_path=queue,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
    )
    manifest_path = searches / manifest["search_id"] / "manifest.json"
    manifest_before = manifest_path.read_bytes()
    commands: list[list[str]] = []

    def command_runner(command: Any) -> int:
        commands.append(list(command))
        return 0

    def production_runner(**kwargs: Any) -> ProductionScanResult:
        run_id = str(kwargs["run_id"])
        run_dir = Path(kwargs["scans_dir"]) / run_id
        run_dir.mkdir(parents=True)
        (run_dir / f"{run_id}_target_status.json").write_text(
            json.dumps(
                {
                    "schema_version": PRODUCTION_TARGET_STATUS_SCHEMA_VERSION,
                    "run_id": run_id,
                    "entries": [
                        {
                            "target_name": "capture_HIP990000_0001",
                            "composite_score": 0.4,
                            "top_pathway": "known_object_annotation",
                            "source_data_path": "data/extended_corpus/HIP990000/capture.dat",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return ProductionScanResult(run_id, run_dir, 1, 0, 0, False)

    result = run_search(
        searches_dir=searches,
        search_id=manifest["search_id"],
        approve_acquisition=True,
        history_path=history,
        stdout=StringIO(),
        command_runner=command_runner,
        production_runner=production_runner,
    )

    assert result["event"] == "run_completed"
    assert manifest_path.read_bytes() == manifest_before
    assert str(manifest_path) in commands[0]
    assert "--results-dir" in commands[0]
    events = load_search(searches, manifest["search_id"])
    assert events["status"] == "completed"
    history_entry = json.loads(history.read_text(encoding="utf-8"))
    assert history_entry["parent_run_id"] == manifest["search_id"]


def test_failed_run_is_loud_and_resumable(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    _write_queue(queue, 1)
    manifest = create_search(
        target_count=1,
        mode="new",
        queue_path=queue,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
    )

    with pytest.raises(SearchLifecycleError, match="remains resumable"):
        run_search(
            searches_dir=searches,
            search_id=manifest["search_id"],
            approve_acquisition=True,
            stdout=StringIO(),
            command_runner=lambda _: 9,
        )

    loaded = load_search(searches, manifest["search_id"])
    assert loaded["status"] == "failed_resumable"
    assert loaded["events"][-1]["exit_code"] == 9


def test_run_rejects_incomplete_output_coverage_before_history_append(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    history = tmp_path / "history.ndjson"
    _write_queue(queue, 2)
    manifest = create_search(
        target_count=2,
        mode="new",
        queue_path=queue,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
    )

    def incomplete_production(**kwargs: Any) -> ProductionScanResult:
        run_id = str(kwargs["run_id"])
        run_dir = Path(kwargs["scans_dir"]) / run_id
        run_dir.mkdir(parents=True)
        (run_dir / f"{run_id}_target_status.json").write_text(
            json.dumps(
                {
                    "schema_version": PRODUCTION_TARGET_STATUS_SCHEMA_VERSION,
                    "run_id": run_id,
                    "entries": [
                        {
                            "target_name": "capture_HIP990000_0001",
                            "composite_score": 0.4,
                            "top_pathway": "known_object_annotation",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return ProductionScanResult(run_id, run_dir, 1, 0, 0, False)

    with pytest.raises(SearchLifecycleError, match="missing: HIP990001"):
        run_search(
            searches_dir=searches,
            search_id=manifest["search_id"],
            approve_acquisition=True,
            history_path=history,
            stdout=StringIO(),
            command_runner=lambda _: 0,
            production_runner=incomplete_production,
        )

    assert not history.exists()
    loaded = load_search(searches, manifest["search_id"])
    assert loaded["status"] == "failed_resumable"
    assert loaded["events"][-1]["stage"] == "composite_interpretation_and_provenance"


def test_follow_up_registry_resolves_identity_and_recommends_action(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    scans = tmp_path / "scans"
    _write_queue(queue, 1, status="already_acquired_local_cache")
    _write_follow_up_ledger(scans, "capture_HIP990000_0001", rfi=True)

    registry = follow_up_registry(scans_dirs=(scans,), queue_path=queue)

    assert registry["eligible_count"] == 1
    entry = registry["eligible_entries"][0]
    assert entry["hip"] == "HIP990000"
    assert entry["follow_up_priority"] == 0.45
    assert "cross-target RFI" in entry["recommended_next_action"]
    assert entry["prior_search_provenance"][0]["run_id"].startswith("RUN-")


def test_follow_up_registry_reads_legacy_v1_ledgers(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    scans = tmp_path / "scans"
    _write_queue(queue, 1, status="already_acquired_local_cache")
    _write_follow_up_ledger(
        scans,
        "capture_HIP990000_0001",
        schema_version="production_follow_ups_v1",
    )

    assert follow_up_registry(scans_dirs=(scans,), queue_path=queue)["eligible_count"] == 1


def test_follow_up_registry_carries_evidence_from_winning_priority(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    scans = tmp_path / "scans"
    _write_queue(queue, 1, status="already_acquired_local_cache")
    _write_follow_up_ledger(
        scans,
        "capture_HIP990000_0001",
        run_id="RUN-2026-07-19_120000Z-AAAA-prod-scan",
        score=0.5,
    )
    _write_follow_up_ledger(
        scans,
        "capture_HIP990000_0001",
        run_id="RUN-2026-07-19_130000Z-BBBB-prod-scan",
        score=0.9,
    )

    entry = follow_up_registry(scans_dirs=(scans,), queue_path=queue)[
        "eligible_entries"
    ][0]
    assert entry["follow_up_priority"] == 0.9
    assert entry["evidence"]["score"] == 0.9
    assert len(entry["prior_search_provenance"]) == 2


def test_required_cli_entrypoints_invoke_real_dispatch_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    scans = tmp_path / "scans"
    _write_queue(queue, 1)
    _write_follow_up_ledger(scans, "capture_HIP990000_0001")

    assert create_new_search(
        [
            "--targets",
            "1",
            "--mode",
            "new",
            "--candidate-catalog",
            str(queue),
            "--searches-dir",
            str(searches),
        ]
    ) == 0
    assert "Created pending new search" in capsys.readouterr().out
    assert create_new_search(
        [
            "--targets",
            "1",
            "--mode",
            "follow-up",
            "--candidate-catalog",
            str(queue),
            "--scans-dir",
            str(scans),
            "--searches-dir",
            str(tmp_path / "follow-up-searches"),
        ]
    ) == 0
    assert "| 0.900 |" in capsys.readouterr().out
    assert show_follow_ups(
        [
            "--candidate-catalog",
            str(queue),
            "--scans-dir",
            str(scans),
            "--searches-dir",
            str(searches),
        ]
    ) == 0
    assert "actionable follow-up target" in capsys.readouterr().out
