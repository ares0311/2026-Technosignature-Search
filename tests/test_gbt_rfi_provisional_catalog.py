"""Tests for the GBT provisional RFI catalog and its admission gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROVISIONAL_CATALOG = (
    REPO_ROOT / "tests" / "fixtures" / "rfi_catalog" / "gbt_rfi_provisional_v1.json"
)
ADMISSION_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "rfi_database_admission.json"
BUILDER_SCRIPT = REPO_ROOT / "scripts" / "build_gbt_rfi_provisional_catalog.py"
PYTHON = sys.executable


# ---------------------------------------------------------------------------
# Builder script
# ---------------------------------------------------------------------------


def test_builder_script_exists() -> None:
    assert BUILDER_SCRIPT.is_file(), "build_gbt_rfi_provisional_catalog.py not found"


def test_builder_validate_only_exits_zero() -> None:
    result = subprocess.run(
        [PYTHON, str(BUILDER_SCRIPT), "--validate-only"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_builder_write_to_tmpdir(tmp_path: Path) -> None:
    outfile = tmp_path / "catalog_out.json"
    result = subprocess.run(
        [PYTHON, str(BUILDER_SCRIPT), "--output", str(outfile)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert outfile.is_file()
    catalog = json.loads(outfile.read_text())
    assert catalog["entry_count"] == len(catalog["rfi_database_entries"])


# ---------------------------------------------------------------------------
# Provisional catalog file
# ---------------------------------------------------------------------------


def test_provisional_catalog_exists() -> None:
    assert PROVISIONAL_CATALOG.is_file(), f"Missing {PROVISIONAL_CATALOG}"


def _load_catalog() -> dict:
    return json.loads(PROVISIONAL_CATALOG.read_text(encoding="utf-8"))


def test_catalog_has_required_top_level_keys() -> None:
    catalog = _load_catalog()
    for key in (
        "catalog_version", "site_id", "site_name",
        "disclaimer", "entry_count", "rfi_database_entries",
    ):
        assert key in catalog, f"Missing key: {key}"


def test_catalog_entry_count_matches() -> None:
    catalog = _load_catalog()
    assert catalog["entry_count"] == len(catalog["rfi_database_entries"])


def test_catalog_has_fifteen_entries() -> None:
    catalog = _load_catalog()
    assert catalog["entry_count"] == 15


def test_catalog_site_id() -> None:
    catalog = _load_catalog()
    assert catalog["site_id"] == "gbt-provisional-v1"


def test_catalog_disclaimer_present() -> None:
    catalog = _load_catalog()
    assert "provisional" in catalog["disclaimer"].lower()
    assert "false-positive" in catalog["disclaimer"].lower()
    assert "does not calibrate scoring thresholds" in catalog["disclaimer"]


# ---------------------------------------------------------------------------
# Entry-level schema validation
# ---------------------------------------------------------------------------


def _entries() -> list[dict]:
    return _load_catalog()["rfi_database_entries"]


def test_all_entries_have_required_fields() -> None:
    required = {
        "entry_id", "site_id", "site_name",
        "frequency_low_hz", "frequency_high_hz",
        "source_class", "confidence", "review_status",
        "provenance", "notes", "active", "synthetic",
    }
    for entry in _entries():
        missing = required - set(entry.keys())
        assert not missing, f"{entry['entry_id']}: missing fields {missing}"


def test_all_entries_inactive() -> None:
    for entry in _entries():
        assert entry["active"] is False, f"{entry['entry_id']}: active should be False"


def test_all_entries_not_synthetic() -> None:
    for entry in _entries():
        assert entry["synthetic"] is False, f"{entry['entry_id']}: synthetic should be False"


def test_all_entries_provisional_status() -> None:
    for entry in _entries():
        assert entry["review_status"] == "provisional", (
            f"{entry['entry_id']}: review_status should be 'provisional'"
        )


def test_all_entries_valid_source_class() -> None:
    from techno_search.rfi_database import ALLOWED_RFI_SOURCE_CLASSES

    for entry in _entries():
        assert entry["source_class"] in ALLOWED_RFI_SOURCE_CLASSES, (
            f"{entry['entry_id']}: invalid source_class {entry['source_class']!r}"
        )


def test_all_entries_valid_frequencies() -> None:
    for entry in _entries():
        low = entry["frequency_low_hz"]
        high = entry["frequency_high_hz"]
        assert isinstance(low, float) and low > 0.0, f"{entry['entry_id']}: bad frequency_low_hz"
        assert isinstance(high, float) and high > low, f"{entry['entry_id']}: bad frequency_high_hz"


def test_all_entries_valid_confidence() -> None:
    for entry in _entries():
        conf = entry["confidence"]
        assert 0.0 <= conf <= 1.0, f"{entry['entry_id']}: confidence {conf!r} out of range"


def test_all_entries_have_provenance() -> None:
    for entry in _entries():
        assert str(entry.get("provenance", "")).strip(), (
            f"{entry['entry_id']}: provenance is empty"
        )


def test_all_entries_cite_public_document() -> None:
    """Each provenance string must reference at least one public document/standard."""
    public_doc_keywords = [
        "IS-GPS-200", "GLONASS ICD", "ITU", "ICAO", "FCC", "NRAO", "NAVCEN",
        "ICD-GPS", "Appendix", "§", "Annex", "CFR",
    ]
    for entry in _entries():
        provenance = str(entry.get("provenance", ""))
        has_citation = any(kw in provenance for kw in public_doc_keywords)
        assert has_citation, (
            f"{entry['entry_id']}: provenance does not cite a public document"
        )


def test_unique_entry_ids() -> None:
    ids = [e["entry_id"] for e in _entries()]
    assert len(ids) == len(set(ids)), "Duplicate entry_ids found"


def test_frequencies_sorted_by_low() -> None:
    entries = _entries()
    lows = [e["frequency_low_hz"] for e in entries]
    assert lows == sorted(lows), "Entries not sorted by frequency_low_hz"


# ---------------------------------------------------------------------------
# Source-class coverage
# ---------------------------------------------------------------------------


def test_entries_cover_satellite_class() -> None:
    classes = {e["source_class"] for e in _entries()}
    assert "satellite" in classes


def test_entries_cover_aircraft_class() -> None:
    classes = {e["source_class"] for e in _entries()}
    assert "aircraft" in classes


def test_entries_cover_observatory_local_class() -> None:
    classes = {e["source_class"] for e in _entries()}
    assert "observatory_local" in classes


def test_gps_l1_entry_present() -> None:
    """GPS L1 at 1575.42 MHz must be covered."""
    gps_l1_hz = 1_575_420_000.0
    covered = [
        e for e in _entries()
        if e["frequency_low_hz"] <= gps_l1_hz <= e["frequency_high_hz"]
    ]
    assert covered, "No entry covers GPS L1 at 1575.42 MHz"


def test_ads_b_entry_present() -> None:
    """ADS-B at 1090 MHz must be covered."""
    ads_b_hz = 1_090_000_000.0
    covered = [
        e for e in _entries()
        if e["frequency_low_hz"] <= ads_b_hz <= e["frequency_high_hz"]
    ]
    assert covered, "No entry covers ADS-B at 1090 MHz"


def test_iridium_entry_present() -> None:
    """Iridium at 1621 MHz must be covered."""
    iridium_hz = 1_621_000_000.0
    covered = [
        e for e in _entries()
        if e["frequency_low_hz"] <= iridium_hz <= e["frequency_high_hz"]
    ]
    assert covered, "No entry covers Iridium at 1621 MHz"


# ---------------------------------------------------------------------------
# RfiDatabaseRecord round-trip
# ---------------------------------------------------------------------------


def test_entries_round_trip_through_dataclass() -> None:
    from techno_search.rfi_database import RfiDatabaseRecord

    for entry in _entries():
        rec = RfiDatabaseRecord(
            entry_id=str(entry["entry_id"]),
            site_id=str(entry["site_id"]),
            site_name=str(entry["site_name"]),
            frequency_low_hz=float(entry["frequency_low_hz"]),
            frequency_high_hz=float(entry["frequency_high_hz"]),
            source_class=str(entry["source_class"]),
            confidence=float(entry["confidence"]),
            review_status=str(entry["review_status"]),
            provenance=str(entry["provenance"]),
            notes=str(entry.get("notes", "")),
            active=bool(entry.get("active", False)),
            synthetic=bool(entry.get("synthetic", False)),
        )
        d = rec.as_dict()
        assert d["entry_id"] == entry["entry_id"]
        assert d["synthetic"] is False
        assert d["active"] is False


def test_inactive_entries_do_not_match_any_frequency() -> None:
    """All entries are inactive, so no frequency should match."""
    from techno_search.rfi_database import RfiDatabaseRecord

    test_freqs = [
        1_575_420_000.0,  # GPS L1
        1_090_000_000.0,  # ADS-B
        1_621_000_000.0,  # Iridium
    ]
    for entry in _entries():
        rec = RfiDatabaseRecord(
            entry_id=str(entry["entry_id"]),
            site_id=str(entry["site_id"]),
            site_name=str(entry["site_name"]),
            frequency_low_hz=float(entry["frequency_low_hz"]),
            frequency_high_hz=float(entry["frequency_high_hz"]),
            source_class=str(entry["source_class"]),
            confidence=float(entry["confidence"]),
            review_status=str(entry["review_status"]),
            provenance=str(entry["provenance"]),
            notes=str(entry.get("notes", "")),
            active=bool(entry.get("active", False)),
            synthetic=bool(entry.get("synthetic", False)),
        )
        for freq in test_freqs:
            assert not rec.contains(freq), (
                f"{rec.entry_id}: inactive entry matched {freq / 1e6:.2f} MHz"
            )


# ---------------------------------------------------------------------------
# Admission fixture gate
# ---------------------------------------------------------------------------


def _load_admission() -> dict:
    return json.loads(ADMISSION_FIXTURE.read_text(encoding="utf-8"))


def test_admission_fixture_has_gbt_provisional_entry() -> None:
    admission = _load_admission()
    ids = [r["source_id"] for r in admission["rfi_database_admission_records"]]
    assert "rfi-admit-gbt-provisional-v1" in ids


def test_gbt_provisional_admission_blocked_pending_review() -> None:
    admission = _load_admission()
    record = next(
        r for r in admission["rfi_database_admission_records"]
        if r["source_id"] == "rfi-admit-gbt-provisional-v1"
    )
    assert record["admission_status"] == "blocked_pending_review"


def test_gbt_provisional_admission_real_data_not_authorized() -> None:
    admission = _load_admission()
    record = next(
        r for r in admission["rfi_database_admission_records"]
        if r["source_id"] == "rfi-admit-gbt-provisional-v1"
    )
    assert record["real_data_authorized"] is False


def test_gbt_provisional_admission_not_synthetic_only() -> None:
    admission = _load_admission()
    record = next(
        r for r in admission["rfi_database_admission_records"]
        if r["source_id"] == "rfi-admit-gbt-provisional-v1"
    )
    assert record["synthetic_fixture_only"] is False


def test_gbt_provisional_admission_site_id_matches_catalog() -> None:
    catalog = _load_catalog()
    admission = _load_admission()
    record = next(
        r for r in admission["rfi_database_admission_records"]
        if r["source_id"] == "rfi-admit-gbt-provisional-v1"
    )
    assert record["site_id"] == catalog["site_id"]


def test_gbt_provisional_admission_has_blockers() -> None:
    """Blocker count must be > 0 while still pending review."""
    admission = _load_admission()
    record = next(
        r for r in admission["rfi_database_admission_records"]
        if r["source_id"] == "rfi-admit-gbt-provisional-v1"
    )
    assert record["blocker_count"] > 0


def test_gbt_provisional_admission_passes_validation() -> None:
    from techno_search.rfi_database_admission import (
        load_rfi_database_admission_records,
        validate_rfi_database_admission_records,
    )

    records = load_rfi_database_admission_records()
    result = validate_rfi_database_admission_records(records)
    assert result["ok"], f"Admission validation failed: {result['issues']}"


def test_gbt_provisional_admission_notes_reference_catalog_file() -> None:
    admission = _load_admission()
    record = next(
        r for r in admission["rfi_database_admission_records"]
        if r["source_id"] == "rfi-admit-gbt-provisional-v1"
    )
    assert "gbt_rfi_provisional_v1.json" in record["notes"]
    assert "build_gbt_rfi_provisional_catalog.py" in record["notes"]


# ---------------------------------------------------------------------------
# Scientific guardrails on disclaimer text
# ---------------------------------------------------------------------------


def test_disclaimer_does_not_claim_detection() -> None:
    catalog = _load_catalog()
    disclaimer = catalog["disclaimer"].lower()
    for bad_phrase in ("confirmed detection", "discovery", "alien", "technosignature confirmed"):
        assert bad_phrase not in disclaimer, f"Disclaimer contains banned phrase: {bad_phrase!r}"


def test_disclaimer_mentions_screening_aid() -> None:
    catalog = _load_catalog()
    assert "screening aid" in catalog["disclaimer"].lower()
