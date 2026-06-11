"""Tests for scripts/build_calibration_target_manifest.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
_SCRIPT_PATH = SCRIPTS_DIR / "build_calibration_target_manifest.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "build_calibration_target_manifest", _SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture(scope="module")
def mod():
    return _load_module()


@pytest.fixture(scope="module")
def manifest(mod):
    return mod.build_manifest()


# ---------------------------------------------------------------------------
# Script existence and importability
# ---------------------------------------------------------------------------


def test_script_exists():
    assert _SCRIPT_PATH.exists(), "build_calibration_target_manifest.py must exist"


def test_module_importable(mod):
    assert mod is not None


# ---------------------------------------------------------------------------
# Manifest structure
# ---------------------------------------------------------------------------


def test_manifest_version(manifest):
    assert manifest["manifest_version"] == "calibration_corpus_manifest_v1"


def test_manifest_has_disclaimer(manifest):
    assert "disclaimer" in manifest
    d = manifest["disclaimer"]
    assert "calibration" in d.lower()
    assert "detection claim" in d.lower()
    assert "external submission" in d.lower()


def test_manifest_has_calibration_gates(manifest):
    gates = manifest["calibration_gates_to_pass"]
    assert gates["minimum_cadences"] >= 3
    assert gates["minimum_targets"] >= 3
    assert gates["minimum_epochs"] >= 2
    assert gates["minimum_hits"] >= 100
    assert 0 < gates["max_cadence_hit_fraction"] <= 1.0


def test_manifest_has_archive_urls(manifest):
    assert "http://blpd0.ssl.berkeley.edu" in manifest["archive_base_url_http"]
    assert "blpd14.ssl.berkeley.edu" in manifest["archive_base_url_https"]


def test_manifest_has_discovery_instructions(manifest):
    assert "archive_discovery_instructions" in manifest
    instructions = manifest["archive_discovery_instructions"]
    assert "curl" in instructions
    assert "blc07" in instructions


# ---------------------------------------------------------------------------
# Target catalog
# ---------------------------------------------------------------------------


def test_target_count(manifest):
    assert manifest["targets_total"] == 5


def test_target_ids_present(manifest):
    ids = {t["target_id"] for t in manifest["targets"]}
    assert "Voyager1" in ids
    assert "HIP65803" in ids
    assert "HIP4436" in ids
    assert "HIP8102" in ids
    assert "HIP16537" in ids


def test_voyager1_already_ingested(manifest):
    voyager = next(t for t in manifest["targets"] if t["target_id"] == "Voyager1")
    assert voyager["status"] == "already_ingested"


def test_voyager1_file_verified(manifest):
    voyager = next(t for t in manifest["targets"] if t["target_id"] == "Voyager1")
    assert all(f.get("verified") is True for f in voyager["files"])


def test_other_targets_recommended_download(manifest):
    for t in manifest["targets"]:
        if t["target_id"] != "Voyager1":
            assert t["status"] == "recommended_download", (
                f"{t['target_id']} must be recommended_download"
            )


def test_targets_have_priorities(manifest):
    priorities = [t["priority"] for t in manifest["targets"]]
    assert sorted(priorities) == list(range(5))


def test_already_ingested_count(manifest):
    assert manifest["targets_already_ingested"] == 1


def test_recommended_download_count(manifest):
    assert manifest["targets_recommended_download"] == 4


# ---------------------------------------------------------------------------
# Provenance template fields
# ---------------------------------------------------------------------------

_REQUIRED_PROVENANCE_FIELDS = {
    "target_id",
    "source_name",
    "target_ra_deg",
    "target_dec_deg",
    "observation_utc_start",
    "observation_mjd",
    "cadence_id",
    "classification",
    "review_status",
    "pipeline_band",
    "citation",
}


def test_provenance_template_required_fields(manifest):
    for t in manifest["targets"]:
        pt = t["provenance_template"]
        missing = _REQUIRED_PROVENANCE_FIELDS - set(pt.keys())
        assert not missing, f"{t['target_id']} missing provenance fields: {missing}"


def test_provenance_classification_real_observation(manifest):
    for t in manifest["targets"]:
        pt = t["provenance_template"]
        assert pt["classification"] == "real_observation", (
            f"{t['target_id']} must have classification='real_observation'"
        )


def test_voyager1_provenance_approved(manifest):
    voyager = next(t for t in manifest["targets"] if t["target_id"] == "Voyager1")
    assert voyager["provenance_template"]["review_status"] == "approved"


def test_unverified_targets_provenance_provisional(manifest):
    for t in manifest["targets"]:
        if t["target_id"] == "Voyager1":
            continue
        pt = t["provenance_template"]
        assert pt["review_status"] == "provisional", (
            f"{t['target_id']} must have review_status='provisional'"
        )


def test_unverified_targets_have_none_epoch(manifest):
    """Unverified targets must not have hardcoded epoch — it depends on the actual file."""
    for t in manifest["targets"]:
        if t["target_id"] == "Voyager1":
            continue
        pt = t["provenance_template"]
        assert pt["observation_utc_start"] is None, (
            f"{t['target_id']} observation_utc_start should be None (set at download time)"
        )
        assert pt["observation_mjd"] is None
        assert pt["cadence_id"] is None


def test_stellar_targets_have_ra_dec(manifest):
    """HIP targets should have valid RA/Dec."""
    for t in manifest["targets"]:
        if t["target_id"] == "Voyager1":
            continue
        pt = t["provenance_template"]
        assert pt["target_ra_deg"] is not None, (
            f"{t['target_id']} missing RA"
        )
        assert pt["target_dec_deg"] is not None, (
            f"{t['target_id']} missing Dec"
        )
        ra = pt["target_ra_deg"]
        dec = pt["target_dec_deg"]
        assert 0 <= ra < 360, f"{t['target_id']} RA={ra} out of range"
        assert -90 <= dec <= 90, f"{t['target_id']} Dec={dec} out of range"


def test_citation_present_and_non_empty(manifest):
    for t in manifest["targets"]:
        citation = t["provenance_template"]["citation"]
        assert citation and len(citation.strip()) > 10, (
            f"{t['target_id']} citation too short"
        )


# ---------------------------------------------------------------------------
# File entries
# ---------------------------------------------------------------------------


def test_each_target_has_files(manifest):
    for t in manifest["targets"]:
        assert len(t["files"]) >= 1, f"{t['target_id']} must have at least one file entry"


def test_voyager1_file_size(manifest):
    voyager = next(t for t in manifest["targets"] if t["target_id"] == "Voyager1")
    assert voyager["files"][0]["size_bytes"] == 50_549_227


def test_http_urls_present(manifest):
    for t in manifest["targets"]:
        for f in t["files"]:
            url = f.get("url_http", "")
            assert url.startswith("http://blpd0.ssl.berkeley.edu"), (
                f"{t['target_id']}: unexpected http URL: {url}"
            )


# ---------------------------------------------------------------------------
# CLI: --list-targets
# ---------------------------------------------------------------------------


def test_main_list_targets(mod, capsys):
    rc = mod.main(["--list-targets"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Calibration Corpus Download Manifest" in out
    assert "Voyager1" in out
    assert "HIP65803" in out


# ---------------------------------------------------------------------------
# CLI: --output writes valid JSON
# ---------------------------------------------------------------------------


def test_main_writes_json(mod, tmp_path):
    out_path = tmp_path / "manifest.json"
    rc = mod.main(["--output", str(out_path)])
    assert rc == 0
    assert out_path.exists()
    data = json.loads(out_path.read_text())
    assert data["manifest_version"] == "calibration_corpus_manifest_v1"
    assert len(data["targets"]) == 5


def test_main_output_is_valid_utf8_json(mod, tmp_path):
    out_path = tmp_path / "manifest.json"
    mod.main(["--output", str(out_path)])
    raw = out_path.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# Scientific guardrails in disclaimer / notes
# ---------------------------------------------------------------------------


def test_disclaimer_no_detection_claim_language(mod):
    d = mod.DISCLAIMER
    assert "detection claim" in d.lower()
    assert "external submission" in d.lower()


def test_manifest_disclaimer_excludes_discovery_language(manifest):
    d = manifest["disclaimer"]
    forbidden = ["confirmed detection", "confirmed technosignature", "definitive"]
    for phrase in forbidden:
        assert phrase.lower() not in d.lower(), (
            f"Disclaimer must not contain '{phrase}'"
        )
