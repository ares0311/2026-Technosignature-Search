import json
from pathlib import Path

from techno_search.cli import score_batch
from techno_search.reporting import REQUIRED_DISCLAIMER

EXAMPLE_REPORTS = (
    "example-radio-clean",
    "example-infrared-clean",
    "example-anomaly-clean",
)
EXPECTED_BATCH_CANDIDATES = {
    "example-radio-clean": "radio",
    "example-infrared-clean": "infrared",
    "example-anomaly-clean": "anomaly",
}
PER_CANDIDATE_MANIFEST_FIELDS = {
    "candidate_id",
    "track",
    "recommended_pathway",
    "markdown_path",
    "json_path",
    "config_version",
    "code_commit",
    "generated_at_utc",
}
BATCH_MANIFEST_FIELDS = {
    "generated_at_utc",
    "input_dir",
    "output_dir",
    "config_version",
    "candidate_count",
    "reports",
}
BATCH_REPORT_FIELDS = {
    "candidate_id",
    "track",
    "recommended_pathway",
    "config_version",
    "input_path",
    "markdown_path",
    "json_path",
    "manifest_path",
}


def test_example_candidate_reports_exist_and_are_conservative() -> None:
    reports_dir = Path("examples/reports")

    for stem in EXAMPLE_REPORTS:
        markdown = (reports_dir / f"{stem}.md").read_text(encoding="utf-8")
        packet = json.loads((reports_dir / f"{stem}.json").read_text(encoding="utf-8"))
        manifest = json.loads(
            (reports_dir / f"{stem}.manifest.json").read_text(encoding="utf-8")
        )

        assert set(manifest) == PER_CANDIDATE_MANIFEST_FIELDS
        assert REQUIRED_DISCLAIMER in markdown
        assert packet["disclaimer"] == REQUIRED_DISCLAIMER
        assert manifest["candidate_id"] == packet["candidate_id"]
        assert packet["candidate_id"].startswith("example-")
        assert packet["positive_evidence"]
        assert packet["negative_evidence"] is not None


def test_batch_example_manifest_covers_all_candidates() -> None:
    reports_dir = Path("examples/batch_reports")
    manifest = json.loads((reports_dir / "batch_manifest.json").read_text(encoding="utf-8"))
    reports = manifest["reports"]

    assert set(manifest) == BATCH_MANIFEST_FIELDS
    assert manifest["candidate_count"] == 3
    assert manifest["input_dir"] == "examples/candidates"
    assert manifest["output_dir"] == "examples/batch_reports"
    assert {report["candidate_id"] for report in reports} == set(EXPECTED_BATCH_CANDIDATES)

    for report in reports:
        assert set(report) == BATCH_REPORT_FIELDS
        candidate_id = report["candidate_id"]
        assert report["track"] == EXPECTED_BATCH_CANDIDATES[candidate_id]
        assert report["recommended_pathway"] == "candidate_review_packet"

        markdown_path = Path(report["markdown_path"])
        json_path = Path(report["json_path"])
        manifest_path = Path(report["manifest_path"])

        assert markdown_path.exists()
        assert json_path.exists()
        assert manifest_path.exists()
        assert REQUIRED_DISCLAIMER in markdown_path.read_text(encoding="utf-8")

        packet = json.loads(json_path.read_text(encoding="utf-8"))
        per_candidate_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert set(per_candidate_manifest) == PER_CANDIDATE_MANIFEST_FIELDS
        assert packet["candidate_id"] == candidate_id
        assert per_candidate_manifest["candidate_id"] == candidate_id


def test_golden_example_reports_match_regenerated_stable_fields(tmp_path) -> None:
    score_batch("examples/candidates", tmp_path)

    stable_fields = {
        "candidate_id",
        "track",
        "config_version",
        "posterior",
        "scores",
        "recommended_pathway",
        "positive_evidence",
        "negative_evidence",
        "blocking_issues",
        "disclaimer",
        "false_positive_discussion",
    }
    for stem in EXAMPLE_REPORTS:
        committed = json.loads(Path(f"examples/batch_reports/{stem}.json").read_text())
        regenerated = json.loads((tmp_path / f"{stem}.json").read_text())

        assert {field: committed[field] for field in stable_fields} == {
            field: regenerated[field] for field in stable_fields
        }
