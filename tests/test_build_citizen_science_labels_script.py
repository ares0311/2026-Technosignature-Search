from pathlib import Path

from scripts.build_citizen_science_labels import (
    COMMITTED_FIXTURE_OUTPUT,
    LOCAL_DEFAULT_OUTPUT,
    resolve_output_path,
)


def test_label_builder_defaults_to_ignored_local_output() -> None:
    assert resolve_output_path(None, update_committed_fixture=False) == LOCAL_DEFAULT_OUTPUT
    assert LOCAL_DEFAULT_OUTPUT.parts[:2] == ("tmp_training", "real_labeled")


def test_label_builder_requires_opt_in_for_committed_fixture() -> None:
    assert (
        resolve_output_path(None, update_committed_fixture=True)
        == COMMITTED_FIXTURE_OUTPUT
    )
    assert Path(
        "examples/real_labeled/hip99427_citizen_science_labels_v1.json"
    ) == COMMITTED_FIXTURE_OUTPUT


def test_label_builder_honors_explicit_output() -> None:
    explicit = Path("/tmp/custom_labels.json")

    assert resolve_output_path(explicit, update_committed_fixture=False) == explicit
    assert resolve_output_path(explicit, update_committed_fixture=True) == explicit
