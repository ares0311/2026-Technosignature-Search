"""Reader for archival/catalog anomaly CSV feature files."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

_NUMERIC_FIELDS = {
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

_NULL_VALUES = {"", "null", "NULL", "nan", "NaN", "none", "None"}


def _coerce_value(key: str, value: str) -> Any:
    cleaned = value.strip()
    if cleaned in _NULL_VALUES:
        return None
    if key.lower() in _NUMERIC_FIELDS:
        return float(cleaned)
    return cleaned


def read_anomaly_csv(path: Path) -> list[dict[str, Any]]:
    """Read a synthetic-compatible archival/catalog anomaly CSV.

    The reader normalizes comment-prefixed CSV files into feature dictionaries
    accepted by ``build_anomaly_candidate``. It is a structural ingestion helper
    only; values remain provenance inputs and are not detection claims.
    """

    with path.open(encoding="utf-8", newline="") as handle:
        lines = [line for line in handle if not line.startswith("#")]

    reader = csv.DictReader(lines)
    rows: list[dict[str, Any]] = []
    for raw in reader:
        row = {
            key.strip(): _coerce_value(key, value)
            for key, value in raw.items()
            if key is not None and value is not None
        }
        if row:
            rows.append(row)
    return rows


def anomaly_rows_to_candidate_dicts(path: Path) -> list[dict[str, Any]]:
    """Return anomaly feature rows compatible with the anomaly prototype."""

    return read_anomaly_csv(path)
