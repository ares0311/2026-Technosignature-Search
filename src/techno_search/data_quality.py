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
    valid_tracks = {"radio", "infrared", "anomaly", "photometry"}
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
    if track_lower == "photometry":
        if suffix not in {".fits", ".fit"}:
            warnings.append(f"Unexpected file suffix '{suffix}'; expected .fits or .fit")
    elif suffix not in {".csv", ".txt", ".dat"}:
        warnings.append(f"Unexpected file suffix '{suffix}'; expected .csv, .txt, or .dat")

    try:
        if track_lower == "radio":
            row_count, issues, warnings = _validate_radio(path, issues, warnings)
        elif track_lower == "infrared":
            row_count, issues, warnings = _validate_infrared(path, issues, warnings)
        elif track_lower == "photometry":
            row_count, issues, warnings = _validate_photometry(path, issues, warnings)
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


def _count_raw_radio_data_lines(path: Path) -> int:
    """Count non-comment, non-header data lines in a turboSETI hit table."""
    raw_text = path.read_text(encoding="utf-8", errors="replace")
    lines = raw_text.splitlines()
    # TAB-format: data lines appear after the "# Top_Hit_#" header, no leading "#"
    past_header = False
    data_count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# Top_Hit_#") or stripped.startswith("#Top_Hit_#"):
            past_header = True
            continue
        if past_header and not stripped.startswith("#"):
            data_count += 1
        elif not stripped.startswith("#"):
            # CSV fallback: non-comment, non-blank line that could be a data row
            data_count += 1
    # Subtract 1 for the CSV header row (plain first non-comment line)
    return max(0, data_count - (0 if past_header else 1))


def _validate_radio(
    path: Path, issues: list[str], warnings: list[str]
) -> tuple[int, list[str], list[str]]:
    # Use the full reader so .dat files (TAB-separated turboSETI format) work
    from techno_search.radio.hit_table_reader import read_hit_table_csv

    try:
        normalized_rows = read_hit_table_csv(path)
    except Exception as exc:  # noqa: BLE001
        issues.append(f"Failed to parse radio hit table: {exc}")
        return 0, issues, warnings

    if not normalized_rows:
        raw_data_lines = _count_raw_radio_data_lines(path)
        if raw_data_lines > 0:
            # Data rows exist but all failed to parse — structurally bad file
            issues.append(
                "No valid hits found in radio hit table "
                "(all rows failed to parse — bad format or non-numeric values)."
            )
        else:
            # No data rows at all — legitimate turboSETI non-detection
            warnings.append(
                "No hits found above threshold in radio hit table. "
                "This is a valid non-detection result."
            )
        return 0, issues, warnings

    # Verify normalized rows have required keys
    for row in normalized_rows[:3]:
        if "frequency_hz" not in row or row["frequency_hz"] is None:
            issues.append("Hit row missing frequency_hz after normalization.")
        if "snr" not in row or row["snr"] is None:
            issues.append("Hit row missing snr after normalization.")

    return len(normalized_rows), issues, warnings


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


def _validate_photometry(
    path: Path, issues: list[str], warnings: list[str]
) -> tuple[int, list[str], list[str]]:
    try:
        from techno_search.photometry.lightcurve_io import load_lightcurve_file
    except Exception as exc:  # noqa: BLE001
        issues.append(f"Failed to import photometry reader: {exc}")
        return 0, issues, warnings

    try:
        lc = load_lightcurve_file(path)
    except RuntimeError as exc:
        issues.append(str(exc))
        return 0, issues, warnings
    except Exception as exc:  # noqa: BLE001
        issues.append(f"Failed to read light curve file: {exc}")
        return 0, issues, warnings

    row_count = int(len(lc.time))
    if row_count == 0:
        issues.append("Light curve file has zero cadences.")
    elif row_count < 10:
        warnings.append(f"Very short light curve: {row_count} cadences.")

    return row_count, issues, warnings
