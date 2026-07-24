"""Reproducible intake for an approved GBT ON/OFF observation cadence."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import ssl
import urllib.request
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import certifi

from techno_search.observation_artifact import (
    OBSERVATION_ARTIFACT_SCHEMA_VERSION,
    assess_observation_artifact,
    provenance_path_for,
    sha256_file,
)
from techno_search.radio.hit_table_reader import read_hit_table_csv

CADENCE_SCHEMA_VERSION = "gbt_observation_cadence_v1"
CADENCE_DERIVATION_SCHEMA_VERSION = "observation_cadence_derivation_v1"
RAW_CADENCE_STATUS_SCHEMA_VERSION = "gbt_raw_cadence_status_v1"
EXPECTED_ROLES = ("on", "off", "on", "off", "on", "off")
HDF5_MAGIC = b"\x89HDF"
TURBOSETI_NUMPY_PATCH_OLD = '" is: %i" % max_val.total_n_hits)'
TURBOSETI_NUMPY_PATCH_NEW = '" is: %i" % int(max_val.total_n_hits[0]))'
# Some turbo_seti releases already index the scalar upstream without our
# defensive int() cast (e.g. `% max_val.total_n_hits[0])`). numpy 2.x formats
# an indexed scalar fine either way, so this variant needs no patch.
TURBOSETI_NUMPY_ALREADY_INDEXED = '" is: %i" % max_val.total_n_hits[0])'
RETAINED_CORPUS_MANIFEST = Path(
    "data_selection/batch_manifests/local_coverage_first_bounded_batch_manifest.json"
)


def load_cadence_manifest(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Cadence manifest must contain a JSON object.")
    validate_cadence_manifest(raw)
    return raw


def validate_cadence_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != CADENCE_SCHEMA_VERSION:
        raise ValueError("Cadence manifest has an unsupported schema_version.")
    if manifest.get("human_approval_status") != "approved":
        raise ValueError("Cadence manifest lacks human approval.")
    if manifest.get("approved_for_local_real_data") is not True:
        raise ValueError("Cadence manifest is not approved for local real-data use.")
    if manifest.get("external_submission_authorized") is not False:
        raise ValueError("Cadence manifest must keep external submission disabled.")

    scans = manifest.get("scans")
    if not isinstance(scans, list) or len(scans) != len(EXPECTED_ROLES):
        raise ValueError("Cadence manifest must contain exactly six scans.")

    roles: list[str] = []
    indexes: list[int] = []
    for scan in scans:
        if not isinstance(scan, dict):
            raise ValueError("Each cadence scan must be a JSON object.")
        roles.append(str(scan.get("scan_role", "")))
        indexes.append(int(scan.get("sequence_index", 0)))
        for field in ("source_name", "utc_start", "filename", "md5", "url"):
            if not str(scan.get(field, "")).strip():
                raise ValueError(f"Cadence scan is missing {field}.")
        if int(scan.get("size_bytes", 0)) <= 0:
            raise ValueError("Cadence scan size_bytes must be positive.")
        parsed = urlparse(str(scan["url"]))
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Cadence scan URL must be a complete HTTPS URL.")

    if tuple(roles) != EXPECTED_ROLES:
        raise ValueError("Cadence scan roles must follow ABACAD ON/OFF ordering.")
    if indexes != list(range(1, len(EXPECTED_ROLES) + 1)):
        raise ValueError("Cadence sequence_index values must be consecutive from 1.")


def md5_file(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def has_hdf5_magic(path: Path) -> bool:
    """Return True when a file starts with the HDF5 file signature."""
    with path.open("rb") as handle:
        return handle.read(len(HDF5_MAGIC)) == HDF5_MAGIC


def apply_turboseti_numpy_compatibility(package_dir: Path) -> bool:
    """Patch turboSETI's array-to-scalar debug formatting for NumPy 2.x."""
    source_path = package_dir / "find_doppler" / "find_doppler.py"
    source = source_path.read_text(encoding="utf-8")
    if TURBOSETI_NUMPY_PATCH_NEW in source or TURBOSETI_NUMPY_ALREADY_INDEXED in source:
        return False
    if TURBOSETI_NUMPY_PATCH_OLD not in source:
        raise RuntimeError("Unsupported turboSETI source; NumPy compatibility patch not applied.")
    source_path.write_text(
        source.replace(TURBOSETI_NUMPY_PATCH_OLD, TURBOSETI_NUMPY_PATCH_NEW, 1),
        encoding="utf-8",
    )
    return True


