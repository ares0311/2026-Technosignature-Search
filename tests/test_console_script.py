import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_installed_console_script_scores_example_candidate() -> None:
    # Prefer the venv script if present (local dev), otherwise use PATH / sys.executable
    venv_script = Path(".venv/bin/techno-search")
    if venv_script.exists():
        cmd = [str(venv_script), "score", "examples/candidates/radio_clean_candidate.json"]
    else:
        path_script = shutil.which("techno-search")
        if path_script:
            cmd = [path_script, "score", "examples/candidates/radio_clean_candidate.json"]
        else:
            cmd = [
                sys.executable,
                "-m",
                "techno_search.cli",
                "score",
                "examples/candidates/radio_clean_candidate.json",
            ]

    result = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
    )
    packet = json.loads(result.stdout)

    assert packet["candidate_id"] == "example-radio-clean"
    assert packet["recommended_pathway"] == "human_review_queue"
    assert packet["score_calibration"]["status"] == "uncalibrated"
    assert packet["score_calibration"]["probability_interpretation_allowed"] is False
    assert packet["disclaimer"]
