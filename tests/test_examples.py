import json
from pathlib import Path

from techno_search.reporting import REQUIRED_DISCLAIMER

EXAMPLE_REPORTS = (
    "example-radio-clean",
    "example-infrared-clean",
    "example-anomaly-clean",
)


def test_example_candidate_reports_exist_and_are_conservative() -> None:
    reports_dir = Path("examples/reports")

    for stem in EXAMPLE_REPORTS:
        markdown = (reports_dir / f"{stem}.md").read_text(encoding="utf-8")
        packet = json.loads((reports_dir / f"{stem}.json").read_text(encoding="utf-8"))
        manifest = json.loads(
            (reports_dir / f"{stem}.manifest.json").read_text(encoding="utf-8")
        )

        assert REQUIRED_DISCLAIMER in markdown
        assert packet["disclaimer"] == REQUIRED_DISCLAIMER
        assert manifest["candidate_id"] == packet["candidate_id"]
        assert packet["candidate_id"].startswith("example-")
        assert packet["positive_evidence"]
        assert packet["negative_evidence"] is not None
