"""Operational provenance records for site weather monitoring events."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

WEATHER_LOG_SCHEMA_VERSION = "weather_log_v1"

WEATHER_LOG_DISCLAIMER = (
    "Weather log entries are operational provenance records — "
    "a weather record does not modify candidate scores or pathway routing, "
    "does not authorize external submission, and does not constitute a detection claim."
)

ALLOWED_WEATHER_KINDS = frozenset(
    {
        "wind_speed",
        "temperature",
        "humidity",
        "precipitation",
        "seeing",
    }
)

ALLOWED_WEATHER_STATUSES = frozenset(
    {
        "nominal",
        "advisory",
        "warning",
        "observation_hold",
    }
)


@dataclass
class WeatherEntry:
    entry_id: str
    weather_kind: str
    status: str
    recorded_by: str
    timestamp_utc: str
    site_id: str | None
    value: float | None
    unit: str | None
    notes: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "weather_kind": self.weather_kind,
            "status": self.status,
            "recorded_by": self.recorded_by,
            "timestamp_utc": self.timestamp_utc,
            "site_id": self.site_id,
            "value": self.value,
            "unit": self.unit,
            "notes": self.notes,
        }


def load_weather_entries(path: Path | None = None) -> list[WeatherEntry]:
    if path is None:
        path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "fixtures"
            / "weather_log.json"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        WeatherEntry(
            entry_id=e["entry_id"],
            weather_kind=e["weather_kind"],
            status=e["status"],
            recorded_by=e["recorded_by"],
            timestamp_utc=e["timestamp_utc"],
            site_id=e.get("site_id"),
            value=e.get("value"),
            unit=e.get("unit"),
            notes=e.get("notes"),
        )
        for e in raw["entries"]
    ]


def weather_log_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_weather_entries(path)
    counts_by_status: dict[str, int] = {}
    for e in entries:
        counts_by_status[e.status] = counts_by_status.get(e.status, 0) + 1
    counts_by_kind: dict[str, int] = {}
    for e in entries:
        counts_by_kind[e.weather_kind] = counts_by_kind.get(e.weather_kind, 0) + 1
    return {
        "schema_version": WEATHER_LOG_SCHEMA_VERSION,
        "disclaimer": WEATHER_LOG_DISCLAIMER,
        "entry_count": len(entries),
        "nominal_count": counts_by_status.get("nominal", 0),
        "advisory_count": counts_by_status.get("advisory", 0),
        "warning_count": counts_by_status.get("warning", 0),
        "observation_hold_count": counts_by_status.get("observation_hold", 0),
        "counts_by_status": counts_by_status,
        "counts_by_kind": counts_by_kind,
    }
