#!/usr/bin/env bash
# download_bl_hits.sh — download real turboSETI hit tables for pipeline testing
#
# Tries sources in order:
#   1. BL GBT L-band survey open data (blpd0.ssl.berkeley.edu)
#   2. turboSETI GitHub test fixtures via git-lfs (real-format .dat files)
#   3. Synthetic .dat files (pipeline format testing only — does NOT close Tier 1 gap)
#
# Run (macOS — use caffeinate to prevent sleep):
#   caffeinate -i bash scripts/download_bl_hits.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${TECHNO_DATA_DIR:-$HOME/technosignature-data}"
BL_HITS_DIR="$DATA_ROOT/bl_hits"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"

mkdir -p "$BL_HITS_DIR"

echo "=== BL Hit Table Download ==="
echo "Output directory: $BL_HITS_DIR"
echo ""

# -----------------------------------------------------------------------
# Helper: check if a file looks like a valid turboSETI .dat
# -----------------------------------------------------------------------
is_valid_dat() {
    local f="$1"
    local size
    size=$(wc -c < "$f" 2>/dev/null || echo 0)
    if [[ $size -lt 200 ]]; then
        return 1
    fi
    if grep -qE "(Top_Hit_#|Drift_Rate|# Source:)" "$f" 2>/dev/null; then
        return 0
    fi
    return 1
}

DOWNLOAD_SUCCESS=0

# -----------------------------------------------------------------------
# Option 1 — BL GBT L-band survey open data (blpd0.ssl.berkeley.edu)
# -----------------------------------------------------------------------
BL_TARGETS=(
    "HIP99427_hits.dat"
    "HIP17378_hits.dat"
    "HIP45167_hits.dat"
    "HIP65352_hits.dat"
    "HIP74995_hits.dat"
)

echo "--- Option 1: BL open data server ---"
echo "Probing https://blpd0.ssl.berkeley.edu/ for directory structure ..."
echo "(Server has an SSL cert mismatch; using -k to bypass)"

# Fetch the server root to discover what paths are available
BL_ROOT_HTML=$(curl -k -sL --max-time 15 "https://blpd0.ssl.berkeley.edu/" 2>/dev/null || true)
if [[ -n "$BL_ROOT_HTML" ]]; then
    echo "  Server responded. Scanning for .dat file paths ..."
    # Extract any href links ending in .dat from the directory listing
    BL_DAT_PATHS=$(echo "$BL_ROOT_HTML" | grep -oE 'href="[^"]*\.dat"' | sed 's/href="//;s/"//' | head -10 || true)
    if [[ -n "$BL_DAT_PATHS" ]]; then
        echo "  Found .dat paths on server:"
        echo "$BL_DAT_PATHS" | while read -r p; do echo "    $p"; done
    else
        # Try known subdirectory paths
        for subdir in "L_band_table" "GBT" "GBT_L_band" "hits" "dat_files"; do
            SUBDIR_HTML=$(curl -k -sL --max-time 10 "https://blpd0.ssl.berkeley.edu/$subdir/" 2>/dev/null || true)
            if echo "$SUBDIR_HTML" | grep -q "\.dat"; then
                echo "  Found .dat files under /$subdir/"
                BL_BASE="https://blpd0.ssl.berkeley.edu/$subdir"
                break
            fi
        done
    fi
else
    echo "  Server did not respond."
fi

for target in "${BL_TARGETS[@]}"; do
    dest="$BL_HITS_DIR/$target"
    if curl -L -k --max-time 30 --retry 2 --retry-delay 2 \
            --fail --show-error \
            -o "$dest" \
            "${BL_BASE:-https://blpd0.ssl.berkeley.edu/L_band_table}/$target" 2>&1; then
        if is_valid_dat "$dest"; then
            echo "  OK: $target ($(wc -c < "$dest") bytes)"
            DOWNLOAD_SUCCESS=$((DOWNLOAD_SUCCESS + 1))
        else
            echo "  WARN: $target invalid ($(wc -c < "$dest" 2>/dev/null || echo 0) bytes)"
            rm -f "$dest"
        fi
    else
        echo "  SKIP: $target (not found at current path)"
        rm -f "$dest" 2>/dev/null || true
    fi
done

if [[ $DOWNLOAD_SUCCESS -gt 0 ]]; then
    echo ""
    echo "Downloaded $DOWNLOAD_SUCCESS real BL hit table(s) — Tier 1 gap partially addressed."
    echo "Run: caffeinate -i bash scripts/run_pipeline_on_bl_data.sh"
    exit 0
