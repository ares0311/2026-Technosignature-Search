"""Tests for the real full BL HPRC target list acquisition script.

The constructed TSV fixture here mirrors the real, verified VizieR ASU-TSV
response format (comment lines, a `Star` header row, then data rows) --
verified via a real live VizieR retrieval, 2026-07-04, see
docs/bl_hprc_target_list_research.md -- with a small number of synthetic
rows for a code-correctness fixture, not training/calibration data, same
pattern as the existing HITRAN xsc test fixtures.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.acquire_bl_hprc_full_catalog import (
    EXPECTED_COLUMNS,
    acquire_bl_hprc_full_catalog,
    parse_vizier_tsv,
)

_SAMPLE_TSV = """\
#Name: J/PASP/129/E4501
#Title: Search for extraterrestrial intelligence (Isaacson+, 2017)
#INFO cites=bibcode:2017PASP..129e4501I
#
#Table J_PASP_129_E4501_table1:
#Name: J/PASP/129/E4501/table1
#Title: Stellar Targets
#
Star\tRAJ2000\tDEJ2000\tEp\tVmag\tSpType\tDist\tpmRA\tpmDE\tSimbadName
---\t---\t---\t---\t---\t---\t---\t---\t---\t---
HIP2\t00 00 07.26\t-19 29 43.5\t2000\t9.10\tK3V\t45.6\t181.21\t-0.93\tHIP 2
HIP8102\t00 05 34.29\t-15 56 33.0\t2000\t3.50\tG8V\t3.65\t-1721.05\t854.16\ttau Cet
HIP118310\t23 59 51.6\t-64 48 22\t2000\t6.55\tK4V\t22.7\t418.5\t-217.9\tHIP 118310
"""


def test_parse_vizier_tsv_extracts_real_rows_skipping_comments_and_separators() -> None:
    rows = parse_vizier_tsv(_SAMPLE_TSV)

    assert len(rows) == 3
    assert rows[0]["Star"] == "HIP2"
    assert rows[-1]["Star"] == "HIP118310"
    assert rows[1]["SimbadName"] == "tau Cet"


def test_parse_vizier_tsv_preserves_all_expected_columns() -> None:
    rows = parse_vizier_tsv(_SAMPLE_TSV)

    for column in EXPECTED_COLUMNS:
        assert column in rows[0]


def test_parse_vizier_tsv_raises_on_missing_header() -> None:
    with pytest.raises(RuntimeError, match="No 'Star' header row found"):
        parse_vizier_tsv("#just a comment\nno header here\n")


def test_parse_vizier_tsv_raises_on_missing_expected_column() -> None:
    bad_tsv = "Star\tRAJ2000\nHIP2\t00 00 07.26\n"

    with pytest.raises(RuntimeError, match="missing columns"):
        parse_vizier_tsv(bad_tsv)


def test_acquire_writes_raw_and_normalized_csv(tmp_path: Path, monkeypatch) -> None:
    import scripts.acquire_bl_hprc_full_catalog as module

    monkeypatch.setattr(module, "fetch_raw_tsv", lambda **kwargs: _SAMPLE_TSV)

    raw_output = tmp_path / "raw.tsv"
    csv_output = tmp_path / "normalized.csv"

    summary = acquire_bl_hprc_full_catalog(
        raw_output=raw_output, csv_output=csv_output, expected_row_count=3
    )

    assert summary["row_count"] == 3
    assert summary["first_star"] == "HIP2"
    assert summary["last_star"] == "HIP118310"
    assert raw_output.read_text(encoding="utf-8") == _SAMPLE_TSV
    assert csv_output.exists()

    csv_text = csv_output.read_text(encoding="utf-8")
    assert "HIP8102" in csv_text
    assert csv_text.splitlines()[0] == ",".join(EXPECTED_COLUMNS)


def test_acquire_raises_on_row_count_mismatch(tmp_path: Path, monkeypatch) -> None:
    import scripts.acquire_bl_hprc_full_catalog as module

    monkeypatch.setattr(module, "fetch_raw_tsv", lambda **kwargs: _SAMPLE_TSV)

    with pytest.raises(RuntimeError, match="VizieR row count changed"):
        acquire_bl_hprc_full_catalog(
            raw_output=tmp_path / "raw.tsv",
            csv_output=tmp_path / "normalized.csv",
            expected_row_count=1709,
        )


def test_acquire_skips_row_count_check_when_none(tmp_path: Path, monkeypatch) -> None:
    import scripts.acquire_bl_hprc_full_catalog as module

    monkeypatch.setattr(module, "fetch_raw_tsv", lambda **kwargs: _SAMPLE_TSV)

    summary = acquire_bl_hprc_full_catalog(
        raw_output=tmp_path / "raw.tsv",
        csv_output=tmp_path / "normalized.csv",
        expected_row_count=None,
    )

    assert summary["row_count"] == 3
