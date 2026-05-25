"""Data quality validator for pipeline input files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATA_QUALITY_SCHEMA_VERSION = "data_quality_v1"
DATA_QUALITY_DISCLAIMER = (
    "Data quality validation checks input file structure for local pipeline "
    "execution only. It does not inspect real astronomical significance, "
    "modify candidate scores, authorize live data access, authorize external "
    "submission, or constitute a detection claim."
)


@dataclass
class DataQualityResult:
    path: Path
    track: str
    ok: bool
    row_count: int
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": DATA_QUALITY_SCHEMA_VERSION,
            "disclaimer": DATA_QUALITY_DISCLAIMER,
            "path": str(self.path),
            "track": self.track,
            "ok": self.ok,
            "row_count": self.row_count,
            "issue_count": len(self.issues),
            "warning_count": len(self.warnings),
            "issues": self.issues,
            "warnings": self.warnings,
        }


def validate_input(path: Path, track: str) -> DataQualityResult:
    """Validate a pipeline input file for the given track.

    Returns a DataQualityResult with issues (blocking) and warnings (informational).
    Does not read astronomical data values; only checks structural correctness.
    """
    issues: list[str] = []
    warnings: list[str] = []
    row_count = 0

    if not path.exists():
        return DataQualityResult(
            path=path,
            track=track,
            ok=False,
            row_count=0,
            issues=[f"File not found: {path}"],
        )

    track_lower = track.lower()
    valid_tracks = {"radio", "infrared", "anomaly"}
    if track_lower not in valid_tracks:
        msg = f"Unknown track '{track}'. Expected: {sorted(valid_tracks)}"
        return DataQualityResult(
            path=path,
            track=track,
            ok=False,
            row_count=0,
            issues=[msg],
        )

    suffix = path.suffix.lower()
    if suffix not in {".csv", ".txt"}:
        warnings.append(f"Unexpected file suffix '{suffix}'; expected .csv or .txt")

    try:
        if track_lower == "radio":
            row_count, issues, warnings = _validate_radio(path, issues, warnings)
        elif track_lower == "infrared":
            row_count, issues, warnings = _validate_infrared(path, issues, warnings)
        else:
            row_count, issues, warnings = _validate_anomaly(path, issues, warnings)
    except Exception as exc:  # noqa: BLE001
        issues.append(f"Failed to read file: {exc}")

    return DataQualityResult(
        path=path,
        track=track_lower,
        ok=len(issues) == 0,
        row_count=row_count,
        issues=issues,
        warnings=warnings,
    )


def _read_csv_lines(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a CSV, skipping comment lines; return (header_fields, row_dicts)."""
    import csv

    with path.open(encoding="utf-8", newline="") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    if not lines:
        return [], []
    reader = csv.DictReader(lines)
    rows = [{k.strip(): (v.strip() if v else "") for k, v in row.items() if k} for row in reader]
    return list(reader.fieldnames or []), rows


def _validate_radio(
    path: Path, issues: list[str], warnings: list[str]
) -> tuple[int, list[str], list[str]]:
    _headers, rows = _read_csv_lines(path)
    if not rows:
        issues.append("No data rows found in radio hit table.")
        return 0, issues, warnings

    # Required columns (accepting aliases)
    freq_aliases = {"frequency", "freq", "frequency_mhz"}
    snr_aliases = {"snr"}
    drift_aliases = {"drift_rate", "drift_rate_hz_per_sec", "driftrate"}

    sample = {k.lower() for k in rows[0]}
    if not sample & freq_aliases:
        issues.append(f"Missing frequency column. Expected one of: {sorted(freq_aliases)}")
    if not sample & snr_aliases:
        issues.append(f"Missing SNR column. Expected one of: {sorted(snr_aliases)}")
    if not sample & drift_aliases:
        warnings.append(f"Missing drift rate column. Expected one of: {sorted(drift_aliases)}")

    # Check for parseable numeric values in first row
    for row in rows[:3]:
        for k, v in row.items():
            if k.lower() in freq_aliases | snr_aliases and v:
                try:
                    float(v)
                except ValueError:
                    issues.append(f"Non-numeric value in column '{k}': '{v}'")

    return len(rows), issues, warnings


def _validate_infrared(
    path: Path, issues: list[str], warnings: list[str]
) -> tuple[int, list[str], list[str]]:
    _headers, rows = _read_csv_lines(path)
    if not rows:
        issues.append("No data rows found in infrared catalog file.")
        return 0, issues, warnings

    ra_aliases = {"ra", "ra_deg", "ra_j2000"}
    dec_aliases = {"dec", "dec_deg", "dec_j2000"}
    sample = {k.lower() for k in rows[0]}

    if not sample & ra_aliases:
        issues.append(f"Missing RA column. Expected one of: {sorted(ra_aliases)}")
    if not sample & dec_aliases:
        issues.append(f"Missing Dec column. Expected one of: {sorted(dec_aliases)}")

    # Check for parseable coordinate values
    for row in rows[:3]:
        for k, v in row.items():
            if k.lower() in ra_aliases | dec_aliases and v:
                try:
                    float(v)
                except ValueError:
                    issues.append(f"Non-numeric coordinate value in column '{k}': '{v}'")

    if len(rows) == 0:
        warnings.append("No rows after header; empty catalog file.")
    elif len(rows) > 10000:
        warnings.append(f"Large input file: {len(rows)} rows. Consider filtering before pipeline.")

    return len(rows), issues, warnings


def _validate_anomaly(
    path: Path, issues: list[str], warnings: list[str]
) -> tuple[int, list[str], list[str]]:
    _headers, rows = _read_csv_lines(path)
    if not rows:
        issues.append("No data rows found in anomaly feature file.")
        return 0, issues, warnings

    required = {
        "historical_epoch",
        "modern_epoch",
        "historical_magnitude",
    }
    sample = {k.lower() for k in rows[0]}
    missing = sorted(required - sample)
    for column in missing:
        issues.append(f"Missing anomaly column: {column}")

    numeric_columns = {
        "ra",
        "dec",
        "historical_epoch",
        "modern_epoch",
        "historical_magnitude",
        "modern_magnitude",
        "modern_limit_magnitude",
        "crossmatch_distance_arcsec",
        "crossmatch_confidence",
        "historical_detection_score",
        "proper_motion_explanation_score",
        "survey_depth_explanation_score",
        "artifact_score",
        "moving_object_score",
        "variability_score",
        "catalog_mismatch_score",
    }
    for row in rows[:3]:
        for key, value in row.items():
            if key.lower() in numeric_columns and value:
                try:
                    float(value)
                except ValueError:
                    issues.append(f"Non-numeric anomaly value in column '{key}': '{value}'")
    return len(rows), issues, warnings
