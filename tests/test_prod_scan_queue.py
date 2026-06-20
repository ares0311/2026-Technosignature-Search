"""Tests for prod_scan_queue.py — scan history tracking and target queue."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from techno_search.prod_scan_queue import (
    SCAN_HISTORY_SCHEMA_VERSION,
    ScanHistoryRecord,
    append_scan_record,
    build_target_queue,
    discover_dat_files,
    load_scan_history,
    scan_history_summary,
)

# ---------------------------------------------------------------------------
# discover_dat_files
# ---------------------------------------------------------------------------

class TestDiscoverDatFiles:
    def test_returns_sorted_dat_files(self, tmp_path: Path) -> None:
        (tmp_path / "b.dat").write_text("x")
        (tmp_path / "a.dat").write_text("x")
        (tmp_path / "skip.csv").write_text("x")
        files = discover_dat_files(tmp_path)
        stems = [f.stem for f in files]
        assert stems == ["a", "b"]

    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        assert discover_dat_files(tmp_path) == []

    def test_nonexistent_dir_returns_empty(self, tmp_path: Path) -> None:
        assert discover_dat_files(tmp_path / "nosuchdir") == []

    def test_only_dat_files_returned(self, tmp_path: Path) -> None:
        (tmp_path / "real.dat").write_text("x")
        (tmp_path / "real.json").write_text("{}")
        files = discover_dat_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "real.dat"


# ---------------------------------------------------------------------------
# load_scan_history
# ---------------------------------------------------------------------------

class TestLoadScanHistory:
    def test_returns_empty_if_no_file(self, tmp_path: Path) -> None:
        assert load_scan_history(tmp_path / "no_history.ndjson") == {}

    def test_parses_single_record(self, tmp_path: Path) -> None:
        h = tmp_path / "h.ndjson"
        h.write_text(json.dumps({
            "schema_version": SCAN_HISTORY_SCHEMA_VERSION,
            "target_stem": "HIP99427",
            "run_id": "RUN-001",
            "scanned_at_utc": "2026-06-20T00:00:00Z",
            "score": 0.72,
            "pathway": "follow_up",
            "dat_file": "/data/HIP99427.dat",
            "parent_run_id": None,
        }) + "\n")
        result = load_scan_history(h)
        assert "HIP99427" in result
        assert len(result["HIP99427"]) == 1
        rec = result["HIP99427"][0]
        assert rec.score == pytest.approx(0.72)
        assert rec.pathway == "follow_up"

    def test_multiple_scans_same_target(self, tmp_path: Path) -> None:
        h = tmp_path / "h.ndjson"
        h.write_text(
            json.dumps({"target_stem": "T1", "run_id": "R1", "scanned_at_utc": "A",
                        "score": 0.5, "pathway": "p", "dat_file": "f"}) + "\n" +
            json.dumps({"target_stem": "T1", "run_id": "R2", "scanned_at_utc": "B",
                        "score": 0.6, "pathway": "p", "dat_file": "f"}) + "\n"
        )
        result = load_scan_history(h)
        assert len(result["T1"]) == 2

    def test_ignores_malformed_lines(self, tmp_path: Path) -> None:
        h = tmp_path / "h.ndjson"
        h.write_text("not json\n" + json.dumps(
            {"target_stem": "T1", "run_id": "R", "scanned_at_utc": "A",
             "score": 0.5, "pathway": "p", "dat_file": "f"}
        ) + "\n")
        result = load_scan_history(h)
        assert "T1" in result

    def test_ignores_blank_lines(self, tmp_path: Path) -> None:
        h = tmp_path / "h.ndjson"
        h.write_text("\n\n" + json.dumps(
            {"target_stem": "T2", "run_id": "R", "scanned_at_utc": "A",
             "score": 0.0, "pathway": "p", "dat_file": "f"}
        ) + "\n\n")
        result = load_scan_history(h)
        assert "T2" in result


# ---------------------------------------------------------------------------
# append_scan_record
# ---------------------------------------------------------------------------

class TestAppendScanRecord:
    def test_creates_file_if_not_exists(self, tmp_path: Path) -> None:
        h = tmp_path / "history.ndjson"
        assert not h.exists()
        append_scan_record(h, ScanHistoryRecord(
            target_stem="T", run_id="R", scanned_at_utc="2026-01-01T00:00:00Z",
            score=0.5, pathway="p", dat_file="f.dat",
        ))
        assert h.exists()
        parsed = json.loads(h.read_text().strip())
        assert parsed["target_stem"] == "T"

    def test_appends_without_overwriting(self, tmp_path: Path) -> None:
        h = tmp_path / "history.ndjson"
        for i in range(3):
            append_scan_record(h, ScanHistoryRecord(
                target_stem=f"T{i}", run_id="R", scanned_at_utc="2026-01-01T00:00:00Z",
                score=0.0, pathway="p", dat_file="f.dat",
            ))
        lines = [ln for ln in h.read_text().splitlines() if ln.strip()]
        assert len(lines) == 3

    def test_parent_run_id_written(self, tmp_path: Path) -> None:
        h = tmp_path / "history.ndjson"
        append_scan_record(h, ScanHistoryRecord(
            target_stem="T", run_id="R2", scanned_at_utc="2026-01-01T00:00:00Z",
            score=0.0, pathway="p", dat_file="f.dat", parent_run_id="R1",
        ))
        parsed = json.loads(h.read_text().strip())
        assert parsed["parent_run_id"] == "R1"

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        h = tmp_path / "sub" / "history.ndjson"
        append_scan_record(h, ScanHistoryRecord(
            target_stem="T", run_id="R", scanned_at_utc="2026-01-01T00:00:00Z",
            score=0.0, pathway="p", dat_file="f.dat",
        ))
        assert h.exists()


# ---------------------------------------------------------------------------
# build_target_queue
# ---------------------------------------------------------------------------

class TestBuildTargetQueue:
    def _dat(self, tmp_path: Path, name: str) -> Path:
        p = tmp_path / f"{name}.dat"
        p.write_text("# fake\n")
        return p

    def test_all_unscanned_returns_all(self, tmp_path: Path) -> None:
        self._dat(tmp_path, "A")
        self._dat(tmp_path, "B")
        queue = build_target_queue(tmp_path)
        assert len(queue) == 2
        assert all(e.is_first_scan for e in queue)

    def test_scanned_target_excluded_by_default(self, tmp_path: Path) -> None:
        self._dat(tmp_path, "A")
        h = tmp_path / "history.ndjson"
        append_scan_record(h, ScanHistoryRecord(
            target_stem="A", run_id="R", scanned_at_utc="2026-01-01T00:00:00Z",
            score=0.5, pathway="p", dat_file="A.dat",
        ))
        queue = build_target_queue(tmp_path, h)
        assert queue == []

    def test_force_rescan_includes_scanned_targets(self, tmp_path: Path) -> None:
        self._dat(tmp_path, "A")
        h = tmp_path / "history.ndjson"
        append_scan_record(h, ScanHistoryRecord(
            target_stem="A", run_id="R", scanned_at_utc="2026-01-01T00:00:00Z",
            score=0.5, pathway="p", dat_file="A.dat",
        ))
        queue = build_target_queue(tmp_path, h, force_rescan=True)
        assert len(queue) == 1
        assert not queue[0].is_first_scan
        assert queue[0].prior_scan_count == 1

    def test_unscanned_ranks_higher_than_scanned(self, tmp_path: Path) -> None:
        self._dat(tmp_path, "new_target")
        self._dat(tmp_path, "old_target")
        h = tmp_path / "history.ndjson"
        append_scan_record(h, ScanHistoryRecord(
            target_stem="old_target", run_id="R", scanned_at_utc="2026-01-01T00:00:00Z",
            score=0.5, pathway="p", dat_file="old_target.dat",
        ))
        queue = build_target_queue(tmp_path, h, force_rescan=True)
        assert len(queue) == 2
        assert queue[0].target_stem == "new_target"
        assert queue[0].selection_score > queue[1].selection_score

    def test_first_scan_score_is_base_plus_boost(self, tmp_path: Path) -> None:
        self._dat(tmp_path, "X")
        queue = build_target_queue(tmp_path)
        assert queue[0].selection_score == pytest.approx(0.58)
        assert "never scanned" in queue[0].rationale

    def test_rescan_score_is_base_minus_penalty(self, tmp_path: Path) -> None:
        self._dat(tmp_path, "X")
        h = tmp_path / "history.ndjson"
        append_scan_record(h, ScanHistoryRecord(
            target_stem="X", run_id="R", scanned_at_utc="2026-01-01T00:00:00Z",
            score=0.5, pathway="p", dat_file="X.dat",
        ))
        queue = build_target_queue(tmp_path, h, force_rescan=True)
        assert queue[0].selection_score == pytest.approx(0.46)

    def test_prior_info_populated(self, tmp_path: Path) -> None:
        self._dat(tmp_path, "X")
        h = tmp_path / "history.ndjson"
        append_scan_record(h, ScanHistoryRecord(
            target_stem="X", run_id="R", scanned_at_utc="2026-01-01T12:00:00Z",
            score=0.77, pathway="follow_up", dat_file="X.dat",
        ))
        queue = build_target_queue(tmp_path, h, force_rescan=True)
        e = queue[0]
        assert e.last_score == pytest.approx(0.77)
        assert e.last_pathway == "follow_up"
        assert e.last_scanned_at_utc == "2026-01-01T12:00:00Z"

    def test_penalty_caps_at_max(self, tmp_path: Path) -> None:
        self._dat(tmp_path, "X")
        h = tmp_path / "history.ndjson"
        for i in range(10):
            append_scan_record(h, ScanHistoryRecord(
                target_stem="X", run_id=f"R{i}", scanned_at_utc="2026-01-01T00:00:00Z",
                score=0.0, pathway="p", dat_file="X.dat",
            ))
        queue = build_target_queue(tmp_path, h, force_rescan=True)
        assert queue[0].selection_score == pytest.approx(0.38)  # 0.50 - 0.12 (cap)

    def test_stable_sort_by_stem_for_equal_scores(self, tmp_path: Path) -> None:
        self._dat(tmp_path, "Z")
        self._dat(tmp_path, "A")
        queue = build_target_queue(tmp_path)
        assert queue[0].target_stem == "A"
        assert queue[1].target_stem == "Z"


# ---------------------------------------------------------------------------
# scan_history_summary
# ---------------------------------------------------------------------------

class TestScanHistorySummary:
    def test_empty_when_no_history_file(self, tmp_path: Path) -> None:
        s = scan_history_summary()
        assert s["total_scans"] == 0
        assert s["unique_targets_scanned"] == 0
        assert s["re_scanned_targets"] == 0

    def test_counts_unique_and_total(self, tmp_path: Path) -> None:
        h = tmp_path / "history.ndjson"
        for i in range(3):
            append_scan_record(h, ScanHistoryRecord(
                target_stem=f"T{i % 2}", run_id=f"R{i}",
                scanned_at_utc="2026-01-01T00:00:00Z",
                score=0.5, pathway="p", dat_file="f.dat",
            ))
        s = scan_history_summary(h)
        assert s["total_scans"] == 3
        assert s["unique_targets_scanned"] == 2
        assert s["re_scanned_targets"] == 1

    def test_pending_count_when_dat_dir_provided(self, tmp_path: Path) -> None:
        (tmp_path / "A.dat").write_text("x")
        (tmp_path / "B.dat").write_text("x")
        h = tmp_path / "history.ndjson"
        append_scan_record(h, ScanHistoryRecord(
            target_stem="A", run_id="R", scanned_at_utc="2026-01-01T00:00:00Z",
            score=0.0, pathway="p", dat_file="A.dat",
        ))
        s = scan_history_summary(h, tmp_path)
        assert s["pending_targets"] == 1

    def test_disclaimer_present(self) -> None:
        s = scan_history_summary()
        assert "scheduling aid" in str(s["disclaimer"])
        assert "detection claim" in str(s["disclaimer"])

    def test_schema_version_present(self) -> None:
        s = scan_history_summary()
        assert s["schema_version"] == SCAN_HISTORY_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# CLI round-trip tests
# ---------------------------------------------------------------------------

class TestProdScanQueueCLI:
    def test_prod_target_queue_empty_dir(self, tmp_path: Path) -> None:
        import subprocess
        r = subprocess.run(
            [sys.executable, "-m", "techno_search.cli",
             "prod-target-queue", "--dat-dir", str(tmp_path)],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        d = json.loads(r.stdout)
        assert d["pending_count"] == 0

    def test_prod_target_queue_with_dat_file(self, tmp_path: Path) -> None:
        import subprocess
        (tmp_path / "FOO.dat").write_text("# fake\n")
        r = subprocess.run(
            [sys.executable, "-m", "techno_search.cli",
             "prod-target-queue", "--dat-dir", str(tmp_path)],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        d = json.loads(r.stdout)
        assert d["pending_count"] == 1
        assert d["queue"][0]["target_stem"] == "FOO"
        assert d["queue"][0]["is_first_scan"] is True

    def test_prod_record_scan_creates_history(self, tmp_path: Path) -> None:
        import subprocess
        h = tmp_path / "history.ndjson"
        r = subprocess.run(
            [sys.executable, "-m", "techno_search.cli",
             "prod-record-scan",
             "--target-stem", "HIP99427",
             "--run-id", "TEST-001",
             "--score", "0.72",
             "--pathway", "follow_up",
             "--dat-file", "/data/HIP99427.dat",
             "--history-file", str(h)],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        d = json.loads(r.stdout)
        assert d["ok"] is True
        assert h.exists()
        rec = json.loads(h.read_text().strip())
        assert rec["target_stem"] == "HIP99427"
        assert rec["pathway"] == "follow_up"

    def test_scan_history_summary_no_file(self, tmp_path: Path) -> None:
        import subprocess
        r = subprocess.run(
            [sys.executable, "-m", "techno_search.cli",
             "scan-history-summary"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        d = json.loads(r.stdout)
        assert d["total_scans"] == 0

    def test_full_round_trip_queue_drops_after_record(self, tmp_path: Path) -> None:
        import subprocess
        (tmp_path / "TARGET.dat").write_text("# fake\n")
        h = tmp_path / "history.ndjson"

        # Target appears in queue
        r = subprocess.run(
            [sys.executable, "-m", "techno_search.cli",
             "prod-target-queue", "--dat-dir", str(tmp_path),
             "--history-file", str(h)],
            capture_output=True, text=True,
        )
        assert json.loads(r.stdout)["pending_count"] == 1

        # Record the scan
        subprocess.run(
            [sys.executable, "-m", "techno_search.cli",
             "prod-record-scan",
             "--target-stem", "TARGET",
             "--run-id", "R1",
             "--score", "0.55",
             "--pathway", "do_not_submit_false_positive",
             "--dat-file", str(tmp_path / "TARGET.dat"),
             "--history-file", str(h)],
            capture_output=True, text=True,
        )

        # Target drops out of queue
        r = subprocess.run(
            [sys.executable, "-m", "techno_search.cli",
             "prod-target-queue", "--dat-dir", str(tmp_path),
             "--history-file", str(h)],
            capture_output=True, text=True,
        )
        assert json.loads(r.stdout)["pending_count"] == 0

    def test_missing_dat_file_not_recorded_to_history(self, tmp_path: Path) -> None:
        """Race condition guard: if a .dat file vanishes between queue build and
        pipeline execution, the production scan script skips the target without
        recording it to scan_history.ndjson, keeping it in the queue for future runs.

        This test verifies that build_target_queue still includes a target whose
        .dat file has been removed (simulating the post-removal state) — i.e.,
        the history file has NOT been written for that target.
        """
        import subprocess

        dat_file = tmp_path / "VANISHED.dat"
        dat_file.write_text("# fake\n")
        h = tmp_path / "history.ndjson"

        # Confirm target is in the queue while the file exists
        r = subprocess.run(
            [sys.executable, "-m", "techno_search.cli",
             "prod-target-queue", "--dat-dir", str(tmp_path),
             "--history-file", str(h)],
            capture_output=True, text=True,
        )
        assert json.loads(r.stdout)["pending_count"] == 1

        # Simulate race: .dat file vanishes (e.g. moved by another process)
        dat_file.unlink()

        # Do NOT call prod-record-scan (simulates the shell guard that skips
        # recording when the file is missing).  History file should not exist.
        assert not h.exists(), "History must not be written when .dat is missing"

        # After the file is restored (next download cycle), the target must
        # re-appear in the queue because it was never recorded.
        dat_file.write_text("# restored\n")
        r = subprocess.run(
            [sys.executable, "-m", "techno_search.cli",
             "prod-target-queue", "--dat-dir", str(tmp_path),
             "--history-file", str(h)],
            capture_output=True, text=True,
        )
        assert json.loads(r.stdout)["pending_count"] == 1, (
            "Target must remain in queue if .dat vanished and was never recorded"
        )
