from pathlib import Path


def test_premature_zenodo_publication_path_is_retired() -> None:
    assert not Path("scripts/generate_zenodo_manifest.py").exists()
    assert not Path("docs/ZENODO_ARCHIVE_MANIFEST.md").exists()


def test_active_entrypoints_do_not_instruct_public_deposit() -> None:
    active_paths = (
        Path("README.md"),
        Path("docs/PRODUCTION_READINESS.md"),
        Path("docs/SYSTEMATIC_SEARCH_PLAN.md"),
    )
    forbidden_instructions = (
        "upload to zenodo",
        "publish the deposit",
        "this satisfies p5",
    )
    active_text = "\n".join(path.read_text(encoding="utf-8").lower() for path in active_paths)
    assert all(instruction not in active_text for instruction in forbidden_instructions)
