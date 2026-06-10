from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.gbt_cadence import (
    TURBOSETI_NUMPY_PATCH_NEW,
    apply_turboseti_numpy_compatibility,
    build_cadence_csv,
    cadence_candidate_context,
    load_cadence_manifest,
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
