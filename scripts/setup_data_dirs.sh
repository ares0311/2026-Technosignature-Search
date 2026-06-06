#!/usr/bin/env bash
# setup_data_dirs.sh — create local technosignature data directory structure
# Run from any directory: bash ~/path/to/scripts/setup_data_dirs.sh

set -euo pipefail

DATA_ROOT="${TECHNO_DATA_DIR:-$HOME/technosignature-data}"

echo "Creating data directory structure under: $DATA_ROOT"

mkdir -p "$DATA_ROOT/bl_hits"
mkdir -p "$DATA_ROOT/pipeline_out"
mkdir -p "$DATA_ROOT/rfi_catalog"
mkdir -p "$DATA_ROOT/catalog_cache"
mkdir -p "$DATA_ROOT/labeled"
mkdir -p "$DATA_ROOT/noise_samples"

cat > "$DATA_ROOT/README.txt" << 'EOF'
technosignature-data/
  bl_hits/         — Breakthrough Listen turboSETI hit tables (.dat files)
  pipeline_out/    — scored candidate reports from run-pipeline
  rfi_catalog/     — site RFI catalogs (CSV/JSON, approved entries only)
  catalog_cache/   — Gaia/WISE/SIMBAD catalog metadata cache (never commit)
  labeled/         — human-labeled candidate CSVs
  noise_samples/   — baseline noise snapshots for threshold calibration
EOF

echo ""
echo "Done. Directory structure:"
find "$DATA_ROOT" -type d | sort
echo ""
echo "Next step: run scripts/download_bl_hits.sh to fetch sample hit tables."
