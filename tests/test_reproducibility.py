import json
from io import StringIO
from pathlib import Path

from techno_search.cli import main
from techno_search.reproducibility import (
    REPRODUCIBILITY_VERIFICATION_DISCLAIMER,
    REPRODUCIBILITY_VERIFICATION_SCHEMA_VERSION,
    verify_packet_against_manifest,
    verify_report_directory,
)


def test_verify_report_directory_reports_no_drift_for_examples() -> None:
    result = verify_report_directory("examples/reports")

    assert result["disclaimer"] == REPRODUCIBILITY_VERIFICATION_DISCLAIMER
    assert result["schema_version"] == REPRODUCIBILITY_VERIFICATION_SCHEMA_VERSION
    assert result["ok"] is True
    assert result["drift_count"] == 0
    assert result["verified_count"] == 3


def test_verify_packet_drift_when_persisted_packet_modified(tmp_path: Path) -> None:
    src_reports = Path("examples/reports")
    candidate_path = Path("examples/candidates/radio_clean_candidate.json")
    persisted_packet_path = src_reports / "example-radio-clean.json"
    manifest_path = src_reports / "example-radio-clean.manifest.json"

    persisted_packet = json.loads(
        persisted_packet_path.read_text(encoding="utf-8")
    )
    persisted_packet["recommended_pathway"] = "do_not_submit_false_positive"
    modified_packet_path = tmp_path / "example-radio-clean.json"
    modified_packet_path.write_text(
        json.dumps(persisted_packet, sort_keys=True, indent=2),
        encoding="utf-8",
    )

    result = verify_packet_against_manifest(
        candidate_path=candidate_path,
        persisted_packet_path=modified_packet_path,
        manifest_path=manifest_path,
    )

    assert result["ok"] is False
    assert result["drift_detected"] is True
    assert result["recommended_pathway_drift"] is True


def test_verify_packet_reports_schema_version_mismatch(tmp_path: Path) -> None:
    candidate_path = Path("examples/candidates/radio_clean_candidate.json")
    persisted_packet_path = Path("examples/reports/example-radio-clean.json")
    manifest_path = Path("examples/reports/example-radio-clean.manifest.json")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = "techno_search_packet_v0_legacy"
    manifest_with_drift = tmp_path / "example-radio-clean.manifest.json"
    manifest_with_drift.write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )

    result = verify_packet_against_manifest(
        candidate_path=candidate_path,
        persisted_packet_path=persisted_packet_path,
        manifest_path=manifest_with_drift,
    )

    assert result["schema_version_match"] is False
    assert result["ok"] is False


def test_cli_verify_report_reproducibility_passes_for_examples() -> None:
    stdout = StringIO()

    exit_code = main(
        ["verify-report-reproducibility", "examples/reports"],
        stdout=stdout,
    )
    result = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert result["ok"] is True
    assert result["drift_count"] == 0
