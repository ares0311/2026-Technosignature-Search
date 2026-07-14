from pathlib import Path

import techno_search.cadence_triage as cadence_triage


def test_project_owned_label_creation_scripts_are_retired() -> None:
    assert not Path("scripts/build_citizen_science_labels.py").exists()
    assert not Path("scripts/combine_citizen_science_labels.py").exists()
    assert not Path("src/techno_search/citizen_science_labels.py").exists()
    assert not Path("src/techno_search/learned_scoring_model.py").exists()


def test_cadence_module_exposes_no_label_dataset_writer() -> None:
    assert not hasattr(cadence_triage, "build_citizen_science_dataset")
    assert not hasattr(cadence_triage, "write_citizen_science_dataset")


def test_label_trained_model_commands_are_absent() -> None:
    cli_source = Path("src/techno_search/cli.py").read_text(encoding="utf-8")
    forbidden_commands = (
        "learned-model-summary",
        "synthetic-training-summary",
        "real-labels-model-summary",
        "combined-model-summary",
    )
    assert all(command not in cli_source for command in forbidden_commands)
