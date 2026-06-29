#!/usr/bin/env python3
"""Ingest verified MeerKAT BLUSE/SETICORE hit metadata for local training.

The current verified source is the Berkeley SETI / Breakthrough Listen
3I/ATLAS public data artifact:

    https://bldata.berkeley.edu/ATLAS/MeerKAT/atlas_hits_2025_11_dups.json.gz

It is gzip-compressed JSON with a top-level array.  Records use SETICORE-style
keys such as ``frequency``, ``driftRate``, ``snr``, ``coarseChannel``, ``beam``,
and ``sourceName``.  The file is public research data, but no explicit license
for redistributing the payload has been identified; keep downloaded payloads and
derived corpora local/ignored.

Scientific guardrail:
  MeerKAT BLUSE hits are used as a false-positive training corpus only.
  No hit in this dataset is claimed to be a technosignature.  Ingested
  hits are stored locally and not committed to the repository.

Source guardrail:
  Do not use Zenodo concept record 10987642; it resolves to unrelated content.
  Do not commit the downloaded gzip, decompressed JSON, normalized NDJSON, or
  fitted scorer payloads.

Usage:
  .venv/bin/python scripts/ingest_meerkat_hits.py --source-url URL
                                                   [--output-dir data/meerkat_hits]
                                                   [--max-hits 200000]
                                                   [--dry-run]
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import ssl
import statistics
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import certifi

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFIED_ATLAS_MEERKAT_URL = (
    "https://bldata.berkeley.edu/ATLAS/MeerKAT/atlas_hits_2025_11_dups.json.gz"
)
VERIFIED_ATLAS_SOURCE_PAGE = "https://seti.berkeley.edu/atlas/"
VERIFIED_ATLAS_SHA256 = (
    "f0ba629077825097b1c247cf94131858992636d5bf8cea3b5bfde23b0384ea17"
)
VERIFIED_ATLAS_CONTENT_LENGTH_BYTES = 94_246_793
SCHEMA_SAMPLE_SIZE = 20

MEERKAT_DISCLAIMER = (
    "MeerKAT BLUSE hit data is used as a false-positive training corpus. "
    "No hit constitutes a technosignature detection or authorizes external "
    "submission. This dataset is stored locally and not committed."
)

MEERKAT_SOURCE_BLOCKER = (
    "No source URL was provided. Use --source-url with the verified Berkeley "
    "SETI / Breakthrough Listen 3I/ATLAS MeerKAT JSON URL documented in "
    "docs/meerkat_bluse_hit_table_research.md, or pass --use-verified-atlas-source."
)

SETICORE_REQUIRED_FIELDS = (
    "frequency",
    "driftRate",
    "snr",
    "sourceName",
    "beam",
    "foff",
    "numChannels",
    "filename",
)

LEGACY_TURBOSETI_FIELD_MAP = {
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


def _float(raw: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(raw.get(key, default))
    except (TypeError, ValueError):
        return default


def _int(raw: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(raw.get(key, default))
    except (TypeError, ValueError):
        return default


def _normalised_drift(drift_rate_hz_per_sec: float, frequency_hz: float) -> float:
    frequency_ghz = frequency_hz / 1e9
    if frequency_ghz <= 0:
        return 0.0
    return drift_rate_hz_per_sec / frequency_ghz


def _frequency_bin(frequency_hz: float, *, bin_hz: float = 1.0) -> int:
    return int(round(frequency_hz / bin_hz))


def _validate_seticore_schema(raw_hits: list[dict[str, Any]]) -> None:
    """Fail fast when the verified ATLAS/MeerKAT JSON schema is not present."""
    if not raw_hits:
        raise ValueError("MeerKAT hit table is empty")

    missing_by_index: list[str] = []
    for index, raw in enumerate(raw_hits[:SCHEMA_SAMPLE_SIZE]):
        missing = [field for field in SETICORE_REQUIRED_FIELDS if field not in raw]
        if missing:
            missing_by_index.append(f"record {index}: {', '.join(missing)}")

    if missing_by_index:
        sample = "; ".join(missing_by_index[:5])
        raise ValueError(
            "Input does not match the verified ATLAS MeerKAT BLUSE/SETICORE "
            f"schema; missing required fields in sample: {sample}"
        )


def _normalise_seticore_hit(
    raw: dict[str, Any],
    *,
    median_snr: float,
    frequency_counts: dict[int, int],
    hit_count: int,
) -> dict[str, Any]:
    """Normalise one verified ATLAS MeerKAT BLUSE/SETICORE hit."""
    frequency_mhz = _float(raw, "frequency")
    frequency_hz = frequency_mhz * 1_000_000.0
    drift = _float(raw, "driftRate")
    snr = _float(raw, "snr")
    foff_mhz = _float(raw, "foff")
    num_channels = _int(raw, "numChannels")
    bandwidth_hz = abs(foff_mhz) * max(0, num_channels) * 1_000_000.0
    normalized_drift = _normalised_drift(drift, frequency_hz)
    frequency_key = _frequency_bin(frequency_hz)
    persistence_denominator = max(1, hit_count - 1)

    return {
        "snr": snr,
        "drift_rate_hz_per_sec": drift,
        "frequency_hz": frequency_hz,
        "bandwidth_hz": bandwidth_hz,
        "normalized_drift_hz_s_per_ghz": normalized_drift,
        "relative_snr": snr / median_snr if median_snr > 0 else snr,
        "on_off_consistency_score": 0.0,
        "is_earth_drift_consistent": 1.0 if abs(normalized_drift) <= 0.44 else 0.0,
        "rfi_band_overlap_score": 0.0,
        "frequency_persistence_score": min(
            1.0,
            max(0, frequency_counts.get(frequency_key, 1) - 1)
            / persistence_denominator,
        ),
        "on_hit_count": 1,
        "off_hit_count": 0,
        "scan_role": "unknown",
        "target_id": str(raw.get("sourceName") or "unknown"),
        "beam": _int(raw, "beam"),
        "coarse_channel": _int(raw, "coarseChannel"),
        "channel_number": _int(raw, "index"),
        "power": _float(raw, "power"),
        "incoherent_power": _float(raw, "incoherentPower"),
        "fch1_mhz": _float(raw, "fch1"),
        "foff_mhz": foff_mhz,
        "tstart_mjd": _float(raw, "tstart"),
        "tsamp_seconds": _float(raw, "tsamp"),
        "ra_deg": _float(raw, "ra"),
        "dec_deg": _float(raw, "dec"),
        "telescope_id": _int(raw, "telescopeId"),
        "num_timesteps": _int(raw, "numTimesteps"),
        "num_channels": num_channels,
        "start_channel": _int(raw, "startChannel"),
        "file_index": _int(raw, "fileindex"),
        "backend_host": str(raw.get("hostname") or ""),
        "source_artifact": str(raw.get("filename") or ""),
        "corpus_source": "meerkat_bluse_seticore_atlas_2025_11",
    }


def _normalise_legacy_turboseti_hit(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalise older turboSETI-style rows retained for backward compatibility."""
    h: dict[str, Any] = {}
    for raw_key, std_key in LEGACY_TURBOSETI_FIELD_MAP.items():
        if raw_key in raw:
            h[std_key] = raw[raw_key]
    if "frequency_hz" not in h:
        h["frequency_hz"] = 0.0
    if "snr" not in h:
        h["snr"] = 0.0
    if "drift_rate_hz_per_sec" not in h:
        h["drift_rate_hz_per_sec"] = 0.0
    h["scan_role"] = raw.get("scan_role", "unknown")
    h["target_id"] = raw.get("source_name", "meerkat_bluse")
    h["bandwidth_hz"] = raw.get("bandwidth_hz", 2.0)
    h["corpus_source"] = "legacy_turboseti_meerkat_bluse"
    return h


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ssl_context() -> ssl.SSLContext:
    """Return the project-standard CA context for public data downloads."""
    return ssl.create_default_context(cafile=certifi.where())


