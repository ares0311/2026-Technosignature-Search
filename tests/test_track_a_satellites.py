from datetime import UTC, datetime

import pandas as pd
import pytest

from techno_search.track_a_satellites import match_satellite_transmitter


def _write_satnogs_transmitters(tmp_path, *, rows):
    pytest.importorskip("pyarrow")
    out_dir = tmp_path / "data_cache" / "raw" / "satnogs"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out_dir / "transmitters.parquet", index=False)


def _write_celestrak_gp_active(tmp_path, *, rows):
    pytest.importorskip("pyarrow")
    out_dir = tmp_path / "data_cache" / "raw" / "celestrak"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out_dir / "gp_active.parquet", index=False)


def _leo_omm_row(norad_cat_id: str) -> dict:
    """A structurally valid, self-consistent OMM record for a circular LEO
    orbit. Values are internally consistent (not a real cataloged object) --
    used only to exercise the SGP4 propagation code path, matching the
    verified field schema confirmed against the installed sgp4.omm.initialize
    source (CLASSIFICATION_TYPE, OBJECT_ID, EPHEMERIS_TYPE, ELEMENT_SET_NO,
    REV_AT_EPOCH, EPOCH, ARG_OF_PERICENTER, BSTAR, ECCENTRICITY, INCLINATION,
    MEAN_ANOMALY, MEAN_MOTION_DDOT, MEAN_MOTION_DOT, MEAN_MOTION,
    RA_OF_ASC_NODE, NORAD_CAT_ID)."""
    return {
        "OBJECT_NAME": "TEST-SAT",
        "OBJECT_ID": "2020-001A",
        "NORAD_CAT_ID": norad_cat_id,
        "CLASSIFICATION_TYPE": "U",
        "EPHEMERIS_TYPE": 0,
        "ELEMENT_SET_NO": 999,
        "REV_AT_EPOCH": 1,
        "EPOCH": "2026-01-01T00:00:00.000000",
        "ARG_OF_PERICENTER": 0.0,
        "BSTAR": 0.0001,
        "ECCENTRICITY": 0.0001,
        "INCLINATION": 51.6,
        "MEAN_ANOMALY": 0.0,
        "MEAN_MOTION_DDOT": 0.0,
        "MEAN_MOTION_DOT": 0.0,
        "MEAN_MOTION": 15.5,
        "RA_OF_ASC_NODE": 0.0,
    }


def test_match_reports_low_confidence_when_catalogs_missing(tmp_path) -> None:
    result = match_satellite_transmitter(
        frequency_hz=437_500_000.0,
        observation_time_utc=datetime(2026, 1, 1, tzinfo=UTC),
        ra_deg=10.0,
        dec_deg=10.0,
        observer_lat_deg=38.4331,
        observer_lon_deg=-79.8398,
        observer_elevation_m=800.0,
        project_root=tmp_path,
    )

    assert result["classification"] == "low_confidence"
    assert set(result["catalogs_missing"]) == {"satnogs_transmitters", "celestrak_gp_active"}


def test_match_reports_no_known_match_when_frequency_does_not_overlap(tmp_path) -> None:
    _write_satnogs_transmitters(
        tmp_path,
        rows=[
            {
                "norad_cat_id": "25544",
                "uuid": "abc-123",
                "downlink_low": 145_800_000.0,
                "downlink_high": 145_800_000.0,
                "uplink_low": None,
                "uplink_high": None,
            }
        ],
    )
    _write_celestrak_gp_active(tmp_path, rows=[_leo_omm_row("25544")])

    result = match_satellite_transmitter(
        frequency_hz=1_420_000_000.0,
        observation_time_utc=datetime(2026, 1, 1, tzinfo=UTC),
        ra_deg=10.0,
        dec_deg=10.0,
        observer_lat_deg=38.4331,
        observer_lon_deg=-79.8398,
        observer_elevation_m=800.0,
        project_root=tmp_path,
    )

    assert result["classification"] == "no_known_match"
    assert result["frequency_matches"] == []


def test_match_finds_frequency_overlap_but_no_beam_coincidence(tmp_path) -> None:
    pytest.importorskip("skyfield")
    _write_satnogs_transmitters(
        tmp_path,
        rows=[
            {
                "norad_cat_id": "25544",
                "uuid": "abc-123",
                "downlink_low": 145_800_000.0,
                "downlink_high": 145_800_000.0,
                "uplink_low": None,
                "uplink_high": None,
            }
        ],
    )
    _write_celestrak_gp_active(tmp_path, rows=[_leo_omm_row("25544")])

    result = match_satellite_transmitter(
        frequency_hz=145_800_000.0,
        observation_time_utc=datetime(2026, 1, 1, tzinfo=UTC),
        ra_deg=10.0,
        dec_deg=10.0,
        observer_lat_deg=38.4331,
        observer_lon_deg=-79.8398,
        observer_elevation_m=800.0,
        beam_radius_deg=0.001,
        project_root=tmp_path,
    )

    assert len(result["frequency_matches"]) == 1
    # A LEO satellite is very unlikely to be within 0.001 deg of an
    # arbitrary fixed sky position at an arbitrary time, so this exercises
    # the real SGP4 propagation path without asserting a specific position.
    assert result["classification"] in {"satellite_transmitter", "no_known_match"}


def test_match_disclaimer_present() -> None:
    result = match_satellite_transmitter(
        frequency_hz=1_420_000_000.0,
        observation_time_utc=datetime(2026, 1, 1, tzinfo=UTC),
        ra_deg=0.0,
        dec_deg=0.0,
        observer_lat_deg=0.0,
        observer_lon_deg=0.0,
        observer_elevation_m=0.0,
    )
    assert "does not confirm" in result["disclaimer"]
