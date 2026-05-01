import json
from pathlib import Path

from techno_search.cli import load_candidate_json
from techno_search.scoring import score_candidate


def test_example_candidate_scores_match_regression_snapshots() -> None:
    snapshots = json.loads(
        Path("tests/fixtures/score_regressions.json").read_text(encoding="utf-8")
    )["candidates"]

    for candidate_path in sorted(Path("examples/candidates").glob("*.json")):
        scored = score_candidate(load_candidate_json(candidate_path))
        expected = snapshots[scored.candidate.candidate_id]

        assert scored.candidate.track.value == expected["track"]
        assert scored.recommended_pathway.value == expected["recommended_pathway"]
        assert scored.scores.as_dict() == expected["scores"]
        assert {key.value: value for key, value in scored.posterior.items()} == expected[
            "posterior"
        ]
