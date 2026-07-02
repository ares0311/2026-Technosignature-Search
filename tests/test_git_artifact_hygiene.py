import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _is_ignored(path: str) -> bool:
    return (
        subprocess.run(
            ["git", "check-ignore", "-q", path],
            cwd=REPO_ROOT,
            check=False,
        ).returncode
        == 0
    )


def test_gitignore_blocks_generated_science_payloads() -> None:
    gitignore = _read(".gitignore")

    required_patterns = {
        "data/",
        "data_cache/",
        "tmp_training/",
        "tmp_features/",
        "cache/",
        "artifacts/",
        "models/",
        "metrics/",
        "results/*",
        "!results/scans/",
        "!results/scans/**",
        "results/scans/RUN-*/",
        "results/scans/RUN-*/**",
        "docs/LOCAL_DATA_INVENTORY.local.md",
        "*.h5",
        "*.hdf5",
        "*.fil",
        "*.fits",
        "*.fit",
        "*.fits.gz",
        "*.dat",
        "!tests/fixtures/**/*.dat",
        "*.npy",
        "*.npz",
        "*.parquet",
        "*.feather",
        "*.pkl",
        "*.pickle",
        "*.joblib",
        "*.sqlite",
        "*.sqlite3",
        "*.db",
        "*.db-wal",
        "*.db-shm",
        "*.db-journal",
        "*.sqlite-journal",
        "*.sqlite3-journal",
        "*.log",
        "uv.lock",
    }

    missing = sorted(pattern for pattern in required_patterns if pattern not in gitignore)
    assert missing == []


def test_gitignore_effectively_blocks_payloads_but_allows_review_safe_exceptions() -> None:
    ignored_paths = [
        "docs/LOCAL_DATA_INVENTORY.local.md",
        "data/extended_corpus/HIP17147/hits.dat",
        "data_cache/raw/htru2/htru2_features.parquet",
        "tmp_training/htru2/work.parquet",
        "tmp_features/htru2/features.parquet",
        "models/track_a_known_explanations.joblib",
        "metrics/track_a_known_explanations.json",
        "random.h5",
        "random.hdf5",
        "random.fil",
        "random.fits",
        "random.dat",
        "random.sqlite3",
        "random.sqlite3-journal",
        "model.joblib",
        "scan.log",
        "uv.lock",
    ]

    not_ignored_paths = [
        "tests/fixtures/radio/new_fixture.dat",
        "results/scans/2026-06-17/summary.md",
    ]

    assert [path for path in ignored_paths if not _is_ignored(path)] == []
    assert [path for path in not_ignored_paths if _is_ignored(path)] == []
    assert _is_ignored(
        "results/scans/RUN-2026-06-30_030350Z-8MGP-prod-scan/validate_all.json"
    )


def test_local_data_inventory_is_sanitized_github_visible_map() -> None:
    inventory = _read("docs/LOCAL_DATA_INVENTORY.md")

    assert "GitHub-visible artifact map" in inventory
    assert "Ignore the payloads, commit the map." in inventory
    assert "docs/LOCAL_DATA_INVENTORY.local.md" in inventory
    assert "DECISION-134" in inventory
    assert "/Users/" not in inventory
    assert "Repo root:" not in inventory
    assert "Machine:" not in inventory
    assert "Generated:" not in inventory


def test_local_inventory_generator_writes_ignored_snapshot() -> None:
    script = _read("scripts/create_data_inventory.sh")

    assert 'INVENTORY="$REPO_ROOT/docs/LOCAL_DATA_INVENTORY.local.md"' in script
    assert "Do not commit docs/LOCAL_DATA_INVENTORY.local.md" in script
    assert "git add docs/LOCAL_DATA_INVENTORY.md" not in script
    assert "git push origin main" not in script


def test_agent_directives_require_git_add_safe_artifact_policy() -> None:
    directives = _read("AGENTS.md")

    assert "GIT ARTIFACT HYGIENE" in directives
    assert "git add --dry-run ." in directives
    assert "ignore the payloads, commit the map" in directives
    assert "docs/LOCAL_DATA_INVENTORY.local.md" in directives
