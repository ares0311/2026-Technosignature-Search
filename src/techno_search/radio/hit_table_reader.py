"""Reader for real turboSETI-format hit-table .dat files."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

# Real turboSETI .dat files are TAB-separated.  The header line starts with
# "# Top_Hit_#" (note the leading "# ").  Metadata lines (Source, MJD, RA,
# DEC, DELTAT, DELTAF) also start with "#".
#
# Example file structure:
#   # Source:HIP99427
#   # MJD: 59045.5
#   # RA: 301.898
#   # DEC: -44.432
#   # DELTAT:  18.25396
#   # DELTAF(Hz):  2.79397
#   #
#   # Top_Hit_# \t Drift_Rate \t SNR \t Uncorrected_Frequency \t Corrected_Frequency ...
#   1 \t -0.37253 \t 15.8634 \t 1420.417858 \t 1420.417858 \t ...

# Column aliases (real name first, then older/alternate names)
_FREQ_ALIASES = ("Corrected_Frequency", "Frequency", "freq", "frequency_mhz", "Freq")
_SNR_ALIASES = ("SNR", "snr", "Signal_to_Noise")
_DRIFT_ALIASES = ("Drift_Rate", "drift_rate", "DriftRate", "drift_rate_hz_s")
_SCAN_ROLE_ALIASES = ("scan_role", "Scan_Role")
_TARGET_ALIASES = ("target_id", "Target_ID")

# Metadata keys to extract from "#" header lines
_META_KEYS = ("Source", "MJD", "RA", "DEC", "DELTAT", "DELTAF")


def _resolve_col(row: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    for name in aliases:
        if name in row:
            return row[name]
    return None


def _parse_metadata(lines: list[str]) -> dict[str, str]:
    """Extract source metadata from turboSETI # header lines."""
    meta: dict[str, str] = {}
    for line in lines:
        if not line.startswith("#"):
            break
        # Strip the leading "# " or "#"
        content = line.lstrip("#").strip()
        if ":" in content:
            key, _, value = content.partition(":")
            key = key.strip()
            value = value.strip()
            # Match any of our known metadata keys (case-insensitive prefix)
            for mk in _META_KEYS:
                if key.upper().startswith(mk.upper()):
                    meta[mk] = value
                    break
    return meta


def _find_column_header(lines: list[str]) -> tuple[list[str], int] | tuple[None, int]:
    """Find the TAB-separated column header line that starts with '# Top_Hit_#'.

    Returns (column_names, line_index) or (None, -1) if not found.
    Column names are returned with the leading '# ' stripped from the first field.
    """
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n\r")
        if stripped.startswith("# Top_Hit_#") or stripped.startswith("#Top_Hit_#"):
            # Strip leading "# " from the first field only, then split on TAB
            header = stripped.lstrip("#").strip()
            cols = [c.strip() for c in header.split("\t")]
            return cols, i
    return None, -1


def read_hit_table_csv(path: Path) -> list[dict[str, Any]]:
    """Read a turboSETI-format .dat hit table into a list of normalized row dicts.

    Handles both:
    - Real turboSETI .dat files (TAB-separated, "# Top_Hit_#" column header)
    - Legacy CSV files (comma-separated, plain header without #)

    Returns rows with normalized keys:
      frequency_hz, snr, drift_rate_hz_per_sec, source_name, mjd, ra_deg, dec_deg
    Frequencies are converted from MHz to Hz.
    """
    raw_text = Path(path).read_text(encoding="utf-8", errors="replace")
    all_lines = raw_text.splitlines(keepends=True)

    # Extract file-level metadata from # header lines
    file_meta = _parse_metadata(all_lines)

    # Try to find the TAB-separated column header line
    col_names, header_idx = _find_column_header(all_lines)

    rows: list[dict[str, Any]] = []

    if col_names is not None:
        # Real turboSETI .dat format: TAB-separated data after the header line
        data_lines = all_lines[header_idx + 1:]
        for line in data_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) < len(col_names):
                # Pad short rows
                fields += [""] * (len(col_names) - len(fields))
            raw: dict[str, str] = {
                col_names[i]: fields[i].strip()
                for i in range(min(len(col_names), len(fields)))
            }
            row = _normalize_row(raw, file_meta)
            if row is not None:
                rows.append(row)
    else:
        # Fallback: comma-separated CSV (legacy / synthetic test fixtures)
        data_lines = [ln for ln in all_lines if not ln.startswith("#")]
        reader = csv.DictReader(io.StringIO("".join(data_lines)))
        for raw_row in reader:
            raw = {k.strip(): v.strip() for k, v in raw_row.items() if k is not None}
            row = _normalize_row(raw, file_meta)
            if row is not None:
                rows.append(row)

    return rows


