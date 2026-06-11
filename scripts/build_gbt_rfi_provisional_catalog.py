#!/usr/bin/env python3
"""Build GBT provisional RFI catalog from publicly-documented frequency allocations.

This script generates a provisional site-specific RFI catalog for Green Bank
Telescope (GBT / NRAO) based on publicly-documented frequency allocations from
ITU Radio Regulations, IS-GPS-200, GLONASS ICD, ICAO Annex 10, and FCC Part 27.

All entries are marked:
  - synthetic: false  (based on published public regulatory documents)
  - review_status: "provisional"  (pending operator sign-off)
  - active: false  (inactive until human review approves each entry)

Scientific guardrail: This catalog is a local false-positive screening aid only.
It does not calibrate scoring thresholds, constitute a detection claim, or
authorize external submission.

Usage:
    .venv/bin/python scripts/build_gbt_rfi_provisional_catalog.py [--output PATH]

Output:
    tests/fixtures/rfi_catalog/gbt_rfi_provisional_v1.json (default)

Admission gate:
    tests/fixtures/rfi_database_admission.json entry "rfi-admit-gbt-provisional-v1"
    is blocked_pending_review until a human operator reviews each entry and
    updates the admission record to ready_for_local_fixture.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

DEFAULT_OUTPUT = (
    REPO_ROOT / "tests" / "fixtures" / "rfi_catalog" / "gbt_rfi_provisional_v1.json"
)

CATALOG_VERSION = "gbt_rfi_provisional_v1"
SITE_ID = "gbt-provisional-v1"
SITE_NAME = "Green Bank Telescope, NRAO (provisional public-documentation catalog)"

DISCLAIMER = (
    "GBT provisional RFI catalog built from publicly-documented frequency "
    "allocations (ITU Radio Regulations, IS-GPS-200, GLONASS ICD, ICAO Annex 10, "
    "FCC CFR Title 47). All entries are provisional and inactive (active=false) "
    "until a human operator reviews each entry and approves the catalog via the "
    "rfi_database_admission.json gate. This catalog is a local false-positive "
    "screening aid only. It does not calibrate scoring thresholds, constitute a "
    "detection claim, or authorize external submission."
)

# ---------------------------------------------------------------------------
# Provisional catalog entries — sorted by frequency_low_hz
# Each entry cites the authoritative public document(s) that establish the band.
# ---------------------------------------------------------------------------
_ENTRIES: list[dict[str, Any]] = [
    {
        "entry_id": "rfi-gbt-prov-0001",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 698_000_000.0,
        "frequency_high_hz": 787_000_000.0,
        "source_class": "unknown",
        "confidence": 0.60,
        "review_status": "provisional",
        "provenance": (
            "FCC 47 CFR Part 27, Table of Frequency Allocations §2.106. "
            "700 MHz cellular uplink/downlink (bands 12, 13, 17). "
            "NRQZ excludes most transmitters, but out-of-zone leakage is documented "
            "in NRAO RFI monitoring reports."
        ),
        "notes": "Wide band; individual sub-bands may be relevant. Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0002",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 960_000_000.0,
        "frequency_high_hz": 1_215_000_000.0,
        "source_class": "aircraft",
        "confidence": 0.75,
        "review_status": "provisional",
        "provenance": (
            "ICAO Annex 10 Volume I Chapter 3; FCC 47 CFR Part 87. "
            "DME (Distance Measuring Equipment) aeronautical navigation band. "
            "Aircraft interrogate ground stations on 962–1213 MHz; replies on "
            "1025–1150 MHz. Both directions present near GBT flight paths."
        ),
        "notes": "Wide band covering DME interrogation and reply. Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0003",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_029_500_000.0,
        "frequency_high_hz": 1_030_500_000.0,
        "source_class": "aircraft",
        "confidence": 0.90,
        "review_status": "provisional",
        "provenance": (
            "ICAO Annex 10 Volume III Part I §3.1.2.6.7.1; Doc 9684 §3.8. "
            "Secondary Surveillance Radar (SSR) / Mode S interrogation at 1030 MHz. "
            "Ground-based SSR interrogators broadcast at 1030 MHz; aircraft "
            "transponders reply at 1090 MHz (see ADS-B entry). Persistent near airports."
        ),
        "notes": "SSR interrogation carrier at 1030 MHz. Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0004",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_089_000_000.0,
        "frequency_high_hz": 1_091_000_000.0,
        "source_class": "aircraft",
        "confidence": 0.97,
        "review_status": "provisional",
        "provenance": (
            "ICAO Annex 10 Volume III Part I §3.1.2.8 (ADS-B); Doc 9684 §2.3. "
            "ADS-B (Automatic Dependent Surveillance-Broadcast) transponders "
            "transmit at 1090 MHz ±500 kHz. All commercial and most general-aviation "
            "aircraft broadcast continuously. GBT is near WV/VA/MD air corridors."
        ),
        "notes": "Strongest aircraft RFI source in L-band. Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0005",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_175_427_000.0,
        "frequency_high_hz": 1_177_473_000.0,
        "source_class": "satellite",
        "confidence": 0.98,
        "review_status": "provisional",
        "provenance": (
            "IS-GPS-200L §3.3.1.5 (NAVCEN public document, ICD-GPS-200). "
            "GPS L5 signal: center 1176.45 MHz, BPSK(10) chip rate 10.23 Mcps, "
            "null-to-null bandwidth ±10.23 MHz (±1.023 MHz for main lobe). "
            "Galileo E5a at same center; BeiDou B2a nearby (1176.45 MHz)."
        ),
        "notes": "GPS/Galileo/BeiDou L5/E5a band. Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0006",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_215_000_000.0,
        "frequency_high_hz": 1_300_000_000.0,
        "source_class": "satellite",
        "confidence": 0.70,
        "review_status": "provisional",
        "provenance": (
            "ITU Radio Regulations Article 5 §5.329 (radionavigation satellite service); "
            "FCC Table of Frequency Allocations §2.106. "
            "L-band EESS (Earth-Exploration Satellite Service) and radiolocation radars "
            "1215–1300 MHz. Includes GPS L2 (1227.6 MHz) region. Also used by "
            "airborne weather radar and various military systems."
        ),
        "notes": "Broad allocation; GPS L2 entry below is more specific. Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0007",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_226_577_000.0,
        "frequency_high_hz": 1_228_623_000.0,
        "source_class": "satellite",
        "confidence": 0.99,
        "review_status": "provisional",
        "provenance": (
            "IS-GPS-200L §3.3.1.2 (NAVCEN public document, ICD-GPS-200). "
            "GPS L2 signal: center 1227.60 MHz, BPSK(1) and BPSK(10) modulation, "
            "main lobe null-to-null bandwidth ±1.023 MHz (BPSK(1)). "
            "GLONASS L2 band 1242–1249 MHz is adjacent (see rfi-gbt-prov-0009)."
        ),
        "notes": "GPS L2 main lobe. Adjacent to GLONASS L2. Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0008",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_242_937_500.0,
        "frequency_high_hz": 1_248_625_000.0,
        "source_class": "satellite",
        "confidence": 0.95,
        "review_status": "provisional",
        "provenance": (
            "GLONASS ICD v5.1 §3.3 (Russian Space Agency, public document). "
            "GLONASS L2 frequency band: f_k = 1246 MHz + k*0.4375 MHz, k = -7..+6. "
            "Lowest channel k=-7: 1242.9375 MHz. Highest k=+6: 1248.625 MHz. "
            "All 24 operational GLONASS satellites transmit continuously."
        ),
        "notes": "GLONASS L2 channel band (all 24 satellites). Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0009",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_525_000_000.0,
        "frequency_high_hz": 1_559_000_000.0,
        "source_class": "satellite",
        "confidence": 0.90,
        "review_status": "provisional",
        "provenance": (
            "ITU Radio Regulations Article 5 §5.357A; FCC §2.106 and Part 25. "
            "L-band Mobile Satellite Service (MSS) downlink allocation 1525–1559 MHz. "
            "Includes Inmarsat (1530–1545 MHz), LightSquared/Ligado, and other MSS "
            "operators. Strong broadband emitters; documented in NRAO RFI monitoring."
        ),
        "notes": "MSS downlink band; Inmarsat dominant. Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0010",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_559_000_000.0,
        "frequency_high_hz": 1_610_000_000.0,
        "source_class": "satellite",
        "confidence": 0.85,
        "review_status": "provisional",
        "provenance": (
            "ITU Radio Regulations §5.328A; IS-GPS-200L; Galileo OS SIS ICD v1.3 "
            "(European GNSS Agency, public document). "
            "RNSS (Radionavigation Satellite Service) allocation 1559–1610 MHz. "
            "Contains GPS L1 (1575.42 MHz), Galileo E1 (1575.42 MHz), "
            "BeiDou B1C (1575.42 MHz), SBAS/WAAS (1575.42 MHz), GLONASS L1 "
            "(1598–1606 MHz), and the protected radio astronomy band upper edge."
        ),
        "notes": (
            "RNSS band; GPS L1 and GLONASS L1 entries below are more specific. "
            "Inactive pending review."
        ),
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0011",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_574_397_000.0,
        "frequency_high_hz": 1_576_443_000.0,
        "source_class": "satellite",
        "confidence": 0.99,
        "review_status": "provisional",
        "provenance": (
            "IS-GPS-200L §3.3.1.1 (NAVCEN public document, ICD-GPS-200). "
            "GPS L1 C/A signal: center 1575.42 MHz, BPSK(1) chip rate 1.023 Mcps, "
            "main lobe null-to-null bandwidth ±1.023 MHz. "
            "Also Galileo E1 OS (1575.42 MHz), BeiDou B1C (1575.42 MHz), "
            "SBAS (WAAS/EGNOS) at same center. Strongest GNSS emission at GBT."
        ),
        "notes": "GPS/Galileo/BeiDou L1/E1/B1C main lobe. Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0012",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_598_062_500.0,
        "frequency_high_hz": 1_605_375_000.0,
        "source_class": "satellite",
        "confidence": 0.97,
        "review_status": "provisional",
        "provenance": (
            "GLONASS ICD v5.1 §3.3 (Russian Space Agency, public document). "
            "GLONASS L1 frequency band: f_k = 1602 MHz + k*0.5625 MHz, k = -7..+6. "
            "Lowest channel k=-7: 1598.0625 MHz. Highest k=+6: 1605.375 MHz. "
            "All 24 operational GLONASS satellites transmit continuously."
        ),
        "notes": "GLONASS L1 channel band (all 24 satellites). Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0013",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_616_000_000.0,
        "frequency_high_hz": 1_626_500_000.0,
        "source_class": "satellite",
        "confidence": 0.96,
        "review_status": "provisional",
        "provenance": (
            "ITU Radio Regulations Appendix 30B; Iridium FCC license SAT-LOA-19920312-00002. "
            "Iridium satellite phone uplink/downlink: 1616.0–1626.5 MHz. "
            "66 active LEO satellites; continuous coverage; documented as strong "
            "broadband L-band emitter in SETI/radio astronomy RFI literature including "
            "GBT observations (Siemion et al. 2013, ApJ 767:94)."
        ),
        "notes": "Iridium FDMA channels; strong and ubiquitous. Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0014",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 1_626_500_000.0,
        "frequency_high_hz": 1_660_500_000.0,
        "source_class": "satellite",
        "confidence": 0.85,
        "review_status": "provisional",
        "provenance": (
            "ITU Radio Regulations Article 5 §5.357A; FCC §2.106 and Part 25. "
            "L-band MSS uplink allocation 1626.5–1660.5 MHz. "
            "Includes Inmarsat uplink (1626.5–1660.5 MHz), Iridium uplink continuation, "
            "and EPIRB (Emergency Position-Indicating Radio Beacon) sub-bands."
        ),
        "notes": "MSS uplink band; adjacent to Iridium at 1626.5 MHz. Inactive pending review.",
        "active": False,
        "synthetic": False,
    },
    {
        "entry_id": "rfi-gbt-prov-0015",
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "frequency_low_hz": 2_400_000_000.0,
        "frequency_high_hz": 2_500_000_000.0,
        "source_class": "observatory_local",
        "confidence": 0.70,
        "review_status": "provisional",
        "provenance": (
            "ITU Radio Regulations §5.150; FCC 47 CFR Part 15 §15.247. "
            "2.4 GHz ISM (Industrial, Scientific, and Medical) band. "
            "WiFi 802.11b/g/n (channels 1–13), Bluetooth, microwave ovens. "
            "NRQZ partially restricts use near GBT, but visitor center and "
            "staff facilities produce documented leakage. "
            "Confirmed in GBT RFI monitoring at https://www.gb.nrao.edu/~fghigo/gbtdoc/rfi.html"
        ),
        "notes": (
            "2.4 GHz WiFi/ISM; confirmed at GBT per NRAO public documentation. "
            "Inactive pending review."
        ),
        "active": False,
        "synthetic": False,
    },
]


def build_catalog() -> dict[str, Any]:
    """Return the full provisional catalog as a dict."""
    return {
        "catalog_version": CATALOG_VERSION,
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "disclaimer": DISCLAIMER,
        "entry_count": len(_ENTRIES),
        "rfi_database_entries": _ENTRIES,
    }


def validate_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    """Run basic schema validation and return issues."""
    from techno_search.rfi_database import (
        ALLOWED_RFI_REVIEW_STATUSES,
        ALLOWED_RFI_SOURCE_CLASSES,
        RfiDatabaseRecord,
    )

    issues: list[str] = []
    for entry in catalog.get("rfi_database_entries", []):
        eid = entry.get("entry_id", "?")
        prefix = f"{eid}: "
        # Check source_class
        if entry.get("source_class") not in ALLOWED_RFI_SOURCE_CLASSES:
            issues.append(prefix + f"invalid source_class {entry.get('source_class')!r}")
        # Check review_status
        if entry.get("review_status") not in ALLOWED_RFI_REVIEW_STATUSES:
            issues.append(prefix + f"invalid review_status {entry.get('review_status')!r}")
        # Check frequencies
        low = entry.get("frequency_low_hz", 0.0)
        high = entry.get("frequency_high_hz", 0.0)
        if not isinstance(low, float) or low <= 0.0:
            issues.append(prefix + "frequency_low_hz must be a positive float")
        if not isinstance(high, float) or high <= low:
            issues.append(prefix + "frequency_high_hz must exceed frequency_low_hz")
        # Check confidence
        conf = entry.get("confidence", -1.0)
        if not (0.0 <= conf <= 1.0):
            issues.append(prefix + f"confidence {conf!r} out of range 0..1")
        # Check provenance
        if not str(entry.get("provenance", "")).strip():
            issues.append(prefix + "provenance is required")
        # Check synthetic flag matches expectation
        if entry.get("synthetic", True):
            issues.append(prefix + "synthetic should be False for public-documentation catalog")
        # Check active flag
        if entry.get("active", True):
            issues.append(prefix + "active should be False (inactive until reviewed)")
        # Round-trip through dataclass
        try:
            rec = RfiDatabaseRecord(
                entry_id=str(entry["entry_id"]),
                site_id=str(entry["site_id"]),
                site_name=str(entry["site_name"]),
                frequency_low_hz=float(entry["frequency_low_hz"]),
                frequency_high_hz=float(entry["frequency_high_hz"]),
                source_class=str(entry["source_class"]),
                confidence=float(entry["confidence"]),
                review_status=str(entry["review_status"]),
                provenance=str(entry["provenance"]),
                notes=str(entry.get("notes", "")),
                active=bool(entry.get("active", False)),
                synthetic=bool(entry.get("synthetic", False)),
            )
            _ = rec.as_dict()
        except (KeyError, TypeError, ValueError) as exc:
            issues.append(prefix + f"dataclass construction failed: {exc}")

    return {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate catalog without writing output file",
    )
    args = parser.parse_args(argv)

    catalog = build_catalog()
    validation = validate_catalog(catalog)

    if not validation["ok"]:
        print("ERROR: catalog validation failed:", file=sys.stderr)
        for issue in validation["issues"]:
            print(f"  {issue}", file=sys.stderr)
        return 1

    if args.validate_only:
        print(f"Catalog validation OK: {catalog['entry_count']} entries, no issues.")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")

    print(f"GBT provisional RFI catalog written: {args.output}")
    print(f"  Site: {catalog['site_name']}")
    print(f"  Entries: {catalog['entry_count']}")
    print()
    print("ALL ENTRIES are marked active=false and review_status='provisional'.")
    print("Remaining steps before production use:")
    print("  1. Review each entry for frequency accuracy and GBT site relevance.")
    print("  2. For each confirmed entry: set active=true, review_status='reviewed'.")
    print("  3. Update tests/fixtures/rfi_database_admission.json entry")
    print("     'rfi-admit-gbt-provisional-v1' to admission_status='ready_for_local_fixture'")
    print("     and real_data_authorized=false (real authorization requires external review).")
    print("  4. Merge approved entries into tests/fixtures/rfi_database.json.")
    print()
    print(f"  {DISCLAIMER[:120]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
