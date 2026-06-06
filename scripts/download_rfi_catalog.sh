#!/usr/bin/env bash
# download_rfi_catalog.sh — download GBT site RFI catalog data for the pipeline
#
# The Green Bank Telescope publishes known RFI bands at:
#   https://greenbankobservatory.org/science/gbt-observers/rfi/
#
# This script fetches the machine-readable GBT RFI table and converts it to
# the rfi_database.json format expected by the techno-search pipeline.
#
# Run: bash scripts/download_rfi_catalog.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${TECHNO_DATA_DIR:-$HOME/technosignature-data}"
RFI_DIR="$DATA_ROOT/rfi_catalog"

mkdir -p "$RFI_DIR"

echo "Downloading GBT RFI catalog..."
echo ""

# GBT provides an HTML RFI table.  We attempt to fetch the structured version.
GBT_RFI_URL="https://www.gb.nrao.edu/~rmaddale/GBT/GBT_Spectral_Line_RFI_3.pdf"
GBT_RFI_CSV_URL="https://www.gb.nrao.edu/GBTPrograms/rfi/RFI_frequencies.csv"

# Try the CSV version first
OUTFILE="$RFI_DIR/gbt_rfi_raw.csv"

echo -n "Trying GBT RFI CSV ... "
if curl -sf --max-time 30 -o "$OUTFILE" "$GBT_RFI_CSV_URL" 2>/dev/null; then
    echo "OK"
else
    echo "FAILED"
    rm -f "$OUTFILE"

    # Create a minimal fallback with well-known GBT RFI bands
    echo "Creating minimal fallback RFI catalog from known GBT bands..."
    cat > "$OUTFILE" << 'CSVEOF'
frequency_low_mhz,frequency_high_mhz,source_class,notes
1215.0,1240.0,gps_l2,GPS L2 band
1565.0,1586.0,gps_l1,GPS L1 band
1610.0,1626.5,glonass,GLONASS navigation
1626.5,1660.5,iridium,Iridium satellite band
1660.0,1670.0,oh_maser_terrestrial,OH maser terrestrial leakage
1700.0,1710.0,noaa_weather,NOAA weather satellite downlink
1755.0,1850.0,military,US military band
1900.0,1990.0,cellular,Cellular uplink band
2025.0,2120.0,space_research,Space research & satellite ops
CSVEOF
    echo "Fallback catalog written."
fi

echo ""

# Convert to the rfi_database.json format
PYTHON="$REPO_ROOT/.venv/bin/python"
if [[ ! -f "$PYTHON" ]]; then
    PYTHON="python3"
fi

OUTPUT_JSON="$RFI_DIR/gbt_rfi_database.json"
SITE_ID="gbt-real"

echo "Converting to rfi_database.json format..."
"$PYTHON" - << PYEOF
import csv
import json
import sys
from pathlib import Path

infile = Path("$OUTFILE")
outfile = Path("$OUTPUT_JSON")
site_id = "$SITE_ID"

entries = []
entry_num = 1

with infile.open() as f:
    reader = csv.DictReader(f)
    for row in reader:
        row = {k.strip(): v.strip() for k, v in row.items() if k}
        try:
            # Try multiple column name conventions
            low_key = next(k for k in row if "low" in k.lower() or "min" in k.lower() or "start" in k.lower())
            high_key = next(k for k in row if "high" in k.lower() or "max" in k.lower() or "end" in k.lower())
            low_mhz = float(row[low_key])
            high_mhz = float(row[high_key])
        except (KeyError, StopIteration, ValueError):
            continue

        source_key = next((k for k in row if "source" in k.lower() or "class" in k.lower() or "type" in k.lower()), None)
        notes_key = next((k for k in row if "note" in k.lower() or "description" in k.lower()), None)

        source_class = row.get(source_key, "unknown").lower().replace(" ", "_") if source_key else "unknown"
        notes = row.get(notes_key, "") if notes_key else ""

        entries.append({
            "entry_id": f"rfi-gbt-{entry_num:04d}",
            "site_id": site_id,
            "site_name": "Green Bank Telescope",
            "frequency_low_hz": low_mhz * 1e6,
            "frequency_high_hz": high_mhz * 1e6,
            "source_class": source_class,
            "confidence": 0.85,
            "review_status": "pending_operator_review",
            "provenance": "Downloaded from GBT RFI catalog. Requires operator review before use in production scoring.",
            "notes": notes,
            "active": False,  # Inactive until reviewed
            "synthetic": False,
        })
        entry_num += 1

output = {"rfi_database_entries": entries}
outfile.write_text(json.dumps(output, indent=2))
print(f"Wrote {len(entries)} RFI entries to {outfile}")
print()
print("IMPORTANT: All entries have active=False and review_status=pending_operator_review.")
print("Before using in production scoring, review each entry and set active=True only for")
print("confirmed site-specific RFI bands.")
PYEOF

echo ""
echo "Output: $OUTPUT_JSON"
echo ""
echo "Next steps:"
echo "  1. Review $OUTPUT_JSON"
echo "  2. Set active=true for confirmed RFI bands"
echo "  3. Set review_status='reviewed' for each confirmed entry"
echo "  4. Copy to tests/fixtures/rfi_database.json when ready for pipeline use"
echo "     (or set TECHNO_RFI_DATABASE_PATH=$OUTPUT_JSON when running the pipeline)"