def _normalize_row(
    raw: dict[str, str],
    file_meta: dict[str, str],
) -> dict[str, Any] | None:
    """Normalize a raw row dict to RadioHit field names. Returns None to skip."""
    freq_mhz = _resolve_col(raw, _FREQ_ALIASES)
    snr = _resolve_col(raw, _SNR_ALIASES)
    drift = _resolve_col(raw, _DRIFT_ALIASES)

    if freq_mhz is None or snr is None or drift is None:
        return None

    try:
        freq_val = float(freq_mhz)
        snr_val = float(snr)
        drift_val = float(drift)
    except (ValueError, TypeError):
        return None

    # Prefer row-level metadata; fall back to file-level header metadata
    source = raw.get("Source_Name") or raw.get("source") or file_meta.get("Source") or ""
    mjd_str = raw.get("MJD") or file_meta.get("MJD")
    ra_str = raw.get("RA") or file_meta.get("RA")
    dec_str = raw.get("DEC") or file_meta.get("DEC")
    sefd_str = raw.get("SEFD") or raw.get("sefd")
    scan_role = _resolve_col(raw, _SCAN_ROLE_ALIASES)
    target_id = _resolve_col(raw, _TARGET_ALIASES)

    def _float_or_none(s: str | None) -> float | None:
        if not s:
            return None
        try:
            return float(s)
        except (ValueError, TypeError):
            return None

    return {
        "frequency_hz": freq_val * 1e6,
        "snr": snr_val,
        "drift_rate_hz_per_sec": drift_val,
        "source_name": source,
        "mjd": _float_or_none(mjd_str),
        "ra_deg": _float_or_none(ra_str),
        "dec_deg": _float_or_none(dec_str),
        "sefd": _float_or_none(sefd_str),
        "scan_role": scan_role.lower() if scan_role else None,
        "target_id": target_id,
    }


def hit_table_to_radio_hit_dicts(path: Path) -> list[dict[str, Any]]:
    """Read a real turboSETI .dat file and return dicts compatible with parse_hit_table().

    Maps real column names to the RadioHit field names used by the prototype.
    """
    raw_rows = read_hit_table_csv(path)
    artifact_context = _artifact_context(path)
    out = []
    for r in raw_rows:
        out.append({
            "frequency_hz": r["frequency_hz"],
            "snr": r["snr"],
            "drift_rate_hz_per_sec": r["drift_rate_hz_per_sec"],
            "bandwidth_hz": 2.79,   # turboSETI default channel width for L-band
            "scan_role": r.get("scan_role") or artifact_context.get("scan_role") or "on",
            "target_id": (
                r.get("target_id")
                or artifact_context.get("target_id")
                or r.get("source_name")
                or "unknown"
            ),
        })
    return out


def _artifact_context(path: Path) -> dict[str, str]:
    sidecar = path.with_name(path.name + ".provenance.json")
    if not sidecar.exists():
        return {}
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        key: str(payload[key])
        for key in ("scan_role", "target_id")
        if payload.get(key) is not None
    }
