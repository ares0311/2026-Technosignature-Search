#!/usr/bin/env python3
"""Build a calibration corpus download manifest for GBT L-band targets.

Generates a prioritized list of Breakthrough Listen public archive targets
suitable for building the noise_threshold_calibration corpus. The manifest
is consumed by scripts/run_calibration_corpus_pipeline.sh.

Requirements from noise_threshold_calibration.py gates:
  - MINIMUM_CADENCES = 3   (3+ distinct cadence observation files)
  - MINIMUM_TARGETS  = 3   (3+ distinct stellar targets)
  - MINIMUM_EPOCHS   = 2   (2+ distinct observation dates)
  - MINIMUM_HITS     = 100 (100+ turboSETI hits across all files)
  - MAX_CADENCE_HIT_FRACTION = 0.50 (no single cadence > 50% of hits)

All targets are from the Breakthrough Listen GBT L-band survey (BL-GBT).
Primary citations:
  Enriquez et al. 2017, ApJ 849:104 — "The Breakthrough Listen Search for
    Intelligent Life: 1.1-1.9 GHz Observations of 692 Nearby Stars"
  Price et al. 2020, AJ 159:86 — "The Breakthrough Listen Search for
    Intelligent Life: Observations of 1327 Nearby Stars over 1.10-3.45 GHz"

BL archive access:
  Primary:  http://blpd0.ssl.berkeley.edu/    (self-signed cert; use HTTP)
  Mirror:   https://blpd14.ssl.berkeley.edu/  (requires --ssl-skip for Python)

File naming convention:
  guppi_{MJD_days}_{scan_number}_{TARGET_NAME}_{sub_bank}.{file_index}.h5
  e.g., guppi_57650_67573_Voyager1_0002.0000.h5

Scientific guardrail:
  This manifest is a local scheduling aid for calibration corpus assembly.
  Downloaded files are not scored candidates. Calibrated thresholds derived
  from these files require independent-method citizen-science review before
  pipeline use. No threshold derived here constitutes a detection claim.

Usage:
  .venv/bin/python scripts/build_calibration_target_manifest.py [OPTIONS]
  .venv/bin/python scripts/build_calibration_target_manifest.py --output manifest.json
  .venv/bin/python scripts/build_calibration_target_manifest.py --list-targets
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_OUTPUT = REPO_ROOT / "data" / "calibration_corpus" / "download_manifest.json"

MANIFEST_VERSION = "calibration_corpus_manifest_v1"

DISCLAIMER = (
    "Calibration corpus download manifest — local scheduling aid for assembling "
    "a real-noise corpus for scoring threshold calibration. Downloaded files are "
    "Breakthrough Listen public archive observations (BL-GBT). "
    "Calibrated thresholds derived from this corpus require independent-method "
    "citizen-science review before use in production scoring. No result from "
    "this manifest constitutes a detection claim or authorizes external submission."
)

# ---------------------------------------------------------------------------
# BL archive base URLs
# ---------------------------------------------------------------------------
BL_HTTP_BASE = "http://blpd0.ssl.berkeley.edu"
BL_HTTPS_BASE = "https://blpd14.ssl.berkeley.edu"

# ---------------------------------------------------------------------------
# Calibration target catalog
#
# Each entry specifies one or more H5 files to download from the BL archive.
# Fields per file:
#   url_http       — HTTP URL (blpd0; no cert issues)
#   url_https      — HTTPS mirror (blpd14; may need SSL skip)
#   sha256_hint    — first 8 hex chars of SHA-256 if known, else None
#   size_bytes     — expected file size, None if unknown
#   verified       — True if URL confirmed accessible, False if from paper citation only
#
# provenance_template fields become the .dat.provenance.json written by the
# run_calibration_corpus_pipeline.sh script:
#   target_id              — star identifier (HIP, HD, or common name)
#   source_name            — as it appears in the H5 header source_name field
#   target_ra_deg          — J2000 RA in decimal degrees
#   target_dec_deg         — J2000 Dec in decimal degrees
#   observation_utc_start  — ISO-8601 UTC (yyyy-mm-dd) — determines epoch_id
#   observation_mjd        — MJD (float) for epoch_id fallback
#   cadence_id             — unique cadence identifier for grouping hits
#   classification         — must be "real_observation" for admission gate
#   review_status          — "provisional" until operator approves
#   pipeline_band          — "L-band" (1.1–1.9 GHz) etc.
#   citation               — academic citation for this observation
# ---------------------------------------------------------------------------

TARGETS: list[dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # TARGET 1: Voyager 1 — ALREADY INGESTED (reference entry)
    # Source: Enriquez et al. 2017; Breakthrough Listen public archive
    # MJD 57650 = 2016-09-04 UTC
    # -----------------------------------------------------------------------
    {
        "target_id": "Voyager1",
        "priority": 0,
        "status": "already_ingested",
        "notes": (
            "Already downloaded and processed in Tier 1 milestone. "
            "Included here as reference for corpus provenance template. "
            "Do not re-download unless reprovisioning."
        ),
        "files": [
            {
                "url_http": (
                    "http://blpd0.ssl.berkeley.edu/Voyager1/blc07/"
                    "guppi_57650_67573_Voyager1_0002.0000.h5"
                ),
                "url_https": (
                    "https://blpd14.ssl.berkeley.edu/Voyager1/blc07/"
                    "guppi_57650_67573_Voyager1_0002.0000.h5"
                ),
                "sha256_hint": None,
                "size_bytes": 50_549_227,
                "verified": True,
                "output_filename": "voyager1_0002.h5",
            }
        ],
        "provenance_template": {
            "target_id": "Voyager1",
            "source_name": "Voyager1",
            "target_ra_deg": None,
            "target_dec_deg": None,
            "observation_utc_start": "2016-09-04",
            "observation_mjd": 57650.0,
            "cadence_id": "gbt-voyager1-mjd57650-blc07",
            "classification": "real_observation",
            "review_status": "approved",
            "pipeline_band": "X-band (8.4 GHz)",
            "citation": (
                "Breakthrough Listen public archive. "
                "guppi_57650_67573_Voyager1_0002.0000.h5. "
                "Voyager 1 X-band carrier, calibration reference only."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # TARGET 2: HIP 65803 (HD 117176 / 70 Virginis)
    # BL GBT L-band survey target. Host of 70 Vir b (planet, 6.9 Mjup).
    # Citation: Enriquez et al. 2017, ApJ 849:104, Table 1, ID 254
    # MJD ~57506-57519 (2016 March) first epoch; ~57890 (2017 March) second
    # Ra=13h28m, Dec=+13°47′  →  RA=202.076 Dec=+13.793
    # Archive dir: HIP65803  (BL naming convention)
    # NOTE: URL marked verified=False — confirm by listing blpd0/HIP65803/
    # -----------------------------------------------------------------------
    {
        "target_id": "HIP65803",
        "priority": 1,
        "status": "recommended_download",
        "notes": (
            "BL L-band survey target (Enriquez+2017 Table 1). "
            "Multiple cadences expected from 2016-03 and 2017-03 epochs. "
            "High stellar radial velocity (Vrad = +4.3 km/s), non-zero drift "
            "expected for genuine ETI, useful for calibration. "
            "Verify URL by listing http://blpd0.ssl.berkeley.edu/HIP65803/"
        ),
        "files": [
            {
                "url_http": (
                    "http://blpd0.ssl.berkeley.edu/HIP65803/blc07/"
                    "guppi_57519_57823_HIP65803_0002.0000.h5"
                ),
                "url_https": (
                    "https://blpd14.ssl.berkeley.edu/HIP65803/blc07/"
                    "guppi_57519_57823_HIP65803_0002.0000.h5"
                ),
                "sha256_hint": None,
                "size_bytes": None,
                "verified": False,
                "output_filename": "hip65803_epoch1.h5",
                "discovery_url": "http://blpd0.ssl.berkeley.edu/HIP65803/",
            },
            {
                "url_http": (
                    "http://blpd0.ssl.berkeley.edu/HIP65803/blc07/"
                    "guppi_57895_58203_HIP65803_0002.0000.h5"
                ),
                "url_https": (
                    "https://blpd14.ssl.berkeley.edu/HIP65803/blc07/"
                    "guppi_57895_58203_HIP65803_0002.0000.h5"
                ),
                "sha256_hint": None,
                "size_bytes": None,
                "verified": False,
                "output_filename": "hip65803_epoch2.h5",
                "discovery_url": "http://blpd0.ssl.berkeley.edu/HIP65803/",
            },
        ],
        "provenance_template": {
            "target_id": "HIP65803",
            "source_name": "HIP65803",
            "target_ra_deg": 202.076,
            "target_dec_deg": 13.793,
            "observation_utc_start": None,
            "observation_mjd": None,
            "cadence_id": None,
            "classification": "real_observation",
            "review_status": "provisional",
            "pipeline_band": "L-band (1.1–1.9 GHz)",
            "citation": (
                "Enriquez et al. 2017, ApJ 849:104, Table 1. "
                "Breakthrough Listen GBT L-band survey. "
                "70 Virginis system (HD 117176)."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # TARGET 3: HIP 4436 (4 Trianguli Australis / HD 5403)
    # BL GBT L-band survey target, southern declination, multiple epochs.
    # Citation: Price et al. 2020, AJ 159:86, BL GBT survey extension
    # RA=00h56m, Dec=−63°48′  →  RA=14.082 Dec=−63.797
    # Archive dir: HIP4436  (BL naming convention)
    # -----------------------------------------------------------------------
    {
        "target_id": "HIP4436",
        "priority": 2,
        "status": "recommended_download",
        "notes": (
            "BL GBT L-band target (Price+2020). "
            "Expected multi-epoch cadences; verify by listing "
            "http://blpd0.ssl.berkeley.edu/HIP4436/"
        ),
        "files": [
            {
                "url_http": "http://blpd0.ssl.berkeley.edu/HIP4436/blc07/",
                "url_https": "https://blpd14.ssl.berkeley.edu/HIP4436/blc07/",
                "sha256_hint": None,
                "size_bytes": None,
                "verified": False,
                "output_filename": "hip4436_epoch1.h5",
                "discovery_url": "http://blpd0.ssl.berkeley.edu/HIP4436/",
                "note": (
                    "Directory listing required to get exact filenames. "
                    "Use: curl http://blpd0.ssl.berkeley.edu/HIP4436/blc07/"
                ),
            }
        ],
        "provenance_template": {
            "target_id": "HIP4436",
            "source_name": "HIP4436",
            "target_ra_deg": 14.082,
            "target_dec_deg": -63.797,
            "observation_utc_start": None,
            "observation_mjd": None,
            "cadence_id": None,
            "classification": "real_observation",
            "review_status": "provisional",
            "pipeline_band": "L-band (1.1–1.9 GHz)",
            "citation": (
                "Price et al. 2020, AJ 159:86. "
                "Breakthrough Listen GBT survey extension. "
                "4 Trianguli Australis (HD 5403)."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # TARGET 4: tau Ceti (HIP 8102 / HD 10700)
    # Classic SETI target; 5 planetary candidates. BL observed it at L/S/C.
    # Citation: Enriquez et al. 2017, ApJ 849:104; prominent in BL survey.
    # RA=01h44m, Dec=−15°56′  →  RA=26.017 Dec=−15.938
    # -----------------------------------------------------------------------
    {
        "target_id": "HIP8102",
        "priority": 3,
        "status": "recommended_download",
        "notes": (
            "Classic SETI target; BL multi-epoch observations available. "
            "Verify by listing http://blpd0.ssl.berkeley.edu/HIP8102/ "
            "or http://blpd0.ssl.berkeley.edu/tauCeti/"
        ),
        "files": [
            {
                "url_http": "http://blpd0.ssl.berkeley.edu/HIP8102/blc07/",
                "url_https": "https://blpd14.ssl.berkeley.edu/HIP8102/blc07/",
                "sha256_hint": None,
                "size_bytes": None,
                "verified": False,
                "output_filename": "tauceti_epoch1.h5",
                "discovery_url": "http://blpd0.ssl.berkeley.edu/HIP8102/",
                "note": "Directory listing required. Try both HIP8102 and tauCeti dir names.",
            }
        ],
        "provenance_template": {
            "target_id": "HIP8102",
            "source_name": "tauCeti",
            "target_ra_deg": 26.017,
            "target_dec_deg": -15.938,
            "observation_utc_start": None,
            "observation_mjd": None,
            "cadence_id": None,
            "classification": "real_observation",
            "review_status": "provisional",
            "pipeline_band": "L-band (1.1–1.9 GHz)",
            "citation": (
                "Enriquez et al. 2017, ApJ 849:104. "
                "Breakthrough Listen GBT L-band survey. "
                "tau Ceti (HIP 8102 / HD 10700)."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # TARGET 5: epsilon Eridani (HIP 16537 / HD 22049)
    # Known debris disk and sub-stellar companion; BL high-priority target.
    # Citation: Enriquez et al. 2017, ApJ 849:104
    # RA=03h33m, Dec=−09°28′  →  RA=53.233 Dec=−9.458
    # -----------------------------------------------------------------------
    {
        "target_id": "HIP16537",
        "priority": 4,
        "status": "recommended_download",
        "notes": (
            "High-priority BL target (epsilon Eridani). "
            "Verify by listing http://blpd0.ssl.berkeley.edu/HIP16537/ "
            "or http://blpd0.ssl.berkeley.edu/epsEri/"
        ),
        "files": [
            {
                "url_http": "http://blpd0.ssl.berkeley.edu/HIP16537/blc07/",
                "url_https": "https://blpd14.ssl.berkeley.edu/HIP16537/blc07/",
                "sha256_hint": None,
                "size_bytes": None,
                "verified": False,
                "output_filename": "epseri_epoch1.h5",
                "discovery_url": "http://blpd0.ssl.berkeley.edu/HIP16537/",
                "note": "Try both HIP16537 and epsEri dir names.",
            }
        ],
        "provenance_template": {
            "target_id": "HIP16537",
            "source_name": "epsEri",
            "target_ra_deg": 53.233,
            "target_dec_deg": -9.458,
            "observation_utc_start": None,
            "observation_mjd": None,
            "cadence_id": None,
            "classification": "real_observation",
            "review_status": "provisional",
            "pipeline_band": "L-band (1.1–1.9 GHz)",
            "citation": (
                "Enriquez et al. 2017, ApJ 849:104. "
                "Breakthrough Listen GBT L-band survey. "
                "epsilon Eridani (HIP 16537 / HD 22049)."
            ),
        },
    },
]


# ---------------------------------------------------------------------------
# Archive discovery helpers
# ---------------------------------------------------------------------------

ARCHIVE_DISCOVERY_INSTRUCTIONS = """
To discover actual filenames in the BL archive for a given target:

1. List the target directory:
   curl -s "http://blpd0.ssl.berkeley.edu/{TARGET_NAME}/" | grep -oP 'blc[0-9]+' | sort -u
   # → shows available compute nodes (blc07, blc17, etc.)

2. List files in a node directory:
   curl -s "http://blpd0.ssl.berkeley.edu/{TARGET_NAME}/blc07/" | grep -oP 'guppi_[^"]+\\.h5'
   # → shows available H5 files with MJD, scan, and sub-bank info

3. Get the MJD and epoch from the filename:
   guppi_{MJD_days}_{scan_number}_{TARGET}_{subband}.{index}.h5
   Example: guppi_57650_67573_Voyager1_0002.0000.h5
   → MJD 57650 = 2016-09-04 UTC (epoch_id: "2016-09-04")

4. For calibration corpus, select files that satisfy:
   - At least 3 different {TARGET_NAME} directories
   - At least 2 different MJD day values (different epochs)
   - Expect ~10-100+ turboSETI hits per L-band file (RFI-rich environment)
"""


def build_manifest() -> dict[str, Any]:
    """Return the full download manifest as a dict."""
    ready_count = sum(1 for t in TARGETS if t["status"] == "recommended_download")
    already_done = sum(1 for t in TARGETS if t["status"] == "already_ingested")
    return {
        "manifest_version": MANIFEST_VERSION,
        "disclaimer": DISCLAIMER,
        "calibration_gates_to_pass": {
            "minimum_cadences": 3,
            "minimum_targets": 3,
            "minimum_epochs": 2,
            "minimum_hits": 100,
            "max_cadence_hit_fraction": 0.50,
        },
        "targets_total": len(TARGETS),
        "targets_already_ingested": already_done,
        "targets_recommended_download": ready_count,
        "archive_base_url_http": BL_HTTP_BASE,
        "archive_base_url_https": BL_HTTPS_BASE,
        "archive_discovery_instructions": ARCHIVE_DISCOVERY_INSTRUCTIONS,
        "targets": TARGETS,
    }


def print_summary(manifest: dict[str, Any]) -> None:
    print("=== Calibration Corpus Download Manifest ===")
    print()
    print(f"Targets total           : {manifest['targets_total']}")
    print(f"Already ingested        : {manifest['targets_already_ingested']}")
    print(f"Recommended download    : {manifest['targets_recommended_download']}")
    print()
    print("Calibration gates to pass:")
    for gate, val in manifest["calibration_gates_to_pass"].items():
        print(f"  {gate:<35}: {val}")
    print()
    print("Priority download order:")
    for t in sorted(manifest["targets"], key=lambda x: x["priority"]):
        status = t["status"]
        n_files = len(t["files"])
        print(f"  [{t['priority']}] {t['target_id']:<20} {status:<30} ({n_files} file(s))")
        print(f"      {t['notes'][:80]}...")
    print()
    print("Archive discovery instructions:")
    print(manifest["archive_discovery_instructions"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument("--list-targets", action="store_true", help="Print summary and exit")
    args = parser.parse_args(argv)

    manifest = build_manifest()

    if args.list_targets:
        print_summary(manifest)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"Calibration manifest written: {args.output}")
    print_summary(manifest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
