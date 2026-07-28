from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any

import pytest

import techno_search.hunter_search as hunter_search_module
from techno_search.hunter_cli import create_new_search, run_new_search, show_follow_ups
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


def _write_queue(
    path: Path,
    count: int,
    *,
    status: str = "raw_download_approval_required",
    include_source_url: bool = True,
) -> None:
    _write_queue_with_statuses(
        path, [status] * count, include_source_url=include_source_url
    )


def _write_queue_with_statuses(
    path: Path,
    statuses: list[str],
    *,
    include_source_url: bool = True,
    target_id_fn: Callable[[int], str] | None = None,
) -> None:
    resolve_target_id = target_id_fn or (lambda index: f"HIP{990000 + index}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TARGET_PRIORITY_QUEUE_FIELDS)
        writer.writeheader()
        for index, status in enumerate(statuses):
            target_id = resolve_target_id(index)
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
                    "source_hdf5_url": (
                        f"https://example.test/{target_id}.h5"
                        if include_source_url
                        else ""
                    ),
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
    source_data_path: str = "",
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
                        "source_data_path": source_data_path,
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
    assert manifest["candidate_catalog"]["candidate_count"] == 12086
    assert manifest["candidate_catalog"]["identity_resolved_count"] == 1184
    assert manifest["eligibility_queue"]["candidate_count"] == 3
    assert manifest["eligibility_queue"]["viable_candidate_count"] == 3
    assert manifest["selection"]["projected_download_gb"] == 0.5
    assert manifest["selection"]["execution_kind_counts"] == {
        "novel_target_archive_processing": 2
    }
    loaded = load_search(tmp_path / "searches", manifest["search_id"])
    assert loaded["status"] == "pending"
    assert [event["event"] for event in loaded["events"]] == ["created"]


def test_create_search_applies_optional_scientific_constraints(tmp_path: Path) -> None:
    queue = tmp_path / "queue.csv"
    _write_queue_with_statuses(
        queue,
        ["raw_download_approval_required"] * 3,
        target_id_fn=lambda index: ("TIC100", "HIP200", "TIC300")[index],
    )

    manifest = create_search(
        target_count=2,
        mode="new",
        queue_path=queue,
        searches_dir=tmp_path / "searches",
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
        constraints={
            "target_prefixes": ("TIC",),
            "min_dec_deg": -1,
            "max_dec_deg": 0,
            "max_estimated_download_gb": 0.5,
        },
    )

    assert [target["hip"] for target in manifest["targets"]] == ["TIC100"]
    assert manifest["selection"]["constraints"]["target_prefixes"] == ["TIC"]
    assert manifest["selection"]["shortfall"]["returned_count"] == 1


def test_create_search_returns_best_available_n_with_shortfall_report(
    tmp_path: Path,
) -> None:
    """A normal top-N request must not fail outright short of the requested count.

    Per the Hunter business contract, rank and absolute quality are distinct: the
    search must freeze the best available N and report the shortfall, not raise.
    """
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    _write_queue(queue, 1)

    manifest = create_search(
        target_count=2,
        mode="new",
        queue_path=queue,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
        created_at_utc="2026-07-19T12:30:00Z",
    )

    assert [target["hip"] for target in manifest["targets"]] == ["HIP990000"]
    assert manifest["selection"]["selected_count"] == 1
    assert manifest["selection"]["requested_count"] == 2
    assert manifest["selection"]["partial_selection_allowed"] is True
    shortfall = manifest["selection"]["shortfall"]
    assert shortfall["requested_count"] == 2
    assert shortfall["returned_count"] == 1
    assert shortfall["shortfall_count"] == 1
    assert shortfall["expansion_headroom_count"] == 0
    assert "1 of 2 requested new targets" in shortfall["reason"]
    assert (searches / manifest["search_id"] / "manifest.json").is_file()


def test_zero_valid_candidates_returns_durable_completed_empty_search(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    _write_queue(queue, 1, status="metadata_discovery_required")
    manifest = create_search(
        target_count=2,
        mode="new",
        queue_path=queue,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
        adaptive_discovery=lambda path, _count, _search_id, _constraints: (
            path,
            {
                "sufficient": True,
                "universe_exhausted": True,
                "round_count": 0,
            },
        ),
    )

    assert manifest["targets"] == []
    assert manifest["selection"]["shortfall"]["returned_count"] == 0
    result = run_search(
        searches_dir=searches,
        search_id=manifest["search_id"],
        stdout=StringIO(),
        command_runner=lambda _command: (_ for _ in ()).throw(AssertionError()),
    )
    assert result["no_valid_targets"] is True
    assert load_search(searches, manifest["search_id"])["status"] == "completed"


def test_create_search_shortfall_reports_real_expansion_headroom(
    tmp_path: Path,
) -> None:
    """Rows awaiting discovery/preflight are real, reportable expansion headroom."""
    queue = tmp_path / "queue.csv"
    _write_queue_with_statuses(
        queue,
        ["raw_download_approval_required"]
        + ["metadata_discovery_required"] * 3
        + ["queued_metadata_discovery"] * 2,
    )

    manifest = create_search(
        target_count=5,
        mode="new",
        queue_path=queue,
        searches_dir=tmp_path / "searches",
    )

    shortfall = manifest["selection"]["shortfall"]
    assert shortfall["returned_count"] == 1
    assert shortfall["shortfall_count"] == 4
    assert shortfall["expansion_headroom_count"] == 2


def test_create_follow_up_search_returns_best_available_n_with_shortfall_report(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "queue.csv"
    scans = tmp_path / "scans"
    _write_queue(queue, 1, status="already_acquired_local_cache", include_source_url=False)
    _write_follow_up_ledger(scans, "capture_HIP990000_0001")

    manifest = create_search(
        target_count=3,
        mode="follow-up",
        queue_path=queue,
        scans_dir=scans,
        searches_dir=tmp_path / "searches",
    )

    assert manifest["selection"]["selected_count"] == 1
    shortfall = manifest["selection"]["shortfall"]
    assert shortfall["requested_count"] == 3
    assert shortfall["returned_count"] == 1
    assert shortfall["shortfall_count"] == 2
    assert shortfall["expansion_headroom_count"] is None
    assert "1 of 3 requested follow-up targets" in shortfall["reason"]


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


def test_load_search_preserves_read_access_to_v1_history(tmp_path: Path) -> None:
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
    search_dir = searches / manifest["search_id"]
    manifest_path = search_dir / "manifest.json"
    legacy_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    legacy_manifest["schema_version"] = "hunter_search_manifest_v1"
    manifest_path.write_text(
        json.dumps(legacy_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    events_path = search_dir / "events.ndjson"
    event = json.loads(events_path.read_text(encoding="utf-8"))
    event["schema_version"] = "hunter_search_event_v1"
    event["manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    events_path.write_text(json.dumps(event, sort_keys=True) + "\n", encoding="utf-8")

    loaded = load_search(searches, manifest["search_id"])

    assert loaded["status"] == "pending"
    assert loaded["manifest"]["schema_version"] == "hunter_search_manifest_v1"


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


def test_run_search_completes_for_non_hip_named_target(tmp_path: Path) -> None:
    """Real live discovery expansion surfaces non-HIP target IDs (e.g. TESS
    TIC-named rows -- 44 already exist in the real production queue), and a
    HIP-only canonicalization pattern silently could never match them,
    durably failing run_search's history-append stage after real
    acquisition/processing had already succeeded. Target-name matching must
    work for any real target-naming scheme, not just HIP<digits>.
    """
    queue = tmp_path / "queue.csv"
    searches = tmp_path / "searches"
    history = tmp_path / "history.ndjson"
    _write_queue_with_statuses(
        queue,
        ["raw_download_approval_required"],
        target_id_fn=lambda _index: "TIC281731203",
    )
    manifest = create_search(
        target_count=1,
        mode="new",
        queue_path=queue,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
    )
    assert manifest["targets"][0]["hip"] == "TIC281731203"

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
                            "target_name": "capture_TIC281731203_0001",
                            "composite_score": 0.4,
                            "top_pathway": "known_object_annotation",
                            "source_data_path": (
                                "data/extended_corpus/TIC281731203/capture.dat"
                            ),
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
        command_runner=lambda _command: 0,
        production_runner=production_runner,
    )

    assert result["event"] == "run_completed"
    events = load_search(searches, manifest["search_id"])
    assert events["status"] == "completed"


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


def test_run_search_resume_reuses_run_id_and_appends_history_once(
    tmp_path: Path,
) -> None:
    """The HUNTER PROD DIRECTIVE requires verifying restart/resume does not
    corrupt or lose state. ``run_resumed`` had zero test coverage before this
    -- this exercises a real failure followed by a real successful resume of
    the *same* search and confirms the run_id stays stable across the
    failure/resume boundary and history is appended exactly once, not
    duplicated.
    """
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
    attempts = {"count": 0}

    def production_runner(**kwargs: Any) -> ProductionScanResult:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("simulated transient failure")
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

    with pytest.raises(RuntimeError, match="simulated transient failure"):
        run_search(
            searches_dir=searches,
            search_id=manifest["search_id"],
            approve_acquisition=True,
            history_path=history,
            stdout=StringIO(),
            command_runner=lambda _command: 0,
            production_runner=production_runner,
        )
    failed_run_id = load_search(searches, manifest["search_id"])["events"][-1]["run_id"]

    result = run_search(
        searches_dir=searches,
        search_id=manifest["search_id"],
        approve_acquisition=True,
        history_path=history,
        stdout=StringIO(),
        command_runner=lambda _command: 0,
        production_runner=production_runner,
    )

    assert result["run_id"] == failed_run_id
    loaded = load_search(searches, manifest["search_id"])
    assert loaded["status"] == "completed"
    assert [event["event"] for event in loaded["events"]] == [
        "created",
        "run_started",
        "run_failed",
        "run_resumed",
        "run_completed",
    ]
    assert loaded["events"][3]["run_id"] == failed_run_id
    history_lines = history.read_text(encoding="utf-8").strip().splitlines()
    assert len(history_lines) == 1


def test_run_search_refuses_to_rerun_a_completed_search(tmp_path: Path) -> None:
    """A completed search must never be silently re-executed -- that would
    risk duplicated history/follow-up records or overwriting a durable
    result. Part of the same restart/resume-safety business validation as
    test_run_search_resume_reuses_run_id_and_appends_history_once.
    """
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

    run_search(
        searches_dir=searches,
        search_id=manifest["search_id"],
        approve_acquisition=True,
        history_path=history,
        stdout=StringIO(),
        command_runner=lambda _command: 0,
        production_runner=production_runner,
    )

    with pytest.raises(SearchLifecycleError, match="already complete"):
        run_search(
            searches_dir=searches,
            search_id=manifest["search_id"],
            approve_acquisition=True,
            history_path=history,
            stdout=StringIO(),
            command_runner=lambda _command: 0,
            production_runner=production_runner,
        )

    history_lines = history.read_text(encoding="utf-8").strip().splitlines()
    assert len(history_lines) == 1


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
    _write_follow_up_ledger(
        scans,
        "capture_HIP990000_0001",
        rfi=True,
        source_data_path="/data/cadence_HIP990000.csv",
    )

    registry = follow_up_registry(scans_dirs=(scans,), queue_path=queue)

    assert registry["eligible_count"] == 1
    entry = registry["eligible_entries"][0]
    assert entry["hip"] == "HIP990000"
    assert entry["follow_up_priority"] == 0.45
    assert entry["source_data_path"] == "/data/cadence_HIP990000.csv"
    assert "cross-target RFI" in entry["recommended_next_action"]
    assert entry["prior_search_provenance"][0]["run_id"].startswith("RUN-")


def test_follow_up_registry_resolves_non_hip_named_target_identity(
    tmp_path: Path,
) -> None:
    """Same non-HIP gap as test_run_search_completes_for_non_hip_named_target,
    but for follow-up matching: a HIP-only pattern would silently count a
    real TIC-named follow-up ledger entry as unresolved identity forever.
    """
    queue = tmp_path / "queue.csv"
    scans = tmp_path / "scans"
    _write_queue_with_statuses(
        queue,
        ["already_acquired_local_cache"],
        target_id_fn=lambda _index: "TIC281731203",
    )
    _write_follow_up_ledger(
        scans,
        "capture_TIC281731203_0001",
        rfi=True,
        source_data_path="/data/cadence_TIC281731203.csv",
    )

    registry = follow_up_registry(scans_dirs=(scans,), queue_path=queue)

    assert registry["unresolved_identity_count"] == 0
    assert registry["eligible_count"] == 1
    entry = registry["eligible_entries"][0]
    assert entry["hip"] == "TIC281731203"
    assert entry["source_data_path"] == "/data/cadence_TIC281731203.csv"


def test_follow_up_search_marks_existing_data_as_reanalysis_not_new_observation(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "queue.csv"
    scans = tmp_path / "scans"
    _write_queue(
        queue,
        1,
        status="already_acquired_local_cache",
        include_source_url=False,
    )
    _write_follow_up_ledger(scans, "capture_HIP990000_0001")

    manifest = create_search(
        target_count=1,
        mode="follow-up",
        queue_path=queue,
        scans_dir=scans,
        searches_dir=tmp_path / "searches",
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
    )

    assert manifest["targets"][0]["execution_kind"] == "existing_data_reanalysis"
    assert manifest["targets"][0]["follow_up_observation_fulfilled"] is False
    assert manifest["selection"]["execution_kind_counts"] == {
        "existing_data_reanalysis": 1
    }
    assert manifest["selection"]["follow_up_observation_fulfilled_count"] == 0


def test_follow_up_lifecycle_schedules_then_defers_unfulfilled_evidence(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "queue.csv"
    scans = tmp_path / "scans"
    searches = tmp_path / "searches"
    history = tmp_path / "history.ndjson"
    _write_queue(
        queue,
        1,
        status="already_acquired_local_cache",
        include_source_url=False,
    )
    _write_follow_up_ledger(scans, "capture_HIP990000_0001")
    manifest = create_search(
        target_count=1,
        mode="follow-up",
        queue_path=queue,
        scans_dir=scans,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
    )

    scheduled = follow_up_registry(
        scans_dirs=(scans, searches), queue_path=queue
    )
    assert scheduled["eligible_count"] == 0
    assert scheduled["scheduled_count"] == 1

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
                            "source_data_path": "data/HIP990000/capture.dat",
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
        history_path=history,
        stdout=StringIO(),
        command_runner=lambda _command: 0,
        production_runner=production_runner,
    )

    assert result["follow_up_completed_count"] == 0
    assert result["follow_up_deferred_count"] == 1
    assert result["follow_up_dispositions"][0]["state"] == "deferred"
    assert "later-epoch cadence" in result["follow_up_dispositions"][0]["reason"]
    deferred = follow_up_registry(
        scans_dirs=(scans, searches), queue_path=queue
    )
    assert deferred["eligible_count"] == 0
    assert deferred["deferred_count"] == 1


def test_stale_pending_search_cannot_suppress_current_follow_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = tmp_path / "queue.csv"
    scans = tmp_path / "scans"
    searches = tmp_path / "searches"
    _write_queue(
        queue,
        1,
        status="already_acquired_local_cache",
        include_source_url=False,
    )
    _write_follow_up_ledger(scans, "capture_HIP990000_0001")
    create_search(
        target_count=1,
        mode="follow-up",
        queue_path=queue,
        scans_dir=scans,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
    )
    monkeypatch.setattr(hunter_search_module, "__version__", "9.9.9")

    registry = follow_up_registry(
        scans_dirs=(scans, searches), queue_path=queue
    )

    assert registry["eligible_count"] == 1
    assert registry["eligible_entries"][0]["hip"] == "HIP990000"
    assert registry["scheduled_count"] == 0
    assert registry["refresh_required_count"] == 1


def test_follow_up_lifecycle_completes_only_after_verified_later_epoch_cadence(
    tmp_path: Path,
) -> None:
    queue = tmp_path / "queue.csv"
    scans = tmp_path / "scans"
    searches = tmp_path / "searches"
    history = tmp_path / "history.ndjson"
    output = tmp_path / "GBT_HIP990000_2017-05-12_ABACAD.csv"
    _write_queue(
        queue,
        1,
        status="already_acquired_local_cache",
        include_source_url=False,
    )
    _write_follow_up_ledger(scans, "capture_HIP990000_0001")
    scan_filenames = [
        (
            "spliced_blc3031323334353637_guppi_57885_"
            f"{30000 + index * 300}_HIP990000_{index:04d}.gpuspec.0002.h5"
        )
        for index in range(2, 8)
    ]

    def discover(
        targets: list[dict[str, Any]], target_count: int
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        assert target_count == 1
        target = dict(targets[0])
        target.update(
            {
                "source_hdf5_url": "",
                "source_data_path": str(output),
                "estimated_download_gb": 1.44,
                "follow_up_cadence": {
                    "schema_version": "hunter_follow_up_cadence_v1",
                    "cadence_id": "GBT_HIP990000_2017-05-12_ABACAD",
                    "target_name": "HIP990000",
                    "instrument": "Green Bank Telescope",
                    "receiver": "L band",
                    "source_archive": "Breakthrough Listen Open Data Archive",
                    "archive_search_url": "https://example.test/search",
                    "data_use_url": "https://example.test/data-use",
                    "data_license": "CC BY 4.0",
                    "validity_state": "valid",
                    "prior_observation_max_mjd": 57752.98,
                    "follow_up_observation_min_mjd": 57885.35,
                    "later_epoch_days": 132.37,
                    "human_approval_status": "pending",
                    "approved_for_local_real_data": False,
                    "external_submission_authorized": False,
                    "analysis": {
                        "max_drift_hz_per_sec": 10.0,
                        "min_drift_hz_per_sec": 0.0001,
                        "snr_threshold": 10.0,
                    },
                    "scans": [
                        {
                            "sequence_index": index,
                            "scan_role": "on" if index % 2 else "off",
                            "source_name": "HIP990000",
                            "utc_start": "2017-05-12T00:00:00Z",
                            "mjd": 57885.35 + index / 1000,
                            "filename": filename,
                            "size_bytes": 240_000_000,
                            "md5": f"{index:032x}",
                            "url": f"https://example.test/{filename}",
                        }
                        for index, filename in enumerate(scan_filenames, 1)
                    ],
                },
            }
        )
        return [target], {"schema_version": "hunter_follow_up_discovery_report_v2"}

    manifest = create_search(
        target_count=1,
        mode="follow-up",
        queue_path=queue,
        scans_dir=scans,
        searches_dir=searches,
        search_id="SEARCH-20260719T123000Z-A1B2C3D4",
        follow_up_discovery=discover,
    )
    assert manifest["targets"][0]["follow_up_observation_scheduled"] is True
    assert manifest["targets"][0]["follow_up_observation_fulfilled"] is False

    commands: list[list[str]] = []
    cadence_attempts = 0

    def command_runner(command: list[str]) -> int:
        nonlocal cadence_attempts
        commands.append(command)
        if any(item.endswith("ingest_gbt_cadence.py") for item in command):
            cadence_attempts += 1
            if cadence_attempts == 1:
                return 7
            output.write_text("Corrected_Frequency,SNR\n", encoding="utf-8")
            output.with_name(output.name + ".provenance.json").write_text(
                json.dumps(
                    {
                        "classification": "derived_real_observation_cadence",
                        "cadence_id": "GBT_HIP990000_2017-05-12_ABACAD",
                        "target_id": "HIP990000",
                        "scan_count": 6,
                        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                        "source_artifacts": [
                            {
                                "artifact_filename": (
                                    filename.removesuffix(".h5") + ".dat"
                                )
                            }
                            for filename in scan_filenames
                        ],
                    }
                ),
                encoding="utf-8",
            )
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
                            "source_data_path": str(output),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return ProductionScanResult(run_id, run_dir, 1, 0, 0, False)

    with pytest.raises(
        SearchLifecycleError,
        match="cadence acquisition/processing failed with exit code 7",
    ):
        run_search(
            searches_dir=searches,
            search_id=manifest["search_id"],
            approve_acquisition=True,
            history_path=history,
            stdout=StringIO(),
            command_runner=command_runner,
            production_runner=production_runner,
        )
    failed = load_search(searches, manifest["search_id"])
    assert failed["status"] == "failed_resumable"
    assert failed["events"][-1]["stage"] == (
        "follow_up_cadence_acquisition_preprocessing"
    )
    execution_manifest = next(
        (searches / manifest["search_id"] / "execution_inputs").glob("*.json")
    )
    frozen_execution_manifest = execution_manifest.read_bytes()

    result = run_search(
        searches_dir=searches,
        search_id=manifest["search_id"],
        approve_acquisition=True,
        history_path=history,
        stdout=StringIO(),
        command_runner=command_runner,
        production_runner=production_runner,
    )

    assert execution_manifest.read_bytes() == frozen_execution_manifest
    assert len(commands) == 3
    assert any(item.endswith("ingest_gbt_cadence.py") for item in commands[0])
    assert any(item.endswith("ingest_gbt_cadence.py") for item in commands[1])
    assert any(
        item.endswith("run_stream_process_evict_batch.sh") for item in commands[2]
    )
    assert result["follow_up_completed_count"] == 1
    assert result["follow_up_dispositions"][0]["state"] == "completed"
    assert "verified six-scan later-epoch cadence" in result[
        "follow_up_dispositions"
    ][0]["reason"]
    completed = follow_up_registry(
        scans_dirs=(scans, searches), queue_path=queue
    )
    assert completed["completed_count"] == 1
    assert completed["eligible_count"] == 0


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
            "--priority-queue",
            str(queue),
            "--searches-dir",
            str(searches),
        ]
    ) == 0
    new_search_output = capsys.readouterr().out
    assert "Created pending new search" in new_search_output
    assert (
        "Type | Distance ly | Spectral | Exoplanet | Prior searches | Prior provenance"
        in new_search_output
    )
    monkeypatch.setattr(
        "techno_search.hunter_cli.discover_follow_up_targets",
        lambda targets, *, target_count: (
            [dict(target) for target in targets[:target_count]],
            {
                "schema_version": "hunter_follow_up_discovery_report_v2",
                "cadence_discovery_count": 0,
            },
        ),
    )
    assert create_new_search(
        [
            "--targets",
            "1",
            "--mode",
            "follow-up",
            "--priority-queue",
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
            "--priority-queue",
            str(queue),
            "--scans-dir",
            str(scans),
            "--searches-dir",
            str(searches),
        ]
    ) == 0
    assert "actionable follow-up target" in capsys.readouterr().out


def test_run_new_search_json_output_is_not_polluted_by_pipeline_progress(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_search(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["command_runner"] is not None
        kwargs["stdout"].write("pipeline progress that must stay out of JSON\n")
        return {
            "event": "run_completed",
            "search_id": "SEARCH-TEST",
            "run_id": "RUN-TEST",
            "target_count": 1,
            "follow_up_required_count": 0,
        }

    monkeypatch.setattr("techno_search.hunter_cli.run_search", fake_run_search)

    assert run_new_search(["--search-id", "SEARCH-TEST", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["event"] == "run_completed"


def test_cli_prints_visible_shortfall_line_when_returning_fewer_than_requested(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    queue = tmp_path / "queue.csv"
    _write_queue(queue, 1)

    assert create_new_search(
        [
            "--targets",
            "5",
            "--mode",
            "new",
            "--priority-queue",
            str(queue),
            "--searches-dir",
            str(tmp_path / "searches"),
        ]
    ) == 0
    out = capsys.readouterr().out
    assert "SHORTFALL: returned 1 of 5 requested target(s)" in out
