"""Tests for the real full-catalog-to-stratifiable-seed conversion script."""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.build_bl_hprc_full_seed import (
    build_seed_rows,
    parse_hip_number,
    sexagesimal_to_deg,
)

pytest.importorskip("astropy")

# Real VizieR-format rows (HIP8102 = tau Ceti, real coordinates matching
# the existing committed data/bl_hprc_seed_targets.csv entry).
_TAU_CETI_ROW = {
    "Star": "HIP8102",
    "RAJ2000": "01 44 04.08",
    "DEJ2000": "-15 56 20.4",
    "Ep": "2000",
    "Vmag": "3.50",
    "SpType": "G8V",
    "Dist": "3.65",
    "pmRA": "-1721.05",
    "pmDE": "854.16",
    "SimbadName": "tau Cet",
}


def test_sexagesimal_to_deg_ra_matches_known_real_value() -> None:
    # Real tau Ceti (HIP8102) RA, matching the committed
    # data/bl_hprc_seed_targets.csv decimal value of 26.017 deg.
    ra_deg = sexagesimal_to_deg("01 44 04.08", is_ra=True)

    assert ra_deg == pytest.approx(26.017, abs=1e-2)


def test_sexagesimal_to_deg_negative_dec() -> None:
    # Real tau Ceti Dec, matching the committed seed CSV's -15.939 deg.
    dec_deg = sexagesimal_to_deg("-15 56 20.4", is_ra=False)

    assert dec_deg == pytest.approx(-15.939, abs=1e-2)


def test_sexagesimal_to_deg_empty_returns_none() -> None:
    assert sexagesimal_to_deg("", is_ra=True) is None


def test_parse_hip_number_extracts_bare_number() -> None:
    assert parse_hip_number("HIP8102") == "8102"
    assert parse_hip_number("HIP2") == "2"


def test_parse_hip_number_returns_none_for_non_hip() -> None:
    assert parse_hip_number("not-a-hip-star") is None


def test_build_seed_rows_computes_real_galactic_latitude_close_to_known_value() -> None:
    rows = build_seed_rows([_TAU_CETI_ROW], exoplanet_hip_numbers=set())

    assert len(rows) == 1
    row = rows[0]
    assert row["hip"] == "8102"
    assert row["name"] == "tau Cet"
    assert row["spec_type"] == "G8V"
    assert float(row["dist_pc"]) == pytest.approx(3.65)
    # Real committed seed CSV records -73.4 for this star; our independent
    # real coordinate-transform computation should land very close to it.
    assert float(row["gal_lat"]) == pytest.approx(-73.4, abs=0.1)
    assert row["exoplanet"] == "0"


def test_build_seed_rows_marks_real_exoplanet_hosts() -> None:
    rows = build_seed_rows([_TAU_CETI_ROW], exoplanet_hip_numbers={"8102"})

    assert rows[0]["exoplanet"] == "1"


def test_build_seed_rows_skips_non_hip_star_field() -> None:
    bad_row = dict(_TAU_CETI_ROW)
    bad_row["Star"] = "not-a-real-hip-star"

    rows = build_seed_rows([bad_row], exoplanet_hip_numbers=set())

    assert rows == []


def test_build_seed_rows_skips_unparsable_distance() -> None:
    bad_row = dict(_TAU_CETI_ROW)
    bad_row["Dist"] = "not-a-number"

    rows = build_seed_rows([bad_row], exoplanet_hip_numbers=set())

    assert rows == []


def test_main_writes_output_csv(tmp_path: Path, monkeypatch) -> None:
    import csv

    import scripts.build_bl_hprc_full_seed as module

    input_csv = tmp_path / "input.csv"
    with input_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_TAU_CETI_ROW.keys()))
        writer.writeheader()
        writer.writerow(_TAU_CETI_ROW)

    output_csv = tmp_path / "output.csv"

    exit_code = module.main(
        [
            "--input",
            str(input_csv),
            "--output",
            str(output_csv),
            "--skip-exoplanet-crossmatch",
        ]
    )

    assert exit_code == 0
    assert output_csv.exists()
    content = output_csv.read_text(encoding="utf-8")
    assert "8102" in content
    assert "tau Cet" in content
