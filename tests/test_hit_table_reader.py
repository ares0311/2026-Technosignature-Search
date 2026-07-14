"""Tests for real turboSETI hit-table reader (CSV and .dat formats)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from techno_search.radio.hit_table_reader import (
    hit_table_to_radio_hit_dicts,
    read_hit_table_csv,
    read_hit_table_csv_with_stats,
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


def test_dat_parses_tabbed_sexagesimal_metadata_header(tmp_path: Path) -> None:
    path = tmp_path / "voyager_style.dat"
    path.write_text(
        "\n".join(
            [
                "# Source:Voyager1",
                "# MJD: 57650.782094907408\tRA: 17h10m03.984s\tDEC: 12d10m58.8s",
                "# DELTAT:  18.253611\tDELTAF(Hz):  -2.793968",
                "# Top_Hit_# \tDrift_Rate \tSNR \tUncorrected_Frequency \tCorrected_Frequency",
                "000001\t -0.397966\t 30.612337\t 8419.319368\t 8419.319368",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rows = read_hit_table_csv(path)

    assert rows[0]["mjd"] == pytest_approx(57650.782094907408)
    assert rows[0]["ra_deg"] == pytest_approx(257.5166)
    assert rows[0]["dec_deg"] == pytest_approx(12.183)


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


def test_dat_exact_normalized_rows_are_deduplicated(tmp_path: Path) -> None:
    path = tmp_path / "duplicate_hits.dat"
    header, row = FIXTURE_DAT.read_text(encoding="utf-8").rsplit("\n", 2)[:2]
    path.write_text(f"{header}\n{row}\n{row}\n", encoding="utf-8")

    rows, stats = read_hit_table_csv_with_stats(path)

    assert len(rows) == 5
    assert stats == {
        "raw_row_count": 6,
        "unique_row_count": 5,
        "duplicate_row_count": 1,
    }


def test_csv_preserves_explicit_scan_role_and_target(tmp_path: Path) -> None:
    path = tmp_path / "cadence.csv"
    path.write_text(
        "Corrected_Frequency,SNR,Drift_Rate,scan_role,target_id\n"
        "1420.0,15.0,0.25,off,HIP99427\n",
        encoding="utf-8",
    )

    rows = hit_table_to_radio_hit_dicts(path)

    assert rows[0]["scan_role"] == "off"
    assert rows[0]["target_id"] == "HIP99427"


def test_dat_uses_scan_role_from_provenance_sidecar(tmp_path: Path) -> None:
    path = tmp_path / "off_scan.dat"
    path.write_text(FIXTURE_DAT.read_text(encoding="utf-8"), encoding="utf-8")
    path.with_name(path.name + ".provenance.json").write_text(
        json.dumps({"scan_role": "off", "target_id": "HIP99427"}),
        encoding="utf-8",
    )

    rows = hit_table_to_radio_hit_dicts(path)

    assert {row["scan_role"] for row in rows} == {"off"}
    assert {row["target_id"] for row in rows} == {"HIP99427"}
