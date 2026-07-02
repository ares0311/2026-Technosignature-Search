"""Track A satellite/transmitter matching: CelesTrak SATCAT/GP + SatNOGS DB.

Implements the remaining Phase 2 catalog from
docs/technosignature_datasets_agent_brief.md: satellite/orbital-object
rejection via CelesTrak SATCAT and active GP (orbital elements), combined
with SatNOGS transmitter frequency ranges. Unlike the four fixed-sky-position
catalogs in track_a_catalogs.py, this requires an observation timestamp (for
SGP4 orbit propagation) and an observer geographic location, not just a
candidate sky position.

The brief's matching rule: an event frequency overlapping a known SatNOGS
transmitter range AND SGP4-propagated satellite position placing that object
near the telescope beam at observation time -> classify as
`satellite_transmitter`.

This module never hardcodes a telescope's geographic location -- no such
value exists anywhere in this repository, and guessing one would put an
unverified coordinate in a rejection-safety-critical path. Callers must
supply observer_lat_deg/observer_lon_deg/observer_elevation_m explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from techno_search.track_a_data_guard import (
    AcquisitionManifestRecord,
    append_acquisition_manifest,
    check_disk_budget_or_raise,
    log_progress,
)

TRACK_A_SATELLITE_MATCH_SCHEMA_VERSION = "track_a_satellite_match_v1"

TRACK_A_SATELLITE_MATCH_DISCLAIMER = (
    "Track A satellite/transmitter matching is a deterministic known-source "
    "check only. No match does not confirm technosignature interest, and a "
    "match does not require confirmation from any other Track A check. This "
    "is not a claim about candidate anomaly status."
)

CELESTRAK_SATCAT_MIN_ROW_COUNT = 30000
CELESTRAK_GP_ACTIVE_MIN_ROW_COUNT = 10000

SATNOGS_ENDPOINTS = ("satellites", "transmitters", "tle", "modes")

DEFAULT_BEAM_RADIUS_DEG = 0.5


def default_satellite_cache_dir(project_root: Path | None = None, *, source: str) -> Path:
    root = project_root or Path(__file__).resolve().parents[2]
    return root / "data_cache" / "raw" / source


# ---------------------------------------------------------------------------
# CelesTrak acquisition
# ---------------------------------------------------------------------------


def acquire_celestrak_satcat(
    *, manifest_path: Path | None = None, project_root: Path | None = None
) -> AcquisitionManifestRecord:
    """Download the CelesTrak SATCAT (all tracked objects) as CSV."""

    try:
        import pandas as pd
        import requests
    except ImportError as exc:
        msg = "requests and pandas are required to acquire CelesTrak SATCAT."
        raise RuntimeError(msg) from exc

    root = project_root or Path(__file__).resolve().parents[2]
    check_disk_budget_or_raise(project_root=root, additional_expected_bytes=20 * 1024 * 1024)

    out_dir = default_satellite_cache_dir(root, source="celestrak")
    out_dir.mkdir(parents=True, exist_ok=True)
    url = "https://celestrak.org/satcat/records.php?FORMAT=CSV"
    csv_path = out_dir / "satcat.csv"

    log_progress(f"[START] Downloading CelesTrak SATCAT from {url}")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    csv_path.write_bytes(response.content)
    log_progress(f"[INFO] Downloaded {len(response.content)} bytes, parsing CSV")

    df = pd.read_csv(csv_path)
    if len(df) <= CELESTRAK_SATCAT_MIN_ROW_COUNT:
        msg = (
            f"CelesTrak SATCAT row count too low: expected >{CELESTRAK_SATCAT_MIN_ROW_COUNT}, "
            f"got {len(df)}"
        )
        raise RuntimeError(msg)

    parquet_path = out_dir / "satcat.parquet"
    df.to_parquet(parquet_path, index=False)
    log_progress(f"[OK] Wrote {len(df)} verified rows -> {parquet_path}")

    record = AcquisitionManifestRecord(
        source_name="celestrak_satcat",
        source_url=url,
        access_method="requests.get + pandas.read_csv",
        downloaded_at_utc=datetime.now(UTC).isoformat(),
        local_path=str(parquet_path),
        file_size_bytes=parquet_path.stat().st_size,
        row_count=len(df),
        auth_required=False,
        license_or_terms="CelesTrak SATCAT, public",
    )
    manifest = manifest_path or (root / "artifacts" / "manifests" / "data_manifest.jsonl")
    append_acquisition_manifest(record, manifest)
    return record


def acquire_celestrak_gp_active(
    *, manifest_path: Path | None = None, project_root: Path | None = None
) -> AcquisitionManifestRecord:
    """Download CelesTrak active-satellite GP (orbital element) data as JSON."""

    try:
        import pandas as pd
        import requests
    except ImportError as exc:
        msg = "requests and pandas are required to acquire CelesTrak active GP data."
        raise RuntimeError(msg) from exc

    root = project_root or Path(__file__).resolve().parents[2]
    check_disk_budget_or_raise(project_root=root, additional_expected_bytes=20 * 1024 * 1024)

    out_dir = default_satellite_cache_dir(root, source="celestrak")
    out_dir.mkdir(parents=True, exist_ok=True)
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json"
    json_path = out_dir / "gp_active.json"

    log_progress(f"[START] Downloading CelesTrak active GP data from {url}")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    json_path.write_bytes(response.content)
    log_progress(f"[INFO] Downloaded {len(response.content)} bytes, parsing JSON")

    df = pd.read_json(json_path)
    if len(df) <= CELESTRAK_GP_ACTIVE_MIN_ROW_COUNT:
        msg = (
            "CelesTrak active GP row count too low: expected "
            f">{CELESTRAK_GP_ACTIVE_MIN_ROW_COUNT}, got {len(df)}"
        )
        raise RuntimeError(msg)

    parquet_path = out_dir / "gp_active.parquet"
    df.to_parquet(parquet_path, index=False)
    log_progress(f"[OK] Wrote {len(df)} verified rows -> {parquet_path}")

    record = AcquisitionManifestRecord(
        source_name="celestrak_gp_active",
        source_url=url,
        access_method="requests.get + pandas.read_json",
        downloaded_at_utc=datetime.now(UTC).isoformat(),
        local_path=str(parquet_path),
        file_size_bytes=parquet_path.stat().st_size,
        row_count=len(df),
        auth_required=False,
        license_or_terms="CelesTrak GP data, public",
    )
    manifest = manifest_path or (root / "artifacts" / "manifests" / "data_manifest.jsonl")
    append_acquisition_manifest(record, manifest)
    return record


# ---------------------------------------------------------------------------
# SatNOGS acquisition
# ---------------------------------------------------------------------------


def _fetch_satnogs_paginated(endpoint: str) -> list[dict[str, Any]]:
    import requests

    url: str | None = f"https://db.satnogs.org/api/{endpoint}/"
    rows: list[dict[str, Any]] = []
    while url:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and "results" in payload:
            rows.extend(payload["results"])
            next_url = payload.get("next")
            url = str(next_url) if next_url else None
        elif isinstance(payload, list):
            rows.extend(payload)
            url = None
        else:
            msg = f"Unexpected SatNOGS payload shape for endpoint {endpoint!r}"
            raise RuntimeError(msg)
    return rows


def acquire_satnogs_endpoint(
    endpoint: str,
    *,
    manifest_path: Path | None = None,
    project_root: Path | None = None,
) -> AcquisitionManifestRecord:
    """Download one SatNOGS DB public endpoint (paginated REST) as parquet."""

    if endpoint not in SATNOGS_ENDPOINTS:
        msg = f"Unknown SatNOGS endpoint: {endpoint!r}, expected one of {SATNOGS_ENDPOINTS}"
        raise ValueError(msg)

    try:
        import pandas as pd
    except ImportError as exc:
        msg = "pandas is required to acquire SatNOGS data."
        raise RuntimeError(msg) from exc

    root = project_root or Path(__file__).resolve().parents[2]
    check_disk_budget_or_raise(project_root=root, additional_expected_bytes=50 * 1024 * 1024)

    out_dir = default_satellite_cache_dir(root, source="satnogs")
    out_dir.mkdir(parents=True, exist_ok=True)

    url = f"https://db.satnogs.org/api/{endpoint}/"
    log_progress(f"[START] Downloading SatNOGS {endpoint} from {url}")
    rows = _fetch_satnogs_paginated(endpoint)
    log_progress(f"[INFO] Downloaded {len(rows)} rows from {endpoint}")
    if not rows:
        msg = f"SatNOGS endpoint {endpoint!r} returned zero rows"
        raise RuntimeError(msg)

    df = pd.DataFrame(rows)
    jsonl_path = out_dir / f"{endpoint}.jsonl"
    parquet_path = out_dir / f"{endpoint}.parquet"
    df.to_json(jsonl_path, orient="records", lines=True)
    df.to_parquet(parquet_path, index=False)
    log_progress(f"[OK] Wrote {len(df)} rows -> {parquet_path}")

    record = AcquisitionManifestRecord(
        source_name=f"satnogs_{endpoint}",
        source_url=url,
        access_method="requests.get (paginated REST)",
        downloaded_at_utc=datetime.now(UTC).isoformat(),
        local_path=str(parquet_path),
        file_size_bytes=parquet_path.stat().st_size,
        row_count=len(df),
        auth_required=False,
        license_or_terms="SatNOGS DB, public read access",
    )
    manifest = manifest_path or (root / "artifacts" / "manifests" / "data_manifest.jsonl")
    append_acquisition_manifest(record, manifest)
    return record


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransmitterFrequencyMatch:
    """One SatNOGS transmitter whose declared range covers the event frequency."""

    norad_cat_id: str
    transmitter_uuid: str
    downlink_low_hz: float | None
    downlink_high_hz: float | None
    uplink_low_hz: float | None
    uplink_high_hz: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "norad_cat_id": self.norad_cat_id,
            "transmitter_uuid": self.transmitter_uuid,
            "downlink_low_hz": self.downlink_low_hz,
            "downlink_high_hz": self.downlink_high_hz,
            "uplink_low_hz": self.uplink_low_hz,
            "uplink_high_hz": self.uplink_high_hz,
        }


def _load_satnogs_transmitters(project_root: Path | None) -> Any | None:
    import pandas as pd

    path = default_satellite_cache_dir(project_root, source="satnogs") / "transmitters.parquet"
    if not path.exists():
        return None
    return pd.read_parquet(path)


def _load_celestrak_gp_active(project_root: Path | None) -> Any | None:
    import pandas as pd

    path = default_satellite_cache_dir(project_root, source="celestrak") / "gp_active.parquet"
    if not path.exists():
        return None
    return pd.read_parquet(path)


def _frequency_matches(value: float, low: Any, high: Any, tolerance_hz: float) -> bool:
    try:
        low_f = float(low)
        high_f = float(high)
    except (TypeError, ValueError):
        return False
    return bool((low_f - tolerance_hz) <= value <= (high_f + tolerance_hz))


def _find_transmitter_matches(
    frequency_hz: float,
    transmitters: Any,
    *,
    tolerance_hz: float,
) -> list[TransmitterFrequencyMatch]:
    matches: list[TransmitterFrequencyMatch] = []
    for _, row in transmitters.iterrows():
        downlink_hit = _frequency_matches(
            frequency_hz, row.get("downlink_low"), row.get("downlink_high"), tolerance_hz
        )
        uplink_hit = _frequency_matches(
            frequency_hz, row.get("uplink_low"), row.get("uplink_high"), tolerance_hz
        )
        if downlink_hit or uplink_hit:
            matches.append(
                TransmitterFrequencyMatch(
                    norad_cat_id=str(row.get("norad_cat_id", "")),
                    transmitter_uuid=str(row.get("uuid", "")),
                    downlink_low_hz=row.get("downlink_low"),
                    downlink_high_hz=row.get("downlink_high"),
                    uplink_low_hz=row.get("uplink_low"),
                    uplink_high_hz=row.get("uplink_high"),
                )
            )
    return matches


def _propagated_separation_deg(
    *,
    omm_fields: dict[str, Any],
    observation_time_utc: datetime,
    observer_lat_deg: float,
    observer_lon_deg: float,
    observer_elevation_m: float,
    ra_deg: float,
    dec_deg: float,
) -> float:
    """Propagate a satellite's position via SGP4 from CCSDS OMM fields.

    CelesTrak's gp.php?FORMAT=json endpoint returns CCSDS OMM (CCSDS
    502.0-B-3) orbital elements, not raw two-line-element strings, so this
    uses Skyfield's EarthSatellite.from_omm() rather than constructing TLE
    lines by hand.
    """

    from skyfield.api import EarthSatellite, load, wgs84

    ts = load.timescale()
    satellite = EarthSatellite.from_omm(ts, omm_fields)
    observer = wgs84.latlon(
        observer_lat_deg, observer_lon_deg, elevation_m=observer_elevation_m
    )
    t = ts.from_datetime(observation_time_utc)
    difference = satellite - observer
    topocentric = difference.at(t)
    sat_ra, sat_dec, _ = topocentric.radec()

    from astropy import units as u
    from astropy.coordinates import SkyCoord

    beam = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg)
    sat_pos = SkyCoord(ra=sat_ra.hours * 15.0 * u.deg, dec=sat_dec.degrees * u.deg)
    return float(beam.separation(sat_pos).degree)


def match_satellite_transmitter(
    *,
    frequency_hz: float,
    observation_time_utc: datetime,
    ra_deg: float,
    dec_deg: float,
    observer_lat_deg: float,
    observer_lon_deg: float,
    observer_elevation_m: float,
    frequency_tolerance_hz: float = 1000.0,
    beam_radius_deg: float = DEFAULT_BEAM_RADIUS_DEG,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Check whether an event is explained by a known satellite transmitter.

    Implements the brief's matching rule: classify as `satellite_transmitter`
    only when both (a) the event frequency overlaps a known SatNOGS
    transmitter's declared downlink/uplink range, AND (b) SGP4-propagated
    position of that same satellite at observation_time_utc, as seen from
    the given observer location, falls within beam_radius_deg of
    (ra_deg, dec_deg).

    observer_lat_deg/observer_lon_deg/observer_elevation_m must be supplied
    by the caller -- this module does not hardcode any telescope location.
    """

    transmitters = _load_satnogs_transmitters(project_root)
    gp_active = _load_celestrak_gp_active(project_root)

    if transmitters is None or gp_active is None:
        loaded = {
            "satnogs_transmitters": transmitters,
            "celestrak_gp_active": gp_active,
        }
        missing = [name for name, df in loaded.items() if df is None]
        return {
            "schema_version": TRACK_A_SATELLITE_MATCH_SCHEMA_VERSION,
            "disclaimer": TRACK_A_SATELLITE_MATCH_DISCLAIMER,
            "classification": "low_confidence",
            "catalogs_missing": missing,
            "frequency_matches": [],
            "confirmed_matches": [],
        }

    frequency_matches = _find_transmitter_matches(
        frequency_hz, transmitters, tolerance_hz=frequency_tolerance_hz
    )

    confirmed: list[dict[str, Any]] = []
    for match in frequency_matches:
        gp_row = gp_active[gp_active["NORAD_CAT_ID"].astype(str) == match.norad_cat_id]
        if gp_row.empty:
            continue
        omm_fields = gp_row.iloc[0].to_dict()
        try:
            separation_deg = _propagated_separation_deg(
                omm_fields=omm_fields,
                observation_time_utc=observation_time_utc,
                observer_lat_deg=observer_lat_deg,
                observer_lon_deg=observer_lon_deg,
                observer_elevation_m=observer_elevation_m,
                ra_deg=ra_deg,
                dec_deg=dec_deg,
            )
        except Exception:  # noqa: BLE001 - propagation of malformed OMM data must not crash the gate
            continue
        if separation_deg <= beam_radius_deg:
            confirmed.append({**match.as_dict(), "separation_deg": separation_deg})

    classification = "satellite_transmitter" if confirmed else "no_known_match"

    return {
        "schema_version": TRACK_A_SATELLITE_MATCH_SCHEMA_VERSION,
        "disclaimer": TRACK_A_SATELLITE_MATCH_DISCLAIMER,
        "classification": classification,
        "catalogs_missing": [],
        "frequency_matches": [m.as_dict() for m in frequency_matches],
        "confirmed_matches": confirmed,
    }
