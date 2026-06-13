"""Tests for data release snapshot and cross-release reproducibility verification."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from techno_search.data_release_snapshot import (
    DATA_RELEASE_SNAPSHOT_SCHEMA_VERSION,
    _pathway_assignment_hash,
    compare_snapshots,
    data_release_snapshot_summary,
    load_data_release_snapshots,
    snapshot_from_batch_manifest,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "data_release_snapshots.json"
)

_REVIEW = "candidate_review_packet"
_FP = "do_not_submit_false_positive"


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------


class TestLoadDataReleaseSnapshots:
    def test_loads_at_least_one_snapshot(self) -> None:
        snapshots = load_data_release_snapshots()
        assert len(snapshots) >= 1

    def test_loads_three_synthetic_snapshots(self) -> None:
        snapshots = load_data_release_snapshots()
        assert len(snapshots) == 3

    def test_snapshot_ids_are_unique(self) -> None:
        snapshots = load_data_release_snapshots()
        ids = [s["snapshot_id"] for s in snapshots]
        assert len(ids) == len(set(ids))

    def test_each_snapshot_has_required_fields(self) -> None:
        snapshots = load_data_release_snapshots()
        required = {
            "schema_version",
            "disclaimer",
            "snapshot_id",
            "data_release_label",
            "pipeline_version",
            "candidate_count",
            "pathway_distribution",
            "per_candidate",
            "pathway_assignment_hash",
        }
        for snap in snapshots:
            assert required <= set(snap.keys()), snap["snapshot_id"]

    def test_per_candidate_has_required_fields(self) -> None:
        snapshots = load_data_release_snapshots()
        for snap in snapshots:
            for entry in snap["per_candidate"]:
                assert "candidate_id" in entry
                assert "track" in entry
                assert "recommended_pathway" in entry

    def test_schema_version_correct(self) -> None:
        snapshots = load_data_release_snapshots()
        for snap in snapshots:
            assert snap["schema_version"] == DATA_RELEASE_SNAPSHOT_SCHEMA_VERSION

    def test_disclaimer_contains_detection_claim(self) -> None:
        snapshots = load_data_release_snapshots()
        for snap in snapshots:
            assert "detection claim" in snap["disclaimer"]


# ---------------------------------------------------------------------------
# Pathway assignment hash
# ---------------------------------------------------------------------------


class TestPathwayAssignmentHash:
    def test_deterministic(self) -> None:
        entries = [
            {"candidate_id": "c1", "track": "radio", "recommended_pathway": _REVIEW},
            {"candidate_id": "c2", "track": "infrared", "recommended_pathway": _FP},
        ]
        h1 = _pathway_assignment_hash(entries)
        h2 = _pathway_assignment_hash(entries)
        assert h1 == h2

    def test_order_independent(self) -> None:
        entries = [
            {"candidate_id": "c1", "track": "radio", "recommended_pathway": _REVIEW},
            {"candidate_id": "c2", "track": "infrared", "recommended_pathway": _FP},
        ]
        reversed_entries = list(reversed(entries))
        assert _pathway_assignment_hash(entries) == _pathway_assignment_hash(
            reversed_entries
        )

    def test_changes_on_pathway_change(self) -> None:
        entries_a = [{"candidate_id": "c1", "track": "radio", "recommended_pathway": _REVIEW}]
        entries_b = [{"candidate_id": "c1", "track": "radio", "recommended_pathway": _FP}]
        assert _pathway_assignment_hash(entries_a) != _pathway_assignment_hash(entries_b)

    def test_is_64_char_hex(self) -> None:
        entries = [{"candidate_id": "c1", "track": "radio", "recommended_pathway": "fp"}]
        h = _pathway_assignment_hash(entries)
        assert len(h) == 64
        int(h, 16)  # raises ValueError if not hex


# ---------------------------------------------------------------------------
# Compare snapshots
# ---------------------------------------------------------------------------


class TestCompareSnapshots:
    def _make_snap(self, snap_id: str, per_candidate: list[dict]) -> dict:
        return {
            "snapshot_id": snap_id,
            "pipeline_version": "scoring_v0",
            "per_candidate": per_candidate,
            "pathway_distribution": {},
            "pathway_assignment_hash": _pathway_assignment_hash(per_candidate),
        }

    def test_same_snapshots_ok(self) -> None:
        cands = [{"candidate_id": "c1", "track": "radio", "recommended_pathway": _REVIEW}]
        snap = self._make_snap("snap-1", cands)
        result = compare_snapshots(snap, snap)
        assert result["ok"] is True
        assert result["pathway_change_count"] == 0
        assert result["same_pathway_assignment_hash"] is True

    def test_pathway_change_detected(self) -> None:
        cands_a = [{"candidate_id": "c1", "track": "radio", "recommended_pathway": _REVIEW}]
        cands_b = [{"candidate_id": "c1", "track": "radio", "recommended_pathway": _FP}]
        snap_a = self._make_snap("snap-a", cands_a)
        snap_b = self._make_snap("snap-b", cands_b)
        result = compare_snapshots(snap_a, snap_b)
        assert result["ok"] is False
        assert result["pathway_change_count"] == 1
        assert result["pathway_changes"][0]["from_pathway"] == _REVIEW
        assert result["pathway_changes"][0]["to_pathway"] == _FP

    def test_new_candidate_detected(self) -> None:
        cands_a = [{"candidate_id": "c1", "track": "radio", "recommended_pathway": "fp"}]
        cands_b = [
            {"candidate_id": "c1", "track": "radio", "recommended_pathway": "fp"},
            {"candidate_id": "c2", "track": "infrared", "recommended_pathway": "fp"},
        ]
        snap_a = self._make_snap("snap-a", cands_a)
        snap_b = self._make_snap("snap-b", cands_b)
        result = compare_snapshots(snap_a, snap_b)
        assert result["ok"] is False
        assert result["new_candidate_count"] == 1
        assert "c2" in result["new_candidates"]

    def test_removed_candidate_detected(self) -> None:
        cands_a = [
            {"candidate_id": "c1", "track": "radio", "recommended_pathway": "fp"},
            {"candidate_id": "c2", "track": "infrared", "recommended_pathway": "fp"},
        ]
        cands_b = [{"candidate_id": "c1", "track": "radio", "recommended_pathway": "fp"}]
        snap_a = self._make_snap("snap-a", cands_a)
        snap_b = self._make_snap("snap-b", cands_b)
        result = compare_snapshots(snap_a, snap_b)
        assert result["ok"] is False
        assert result["removed_candidate_count"] == 1

    def test_snapshot_ids_in_result(self) -> None:
        cands = [{"candidate_id": "c1", "track": "radio", "recommended_pathway": "fp"}]
        snap_a = self._make_snap("snap-alpha", cands)
        snap_b = self._make_snap("snap-beta", cands)
        result = compare_snapshots(snap_a, snap_b)
        assert result["snapshot_a_id"] == "snap-alpha"
        assert result["snapshot_b_id"] == "snap-beta"

    def test_disclaimer_present(self) -> None:
        cands = [{"candidate_id": "c1", "track": "radio", "recommended_pathway": "fp"}]
        snap = self._make_snap("snap-1", cands)
        result = compare_snapshots(snap, snap)
        assert "detection claim" in result["disclaimer"]


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


class TestDataReleaseSnapshotSummary:
    def test_ok_with_default_fixture(self) -> None:
        summary = data_release_snapshot_summary()
        assert isinstance(summary, dict)

    def test_snapshot_count_three(self) -> None:
        summary = data_release_snapshot_summary()
        assert summary["snapshot_count"] == 3

    def test_comparison_count_two(self) -> None:
        summary = data_release_snapshot_summary()
        assert summary["cross_release_comparison_count"] == 2

    def test_pathway_change_detected_in_third_snapshot(self) -> None:
        summary = data_release_snapshot_summary()
        assert summary["total_pathway_changes_detected"] >= 1

    def test_schema_version(self) -> None:
        summary = data_release_snapshot_summary()
        assert summary["schema_version"] == DATA_RELEASE_SNAPSHOT_SCHEMA_VERSION

    def test_disclaimer_present(self) -> None:
        summary = data_release_snapshot_summary()
        assert "detection claim" in summary["disclaimer"]

    def test_pipeline_versions_in_output(self) -> None:
        summary = data_release_snapshot_summary()
        assert len(summary["pipeline_versions_seen"]) >= 1


# ---------------------------------------------------------------------------
# snapshot_from_batch_manifest
# ---------------------------------------------------------------------------


class TestSnapshotFromBatchManifest:
    def test_builds_from_batch_manifest(self, tmp_path: Path) -> None:
        manifest = {
            "config_version": "scoring_v0",
            "generated_at_utc": "2026-01-01T00:00:00+00:00",
            "reports": [
                {"candidate_id": "cid-1", "track": "radio", "recommended_pathway": _REVIEW},
                {"candidate_id": "cid-2", "track": "infrared", "recommended_pathway": _FP},
            ],
        }
        manifest_path = tmp_path / "batch_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        snap = snapshot_from_batch_manifest(
            manifest_path,
            snapshot_id="test-snap",
            data_release_label="Test release",
        )
        assert snap["snapshot_id"] == "test-snap"
        assert snap["candidate_count"] == 2
        assert snap["pathway_distribution"][_REVIEW] == 1
        assert snap["pathway_distribution"][_FP] == 1
        assert len(snap["pathway_assignment_hash"]) == 64

    def test_schema_version_in_result(self, tmp_path: Path) -> None:
        manifest = {"config_version": "v0", "generated_at_utc": "", "reports": []}
        manifest_path = tmp_path / "m.json"
        manifest_path.write_text(json.dumps(manifest))
        snap = snapshot_from_batch_manifest(
            manifest_path, snapshot_id="s1", data_release_label="l"
        )
        assert snap["schema_version"] == DATA_RELEASE_SNAPSHOT_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestDataReleaseSnapshotCLI:
    def _run(self, *args: str) -> tuple[int, dict]:
        result = subprocess.run(
            [sys.executable, "-m", "techno_search.cli", *args],
            capture_output=True,
            text=True,
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            data = {}
        return result.returncode, data

    def test_data_release_snapshot_summary_exits_zero(self) -> None:
        rc, data = self._run("data-release-snapshot-summary")
        assert rc == 0
        assert data.get("snapshot_count") == 3

    def test_compare_data_releases_identical(self) -> None:
        rc, data = self._run(
            "compare-data-releases",
            "release-hip99427-2026-06-01-v1",
            "release-hip99427-2026-06-12-v2",
        )
        assert rc == 0
        assert data.get("ok") is True
        assert data.get("pathway_change_count") == 0

    def test_compare_data_releases_detects_change(self) -> None:
        rc, data = self._run(
            "compare-data-releases",
            "release-hip99427-2026-06-12-v2",
            "release-hip99427-2026-06-12-v3-learned-model",
        )
        assert rc == 0
        assert data.get("pathway_change_count") == 1

    def test_compare_data_releases_unknown_id_returns_error(self) -> None:
        rc, data = self._run(
            "compare-data-releases",
            "nonexistent-snap-a",
            "nonexistent-snap-b",
        )
        assert rc == 1
        assert data.get("ok") is False

    def test_validate_all_includes_snapshot_count(self) -> None:
        rc, data = self._run("validate-all")
        assert rc == 0
        assert data.get("ok") is True
        assert isinstance(data.get("data_release_snapshot_count"), int)
        assert data["data_release_snapshot_count"] >= 1

    def test_validation_summary_includes_snapshot_count(self) -> None:
        rc, data = self._run("validation-summary")
        assert rc == 0
        assert "data_release_snapshot_count" in data
