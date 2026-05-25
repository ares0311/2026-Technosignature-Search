"""Reader for real turboSETI-format hit-table CSV files."""
from __future__ import annotations

from pathlib import Path
from typing import Any

# turboSETI CSV column names (as produced by turboSETI >= 2.0)
_TURBOSETI_REQUIRED = {"Frequency", "SNR", "Drift_Rate"}
_TURBOSETI_OPTIONAL = {
    "SEFD", "Coarse_Channel_Width", "Full_Number_of_Hits",
    "Source_Name", "MJD", "RA", "DEC", "FOFF", "Index", "top_hit_num",
}

# Column name aliases for older turboSETI versions
_FREQ_ALIASES = ("Frequency", "freq", "frequency_mhz", "Freq")
_SNR_ALIASES = ("SNR", "snr", "Signal_to_Noise")
_DRIFT_ALIASES = ("Drift_Rate", "drift_rate", "DriftRate", "drift_rate_hz_s")


def _resolve_col(row: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    for name in aliases:
        if name in row:
            return row[name]
    return None


def read_hit_table_csv(path: Path) -> list[dict[str, Any]]:
    """Read a turboSETI-format hit-table CSV into a list of row dicts.

    Returns rows with normalized keys matching RadioHit field names:
      frequency_hz, snr, drift_rate_hz_per_sec, source_name, mjd, ra_deg, dec_deg
    Frequencies are converted from MHz to Hz.
    """
    import csv

    rows: list[dict[str, Any]] = []
    with open(path, newline="") as f:
        # turboSETI files sometimes begin with comment lines starting with '#'
        lines = [ln for ln in f if not ln.startswith("#")]

    reader = csv.DictReader(lines)
    for raw in reader:
        raw = {k.strip(): v.strip() for k, v in raw.items() if k is not None}

        freq_mhz = _resolve_col(raw, _FREQ_ALIASES)
        snr = _resolve_col(raw, _SNR_ALIASES)
        drift = _resolve_col(raw, _DRIFT_ALIASES)

        if freq_mhz is None or snr is None or drift is None:
            continue

        row: dict[str, Any] = {
            "frequency_hz": float(freq_mhz) * 1e6,
            "snr": float(snr),
            "drift_rate_hz_per_sec": float(drift),
            "source_name": raw.get("Source_Name", ""),
            "mjd": float(raw["MJD"]) if raw.get("MJD") else None,
            "ra_deg": float(raw["RA"]) if raw.get("RA") else None,
            "dec_deg": float(raw["DEC"]) if raw.get("DEC") else None,
            "sefd": float(raw["SEFD"]) if raw.get("SEFD") else None,
        }
        rows.append(row)
    return rows


def hit_table_to_radio_hit_dicts(path: Path) -> list[dict[str, Any]]:
    """Read a real turboSETI CSV and return dicts compatible with parse_hit_table().

    Maps real column names to the RadioHit field names used by the prototype.
    """
    raw_rows = read_hit_table_csv(path)
    out = []
    for r in raw_rows:
        out.append({
            "frequency_hz": r["frequency_hz"],
            "snr": r["snr"],
            "drift_rate_hz_per_sec": r["drift_rate_hz_per_sec"],
            "bandwidth_hz": 2.79,   # turboSETI default channel width for L-band
            "scan_role": "on",       # single-dish files default to on-source
            "target_id": r.get("source_name") or "unknown",
        })
    return out
