import json
from pathlib import Path

from techno_search.cli import candidate_from_mapping
from techno_search.schemas import Pathway
from techno_search.scoring import score_candidate


def test_false_positive_calibration_fixtures_are_suppressed() -> None:
    fixture_path = Path("tests/fixtures/calibration_false_positives.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))

    for fixture in data["fixtures"]:
        candidate = candidate_from_mapping(fixture["candidate"])
        scored = score_candidate(candidate)

        assert scored.recommended_pathway == Pathway(fixture["expected_pathway"])
        assert scored.scores.false_positive_probability >= 0.8
        assert scored.evidence.negative_evidence
