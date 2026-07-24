"""Tests for the SIMBAD-backed archive-identity enrichment script."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

MODULE_NAME = "enrich_bl_archive_candidate_identity"
MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / f"{MODULE_NAME}.py"
_spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
assert _spec is not None and _spec.loader is not None
enrich = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = enrich
_spec.loader.exec_module(enrich)


def _row(label: str, **overrides: str) -> dict[str, str]:
    base = {
        "candidate_id": f"BLARCHIVE-{label}",
        "archive_target_label": label,
        "canonical_target_id": "",
        "identity_status": "unresolved_archive_label",
        "identity_provenance": "no_exact_target_priority_queue_alias",
        "archive_target_present": "true",
        "queue_status": "",
        "local_coverage_status": "",
        "target_selection_score": "",
        "ranking_eligible": "false",
        "eligibility_reason": "identity_and_file_metadata_enrichment_required",
        "ra_deg": "",
        "dec_deg": "",
        "source_endpoint": "http://seti.berkeley.edu/opendata/api/list-targets",
        "retrieved_at_utc": "2026-07-19T13:59:03Z",
        "schema_version": "bl_archive_candidate_catalog_v1",
    }
    base.update(overrides)
    return base


def _fake_simbad(responses: dict[frozenset[str], str]):
    def fetcher(script: str) -> str:
        names = [
            line.removeprefix("query id ")
            for line in script.splitlines()
            if line.startswith("query id ")
        ]
        key = frozenset(names)
        if key not in responses:
            raise AssertionError(f"Unexpected SIMBAD batch: {sorted(names)}")
        return responses[key]

    return fetcher


def _simbad_response(*, data_lines: list[str], errors: dict[int, str]) -> str:
    error_block = "\n".join(
        f"[{index}] '{name}': No known catalog could be found" for index, name in errors.items()
    )
    return (
        "::script::::::::::::::::::::::::::::::::::::::::::\n\n...\n\n"
        "::console::::::::::::::::::::::::::::::::::::::::::\n\nok\n\n"
        f"::error::::::::::::::::::::::::::::::::::::::::::::\n\n{error_block}\n\n"
        f"::data::::::::::::::::::::::::::::::::::::::::::::::\n\n" + "\n".join(data_lines) + "\n\n"
    )


def test_query_name_strips_only_documented_cadence_suffixes() -> None:
    assert enrich.query_name("0407-658_S") == ("0407-658", "suffix_stripped:_S:arxiv:1906.07391")
    assert enrich.query_name("0407-658_R") == ("0407-658", "suffix_stripped:_R:arxiv:1906.07391")
    assert enrich.query_name("0407-658_B1") == ("0407-658_B1", "direct_label")
    assert enrich.query_name("HIP12345") == ("HIP12345", "direct_label")


def test_resolve_batch_aligns_by_explicit_error_index_not_row_order() -> None:
    # Deliberately put the failing query in the middle to prove alignment
    # does not rely on assuming failures are dropped from the end.
    names = ["AAAFAIL", "HIP99427", "HIP100"]
    response = _simbad_response(
        data_lines=[
            "HD 193202 | 302.7184064746421 | +77.2389729444722",
            "HD 224844 | 000.3163726343500 | +19.7412486221300",
        ],
        errors={2: "AAAFAIL"},
    )
    fetcher = _fake_simbad({frozenset(names): response})

    result = enrich.resolve_batch(names, fetcher=fetcher)

    assert "AAAFAIL" not in result
    assert result["HIP99427"] == ("HD 193202", 302.7184064746421, 77.2389729444722)
    assert result["HIP100"] == ("HD 224844", 0.31637263435, 19.74124862213)


def test_resolve_batch_handles_all_queries_failing_with_no_data_section() -> None:
    # Verified live: when every query in a batch fails, SIMBAD omits the
    # ``::data::`` section entirely rather than emitting an empty one.
    names = ["FAKE1", "FAKE2"]

    def fetcher(_script: str) -> str:
        return (
            "::script::::::::::::::::::::::::::::::::::::::::::\n\n...\n\n"
            "::console::::::::::::::::::::::::::::::::::::::::::\n\nsimbatch done\n\n"
            "::error::::::::::::::::::::::::::::::::::::::::::::\n\n"
            "[2] Identifier not found in the database : FAKE1\n"
            "[3] Identifier not found in the database : FAKE2\n"
        )

    result = enrich.resolve_batch(names, fetcher=fetcher)

    assert result == {}


def test_resolve_batch_retries_on_missing_console_marker() -> None:
    attempts: list[str] = []

    def fetcher(script: str) -> str:
        attempts.append(script)
        if len(attempts) < 2:
            return "::script::::::::::::::::::::::::::::::::::::::::::\n\nquery id HIP99427"
        return _simbad_response(
            data_lines=["HD 193202 | 302.7184064746421 | +77.2389729444722"], errors={}
        )

    result = enrich.resolve_batch(["HIP99427"], fetcher=fetcher, retry_delay_seconds=0.0)

    assert len(attempts) == 2
    assert result["HIP99427"] == ("HD 193202", 302.7184064746421, 77.2389729444722)


def test_resolve_batch_raises_rather_than_guess_on_count_mismatch() -> None:
    names = ["A", "B"]

    def fetcher(_script: str) -> str:
        return (
            "::console::::::::::::::::::::::::::::::::::::::::::\n\nok\n\n"
            "::data::::::::::::::::::::::::::::::::::::::::::::::\n\n"
            "ONLY ONE | 1.0 | 2.0\n\n"
        )

    try:
        enrich.resolve_batch(names, fetcher=fetcher)
    except enrich.IdentityEnrichmentError as exc:
        assert "refusing to guess alignment" in str(exc)
    else:
        raise AssertionError("expected an IdentityEnrichmentError")


def test_resolve_unresolved_rows_leaves_already_resolved_rows_untouched() -> None:
    resolved_row = _row(
        "ALREADYDONE",
        identity_status="resolved_existing_queue_alias",
        canonical_target_id="HIP1",
        ra_deg="1.0",
        dec_deg="2.0",
    )
    unresolved_row = _row("HIP99427")
    rows = [resolved_row, unresolved_row]
    response = _simbad_response(
        data_lines=["HD 193202 | 302.7184064746421 | +77.2389729444722"], errors={}
    )
    fetcher = _fake_simbad({frozenset(["HIP99427"]): response})

    counts = enrich.resolve_unresolved_rows(rows, fetcher=fetcher, request_delay_seconds=0.0)

    assert counts == {"resolved": 1, "unresolved": 0}
    assert resolved_row == _row(
        "ALREADYDONE",
        identity_status="resolved_existing_queue_alias",
        canonical_target_id="HIP1",
        ra_deg="1.0",
        dec_deg="2.0",
    )
    assert unresolved_row["identity_status"] == "resolved_via_simbad_name_lookup"
    assert unresolved_row["canonical_target_id"] == "HD 193202"
    assert unresolved_row["ra_deg"] == repr(302.7184064746421)
    assert unresolved_row["ranking_eligible"] == "false"
    assert (
        unresolved_row["eligibility_reason"]
        == "identity_resolved_pending_file_metadata_enrichment"
    )


def test_resolve_unresolved_rows_tries_pks_prefix_only_for_pks_shaped_names() -> None:
    rows = [_row("0407-658"), _row("NOTPKSSHAPE")]
    direct_response = _simbad_response(
        data_lines=[], errors={2: "0407-658", 3: "NOTPKSSHAPE"}
    )
    pks_response = _simbad_response(
        data_lines=["ICRF J040820.3-654509 | 62.08491183 | -65.75252239"], errors={}
    )
    fetcher = _fake_simbad(
        {
            frozenset(["0407-658", "NOTPKSSHAPE"]): direct_response,
            frozenset(["PKS 0407-658"]): pks_response,
        }
    )

    counts = enrich.resolve_unresolved_rows(rows, fetcher=fetcher, request_delay_seconds=0.0)

    assert counts == {"resolved": 1, "unresolved": 1}
    pks_row = next(row for row in rows if row["archive_target_label"] == "0407-658")
    assert pks_row["canonical_target_id"] == "ICRF J040820.3-654509"
    assert pks_row["identity_provenance"] == "simbad_pks_prefix_match;direct_label"
    other_row = next(row for row in rows if row["archive_target_label"] == "NOTPKSSHAPE")
    assert other_row["identity_status"] == "unresolved_archive_label"


def test_suffix_variant_inherits_base_resolution() -> None:
    rows = [_row("0407-658_S")]
    response = _simbad_response(
        data_lines=["ICRF J040820.3-654509 | 62.08491183 | -65.75252239"], errors={}
    )
    fetcher = _fake_simbad({frozenset(["0407-658"]): response})

    counts = enrich.resolve_unresolved_rows(rows, fetcher=fetcher, request_delay_seconds=0.0)

    assert counts == {"resolved": 1, "unresolved": 0}
    assert rows[0]["canonical_target_id"] == "ICRF J040820.3-654509"
    assert rows[0]["identity_provenance"] == (
        "simbad_direct_name_match;suffix_stripped:_S:arxiv:1906.07391"
    )


def test_enrich_catalog_preserves_schema_and_row_count(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.csv"
    rows = [_row("HIP99427"), _row("STAYSUNRESOLVED")]
    with catalog_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    response = _simbad_response(
        data_lines=["HD 193202 | 302.7184064746421 | +77.2389729444722"],
        errors={3: "STAYSUNRESOLVED"},
    )
    fetcher = _fake_simbad({frozenset(["HIP99427", "STAYSUNRESOLVED"]): response})

    summary = enrich.enrich_catalog(catalog_path, fetcher=fetcher)

    assert summary["ok"] is True
    assert summary["resolved_count"] == 1
    assert summary["still_unresolved_count"] == 1
    assert summary["raw_science_payload_downloaded"] is False

    with catalog_path.open(newline="", encoding="utf-8") as handle:
        out_rows = list(csv.DictReader(handle))
    assert [r["archive_target_label"] for r in out_rows] == ["HIP99427", "STAYSUNRESOLVED"]
    assert out_rows[0]["identity_status"] == "resolved_via_simbad_name_lookup"
    assert out_rows[0]["ranking_eligible"] == "false"
    assert out_rows[1]["identity_status"] == "unresolved_archive_label"