def download_meerkat_hits(
    output_dir: Path,
    source_url: str,
    expected_sha256: str | None,
) -> tuple[Path, dict[str, Any]]:
    """Download the MeerKAT hit table and return the local path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    gz_path = output_dir / Path(source_url).name
    json_path = output_dir / "meerkat_bluse_hits.json"
    headers: dict[str, str] = {}

    if not gz_path.exists():
        print("[START] Downloading MeerKAT BLUSE hits from:")
        print(f"        {source_url}")
        print("[INFO]  Download may take several minutes.")
        t0 = time.time()
        request = Request(source_url, headers={"User-Agent": "techno-search/1.1"})
        with (
            urlopen(request, timeout=120, context=_ssl_context()) as response,
            gz_path.open("wb") as out,
        ):
            headers = {key.lower(): value for key, value in response.headers.items()}
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        elapsed = time.time() - t0
        size = gz_path.stat().st_size / 1e6
        print(f"[OK]    Downloaded: {gz_path} ({size:.1f} MB in {elapsed:.0f}s)")
    else:
        print(f"[SKIP]  Already downloaded: {gz_path}")

    actual_sha256 = _sha256(gz_path)
    if expected_sha256 and actual_sha256.lower() != expected_sha256.lower():
        raise ValueError(
            f"SHA256 mismatch for {gz_path}: expected {expected_sha256}, "
            f"got {actual_sha256}"
        )

    if not json_path.exists():
        print(f"[INFO]  Decompressing {gz_path}...")
        with gzip.open(gz_path, "rb") as gz_in:
            json_path.write_bytes(gz_in.read())
        print(f"[OK]    Decompressed to {json_path}")
    else:
        print(f"[SKIP]  Already decompressed: {json_path}")

    metadata = {
        "source_url": source_url,
        "source_page": VERIFIED_ATLAS_SOURCE_PAGE,
        "sha256": actual_sha256,
        "content_length_bytes": gz_path.stat().st_size,
        "http_content_length_bytes": int(headers.get("content-length", "0") or 0),
        "etag": headers.get("etag", ""),
        "last_modified": headers.get("last-modified", ""),
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "local_gzip_path": str(gz_path),
    }
    return json_path, metadata


def _extract_raw_hits(raw_data: Any, json_path: Path) -> list[dict[str, Any]]:
    if isinstance(raw_data, list):
        raw_hits = raw_data
    elif isinstance(raw_data, dict):
        raw_hits = raw_data.get("hits", raw_data.get("data", []))
    else:
        raise ValueError(f"Unexpected JSON structure in {json_path}")
    if not isinstance(raw_hits, list):
        raise ValueError(f"Expected hit list in {json_path}")
    if not all(isinstance(item, dict) for item in raw_hits[:SCHEMA_SAMPLE_SIZE]):
        raise ValueError(f"Expected JSON objects in first records of {json_path}")
    return raw_hits


def ingest_hits(json_path: Path, output_dir: Path, max_hits: int) -> Path:
    """Parse and normalise up to max_hits hits, write NDJSON output."""
    print(f"[START] Ingesting up to {max_hits:,} hits from {json_path}")
    t0 = time.time()

    out_path = output_dir / f"meerkat_normalised_{max_hits}.ndjson"
    if out_path.exists():
        print(f"[SKIP]  Already ingested: {out_path}")
        return out_path

    raw_data = json.loads(json_path.read_text(encoding="utf-8"))
    raw_hits = _extract_raw_hits(raw_data, json_path)
    total_raw = len(raw_hits)
    print(f"[INFO]  Total raw hits: {total_raw:,}")
    selected_hits = raw_hits[:max_hits]
    is_seticore_schema = bool(selected_hits and "frequency" in selected_hits[0])
    if is_seticore_schema:
        _validate_seticore_schema(selected_hits)

    snrs = [_float(raw, "snr") for raw in selected_hits]
    median_snr = statistics.median(snrs) if snrs else 1.0
    if median_snr <= 0:
        median_snr = 1.0
    frequency_counts: dict[int, int] = {}
    if is_seticore_schema:
        for raw in selected_hits:
            frequency_key = _frequency_bin(_float(raw, "frequency") * 1_000_000.0)
            frequency_counts[frequency_key] = frequency_counts.get(frequency_key, 0) + 1

    n_written = 0
    malformed_count = 0
    with out_path.open("w", encoding="utf-8") as f_out:
        for i, raw in enumerate(selected_hits):
            if i % 50_000 == 0 and i > 0:
                print(f"[{n_written:,}/{max_hits:,}] Processed {i:,} raw hits...")
            try:
                if is_seticore_schema:
                    hit = _normalise_seticore_hit(
                        raw,
                        median_snr=median_snr,
                        frequency_counts=frequency_counts,
                        hit_count=len(selected_hits),
                    )
                else:
                    hit = _normalise_legacy_turboseti_hit(raw)
                f_out.write(json.dumps(hit, sort_keys=True) + "\n")
                n_written += 1
            except Exception as exc:
                _ = exc
                malformed_count += 1
                continue
    if n_written == 0:
        raise ValueError(f"No normalized hits were written from {json_path}")

    elapsed = time.time() - t0
    size_mb = out_path.stat().st_size / 1e6
    print(f"[DONE]  Wrote {n_written:,} normalised hits in {elapsed:.1f}s")
    if malformed_count:
        print(f"[WARN]  Skipped {malformed_count:,} malformed hits after schema validation")
    print(f"[INFO]  Output: {out_path} ({size_mb:.1f} MB)")
    return out_path


def write_provenance(
    output_dir: Path,
    out_path: Path,
    max_hits: int,
    source_url: str,
    source_metadata: dict[str, Any],
) -> None:
    """Write a provenance JSON file alongside the normalised hits."""
    prov = {
        "schema_version": "meerkat_ingest_provenance_v1",
        "disclaimer": MEERKAT_DISCLAIMER,
        "source": "Berkeley SETI / Breakthrough Listen ATLAS MeerKAT BLUSE/SETICORE hits",
        "source_url": source_url,
        "source_page": VERIFIED_ATLAS_SOURCE_PAGE,
        "sha256": source_metadata.get("sha256", ""),
        "content_length_bytes": source_metadata.get("content_length_bytes", 0),
        "http_content_length_bytes": source_metadata.get("http_content_length_bytes", 0),
        "etag": source_metadata.get("etag", ""),
        "last_modified": source_metadata.get("last_modified", ""),
        "retrieved_at_utc": source_metadata.get("retrieved_at_utc", ""),
        "frequency_range_mhz": "900-1670",
        "telescope": "MeerKAT",
        "use": "false_positive_training_corpus",
        "license_policy": (
            "No explicit license text for this exact JSON artifact was identified; "
            "use locally with attribution and do not redistribute payloads."
        ),
        "max_hits_ingested": max_hits,
        "output_file": str(out_path),
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    prov_path = output_dir / "meerkat_ingest_provenance.json"
    prov_path.write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print(f"[INFO]  Provenance written: {prov_path}")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-url",
        default=None,
        help=(
            "Verified MeerKAT BLUSE/SETICORE hit-table URL. Use "
            "--use-verified-atlas-source for the committed Berkeley source."
        ),
    )
    parser.add_argument(
        "--use-verified-atlas-source",
        action="store_true",
        help="Use the verified Berkeley SETI / Breakthrough Listen ATLAS MeerKAT URL.",
    )
    parser.add_argument(
        "--expected-sha256",
        default=None,
        help="Expected SHA256 for the gzip payload. Defaults to the verified ATLAS hash.",
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
    args = parser.parse_args(argv)
    source_url = args.source_url
    if args.use_verified_atlas_source:
        source_url = VERIFIED_ATLAS_MEERKAT_URL
    expected_sha256 = args.expected_sha256
    if expected_sha256 is None and source_url == VERIFIED_ATLAS_MEERKAT_URL:
        expected_sha256 = VERIFIED_ATLAS_SHA256

    if args.dry_run:
        print("[DRY-RUN] Would download:")
        print(f"  URL: {source_url or '(blocked: no source URL)'}")
        print(f"  Output dir: {args.output_dir}")
        print(f"  Max hits: {args.max_hits:,}")
        print(f"  Expected SHA256: {expected_sha256 or '(not provided)'}")
        print(f"  Disclaimer: {MEERKAT_DISCLAIMER}")
        if not source_url:
            print(f"  Blocker: {MEERKAT_SOURCE_BLOCKER}")
        return

    if not source_url:
        raise SystemExit(MEERKAT_SOURCE_BLOCKER)

    print("[START] MeerKAT BLUSE hit ingestion")
    print(f"[INFO]  Output dir: {args.output_dir}")
    print(f"[INFO]  Max hits: {args.max_hits:,}")

    json_path, source_metadata = download_meerkat_hits(
        args.output_dir,
        source_url,
        expected_sha256,
    )
    out_path = ingest_hits(json_path, args.output_dir, args.max_hits)
    write_provenance(args.output_dir, out_path, args.max_hits, source_url, source_metadata)

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
