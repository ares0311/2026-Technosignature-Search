#!/usr/bin/env python3
"""Write a .dat.provenance.json sidecar for a turboSETI hit table.

This script creates the provenance sidecar required by the
noise_threshold_calibration admission gate before a real-observation
.dat file can be admitted to the calibration corpus.

Required fields documented in src/techno_search/observation_artifact.py.
The caller must supply all scientifically meaningful fields — this script
only constructs and validates the sidecar; it does not modify scores.

Scientific guardrail:
  Provenance sidecars are admissibility records only. Writing a sidecar
  does not modify candidate scores, authorize external submission, or
  constitute a detection claim. Human approval fields must be set to
  "approved" by the operator who reviewed the observation.

Usage:
  .venv/bin/python scripts/write_calibration_provenance.py \\
      --dat-file data/calibration_corpus/hip65803_epoch1.dat \\
      --target-id HIP65803 \\
      --cadence-id gbt-HIP65803-mjd57519-blc07 \\
      --epoch-utc 2016-04-05 \\
      --source-url https://blpd14.ssl.berkeley.edu/HIP65803/blc07/
          guppi_57519_57823_HIP65803_0002.0000.h5 \\
      --instrument "GBT L-band (1.1-1.9 GHz)" \\
      --observation-mjd 57519.0

  # Dry-run: print what would be written without creating the file
  .venv/bin/python scripts/write_calibration_provenance.py \\
      --dat-file data/calibration_corpus/hip65803_epoch1.dat \\
      --dry-run
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

SCHEMA_VERSION = "observation_artifact_provenance_v1"

DISCLAIMER = (
    "This provenance sidecar is an admissibility record for local calibration "
    "corpus use only. It does not modify scoring thresholds, authorize external "
    "submission, or constitute a detection claim. Human approval is required "
    "before the calibration gate will admit this file."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_dat_headers(path: Path) -> dict[str, str]:
    """Read # KEY: VALUE headers from a turboSETI .dat file."""
    headers: dict[str, str] = {}
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip()
                if not line.startswith("#"):
                    break
                if ":" in line:
                    key, _, value = line[1:].partition(":")
                    headers[key.strip()] = value.strip()
    except OSError:
        pass
    return headers


def build_provenance(
    dat_path: Path,
    *,
    target_id: str,
    cadence_id: str,
    epoch_utc: str,
    source_url: str,
    instrument: str,
    observation_mjd: float | None,
    source_archive: str,
    citation: str,
    operator_notes: str,
    human_approved: bool,
) -> dict:
    sha256 = sha256_file(dat_path)
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: UP017

    approval_status = "approved" if human_approved else "pending"

    return {
        "schema_version": SCHEMA_VERSION,
        "disclaimer": DISCLAIMER,
        "artifact_filename": dat_path.name,
        "sha256": sha256,
        "classification": "real_observation",
        "target_id": target_id,
        "cadence_id": cadence_id,
        "observation_utc_start": epoch_utc,
        "observation_mjd": observation_mjd,
        "source_url": source_url,
        "source_archive": source_archive,
        "instrument": instrument,
        "citation": citation,
        "downloaded_utc": now_utc,
        "operator_notes": operator_notes,
        "data_use_review_status": approval_status,
        "provenance_review_status": approval_status,
        "human_approval_status": approval_status,
        "approved_for_local_real_data": human_approved,
        "external_submission_authorized": False,
    }


