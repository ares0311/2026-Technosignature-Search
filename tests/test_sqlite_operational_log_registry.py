from __future__ import annotations

import json
from pathlib import Path

from techno_search.sqlite_operational_log_registry import (
    SQLITE_OPERATIONAL_LOG_REGISTRY_SCHEMA_VERSION,
    SQLITE_REQUIRED_POLICY,
    load_sqlite_operational_log_registry,
    load_sqlite_operational_log_registry_entries,
    sqlite_operational_log_registry_summary,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sqlite_operational_log_registry.json"


def _write_registry(
    path: Path,
    *,
    log_ids: list[str] | None = None,
    sqlite_policy: str = SQLITE_REQUIRED_POLICY,
) -> Path:
    registry_path = path / "registry.json"
    ids = log_ids if log_ids is not None else ["example_log"]
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": SQLITE_OPERATIONAL_LOG_REGISTRY_SCHEMA_VERSION,
                "expected_registry": {
                    "expected_log_count": len(ids),
                    "require_module_files": True,
                    "require_schema_files": True,
                    "require_fixture_files": True,
                    "require_schema_keys": True,
                    "require_cli_commands": True,
                    "require_sqlite_policy": True,
                    "sqlite_policy": sqlite_policy,
                    "sqlite_backed_log_ids": [],
                    "cli_command_overrides": {
                        "example_log": "example-log-summary",
                    },
                    "log_ids": ids,
                },
            }
        ),
        encoding="utf-8",
    )
    return registry_path


def _write_project(path: Path, *, command: str = "example-log-summary") -> None:
    (path / "src" / "techno_search").mkdir(parents=True)
    (path / "schemas").mkdir()
    (path / "tests" / "fixtures").mkdir(parents=True)
    (path / "src" / "techno_search" / "example_log.py").write_text(
        "\"\"\"Example log.\"\"\"\n",
        encoding="utf-8",
    )
    (path / "schemas" / "example_log.schema.json").write_text("{}", encoding="utf-8")
    (path / "tests" / "fixtures" / "example_log.json").write_text(
        "{}",
        encoding="utf-8",
    )
    (path / "src" / "techno_search" / "cli.py").write_text(
        f'"{command}"\n',
        encoding="utf-8",
    )


def test_load_fixture_expectations() -> None:
    registry = load_sqlite_operational_log_registry(FIXTURE_PATH)

    assert registry["expected_log_count"] == 0
    assert registry["sqlite_policy"] == SQLITE_REQUIRED_POLICY


def test_load_registry_entries_expand_paths_and_commands() -> None:
    entries = load_sqlite_operational_log_registry_entries(FIXTURE_PATH)

    assert len(entries) == 0


def test_default_project_registry_passes() -> None:
    summary = sqlite_operational_log_registry_summary()

    assert summary["schema_version"] == SQLITE_OPERATIONAL_LOG_REGISTRY_SCHEMA_VERSION
    assert summary["ok"] is True
    assert summary["issue_count"] == 0
    assert summary["registered_log_count"] == 0
    assert summary["missing_cli_command_count"] == 0
    assert summary["missing_schema_key_count"] == 0
    assert summary["missing_sqlite_policy_count"] == 0
    assert summary["sqlite_required_before_production_count"] == 0


def test_custom_registry_passes(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path)
    _write_project(tmp_path)

    summary = sqlite_operational_log_registry_summary(
        registry_path,
        project_root=tmp_path,
        schema_names={"example_log"},
    )

    assert summary["ok"] is True
    assert summary["registered_log_count"] == 1


def test_detects_missing_module(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path)
    _write_project(tmp_path)
    (tmp_path / "src" / "techno_search" / "example_log.py").unlink()

    summary = sqlite_operational_log_registry_summary(
        registry_path,
        project_root=tmp_path,
        schema_names={"example_log"},
    )

    assert summary["ok"] is False
    assert summary["missing_module_count"] == 1


def test_detects_missing_cli_command(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path)
    _write_project(tmp_path, command="different-command")

    summary = sqlite_operational_log_registry_summary(
        registry_path,
        project_root=tmp_path,
        schema_names={"example_log"},
    )

    assert summary["ok"] is False
    assert summary["missing_cli_command_count"] == 1


def test_detects_missing_schema_key(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path)
    _write_project(tmp_path)

    summary = sqlite_operational_log_registry_summary(
        registry_path,
        project_root=tmp_path,
        schema_names=set(),
    )

    assert summary["ok"] is False
    assert summary["missing_schema_key_count"] == 1


def test_detects_missing_sqlite_policy(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path, sqlite_policy="fixture_only")
    _write_project(tmp_path)

    summary = sqlite_operational_log_registry_summary(
        registry_path,
        project_root=tmp_path,
        schema_names={"example_log"},
    )

    assert summary["ok"] is False
    assert summary["missing_sqlite_policy_count"] == 1
