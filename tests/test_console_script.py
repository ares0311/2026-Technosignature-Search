import json
import subprocess
from pathlib import Path


def test_installed_console_script_scores_example_candidate() -> None:
    script = Path(".venv/bin/techno-search")
    assert script.exists()

    result = subprocess.run(
        [str(script), "score", "examples/candidates/radio_clean_candidate.json"],
        check=True,
        capture_output=True,
        text=True,
    )
    packet = json.loads(result.stdout)

    assert packet["candidate_id"] == "example-radio-clean"
    assert packet["recommended_pathway"] == "candidate_review_packet"
    assert packet["disclaimer"]
