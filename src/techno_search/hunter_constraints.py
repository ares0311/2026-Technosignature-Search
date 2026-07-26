"""Validated optional constraints shared by Hunter selection and discovery."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def normalize_constraints(
    constraints: Mapping[str, Any] | None,
) -> dict[str, Any]:
    values = dict(constraints or {})
    normalized: dict[str, Any] = {}
    for name in (
        "min_ra_deg",
        "max_ra_deg",
        "min_dec_deg",
        "max_dec_deg",
        "min_abs_galactic_latitude_deg",
        "max_estimated_download_gb",
    ):
        value = values.get(name)
        if value is not None:
            normalized[name] = float(value)
    prefixes = sorted(
        {
            str(prefix).strip().upper()
            for prefix in values.get("target_prefixes", ())
            if str(prefix).strip()
        }
    )
    if prefixes:
        normalized["target_prefixes"] = prefixes
    if not 0 <= normalized.get("min_ra_deg", 0) <= 360:
        raise ValueError("min_ra_deg must be between 0 and 360")
    if not 0 <= normalized.get("max_ra_deg", 360) <= 360:
        raise ValueError("max_ra_deg must be between 0 and 360")
    if normalized.get("min_ra_deg", 0) > normalized.get("max_ra_deg", 360):
        raise ValueError("min_ra_deg must not exceed max_ra_deg")
    if not -90 <= normalized.get("min_dec_deg", -90) <= 90:
        raise ValueError("min_dec_deg must be between -90 and 90")
    if not -90 <= normalized.get("max_dec_deg", 90) <= 90:
        raise ValueError("max_dec_deg must be between -90 and 90")
    if normalized.get("min_dec_deg", -90) > normalized.get("max_dec_deg", 90):
        raise ValueError("min_dec_deg must not exceed max_dec_deg")
    if not 0 <= normalized.get("min_abs_galactic_latitude_deg", 0) <= 90:
        raise ValueError(
            "min_abs_galactic_latitude_deg must be between 0 and 90"
        )
    if normalized.get("max_estimated_download_gb", 0) < 0:
        raise ValueError("max_estimated_download_gb must be non-negative")
    return normalized


def target_matches_constraints(
    row: Mapping[str, Any],
    constraints: Mapping[str, Any],
    *,
    allow_unknown_download_size: bool = False,
) -> bool:
    if not constraints:
        return True
    target_id = str(row.get("target_id") or row.get("hip") or "").upper()
    prefixes = constraints.get("target_prefixes", ())
    if prefixes and not any(target_id.startswith(prefix) for prefix in prefixes):
        return False
    checks = (
        ("ra_deg", "min_ra_deg", "max_ra_deg"),
        ("dec_deg", "min_dec_deg", "max_dec_deg"),
    )
    for field, minimum, maximum in checks:
        if minimum not in constraints and maximum not in constraints:
            continue
        value = _optional_float(row.get(field))
        if value is None:
            return False
        if minimum in constraints and value < float(constraints[minimum]):
            return False
        if maximum in constraints and value > float(constraints[maximum]):
            return False
    if "min_abs_galactic_latitude_deg" in constraints:
        latitude = _optional_float(row.get("galactic_latitude_deg"))
        if latitude is None or abs(latitude) < float(
            constraints["min_abs_galactic_latitude_deg"]
        ):
            return False
    if "max_estimated_download_gb" in constraints:
        size = _optional_float(row.get("estimated_download_gb"))
        if size is None and allow_unknown_download_size:
            return True
        if size is None or size > float(constraints["max_estimated_download_gb"]):
            return False
    return True


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(str(value))
