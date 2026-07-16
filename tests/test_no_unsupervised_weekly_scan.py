from pathlib import Path


def test_retired_weekly_scan_and_duplicate_guides_stay_absent() -> None:
    retired_paths = (
        ".github/workflows/weekly_scan.yml",
        "docs/PRODUCTION_SCAN_GUIDE.md",
        "docs/SCAN_SCHEDULE.md",
    )
    assert all(not Path(path).exists() for path in retired_paths)


def test_active_workflows_do_not_push_generated_scans_to_main() -> None:
    workflow_dir = Path(".github/workflows")
    workflow_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(workflow_dir.glob("*.yml"))
    )
    assert "git push origin main" not in workflow_text
    assert "results/scans/" not in workflow_text
