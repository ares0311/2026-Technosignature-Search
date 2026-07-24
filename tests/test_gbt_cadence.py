from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.gbt_cadence import (
    TURBOSETI_NUMPY_PATCH_NEW,
    apply_turboseti_numpy_compatibility,
    build_cadence_csv,
    cadence_candidate_context,
    has_hdf5_magic,
    load_cadence_manifest,
    md5_file,
    raw_cadence_status,
    retained_archive_candidate_context,
    validate_cadence_manifest,
    verify_archive_file,
    write_hit_provenance,
)
from techno_search.observation_artifact import assess_observation_artifact
from techno_search.radio.hit_table_reader import hit_table_to_radio_hit_dicts

MANIFEST = Path("configs/gbt_hip99427_cadence_v1.json")


def _write_dat(path: Path, source: str) -> Path:
    path.write_text(
        "\n".join(
            (
                f"# Source:{source}",
                "# MJD:57752.9609",
                "# RA:302.7191",
                "# DEC:77.2411",
                (
                    "# Top_Hit_#\tDrift_Rate\tSNR\tUncorrected_Frequency"
                    "\tCorrected_Frequency"
                ),
                "1\t0.25\t15.0\t1420.0\t1420.0",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_retained_archive_context_recovers_exact_gbt_provenance(tmp_path: Path) -> None:
    manifest = (
        tmp_path
        / "data_selection"
        / "batch_manifests"
        / "local_coverage_first_bounded_batch_manifest.json"
    )
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "targets": [
                    {
                        "hip": "HIP103096",
                        "source_hdf5_url": (
                            "https://bldata.berkeley.edu/pipeline/AGBT16B_999_50/"
                            "holding/capture_HIP103096.h5"
                        ),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    dat = tmp_path / "capture_HIP103096.dat"
    dat.write_text("# retained hit table\n", encoding="utf-8")

    source_ids, provenance = retained_archive_candidate_context(
        dat, project_root=tmp_path
    )

    assert source_ids == ("capture_HIP103096.dat",)
    assert provenance["instrument"] == "GBT"
    assert provenance["archive_provenance_match"] == "exact_hdf5_filename"
    assert provenance["instrument_provenance_basis"] == (
        "archive_program_path_prefix_AGBT"
    )


def test_retained_archive_context_rejects_ambiguous_filename_match(
    tmp_path: Path,
) -> None:
    manifest = (
        tmp_path
        / "data_selection"
        / "batch_manifests"
        / "local_coverage_first_bounded_batch_manifest.json"
    )
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "targets": [
                    {"source_hdf5_url": "https://one.test/AGBT1/capture.h5"},
                    {"source_hdf5_url": "https://two.test/AGBT2/capture.h5"},
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Ambiguous retained archive provenance"):
        retained_archive_candidate_context(
            tmp_path / "capture.dat", project_root=tmp_path
        )


def _tiny_manifest(tmp_path: Path) -> dict:
    manifest = json.loads(json.dumps(load_cadence_manifest(MANIFEST)))
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    for scan in manifest["scans"]:
        path = raw_dir / scan["filename"]
        path.write_bytes(b"\x89HDF\r\n\x1a\n" + f"raw scan {scan['sequence_index']}".encode())
        scan["size_bytes"] = path.stat().st_size
        scan["md5"] = md5_file(path)
    return manifest


def test_approved_manifest_has_complete_abacad_order() -> None:
    manifest = load_cadence_manifest(MANIFEST)

    assert [scan["scan_role"] for scan in manifest["scans"]] == [
        "on",
        "off",
        "on",
        "off",
        "on",
        "off",
    ]
    assert manifest["external_submission_authorized"] is False
    assert manifest["analysis"]["max_drift_hz_per_sec"] == pytest.approx(10.0)
    assert "9.7960855" in manifest["analysis"]["resolution_note"]


def test_manifest_rejects_non_alternating_roles() -> None:
    manifest = load_cadence_manifest(MANIFEST)
    manifest["scans"][1]["scan_role"] = "on"

    with pytest.raises(ValueError, match="ABACAD"):
        validate_cadence_manifest(manifest)


def test_archive_verification_rejects_wrong_size(tmp_path: Path) -> None:
    artifact = tmp_path / "scan.h5"
    artifact.write_bytes(b"observation")

    with pytest.raises(ValueError, match="size mismatch"):
        verify_archive_file(
            artifact,
            {"size_bytes": 999, "md5": "00000000000000000000000000000000"},
        )


def test_hdf5_magic_detects_raw_file_signature(tmp_path: Path) -> None:
    hdf5 = tmp_path / "scan.h5"
    text = tmp_path / "scan.txt"
    hdf5.write_bytes(b"\x89HDF\r\n\x1a\npayload")
    text.write_bytes(b"not hdf5")

    assert has_hdf5_magic(hdf5) is True
    assert has_hdf5_magic(text) is False


def test_raw_cadence_status_reports_missing_files(tmp_path: Path) -> None:
    manifest = load_cadence_manifest(MANIFEST)
    result = raw_cadence_status(manifest, tmp_path / "missing")

    assert result["ok"] is False
    assert result["scan_count"] == 6
    assert result["missing_count"] == 6
    assert result["verified_count"] == 0
    assert {scan["issue"] for scan in result["scans"]} == {"missing_raw_file"}
    assert result["external_submission_authorized"] is False


def test_raw_cadence_status_verifies_complete_manifest(tmp_path: Path) -> None:
    manifest = _tiny_manifest(tmp_path)
    result = raw_cadence_status(manifest, tmp_path / "raw")

    assert result["ok"] is True
    assert result["verified_count"] == 6
    assert result["missing_count"] == 0
    assert result["mismatch_count"] == 0
    assert [scan["scan_role"] for scan in result["scans"]] == [
        "on",
        "off",
        "on",
        "off",
        "on",
        "off",
    ]
    assert all(scan["hdf5_signature_verified"] for scan in result["scans"])


def test_raw_cadence_status_reports_checksum_mismatch(tmp_path: Path) -> None:
    manifest = _tiny_manifest(tmp_path)
    first = manifest["scans"][0]
    (tmp_path / "raw" / first["filename"]).write_bytes(b"changed")
    first["size_bytes"] = len(b"changed")

    result = raw_cadence_status(manifest, tmp_path / "raw")

    assert result["ok"] is False
    assert result["mismatch_count"] == 1
    assert result["scans"][0]["issue"] == "md5_mismatch"


def test_raw_cadence_status_rejects_checksum_valid_non_hdf5_file(tmp_path: Path) -> None:
    manifest = _tiny_manifest(tmp_path)
    first = manifest["scans"][0]
    path = tmp_path / "raw" / first["filename"]
    path.write_bytes(b"not an hdf5 payload")
    first["size_bytes"] = path.stat().st_size
    first["md5"] = md5_file(path)

    result = raw_cadence_status(manifest, tmp_path / "raw")

    assert result["ok"] is False
    assert result["mismatch_count"] == 1
    assert result["scans"][0]["issue"] == "hdf5_signature_mismatch"
    assert result["scans"][0]["hdf5_signature_verified"] is False


def test_turboseti_numpy_compatibility_patch_is_idempotent(tmp_path: Path) -> None:
    source_dir = tmp_path / "find_doppler"
    source_dir.mkdir()
    source = source_dir / "find_doppler.py"
    source.write_text(
        'logger.debug("Total" + " is: %i" % max_val.total_n_hits)\n',
        encoding="utf-8",
    )

    assert apply_turboseti_numpy_compatibility(tmp_path) is True
    assert TURBOSETI_NUMPY_PATCH_NEW in source.read_text(encoding="utf-8")
    assert apply_turboseti_numpy_compatibility(tmp_path) is False


def test_provenance_approves_derived_real_hit_table(tmp_path: Path) -> None:
    manifest = load_cadence_manifest(MANIFEST)
    scan = manifest["scans"][0]
    hdf5 = tmp_path / scan["filename"]
    hdf5.write_bytes(b"real observation fixture")
    dat = _write_dat(tmp_path / "HIP99427.dat", "HIP99427")

    write_hit_provenance(dat, hdf5, manifest, scan, turbo_seti_version="2.3.2")
    assessment = assess_observation_artifact(dat)

    assert assessment.approved_for_pipeline is True
    provenance = json.loads(assessment.provenance_path.read_text(encoding="utf-8"))
    assert provenance["scan_role"] == "on"
    assert provenance["external_submission_authorized"] is False


def test_cadence_csv_preserves_on_off_roles(tmp_path: Path) -> None:
    manifest = load_cadence_manifest(MANIFEST)
    dat_paths: list[Path] = []
    for scan in manifest["scans"][:2]:
        hdf5 = tmp_path / scan["filename"]
        hdf5.write_bytes(f"real observation {scan['sequence_index']}".encode())
        dat = _write_dat(tmp_path / f"scan_{scan['sequence_index']}.dat", scan["source_name"])
        write_hit_provenance(dat, hdf5, manifest, scan, turbo_seti_version="2.3.2")
        dat_paths.append(dat)

    destination = tmp_path / "cadence.csv"
    result = build_cadence_csv(
        dat_paths,
        destination,
        cadence_id=manifest["cadence_id"],
        target_name=manifest["target_name"],
    )
    rows = hit_table_to_radio_hit_dicts(destination)

    assert result["row_count"] == 2
    assert [row["scan_role"] for row in rows] == ["on", "off"]
    assert {row["target_id"] for row in rows} == {"HIP99427", "HIP100670"}
    source_ids, provenance = cadence_candidate_context(destination)
    assert source_ids == ("scan_1.dat", "scan_2.dat")
    assert provenance["source_dataset"] == manifest["cadence_id"]
    assert provenance["instrument"] == "Green Bank Telescope"
    assert provenance["processing_tool"] == "turboSETI"
    assert provenance["processing_tool_version"] == "2.3.2"
    assert provenance["processing_snr_threshold"] == 10.0
    assert provenance["source_url_count"] == 2
    assert provenance["external_submission_authorized"] is False


def test_cadence_context_rejects_tampered_csv(tmp_path: Path) -> None:
    manifest = load_cadence_manifest(MANIFEST)
    scan = manifest["scans"][0]
    hdf5 = tmp_path / scan["filename"]
    hdf5.write_bytes(b"real observation")
    dat = _write_dat(tmp_path / "scan_1.dat", scan["source_name"])
    write_hit_provenance(dat, hdf5, manifest, scan, turbo_seti_version="2.3.2")
    destination = tmp_path / "cadence.csv"
    build_cadence_csv(
        [dat],
        destination,
        cadence_id=manifest["cadence_id"],
        target_name=manifest["target_name"],
    )
    destination.write_text(destination.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        cadence_candidate_context(destination)