fi

echo ""
echo "BL server download failed. Trying Option 2..."
echo ""

# -----------------------------------------------------------------------
# Option 2 — turboSETI GitHub test fixtures via LFS batch API (no auth needed)
# Clones pointer files only, then fetches real objects via the public LFS batch API.
# This bypasses git-lfs credential requirements for public repos.
# -----------------------------------------------------------------------
echo "--- Option 2: turboSETI GitHub test data (LFS batch API) ---"

CLONE_DIR=$(mktemp -d)
echo "  Cloning turboSETI pointer tree (GIT_LFS_SKIP_SMUDGE=1) ..."

# Skip LFS smudge during clone so we get pointer files, not stalled auth attempts
if GIT_LFS_SKIP_SMUDGE=1 git clone --depth=1 \
        "https://github.com/UCBerkeleySETI/turbo_seti" "$CLONE_DIR" 2>&1; then

    # Collect .dat pointer files (LFS pointers are ~134 bytes, start with "version https://git-lfs")
    POINTER_FILES=()
    while IFS= read -r -d '' f; do
        sz=$(wc -c < "$f" 2>/dev/null || echo 0)
        if [[ $sz -lt 500 ]] && grep -q "^version https://git-lfs" "$f" 2>/dev/null; then
            POINTER_FILES+=("$f")
        fi
    done < <(find "$CLONE_DIR/tests/test_data" -name "*.dat" -print0 2>/dev/null)

    if [[ ${#POINTER_FILES[@]} -eq 0 ]]; then
        echo "  No LFS pointer files found — test_data may have moved."
    else
        echo "  Found ${#POINTER_FILES[@]} LFS pointer(s). Calling batch API ..."

        # Use Python to build batch request, call LFS API, and download
        "$VENV_PYTHON" - "$BL_HITS_DIR" "${POINTER_FILES[@]}" <<'PYEOF'
import sys, json, os, urllib.request, urllib.error

dest_dir = sys.argv[1]
pointer_paths = sys.argv[2:]

# Parse OID + size from each pointer file
objects = []
path_by_oid = {}
for p in pointer_paths:
    oid = size = None
    try:
        for line in open(p).read().splitlines():
            if line.startswith("oid sha256:"):
                oid = line.split(":", 1)[1].strip()
            elif line.startswith("size "):
                size = int(line.split(" ", 1)[1].strip())
    except Exception:
        pass
    if oid and size:
        objects.append({"oid": oid, "size": size})
        path_by_oid[oid] = p

if not objects:
    print("  Could not parse any LFS pointers.")
    sys.exit(0)

# Call the GitHub LFS batch API — public repos return signed download URLs
batch_url = "https://github.com/UCBerkeleySETI/turbo_seti.git/info/lfs/objects/batch"
payload = json.dumps({
    "operation": "download",
    "transfers": ["basic"],
    "objects": objects,
}).encode()

req = urllib.request.Request(
    batch_url,
    data=payload,
    headers={
        "Accept": "application/vnd.git-lfs+json",
        "Content-Type": "application/vnd.git-lfs+json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        batch = json.loads(resp.read())
except urllib.error.HTTPError as e:
    body = e.read().decode(errors="replace")
    print(f"  LFS batch API error {e.code}: {body[:200]}")
    sys.exit(0)
except Exception as e:
    print(f"  LFS batch API failed: {e}")
    sys.exit(0)

downloaded = 0
for obj in batch.get("objects", []):
    oid = obj.get("oid", "")
    err = obj.get("error")
    if err:
        print(f"  LFS error for {oid[:8]}: {err.get('message','')}")
        continue
    href = obj.get("actions", {}).get("download", {}).get("href", "")
    if not href:
        print(f"  No download URL for {oid[:8]}")
        continue
    src_path = path_by_oid.get(oid, "")
    filename = os.path.basename(src_path) if src_path else f"{oid[:8]}.dat"
    dest = os.path.join(dest_dir, filename)
    try:
        dl_req = urllib.request.Request(href, headers={"User-Agent": "techno-search/1.0"})
        with urllib.request.urlopen(dl_req, timeout=60) as dl_resp:
            data = dl_resp.read()
        with open(dest, "wb") as fh:
            fh.write(data)
        print(f"  OK: {filename} ({len(data)} bytes) [turboSETI test fixture]")
        downloaded += 1
    except Exception as e:
        print(f"  Failed {filename}: {e}")

if downloaded > 0:
    print(f"\nDownloaded {downloaded} real .dat file(s) via LFS batch API.")
    print("NOTE: These are GBT-derived test fixtures, useful for format/pipeline testing.")
    print("Run: caffeinate -i bash scripts/run_pipeline_on_bl_data.sh")
    # Signal success to the shell wrapper
    with open(os.path.join(dest_dir, ".lfs_download_count"), "w") as fh:
        fh.write(str(downloaded))
else:
    print("  LFS batch API returned no downloadable objects.")
PYEOF

        # Check if Python download succeeded
        if [[ -f "$BL_HITS_DIR/.lfs_download_count" ]]; then
            LFS_COUNT=$(cat "$BL_HITS_DIR/.lfs_download_count")
            rm -f "$BL_HITS_DIR/.lfs_download_count"
            if [[ "$LFS_COUNT" -gt 0 ]]; then
                rm -rf "$CLONE_DIR"
                exit 0
            fi
        fi
    fi

    rm -rf "$CLONE_DIR"
else
    echo "  git clone failed (network issue or repo moved)."
    rm -rf "$CLONE_DIR" 2>/dev/null || true
fi

echo ""
echo "All network sources failed. Trying Option 3 (manual instructions below)..."
echo ""

# -----------------------------------------------------------------------
# Option 3 — Synthetic files (pipeline format testing only)
# -----------------------------------------------------------------------
echo "--- Option 3: Synthetic .dat files (pipeline format testing) ---"
echo "NOTE: These do NOT constitute real observation data."
echo "      See docs/BL_DATA_DOWNLOAD.md for manual download instructions."
echo ""

"$VENV_PYTHON" - "$BL_HITS_DIR" <<'PYEOF'
import sys
import random

out_dir = sys.argv[1]

TARGETS = [
    ("GBT_synth_HIP99427", "57650.123", "301.4500", "+21.2300"),
    ("GBT_synth_HIP17378", "57651.456", "55.8900",  "-17.4500"),
    ("GBT_synth_HIP45167", "57652.789", "138.2300", "+12.7800"),
    ("GBT_synth_HIP65352", "57653.012", "201.5600", "+05.1200"),
    ("GBT_synth_HIP74995", "57654.345", "229.9800", "-03.4400"),
]

COLUMNS = "\t".join([
    "# Top_Hit_#", "Drift_Rate", "SNR", "Uncorrected_Frequency",
    "Corrected_Frequency", "Index", "freq_start", "freq_end",
    "SEFD", "SEFD_freq", "Coarse_Channel_Number",
    "Full_number_of_hits",
])

random.seed(42)

for source, mjd, ra, dec in TARGETS:
    filename = f"{source}_hits.dat"
    filepath = f"{out_dir}/{filename}"
    with open(filepath, "w") as f:
        f.write(f"# Source:{source}\n")
        f.write(f"# MJD:{mjd}\n")
        f.write(f"# RA:{ra}\n")
        f.write(f"# DEC:{dec}\n")
        f.write("# DELTAT:18.253611\n")
        f.write("# DELTAF(Hz):2.793968\n")
        f.write(f"{COLUMNS}\n")
        n_hits = random.randint(3, 8)
        for i in range(1, n_hits + 1):
            freq = round(random.uniform(1200.0, 1800.0), 6)
            drift = round(random.uniform(-2.0, 2.0), 6)
            snr = round(random.uniform(6.0, 50.0), 6)
            row = "\t".join([
                str(i),
                str(drift),
                str(snr),
                str(freq),
                str(freq),
                str(random.randint(1000, 9000)),
                str(round(freq - 0.001, 6)),
                str(round(freq + 0.001, 6)),
                "11.0",
                str(freq),
                str(random.randint(0, 63)),
                str(n_hits),
            ])
            f.write(f"{row}\n")
    print(f"  Created: {filename} ({n_hits} hits) [SYNTHETIC]")

print("")
print("Run: caffeinate -i bash scripts/run_pipeline_on_bl_data.sh")
print("")
print("For real BL data, see docs/BL_DATA_DOWNLOAD.md")
PYEOF

echo ""
echo "=== Manual download options ==="
echo "1. Browser: https://seti.berkeley.edu/listen/data.html"
echo "   Download .dat files to ~/technosignature-data/bl_hits/"
echo ""
echo "2. git-lfs (if not installed): brew install git-lfs"
echo "   Then re-run this script."
echo ""
echo "3. See docs/BL_DATA_DOWNLOAD.md for full instructions."
