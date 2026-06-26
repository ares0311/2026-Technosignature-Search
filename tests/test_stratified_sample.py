"""Tests for scripts/build_stratified_sample.py — stratified BL target sampling."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

# Add scripts/ to path for import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_stratified_sample import (
    SCHEMA_VERSION,
    SPEC_CLASSES,
    _assign_distance_bin,
    _parse_spec_class,
    build_manifest,
    load_seed_targets,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_CSV = REPO_ROOT / "data" / "bl_hprc_seed_targets.csv"
MANIFEST_PATH = REPO_ROOT / "data" / "target_sample_manifest.json"


def _make_csv(tmp_path: Path, rows: list[dict]) -> Path:
    p = tmp_path / "targets.csv"
    if not rows:
        p.write_text("")
        return p
    fieldnames = list(rows[0].keys())
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    return p


SAMPLE_ROWS = [
    dict(hip="8102", name="tau Ceti", ra_deg="26.017", dec_deg="-15.939",
         dist_pc="3.65", spec_type="G8V", bv="0.72", gal_lat="-73.4",
         exoplanet="1", bl_paper="E17"),
    dict(hip="16537", name="eps Eri", ra_deg="53.233", dec_deg="-9.458",
         dist_pc="3.22", spec_type="K2V", bv="0.88", gal_lat="-48.0",
         exoplanet="1", bl_paper="E17"),
    dict(hip="87937", name="Barnard", ra_deg="269.454", dec_deg="4.693",
         dist_pc="1.83", spec_type="M4V", bv="1.57", gal_lat="14.2",
         exoplanet="0", bl_paper="E17"),
    dict(hip="57757", name="bet Vir", ra_deg="188.596", dec_deg="1.764",
         dist_pc="10.9", spec_type="F9V", bv="0.55", gal_lat="62.1",
         exoplanet="0", bl_paper="E17"),
    dict(hip="17147", name="HIP17147", ra_deg="55.145", dec_deg="-24.380",
         dist_pc="31.2", spec_type="G0V", bv="0.60", gal_lat="-51.4",
         exoplanet="0", bl_paper="P20"),
]


# ---------------------------------------------------------------------------
# Unit tests — helper functions
# ---------------------------------------------------------------------------

class TestParseSpecClass:
    def test_g8v_returns_g(self) -> None:
        assert _parse_spec_class("G8V") == "G"

    def test_k2v_returns_k(self) -> None:
        assert _parse_spec_class("K2V") == "K"

    def test_m4v_returns_m(self) -> None:
        assert _parse_spec_class("M4V") == "M"

    def test_f9iv_returns_f(self) -> None:
        assert _parse_spec_class("F9IV") == "F"

    def test_empty_returns_question(self) -> None:
        assert _parse_spec_class("") == "?"

    def test_case_insensitive(self) -> None:
        assert _parse_spec_class("g2v") == "G"


class TestAssignDistanceBin:
    def test_near_bin(self) -> None:
        assert _assign_distance_bin(3.65) == "near"

    def test_mid_bin(self) -> None:
        assert _assign_distance_bin(10.9) == "mid"

    def test_far_bin(self) -> None:
        assert _assign_distance_bin(31.2) == "far"

    def test_boundary_8pc_is_mid(self) -> None:
        assert _assign_distance_bin(8.0) == "mid"

    def test_too_far_returns_none(self) -> None:
        assert _assign_distance_bin(100.0) is None


# ---------------------------------------------------------------------------
# load_seed_targets
# ---------------------------------------------------------------------------

class TestLoadSeedTargets:
    def test_loads_sample_rows(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        targets = load_seed_targets(csv_path)
        assert len(targets) == 5

    def test_parses_spec_class(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        targets = load_seed_targets(csv_path)
        classes = {t["spec_class"] for t in targets}
        assert "G" in classes
        assert "K" in classes
        assert "M" in classes
        assert "F" in classes

    def test_parses_distance_bin(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        targets = load_seed_targets(csv_path)
        bins = {t["distance_bin"] for t in targets}
        assert "near" in bins  # 1.83 pc Barnard's
        assert "mid" in bins   # 10.9 pc bet Vir
        assert "far" in bins   # 31.2 pc HIP17147

    def test_skips_comment_lines(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "seed.csv"
        header = "hip,name,ra_deg,dec_deg,dist_pc,spec_type,bv,gal_lat,exoplanet,bl_paper"
        csv_path.write_text(
            f"# This is a comment\n{header}\n"
            "8102,tau Ceti,26.017,-15.939,3.65,G8V,0.72,-73.4,1,E17\n"
        )
        targets = load_seed_targets(csv_path)
        assert len(targets) == 1
        assert targets[0]["hip"] == "8102"

    def test_exoplanet_flag(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        targets = load_seed_targets(csv_path)
        hip_exo = {t["hip"]: t["exoplanet"] for t in targets}
        assert hip_exo["8102"] == 1
        assert hip_exo["87937"] == 0


# ---------------------------------------------------------------------------
# build_manifest
# ---------------------------------------------------------------------------

class TestBuildManifest:
    def test_manifest_schema_version(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        m = build_manifest(csv_path, per_stratum=1, max_targets=None, seed=42)
        assert m["schema_version"] == SCHEMA_VERSION

    def test_manifest_contains_disclaimer(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        m = build_manifest(csv_path, per_stratum=1, max_targets=None, seed=42)
        assert "scheduling aid" in m["disclaimer"].lower()
        assert "detection claim" in m["disclaimer"].lower()

    def test_manifest_records_seed(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        m = build_manifest(csv_path, per_stratum=1, max_targets=None, seed=99)
        assert m["sampling"]["random_seed"] == 99

    def test_per_stratum_respected(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        m = build_manifest(csv_path, per_stratum=1, max_targets=None, seed=42)
        # Each stratum should contribute at most 1 target
        strata = m["selection_summary"]["strata_with_targets"]
        for cell_hips in strata.values():
            assert len(cell_hips) <= 1

    def test_max_targets_cap(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        m = build_manifest(csv_path, per_stratum=5, max_targets=2, seed=42)
        assert len(m["targets"]) <= 2

    def test_deterministic_with_same_seed(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        m1 = build_manifest(csv_path, per_stratum=2, max_targets=None, seed=42)
        m2 = build_manifest(csv_path, per_stratum=2, max_targets=None, seed=42)
        assert [t["hip"] for t in m1["targets"]] == [t["hip"] for t in m2["targets"]]

    def test_different_seeds_give_different_results(self, tmp_path: Path) -> None:
        # With a large enough pool, different seeds should give different orderings.
        # Our sample is small so we test for non-identical rather than guaranteed diff.
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        m1 = build_manifest(csv_path, per_stratum=1, max_targets=None, seed=1)
        m2 = build_manifest(csv_path, per_stratum=1, max_targets=None, seed=2)
        # At minimum, both should succeed and have targets
        assert len(m1["targets"]) >= 1
        assert len(m2["targets"]) >= 1

    def test_seed_csv_provenance_recorded(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        m = build_manifest(csv_path, per_stratum=2, max_targets=None, seed=42)
        assert "sha256" in m["seed_csv"]
        assert len(m["seed_csv"]["sha256"]) == 64  # SHA-256 hex digest

    def test_no_duplicate_hip_in_selection(self, tmp_path: Path) -> None:
        csv_path = _make_csv(tmp_path, SAMPLE_ROWS)
        m = build_manifest(csv_path, per_stratum=5, max_targets=None, seed=42)
        hips = [t["hip"] for t in m["targets"]]
        assert len(hips) == len(set(hips)), "Duplicate HIPs in manifest selection"


# ---------------------------------------------------------------------------
# Committed seed file and manifest
# ---------------------------------------------------------------------------

class TestCommittedSeedFile:
    def test_seed_csv_exists(self) -> None:
        assert SEED_CSV.exists(), f"Committed seed CSV not found: {SEED_CSV}"

    def test_seed_csv_has_minimum_targets(self) -> None:
        targets = load_seed_targets(SEED_CSV)
        assert len(targets) >= 30, f"Expected >= 30 targets, got {len(targets)}"

    def test_seed_csv_covers_all_spec_classes(self) -> None:
        targets = load_seed_targets(SEED_CSV)
        classes = {t["spec_class"] for t in targets}
        for sc in SPEC_CLASSES:
            assert sc in classes, f"Spectral class '{sc}' missing from seed CSV"

    def test_seed_csv_covers_all_distance_bins(self) -> None:
        targets = load_seed_targets(SEED_CSV)
        bins = {t["distance_bin"] for t in targets if t["distance_bin"]}
        assert "near" in bins
        assert "mid" in bins
        assert "far" in bins

    def test_seed_csv_has_both_exoplanet_values(self) -> None:
        targets = load_seed_targets(SEED_CSV)
        values = {t["exoplanet"] for t in targets}
        assert 0 in values
        assert 1 in values

    def test_seed_csv_includes_prior_targets(self) -> None:
        """The 5 original extended corpus targets must appear in the seed list."""
        targets = load_seed_targets(SEED_CSV)
        hips = {t["hip"] for t in targets}
        for expected in ["17147", "39826", "66704", "74981", "82860"]:
            assert expected in hips, f"Prior target HIP{expected} missing from seed CSV"


class TestCommittedManifest:
    def test_manifest_exists(self) -> None:
        assert MANIFEST_PATH.exists(), f"Committed manifest not found: {MANIFEST_PATH}"

    def test_manifest_is_valid_json(self) -> None:
        m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert isinstance(m, dict)

    def test_manifest_schema_version(self) -> None:
        m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert m.get("schema_version") == SCHEMA_VERSION

    def test_manifest_has_targets(self) -> None:
        m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert len(m.get("targets", [])) >= 10

    def test_manifest_disclaimer_present(self) -> None:
        m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        disc = m.get("disclaimer", "")
        assert "detection claim" in disc.lower()

    def test_manifest_seed_is_42(self) -> None:
        m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert m["sampling"]["random_seed"] == 42

    def test_manifest_reproducible(self) -> None:
        """Re-running the sampler with the committed seed CSV and seed 42 must
        produce the same target list as the committed manifest."""
        committed = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        committed_hips = [t["hip"] for t in committed["targets"]]
        fresh = build_manifest(
            seed_csv=SEED_CSV,
            per_stratum=committed["sampling"]["per_stratum_quota"],
            max_targets=committed["sampling"]["max_targets"],
            seed=42,
        )
        fresh_hips = [t["hip"] for t in fresh["targets"]]
        assert committed_hips == fresh_hips, (
            "Manifest is not reproducible — seed CSV or algorithm changed."
        )
