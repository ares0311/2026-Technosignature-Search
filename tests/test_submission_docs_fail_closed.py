from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_external_submission_boundary_is_fail_closed() -> None:
    protocol = _read("docs/EXTERNAL_SUBMISSION_PROTOCOL.md")

    assert "**Status:** Blocked." in protocol
    assert "credentialed third-party expert review" in protocol
    assert "explicitly approved" in protocol
    assert "SNR ≥ 42.4" not in protocol
    assert "operator_cleared: True" not in protocol
    assert "Acceptable public venues" not in protocol


def test_limitations_reject_retired_calibration_claims() -> None:
    limitations = _read("docs/KNOWN_LIMITATIONS.md")

    assert "No Calibrated Scoring Or Escalation Threshold" in limitations
    assert "zero independently escalation-ready candidates" in limitations
    assert "99.19%" not in limitations
    assert "Calibrated SNR thresholds" not in limitations


def test_local_pathways_do_not_create_labels_or_external_action() -> None:
    pathways = _read("docs/SUBMISSION_PATHWAYS.md")
    normalized = " ".join(pathways.split())

    assert "must not create a labeling queue" in normalized
    assert "external action\n  -> blocked" in pathways
    assert "ask reviewers to classify" not in pathways
    assert "citizen-science review" not in pathways


def test_background_user_decisions_cannot_authorize_submission() -> None:
    cli_source = _read("src/techno_search/cli.py")
    schema = _read("schemas/background_user_decisions.schema.json")

    assert "--confirm-external-submission-approval" not in cli_source
    assert 'choices=["request_more_tests", "close_as_reviewed"]' in cli_source
    assert '"external_submission_approved": {\n            "const": false' in schema
    assert '"submission_destination": {\n            "const": null' in schema
