#!/usr/bin/env python3
"""
ingest_meerkat_hits.py

Ingests a verified MeerKAT BLUSE turboSETI hit table as a false-positive
corpus for generalisation.

This dataset covers 900–1670 MHz from MeerKAT and provides ~2 million
turboSETI hits that are almost entirely RFI.  It is an ideal training
corpus for the semi-supervised anomaly scorer because:
  - It is from a different telescope and frequency range than GBT.
  - It is publicly documented (Sheikh et al. 2025).
  - Its overwhelming RFI content makes it a safe "normal" training set.

Scientific guardrail:
  MeerKAT BLUSE hits are used as a false-positive training corpus only.
  No hit in this dataset is claimed to be a technosignature.  Ingested
  hits are stored locally and not committed to the repository.

Important source guardrail:
  No verified public MeerKAT BLUSE hit-table URL is currently committed. Earlier
  iterations pointed at Zenodo concept record 10987642, but that concept resolves
  to unrelated content and must not be used. Until a real source URL is verified,
  use:

    .venv/bin/techno-search semisupervised-corpus-build \
        --dat-dir data/extended_corpus \
        --output data/meerkat_hits/real_turboseti_training.ndjson

Usage:
  .venv/bin/python scripts/ingest_meerkat_hits.py --source-url URL
                                                   [--output-dir data/meerkat_hits]
                                                   [--max-hits 200000]
                                                   [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MEERKAT_DISCLAIMER = (
    "MeerKAT BLUSE hit data is used as a false-positive training corpus. "
    "No hit constitutes a technosignature detection or authorizes external "
    "submission. This dataset is stored locally and not committed."
)

MEERKAT_SOURCE_BLOCKER = (
    "No verified public MeerKAT BLUSE turboSETI hit-table URL is configured. "
    "Do not use Zenodo concept 10987642; current metadata resolves to unrelated "
    "content. Provide --source-url only after independently verifying the data "
    "release, or build a scorer corpus from real local turboSETI .dat files "
    "with .venv/bin/techno-search semisupervised-corpus-build."
)

# turboSETI field mapping for MeerKAT → standard field names
MEERKAT_FIELD_MAP = {
    "Drift_Rate": "drift_rate_hz_per_sec",
    "SNR": "snr",
    "Uncorrected_Frequency": "frequency_hz",
    "Corrected_Frequency": "frequency_hz",   # prefer corrected if present
    "SEFD": "sefd",
    "Channel_Number": "channel_number",
    "Coarse_Channel_Number": "coarse_channel",
    "Full_number_of_hits": "hit_count",
    "status": "status",
}


def _normalise_hit(raw: dict) -> dict:
    """Normalise a MeerKAT turboSETI hit to standard field names."""
    h: dict = {}
    for raw_key, std_key in MEERKAT_FIELD_MAP.items():
        if raw_key in raw:
            h[std_key] = raw[raw_key]
    # Fallback fields
    if "frequency_hz" not in h:
        h["frequency_hz"] = 0.0
    if "snr" not in h:
        h["snr"] = 0.0
    if "drift_rate_hz_per_sec" not in h:
        h["drift_rate_hz_per_sec"] = 0.0
    # MeerKAT BLUSE scans are single-pointing; mark scan_role unknown
    h["scan_role"] = raw.get("scan_role", "unknown")
    h["target_id"] = raw.get("source_name", "meerkat_bluse")
    h["bandwidth_hz"] = raw.get("bandwidth_hz", 2.0)
    h["corpus_source"] = "meerkat_bluse_sheikh2025"
    return h


def download_meerkat_hits(output_dir: Path, max_hits: int, source_url: str) -> Path:
    """Download the MeerKAT hit table and return the local path."""
    import gzip
    import urllib.request

    output_dir.mkdir(parents=True, exist_ok=True)
    gz_path = output_dir / "meerkat_bluse_hits.json.gz"
    json_path = output_dir / "meerkat_bluse_hits.json"

    if not gz_path.exists():
        print("[START] Downloading MeerKAT BLUSE hits from:")
        print(f"        {source_url}")
        print("[INFO]  Download may take several minutes.")
        t0 = time.time()
        urllib.request.urlretrieve(source_url, gz_path)
        elapsed = time.time() - t0
        size = gz_path.stat().st_size / 1e6
        print(f"[OK]    Downloaded: {gz_path} ({size:.1f} MB in {elapsed:.0f}s)")
    else:
        print(f"[SKIP]  Already downloaded: {gz_path}")

    if not json_path.exists():
        print(f"[INFO]  Decompressing {gz_path}...")
        with gzip.open(gz_path, "rb") as gz_in:
            json_path.write_bytes(gz_in.read())
        print(f"[OK]    Decompressed to {json_path}")
    else:
        print(f"[SKIP]  Already decompressed: {json_path}")

    return json_path


def ingest_hits(json_path: Path, output_dir: Path, max_hits: int) -> Path:
    """Parse and normalise up to max_hits hits, write NDJSON output."""
    print(f"[START] Ingesting up to {max_hits:,} hits from {json_path}")
    t0 = time.time()

    out_path = output_dir / f"meerkat_normalised_{max_hits}.ndjson"
    if out_path.exists():
        print(f"[SKIP]  Already ingested: {out_path}")
        return out_path

    raw_data = json.loads(json_path.read_text(encoding="utf-8"))
    # Accept list or {"hits": [...]} structure
    if isinstance(raw_data, list):
        raw_hits = raw_data
    elif isinstance(raw_data, dict):
        raw_hits = raw_data.get("hits", raw_data.get("data", []))
    else:
        raise ValueError(f"Unexpected JSON structure in {json_path}")

    total_raw = len(raw_hits)
    print(f"[INFO]  Total raw hits: {total_raw:,}")

    n_written = 0
    with open(out_path, "w", encoding="utf-8") as f_out:
        for i, raw in enumerate(raw_hits):
            if n_written >= max_hits:
                break
            if i % 50_000 == 0 and i > 0:
                print(f"[{n_written:,}/{max_hits:,}] Processed {i:,} raw hits...")
            try:
                hit = _normalise_hit(raw)
                f_out.write(json.dumps(hit) + "\n")
                n_written += 1
            except Exception as exc:
                # Skip malformed hits silently
                _ = exc
                continue

    elapsed = time.time() - t0
    size_mb = out_path.stat().st_size / 1e6
    print(f"[DONE]  Wrote {n_written:,} normalised hits in {elapsed:.1f}s")
    print(f"[INFO]  Output: {out_path} ({size_mb:.1f} MB)")
    return out_path


def write_provenance(
    output_dir: Path,
    out_path: Path,
    max_hits: int,
    source_url: str,
) -> None:
    """Write a provenance JSON file alongside the normalised hits."""
    prov = {
        "schema_version": "meerkat_ingest_provenance_v1",
        "disclaimer": MEERKAT_DISCLAIMER,
        "source": "MeerKAT BLUSE turboSETI hits (Sheikh et al. 2025)",
        "url": source_url,
        "frequency_range_mhz": "900–1670",
        "telescope": "MeerKAT",
        "use": "false_positive_training_corpus",
        "max_hits_ingested": max_hits,
        "output_file": str(out_path),
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    prov_path = output_dir / "meerkat_ingest_provenance.json"
    prov_path.write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print(f"[INFO]  Provenance written: {prov_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-url",
        default=None,
        help=(
            "Verified MeerKAT BLUSE hit-table URL. Required for network ingest; "
            "no default is committed because the previous Zenodo source was invalid."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "meerkat_hits",
        help="Directory to store downloaded and normalised hits",
    )
    parser.add_argument(
        "--max-hits",
        type=int,
        default=200_000,
        help="Maximum number of normalised hits to ingest (default: 200000)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done; do not download or write files",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY-RUN] Would download:")
        print(f"  URL: {args.source_url or '(blocked: no verified source URL)'}")
        print(f"  Output dir: {args.output_dir}")
        print(f"  Max hits: {args.max_hits:,}")
        print(f"  Disclaimer: {MEERKAT_DISCLAIMER}")
        if not args.source_url:
            print(f"  Blocker: {MEERKAT_SOURCE_BLOCKER}")
        return

    if not args.source_url:
        raise SystemExit(MEERKAT_SOURCE_BLOCKER)

    print("[START] MeerKAT BLUSE hit ingestion")
    print(f"[INFO]  Output dir: {args.output_dir}")
    print(f"[INFO]  Max hits: {args.max_hits:,}")

    json_path = download_meerkat_hits(args.output_dir, args.max_hits, args.source_url)
    out_path = ingest_hits(json_path, args.output_dir, args.max_hits)
    write_provenance(args.output_dir, out_path, args.max_hits, args.source_url)

    print("")
    print("Scientific guardrail:")
    print(f"  {MEERKAT_DISCLAIMER}")
    print("")
    print("Next step: train the semi-supervised scorer on this corpus:")
    print("  caffeinate -i .venv/bin/techno-search semisupervised-scorer-train \\")
    print(f"      --corpus {out_path} \\")
    print("      --workers 12")


if __name__ == "__main__":
    main()