def validate_provenance(record: dict) -> list[str]:
    """Return a list of issues; empty means the record will pass the gate."""
    issues: list[str] = []
    required_str = [
        "artifact_filename", "sha256", "source_url", "source_archive",
        "instrument", "downloaded_utc",
    ]
    for field in required_str:
        if not str(record.get(field, "")).strip():
            issues.append(f"Missing required field: {field}")

    if record.get("classification") != "real_observation":
        issues.append("classification must be 'real_observation'")
    if record.get("human_approval_status") != "approved":
        issues.append("human_approval_status must be 'approved' — set --approved flag")
    if record.get("data_use_review_status") != "approved":
        issues.append("data_use_review_status not approved")
    if record.get("provenance_review_status") != "approved":
        issues.append("provenance_review_status not approved")
    if record.get("approved_for_local_real_data") is not True:
        issues.append("approved_for_local_real_data must be true")
    if record.get("external_submission_authorized") is not False:
        issues.append("external_submission_authorized must be false")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.strip().split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dat-file", required=True, type=Path,
        help="Path to the .dat turboSETI hit table file."
    )
    parser.add_argument(
        "--target-id", default="",
        help="Star identifier (e.g. HIP65803). Defaults to dat filename stem."
    )
    parser.add_argument(
        "--cadence-id", default="",
        help="Unique cadence ID (e.g. gbt-HIP65803-mjd57519-blc07). "
             "Defaults to dat filename stem."
    )
    parser.add_argument(
        "--epoch-utc", default="",
        help="Observation date ISO-8601 (YYYY-MM-DD). Determines epoch_id."
    )
    parser.add_argument(
        "--observation-mjd", type=float, default=None,
        help="MJD of observation (float). Used as epoch_id fallback if --epoch-utc absent."
    )
    parser.add_argument(
        "--source-url", default="",
        help="HTTPS URL of the source H5 file on the BL archive."
    )
    parser.add_argument(
        "--instrument", default="GBT L-band (1.1-1.9 GHz)",
        help="Instrument description."
    )
    parser.add_argument(
        "--source-archive", default="Breakthrough Listen Open Data Archive",
        help="Human-readable archive name."
    )
    parser.add_argument(
        "--citation", default="",
        help="Academic citation for this observation (e.g. Enriquez et al. 2017)."
    )
    parser.add_argument(
        "--notes", default="",
        help="Operator notes about this observation."
    )
    parser.add_argument(
        "--approved", action="store_true",
        help="Mark this record as human-approved (sets all review statuses to 'approved'). "
             "Only set this flag after reviewing the observation for local calibration use."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be written without creating the sidecar file."
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite an existing sidecar without prompting."
    )
    args = parser.parse_args(argv)

    dat_path = Path(args.dat_file).resolve()
    if not dat_path.is_file():
        print(f"ERROR: .dat file not found: {dat_path}", file=sys.stderr)
        return 1

    # Auto-read turboSETI header fields (# Source:, # MJD:, # RA:, # DEC:)
    dat_headers = read_dat_headers(dat_path)
    header_source = dat_headers.get("Source", "").strip()
    header_mjd_str = dat_headers.get("MJD", "").strip()

    # target_id: CLI arg > header Source > filename stem
    target_id = args.target_id or header_source or dat_path.stem
    # cadence_id: CLI arg > derive from target + survey tag
    if args.cadence_id:
        cadence_id = args.cadence_id
    elif header_source:
        cadence_id = f"{header_source}-lband-survey"
    else:
        cadence_id = dat_path.stem

    # Extract MJD: CLI arg > guppi filename convention > header MJD
    mjd = args.observation_mjd
    if mjd is None:
        parts = dat_path.stem.split("_")
        if len(parts) >= 2 and parts[0].lower() in ("guppi",):
            with contextlib.suppress(ValueError):
                mjd = float(parts[1])
    if mjd is None and header_mjd_str:
        with contextlib.suppress(ValueError):
            mjd = float(header_mjd_str.split()[0])

    # Derive epoch_utc from MJD if not supplied
    epoch_utc = args.epoch_utc
    if not epoch_utc and mjd is not None:
        # MJD 51544.5 = 2000-01-01T12:00Z (J2000)
        # Simple integer-day conversion (accurate to ±1 day for provenance)
        jd = mjd + 2400000.5
        # Julian Day Number → calendar date (Meeus algorithm)
        jd_int = int(jd + 0.5)
        a = jd_int + 32044
        b = (4 * a + 3) // 146097
        c = a - (146097 * b) // 4
        d = (4 * c + 3) // 1461
        e = c - (1461 * d) // 4
        m = (5 * e + 2) // 153
        day = e - (153 * m + 2) // 5 + 1
        month = m + 3 - 12 * (m // 10)
        year = 100 * b + d - 4800 + m // 10
        epoch_utc = f"{year:04d}-{month:02d}-{day:02d}"

    source_url = args.source_url
    # Auto-derive source_url for L_band_table files when not supplied
    if not source_url and header_source:
        source_url = (
            f"https://blpd0.ssl.berkeley.edu/L_band_table/{header_source}_hits.dat"
        )
        print(f"[INFO] Auto-derived source_url from header: {source_url}")
    # Ensure HTTPS
    if source_url.startswith("http://"):
        source_url = "https://" + source_url[7:]
        print(f"[INFO] Converted source_url to HTTPS: {source_url}")

    record = build_provenance(
        dat_path,
        target_id=target_id,
        cadence_id=cadence_id,
        epoch_utc=epoch_utc,
        source_url=source_url,
        instrument=args.instrument,
        observation_mjd=mjd,
        source_archive=args.source_archive,
        citation=args.citation,
        operator_notes=args.notes,
        human_approved=args.approved,
    )

    issues = validate_provenance(record)
    sidecar_path = dat_path.with_name(dat_path.name + ".provenance.json")

    if args.dry_run:
        print("=== DRY RUN — would write sidecar ===")
        print(f"  Target  : {sidecar_path}")
        print(f"  SHA-256 : {record['sha256']}")
        print()
        print(json.dumps(record, indent=2))
        print()
        if issues:
            print(f"VALIDATION ISSUES ({len(issues)}) — gate will NOT admit this file:")
            for issue in issues:
                print(f"  - {issue}")
            print()
            print("Fix issues before removing --dry-run. "
                  "Add --approved after reviewing the observation.")
        else:
            print("Validation: PASS — gate will admit this file.")
        return 0

    if sidecar_path.exists() and not args.force:
        print(f"ERROR: Sidecar already exists: {sidecar_path}", file=sys.stderr)
        print("Use --force to overwrite.", file=sys.stderr)
        return 1

    sidecar_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Sidecar written: {sidecar_path}")
    print(f"  Target   : {record['target_id']}")
    print(f"  Cadence  : {record['cadence_id']}")
    print(f"  Epoch    : {record['observation_utc_start']}")
    print(f"  SHA-256  : {record['sha256']}")
    print(f"  Approved : {record['human_approval_status']}")
    print()

    if issues:
        print(f"WARNING: {len(issues)} validation issue(s) — gate will NOT admit this file:")
        for issue in issues:
            print(f"  - {issue}")
        print()
        print("The sidecar was written but needs correction before the calibration "
              "gate will admit it. Add --approved (and --force) after review.")
        return 1

    print("Validation: PASS — calibration gate will admit this file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
