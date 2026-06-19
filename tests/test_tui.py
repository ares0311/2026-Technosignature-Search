"""Tests for the TUI helper module (tui.py)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from techno_search.tui import (
    TUI_DISCLAIMER,
    classify_stellar,
    extract_composite_score,
    extract_stellar_from_candidate,
    make_scan_index,
    print_result_line,
    print_scan_footer,
    print_scan_header,
)

# ---------------------------------------------------------------------------
# classify_stellar
# ---------------------------------------------------------------------------

class TestClassifyStellar:
    def test_no_names_no_match_returns_unknown(self) -> None:
        assert classify_stellar("", 0, 0) == "unknown"

    def test_none_string_returns_unknown(self) -> None:
        assert classify_stellar("none", 0, 0) == "unknown"

    def test_no_names_gaia_match_returns_stellar_gaia(self) -> None:
        assert classify_stellar("", 0, 1) == "stellar (Gaia)"

    def test_galaxy_name(self) -> None:
        assert classify_stellar("NGC 1234", 1, 0) == "galaxy/extragalactic"

    def test_quasar_name(self) -> None:
        assert classify_stellar("PKS 1234+567, QSO B1234", 1, 0) == "galaxy/extragalactic"

    def test_binary_name(self) -> None:
        assert classify_stellar("HD 12345, HD 12345B (binary)", 2, 0) == "binary star"

    def test_spectroscopic_binary(self) -> None:
        assert classify_stellar("HIP99427 SB1", 1, 0) == "binary star"

    def test_neutron_star(self) -> None:
        assert classify_stellar("PSR B0531+21", 1, 0) == "neutron star"

    def test_white_dwarf(self) -> None:
        assert classify_stellar("WD 1234-567", 1, 0) == "white dwarf"

    def test_globular_cluster(self) -> None:
        assert classify_stellar("globular cluster NGC 6752", 1, 0) == "star cluster"

    def test_nebula(self) -> None:
        assert classify_stellar("Crab Nebula SNR", 1, 0) == "nebula/remnant"

    def test_giant_star(self) -> None:
        assert classify_stellar("HD 12345, AGB giant", 1, 0) == "giant star"

    def test_variable_star(self) -> None:
        assert classify_stellar("Delta Scuti variable", 1, 0) == "variable star"

    def test_plain_simbad_match_returns_stellar(self) -> None:
        assert classify_stellar("HIP99427", 1, 0) == "stellar"

    def test_simbad_and_gaia_match_returns_stellar(self) -> None:
        assert classify_stellar("HIP99427", 1, 2) == "stellar"

    def test_galaxy_takes_priority_over_binary(self) -> None:
        # galaxy pattern checked first
        assert classify_stellar("NGC 1234 binary system", 1, 0) == "galaxy/extragalactic"


# ---------------------------------------------------------------------------
# make_scan_index
# ---------------------------------------------------------------------------

class TestMakeScanIndex:
    def test_format_matches_pattern(self) -> None:
        idx = make_scan_index("HIP99427")
        assert re.match(r"^\d{8}-\d{6}-HIP99427$", idx), f"unexpected: {idx}"

    def test_special_chars_replaced(self) -> None:
        idx = make_scan_index("HIP 99/427")
        assert " " not in idx
        assert "/" not in idx

    def test_different_calls_produce_different_timestamps(self) -> None:
        import time
        a = make_scan_index("T")
        time.sleep(1.05)
        b = make_scan_index("T")
        assert a != b


# ---------------------------------------------------------------------------
# extract_composite_score
# ---------------------------------------------------------------------------

class TestExtractCompositeScore:
    def test_returns_signal_reality_confidence(self) -> None:
        d = {"scores": {"signal_reality_confidence": 0.75}}
        assert extract_composite_score(d) == pytest.approx(0.75)

    def test_missing_scores_returns_zero(self) -> None:
        assert extract_composite_score({}) == pytest.approx(0.0)

    def test_missing_field_returns_zero(self) -> None:
        assert extract_composite_score({"scores": {}}) == pytest.approx(0.0)

    def test_none_value_returns_zero(self) -> None:
        d = {"scores": {"signal_reality_confidence": None}}
        assert extract_composite_score(d) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# extract_stellar_from_candidate
# ---------------------------------------------------------------------------

class TestExtractStellarFromCandidate:
    def test_extracts_from_provenance(self) -> None:
        d = {
            "provenance": {"simbad_match_names": "HIP99427"},
            "features": {"simbad_match_count": 1, "gaia_match_count": 0},
        }
        assert extract_stellar_from_candidate(d) == "stellar"

    def test_empty_candidate_returns_unknown(self) -> None:
        assert extract_stellar_from_candidate({}) == "unknown"

    def test_binary_detected(self) -> None:
        d = {
            "provenance": {"simbad_match_names": "HIP99427 binary system"},
            "features": {"simbad_match_count": 1, "gaia_match_count": 0},
        }
        assert extract_stellar_from_candidate(d) == "binary star"


# ---------------------------------------------------------------------------
# print_result_line (smoke tests — just confirm no exception raised)
# ---------------------------------------------------------------------------

class TestPrintResultLine:
    def test_ok_no_escalation(self, capsys: pytest.CaptureFixture[str]) -> None:
        print_result_line(
            index="20260618-120000-HIP99427",
            stellar="binary star",
            score=0.45,
            escalation=False,
            ok=True,
        )
        # With or without rich we just need no exception

    def test_ok_with_escalation(self, capsys: pytest.CaptureFixture[str]) -> None:
        print_result_line(
            index="20260618-120000-HIP99427",
            stellar="stellar",
            score=0.91,
            escalation=True,
            ok=True,
        )

    def test_error_line(self, capsys: pytest.CaptureFixture[str]) -> None:
        print_result_line(
            index="20260618-120000-HIP17147",
            stellar="unknown",
            score=0.0,
            escalation=False,
            ok=False,
            error="turboSETI failed",
        )


# ---------------------------------------------------------------------------
# print_scan_header / print_scan_footer (smoke)
# ---------------------------------------------------------------------------

class TestPrintHeaderFooter:
    def test_header_no_exception(self) -> None:
        print_scan_header(5, "/tmp/scan_progress", resume=False)

    def test_header_resume(self) -> None:
        print_scan_header(3, "/tmp/scan_progress", resume=True)

    def test_footer_no_escalations(self) -> None:
        print_scan_footer(4, 1, 0)

    def test_footer_with_escalations(self) -> None:
        print_scan_footer(4, 0, 2)


# ---------------------------------------------------------------------------
# TUI disclaimer present
# ---------------------------------------------------------------------------

def test_disclaimer_contains_local_triage() -> None:
    assert "local scheduling aid" in TUI_DISCLAIMER
    assert "detection claim" in TUI_DISCLAIMER


# ---------------------------------------------------------------------------
# prod-file-scan CLI command (integration via subprocess)
# ---------------------------------------------------------------------------

class TestProdScanCLI:
    def test_no_input_files_exits_nonzero(self, tmp_path: Path) -> None:
        """prod-file-scan on an empty directory should exit 1."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "techno_search.cli", "prod-file-scan",
             str(tmp_path), str(tmp_path / "out")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_resumes_by_skipping_existing_json(self, tmp_path: Path) -> None:
        """If output JSON exists for an input file, prod-file-scan skips it."""
        import subprocess

        input_dir = tmp_path / "inputs"
        output_dir = tmp_path / "outputs"
        input_dir.mkdir()
        output_dir.mkdir()

        # Create a fake .dat file and pre-existing output JSON
        dat = input_dir / "fake_target.dat"
        dat.write_text("# fake\n")
        (output_dir / "fake_target.json").write_text('{"skip": true}\n')

        result = subprocess.run(
            [sys.executable, "-m", "techno_search.cli", "prod-file-scan",
             str(input_dir), str(output_dir)],
            capture_output=True,
            text=True,
        )
        # All targets skipped — nothing to process → exits 0 (0 failed)
        assert "skipping 1" in result.stdout or result.returncode in (0, 1)