def verify_archive_file(path: Path, scan: Mapping[str, Any]) -> None:
    expected_size = int(scan["size_bytes"])
    actual_size = path.stat().st_size
    if actual_size != expected_size:
        raise ValueError(
            f"Archive size mismatch for {path.name}: expected {expected_size}, got {actual_size}."
        )
    expected_md5 = str(scan["md5"]).lower()
    actual_md5 = md5_file(path)
    if actual_md5 != expected_md5:
        raise ValueError(
            f"Archive MD5 mismatch for {path.name}: expected {expected_md5}, got {actual_md5}."
        )


def download_archive_file(scan: Mapping[str, Any], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        verify_archive_file(destination, scan)
        return destination

    partial = destination.with_name(destination.name + ".part")
    partial.unlink(missing_ok=True)
    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with (
            urllib.request.urlopen(str(scan["url"]), context=context) as response,
            partial.open("wb") as handle,
        ):
            shutil.copyfileobj(response, handle, length=1024 * 1024)
        verify_archive_file(partial, scan)
        partial.replace(destination)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return destination


def raw_cadence_status(manifest: Mapping[str, Any], raw_dir: Path) -> dict[str, Any]:
    """Return local raw HDF5 presence/checksum status for an approved cadence."""
    validate_cadence_manifest(manifest)
    raw_path = Path(raw_dir)
    scan_entries: list[dict[str, Any]] = []
    verified_count = 0
    missing_count = 0
    mismatch_count = 0
    for scan in _sequence(manifest["scans"]):
        filename = str(scan["filename"])
        path = raw_path / filename
        entry: dict[str, Any] = {
            "sequence_index": int(scan["sequence_index"]),
            "scan_role": str(scan["scan_role"]),
            "source_name": str(scan["source_name"]),
            "filename": filename,
            "path": str(path),
            "exists": path.exists(),
            "expected_size_bytes": int(scan["size_bytes"]),
            "expected_md5": str(scan["md5"]).lower(),
            "verified": False,
            "hdf5_signature_verified": False,
        }
        if not path.exists():
            missing_count += 1
            entry["issue"] = "missing_raw_file"
            scan_entries.append(entry)
            continue
        actual_size = path.stat().st_size
        entry["actual_size_bytes"] = actual_size
        if actual_size != int(scan["size_bytes"]):
            mismatch_count += 1
            entry["issue"] = "size_mismatch"
            scan_entries.append(entry)
            continue
        actual_md5 = md5_file(path)
        entry["actual_md5"] = actual_md5
        if actual_md5 != str(scan["md5"]).lower():
            mismatch_count += 1
            entry["issue"] = "md5_mismatch"
            scan_entries.append(entry)
            continue
        if not has_hdf5_magic(path):
            mismatch_count += 1
            entry["issue"] = "hdf5_signature_mismatch"
            scan_entries.append(entry)
            continue
        entry["hdf5_signature_verified"] = True
        entry["verified"] = True
        verified_count += 1
        scan_entries.append(entry)

    return {
        "schema_version": RAW_CADENCE_STATUS_SCHEMA_VERSION,
        "cadence_id": str(manifest["cadence_id"]),
        "target_name": str(manifest["target_name"]),
        "raw_dir": str(raw_path),
        "expected_scan_count": len(EXPECTED_ROLES),
        "scan_count": len(scan_entries),
        "verified_count": verified_count,
        "missing_count": missing_count,
        "mismatch_count": mismatch_count,
        "ok": verified_count == len(EXPECTED_ROLES)
        and missing_count == 0
        and mismatch_count == 0,
        "external_submission_authorized": False,
        "detection_claimed": False,
        "scans": scan_entries,
    }


def write_hit_provenance(
    dat_path: Path,
    hdf5_path: Path,
    manifest: Mapping[str, Any],
    scan: Mapping[str, Any],
    *,
    turbo_seti_version: str,
) -> Path:
    analysis = _mapping(manifest["analysis"])
    payload = {
        "schema_version": OBSERVATION_ARTIFACT_SCHEMA_VERSION,
        "artifact_filename": dat_path.name,
        "sha256": sha256_file(dat_path),
        "classification": "real_observation",
        "source_archive": str(manifest["source_archive"]),
        "source_url": str(scan["url"]),
        "instrument": str(manifest["instrument"]),
        "receiver": str(manifest["receiver"]),
        "downloaded_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "data_use_review_status": "approved",
        "provenance_review_status": "approved",
        "human_approval_status": "approved",
        "approved_for_local_real_data": True,
        "external_submission_authorized": False,
        "cadence_id": str(manifest["cadence_id"]),
        "sequence_index": int(scan["sequence_index"]),
        "scan_role": str(scan["scan_role"]),
        "target_id": str(scan["source_name"]),
        "source_name": str(scan["source_name"]),
        "source_hdf5_filename": hdf5_path.name,
        "source_hdf5_sha256": sha256_file(hdf5_path),
        "source_archive_md5": str(scan["md5"]),
        "source_archive_size_bytes": int(scan["size_bytes"]),
        "observation_utc_start": str(scan["utc_start"]),
        "observation_mjd": float(scan["mjd"]),
        "processing_tool": "turboSETI",
        "processing_tool_version": turbo_seti_version,
        "processing_compatibility_note": (
            "turboSETI 2.3.2 hit-counter debug formatting patched from array to scalar "
            "for NumPy 2.x; search mathematics unchanged"
        ),
        "processing_parameters": {
            "max_drift_hz_per_sec": float(analysis["max_drift_hz_per_sec"]),
            "min_drift_hz_per_sec": float(analysis["min_drift_hz_per_sec"]),
            "snr_threshold": float(analysis["snr_threshold"]),
        },
        "data_license": str(manifest["data_license"]),
        "data_use_url": str(manifest["data_use_url"]),
        "observation_summary_url": str(manifest["observation_summary_url"]),
    }
    destination = provenance_path_for(dat_path)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def build_cadence_csv(
    dat_paths: Sequence[Path],
    destination: Path,
    *,
    cadence_id: str,
    target_name: str,
) -> dict[str, Any]:
    fieldnames = (
        "Corrected_Frequency",
        "SNR",
        "Drift_Rate",
        "Source_Name",
        "MJD",
        "RA",
        "DEC",
        "scan_role",
        "target_id",
        "source_artifact",
    )
    rows_written = 0
    scan_summaries: list[dict[str, Any]] = []
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for dat_path in dat_paths:
            assessment = assess_observation_artifact(dat_path)
            if not assessment.approved_for_pipeline:
                raise ValueError(
                    f"Cadence source is not approved: {dat_path.name}: "
                    + "; ".join(assessment.issues)
                )
            provenance = json.loads(
                provenance_path_for(dat_path).read_text(encoding="utf-8")
            )
            role = str(provenance["scan_role"])
            source_rows = read_hit_table_csv(dat_path)
            for row in source_rows:
                writer.writerow(
                    {
                        "Corrected_Frequency": float(row["frequency_hz"]) / 1e6,
                        "SNR": row["snr"],
                        "Drift_Rate": row["drift_rate_hz_per_sec"],
                        "Source_Name": row.get("source_name", ""),
                        "MJD": row.get("mjd") or "",
                        "RA": row.get("ra_deg") or "",
                        "DEC": row.get("dec_deg") or "",
                        "scan_role": role,
                        "target_id": provenance["target_id"],
                        "source_artifact": dat_path.name,
                    }
                )
                rows_written += 1
            scan_summaries.append(
                {
                    "artifact_filename": dat_path.name,
                    "sha256": assessment.sha256,
                    "scan_role": role,
                    "source_name": provenance["source_name"],
                    "hit_count": len(source_rows),
                }
            )

    sidecar = destination.with_name(destination.name + ".provenance.json")
    sidecar.write_text(
        json.dumps(
            {
                "schema_version": CADENCE_DERIVATION_SCHEMA_VERSION,
                "artifact_filename": destination.name,
                "sha256": sha256_file(destination),
                "classification": "derived_real_observation_cadence",
                "cadence_id": cadence_id,
                "target_id": target_name,
                "scan_count": len(scan_summaries),
                "row_count": rows_written,
                "source_artifacts": scan_summaries,
                "external_submission_authorized": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "cadence_csv": str(destination),
        "cadence_sha256": sha256_file(destination),
        "row_count": rows_written,
        "scan_summaries": scan_summaries,
    }


def cadence_candidate_context(path: Path) -> tuple[tuple[str, ...], dict[str, Any]]:
    sidecar = path.with_name(path.name + ".provenance.json")
    if not sidecar.exists():
        return retained_archive_candidate_context(path)
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return (), {}
    if payload.get("schema_version") == OBSERVATION_ARTIFACT_SCHEMA_VERSION:
        assessment = assess_observation_artifact(path)
        if not assessment.approved_for_pipeline:
            raise ValueError(
                "Observation provenance sidecar failed admission: "
                + "; ".join(assessment.issues)
            )
        return (
            (str(payload["artifact_filename"]),),
            {
                "source_dataset": str(payload["source_archive"]),
                "source_url": str(payload["source_url"]),
                "input_sha256": assessment.sha256,
                "classification": "derived_real_observation_hit_table",
                "instrument": str(payload["instrument"]),
                "source_hdf5_filename": str(payload.get("source_hdf5_filename", "")),
                "source_hdf5_sha256": str(payload.get("source_hdf5_sha256", "")),
                "provenance_limitation": str(payload.get("provenance_limitation", "")),
                "processing_tool": str(payload.get("processing_tool", "")),
                "processing_tool_version": str(
                    payload.get("processing_tool_version", "")
                ),
                "processing_snr_threshold": float(
                    _mapping(payload.get("processing_parameters", {})).get(
                        "snr_threshold", 0.0
                    )
                ),
                "external_submission_authorized": False,
            },
        )
    if payload.get("schema_version") != CADENCE_DERIVATION_SCHEMA_VERSION:
        raise ValueError("Observation provenance sidecar has an unsupported schema version.")
    if payload.get("artifact_filename") != path.name:
        raise ValueError("Cadence provenance artifact_filename does not match the input.")
    if payload.get("sha256") != sha256_file(path):
        raise ValueError("Cadence provenance SHA-256 does not match the input.")
    if payload.get("external_submission_authorized") is not False:
        raise ValueError("Cadence provenance must keep external submission disabled.")

    source_artifacts = payload.get("source_artifacts")
    if not isinstance(source_artifacts, list) or not source_artifacts:
        raise ValueError("Cadence provenance must name source artifacts.")
    source_ids: list[str] = []
    source_provenance: list[Mapping[str, Any]] = []
    for source in source_artifacts:
        if not isinstance(source, dict):
            raise ValueError("Cadence provenance source artifact must be a JSON object.")
        filename = str(source.get("artifact_filename", ""))
        source_path = path.parent / filename
        assessment = assess_observation_artifact(source_path)
        if not assessment.approved_for_pipeline:
            raise ValueError(f"Cadence source artifact is not approved: {filename}.")
        if assessment.sha256 != source.get("sha256"):
            raise ValueError(f"Cadence source artifact SHA-256 does not match: {filename}.")
        source_ids.append(filename)
        raw_provenance = json.loads(
            provenance_path_for(source_path).read_text(encoding="utf-8")
        )
        if not isinstance(raw_provenance, Mapping):
            raise ValueError(f"Cadence source provenance is not an object: {filename}.")
        source_provenance.append(raw_provenance)

    instruments = _consistent_values(source_provenance, "instrument")
    processing_tools = _consistent_values(source_provenance, "processing_tool")
    processing_versions = _consistent_values(
        source_provenance, "processing_tool_version"
    )
    thresholds = {
        float(_mapping(item.get("processing_parameters", {}))["snr_threshold"])
        for item in source_provenance
    }
    if len(thresholds) != 1:
        raise ValueError("Cadence source artifacts use inconsistent detector thresholds.")
    source_urls = _consistent_or_distinct_values(source_provenance, "source_url")

    provenance = {
        "source_dataset": str(payload["cadence_id"]),
        "input_sha256": str(payload["sha256"]),
        "classification": str(payload["classification"]),
        "scan_count": int(payload["scan_count"]),
        "row_count": int(payload["row_count"]),
        "instrument": instruments,
        "processing_tool": processing_tools,
        "processing_tool_version": processing_versions,
        "processing_snr_threshold": thresholds.pop(),
        "source_url": source_urls[0],
        "source_url_count": len(source_urls),
        "external_submission_authorized": False,
    }
    return tuple(source_ids), provenance


def retained_archive_candidate_context(
    path: Path,
    *,
    project_root: Path | None = None,
) -> tuple[tuple[str, ...], dict[str, Any]]:
    """Recover retained-DAT archive provenance by exact HDF5 filename.

    The committed bounded-corpus manifest is metadata evidence, not a guessed
    target-name association. Ambiguous filename matches fail loudly.
    """

    root = project_root or Path(__file__).resolve().parents[2]
    manifest_path = root / RETAINED_CORPUS_MANIFEST
    if path.suffix.lower() != ".dat" or not manifest_path.is_file():
        return (), {}
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Retained corpus manifest is not a JSON object: {manifest_path}")
    expected_hdf5 = path.with_suffix(".h5").name.casefold()
    urls = {
        str(row.get("source_hdf5_url", "")).strip()
        for row in _sequence(payload.get("targets", []))
        if Path(urlparse(str(row.get("source_hdf5_url", ""))).path).name.casefold()
        == expected_hdf5
    }
    urls.discard("")
    if not urls:
        return (), {}
    if len(urls) != 1:
        raise ValueError(
            f"Ambiguous retained archive provenance for {path.name}: {sorted(urls)}"
        )
    source_url = urls.pop()
    program_segment = next(
        (
            segment
            for segment in Path(urlparse(source_url).path).parts
            if segment.upper().startswith("AGBT")
        ),
        "",
    )
    instrument = "GBT" if program_segment else ""
    return (
        (path.name,),
        {
            "source_dataset": "Breakthrough Listen public archive",
            "source_url": source_url,
            "classification": "derived_public_archive_hit_table",
            "instrument": instrument,
            "instrument_provenance_basis": (
                "archive_program_path_prefix_AGBT" if instrument else "unresolved"
            ),
            "archive_manifest_path": str(RETAINED_CORPUS_MANIFEST),
            "archive_provenance_match": "exact_hdf5_filename",
            "external_submission_authorized": False,
        },
    )


def _mapping(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("Expected a JSON object.")
    return value


def _sequence(value: object) -> Sequence[Mapping[str, Any]]:
    if not isinstance(value, Sequence):
        raise ValueError("Expected a JSON array.")
    scans: list[Mapping[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("Expected a JSON object.")
        scans.append(item)
    return scans


def _consistent_values(rows: Sequence[Mapping[str, Any]], field: str) -> str:
    values = _consistent_or_distinct_values(rows, field)
    if len(values) != 1:
        raise ValueError(f"Cadence source artifacts use inconsistent {field} values.")
    return values[0]


def _consistent_or_distinct_values(
    rows: Sequence[Mapping[str, Any]], field: str
) -> list[str]:
    values = sorted({str(row.get(field, "")).strip() for row in rows})
    if not values or "" in values:
        raise ValueError(f"Cadence source artifacts are missing {field} provenance.")
    return values
