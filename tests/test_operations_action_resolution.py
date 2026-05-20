import json
import subprocess
import sys

from techno_search.operations_action_resolution import (
    ALLOWED_ACTION_RESOLUTION_STATUSES,
    OPERATIONS_ACTION_RESOLUTION_DISCLAIMER,
    OPERATIONS_ACTION_RESOLUTION_SCHEMA_VERSION,
    load_operations_action_resolution_records,
    operations_action_resolution_summary,
)


def test_resolution_loader_records_present() -> None:
    records = load_operations_action_resolution_records()

    assert len(records) == 6
    assert records[0].resolution_id == "ops-resolution-001"
    assert records[0].action_id == "ops-action-001"


def test_summary_schema_version_and_disclaimer() -> None:
    result = operations_action_resolution_summary()

    assert result["schema_version"] == OPERATIONS_ACTION_RESOLUTION_SCHEMA_VERSION
    assert result["disclaimer"] == OPERATIONS_ACTION_RESOLUTION_DISCLAIMER
    assert "local workflow provenance only" in result["disclaimer"]


def test_summary_status_counts() -> None:
    result = operations_action_resolution_summary()

    assert result["record_count"] == 6
    assert result["open_count"] == 2
    assert result["acknowledged_count"] == 1
    assert result["deferred_count"] == 2
    assert result["resolved_count"] == 1


def test_summary_authorization_counts_zero() -> None:
    result = operations_action_resolution_summary()

    assert result["live_data_authorized_count"] == 0
    assert result["external_submission_authorized_count"] == 0
    assert result["all_external_authorization_disabled"] is True


def test_summary_residual_blocker_total() -> None:
    result = operations_action_resolution_summary()

    assert result["residual_blocker_total"] == 23


def test_statuses_allowed() -> None:
    records = load_operations_action_resolution_records()

    assert {record.resolution_status for record in records} <= (
        ALLOWED_ACTION_RESOLUTION_STATUSES
    )


def test_cli_operations_action_resolution_summary_outputs_json() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "techno_search.cli", "operations-action-resolution-summary"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    result = json.loads(completed.stdout)
    assert result["schema_version"] == OPERATIONS_ACTION_RESOLUTION_SCHEMA_VERSION
    assert result["record_count"] == 6
    assert "ops-action-001" in result["action_ids"]
