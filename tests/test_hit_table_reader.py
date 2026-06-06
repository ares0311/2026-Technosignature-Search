"""Tests for real turboSETI hit-table reader (CSV and .dat formats)."""
from __future__ import annotations

from pathlib import Path

import pytest

from techno_search.radio.hit_table_reader import (
    hit_table_to_radio_hit_dicts,
    read_hit_table_csv,
)
from techno_search.radio.prototype import parse_hit_table

pytest_approx = pytest.approx

FIXTURE = Path(__file__).parent / "fixtures" / "radio" / "sample_hits.csv"
FIXTURE_DAT = Path(__file__).parent / "fixtures" / "radio" / "sample_hits_real_format.dat"


def test_read_returns_five_rows() -> None:
    rows = read_hit_table_csv(FIXTURE)
    assert len(rows) == 5


def test_frequency_converted_mhz_to_hz() -> None:
    rows = read_hit_table_csv(FIXTURE)
    # 1420.405752 MHz → 1_420_405_752 Hz
    assert rows[0]["frequency_hz"] == pytest_approx(1_420_405_752.0)


def test_snr_parsed() -> None:
    rows = read_hit_table_csv(FIXTURE)
    assert rows[0]["snr"] == pytest_approx(25.3)


def test_drift_rate_parsed() -> None:
    rows = read_hit_table_csv(FIXTURE)
    assert rows[0]["drift_rate_hz_per_sec"] == pytest_approx(-0.382)


def test_source_name_parsed() -> None:
    rows = read_hit_table_csv(FIXTURE)
    assert rows[0]["source_name"] == "GBT_synth_target"


def test_mjd_parsed() -> None:
    rows = read_hit_table_csv(FIXTURE)
    assert rows[0]["mjd"] == pytest_approx(59000.5)


def test_ra_dec_parsed() -> None:
    rows = read_hit_table_csv(FIXTURE)
    assert rows[0]["ra_deg"] == pytest_approx(83.8221)
    assert rows[0]["dec_deg"] == pytest_approx(22.0145)


def test_gps_l1_frequency_present() -> None:
    rows = read_hit_table_csv(FIXTURE)
    freqs_mhz = [r["frequency_hz"] / 1e6 for r in rows]
    assert any(abs(f - 1575.42) < 0.01 for f in freqs_mhz)


def test_hit_table_to_radio_hit_dicts_count() -> None:
    dicts = hit_table_to_radio_hit_dicts(FIXTURE)
    assert len(dicts) == 5


def test_radio_hit_dicts_have_required_keys() -> None:
    dicts = hit_table_to_radio_hit_dicts(FIXTURE)
    for d in dicts:
        assert "frequency_hz" in d
        assert "snr" in d
        assert "drift_rate_hz_per_sec" in d
        assert "scan_role" in d


def test_radio_hit_dicts_feed_parse_hit_table() -> None:
    dicts = hit_table_to_radio_hit_dicts(FIXTURE)
    hits = parse_hit_table(dicts)
    assert len(hits) == 5
    assert all(h.frequency_hz > 0 for h in hits)


def test_highest_snr_hit() -> None:
    rows = read_hit_table_csv(FIXTURE)
    best = max(rows, key=lambda r: r["snr"])
    # GPS L1 band at 1575.42 MHz has SNR 45.1 in fixture
    assert best["snr"] == pytest_approx(45.1)


# --- Real turboSETI .dat format tests ---

def test_dat_read_returns_five_rows() -> None:
    rows = read_hit_table_csv(FIXTURE_DAT)
    assert len(rows) == 5


def test_dat_frequency_converted_mhz_to_hz() -> None:
    rows = read_hit_table_csv(FIXTURE_DAT)
    assert rows[0]["frequency_hz"] == pytest_approx(1_420_405_752.0)


def test_dat_snr_parsed() -> None:
    rows = read_hit_table_csv(FIXTURE_DAT)
    assert rows[0]["snr"] == pytest_approx(25.3)


def test_dat_drift_rate_parsed() -> None:
    rows = read_hit_table_csv(FIXTURE_DAT)
    assert rows[0]["drift_rate_hz_per_sec"] == pytest_approx(-0.382)


def test_dat_source_name_from_metadata_header() -> None:
    """Source name comes from the # Source: header line, not a data column."""
    rows = read_hit_table_csv(FIXTURE_DAT)
    assert rows[0]["source_name"] == "GBT_synth_target"


def test_dat_mjd_from_metadata_header() -> None:
    rows = read_hit_table_csv(FIXTURE_DAT)
    assert rows[0]["mjd"] == pytest_approx(59000.5)


def test_dat_ra_dec_from_metadata_header() -> None:
    rows = read_hit_table_csv(FIXTURE_DAT)
    assert rows[0]["ra_deg"] == pytest_approx(83.8221)
    assert rows[0]["dec_deg"] == pytest_approx(22.0145)


def test_dat_corrected_frequency_used() -> None:
    """Corrected_Frequency column is preferred when present."""
    rows = read_hit_table_csv(FIXTURE_DAT)
    assert all(r["frequency_hz"] > 1e9 for r in rows)


def test_dat_hit_table_to_radio_hit_dicts() -> None:
    dicts = hit_table_to_radio_hit_dicts(FIXTURE_DAT)
    assert len(dicts) == 5
    for d in dicts:
        assert "frequency_hz" in d
        assert "snr" in d
        assert "drift_rate_hz_per_sec" in d
        assert "scan_role" in d


def test_dat_feeds_parse_hit_table() -> None:
    dicts = hit_table_to_radio_hit_dicts(FIXTURE_DAT)
    hits = parse_hit_table(dicts)
    assert len(hits) == 5
    assert all(h.frequency_hz > 0 for h in hits)
