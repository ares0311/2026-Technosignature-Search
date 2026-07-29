"""Exact installed-entry-point acceptance for the canonical Hunter lifecycle."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from techno_search import __version__
from techno_search.hunter_acceptance import CONTROLLED_ACCEPTANCE_SCHEMA_VERSION

COMMITTED_EVIDENCE = Path(
    "docs/evidence/hunter_v1_2_71_controlled_acceptance.json"
)


def test_installed_hunter_controlled_prod_acceptance_is_fresh_and_complete(
    tmp_path: Path,
) -> None:
    work_dir = tmp_path / "fresh_state"
    evidence_path = tmp_path / "acceptance.json"
    executable = Path(
        shutil.which("Techno-Hunter")
        or ".venv/bin/Techno-Hunter"
    )

    completed = subprocess.run(
        [
            str(executable),
            "--acceptance-work-dir",
            str(work_dir),
            "--acceptance-evidence",
            str(evidence_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=240,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["schema_version"] == CONTROLLED_ACCEPTANCE_SCHEMA_VERSION
    assert evidence["release"]["app_version"] == __version__
    assert evidence["release"]["installed_entry_point"] == "Techno-Hunter"
    assert evidence["request"] == {
        "new": {"mode": "new", "target_count": 1},
        "follow_up": {"mode": "follow-up", "target_count": 1},
    }
    assert evidence["selected_targets"] == {
        "new": ["OUTSIDE"],
        "follow_up": ["OUTSIDE"],
    }
    assert evidence["discovery_coverage"]["expansion_report"]["round_count"] == 1
    assert evidence["validity_report"]["excluded"] == {
        "INVALID": "invalid",
        "PRIOR": "ineligible_new_due_to_prior_search",
        "STALE": "refresh-required",
    }
    assert evidence["search_runs"]["new"]["event_sequence"] == [
        "created",
        "run_started",
        "run_completed",
    ]
    assert evidence["search_runs"]["follow_up"]["event_sequence"] == [
        "created",
        "run_started",
        "run_failed",
        "run_resumed",
        "run_completed",
    ]
    assert all(item["passed"] for item in evidence["assertion_results"])
    assert evidence["follow_up_state"]["history_record_count"] == 2
    assert evidence["detection_claimed"] is False
    assert evidence["discovery_claimed"] is False
    assert evidence["expert_review_claimed"] is False
    assert evidence["external_validation_claimed"] is False
    assert evidence["external_submission_allowed"] is False

    required_portable_sections = {
        "request",
        "discovery_coverage",
        "validity_report",
        "provenance_trace",
        "ranking_evidence",
        "selected_targets",
        "search_runs",
        "follow_up_state",
        "assertion_results",
        "embedded_artifacts",
    }
    assert required_portable_sections <= set(evidence)
    assert "$ACCEPTANCE_WORK_DIR" in json.dumps(evidence["transcript"])
    assert str(work_dir) not in json.dumps(evidence)
    assert evidence["embedded_artifacts"]["observation_provenance"][
        "classification"
    ] == "controlled_acceptance_fixture"
    assert evidence["embedded_artifacts"]["new_candidate_interpretation"][
        "track"
    ] == "radio"
    assert evidence["embedded_artifacts"]["follow_up_candidate_interpretation"][
        "track"
    ] == "radio"
    assert not list(work_dir.glob("data/**/*.h5"))


def test_retired_duplicate_candidate_store_surface_is_absent() -> None:
    cli = Path("src/techno_search/cli.py").read_text(encoding="utf-8")

    assert not Path("src/techno_search/candidate_store.py").exists()
    for command in (
        "candidate-store-init",
        "candidate-store-summary",
        "candidate-store-list",
    ):
        assert command not in cli


def test_committed_v1_2_71_evidence_is_portable_and_bound_to_clean_code() -> None:
    evidence = json.loads(COMMITTED_EVIDENCE.read_text(encoding="utf-8"))

    assert evidence["schema_version"] == CONTROLLED_ACCEPTANCE_SCHEMA_VERSION
    assert evidence["release"]["app_version"] == __version__
    assert evidence["release"]["code_commit"] == "30f4103"
    assert all(item["passed"] for item in evidence["assertion_results"])
    assert len(evidence["assertion_results"]) == 14
    assert evidence["selected_targets"] == {
        "new": ["OUTSIDE"],
        "follow_up": ["OUTSIDE"],
    }
    assert evidence["search_runs"]["follow_up"]["event_sequence"] == [
        "created",
        "run_started",
        "run_failed",
        "run_resumed",
        "run_completed",
    ]
    serialized = json.dumps(evidence)
    assert "$ACCEPTANCE_WORK_DIR" in serialized
    assert "/tmp/techno-hunter-v1-2-71-30f4103" not in serialized
    assert "/private/var/folders" not in serialized
