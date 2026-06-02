"""Registry consistency checks for operational log families."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

SQLITE_OPERATIONAL_LOG_REGISTRY_SCHEMA_VERSION = (
    "sqlite_operational_log_registry_v1"
)

SQLITE_OPERATIONAL_LOG_REGISTRY_DISCLAIMER = (
    "SQLite operational log registry checks are local provenance visibility "
    "gates only. They verify that operational log modules, schemas, fixtures, "
    "CLI summaries, and SQLite policy records stay aligned. They do not ingest "
    "real observation data, mutate operational databases, authorize live data "
    "access, authorize external submission, or constitute detections, "
    "discoveries, or external validation."
)

SQLITE_REQUIRED_POLICY = "top_level_sqlite_required_before_production"


@dataclass(frozen=True)
class SqliteOperationalLogRegistryEntry:
    log_id: str
    module_path: str
    schema_path: str
    fixture_path: str
    cli_command: str
    sqlite_policy: str
    sqlite_backed: bool


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_registry_path() -> Path:
    return (
        _project_root()
        / "tests"
        / "fixtures"
        / "sqlite_operational_log_registry.json"
    )


def load_sqlite_operational_log_registry(
    path: Path | None = None,
) -> dict[str, Any]:
    registry_path = path if path is not None else _default_registry_path()
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw["expected_registry"])


def load_sqlite_operational_log_registry_entries(
    path: Path | None = None,
) -> list[SqliteOperationalLogRegistryEntry]:
    registry = load_sqlite_operational_log_registry(path)
    log_ids = [str(log_id) for log_id in registry.get("log_ids", [])]
    overrides = {
        str(key): str(value)
        for key, value in dict(registry.get("cli_command_overrides", {})).items()
    }
    sqlite_policy = str(registry.get("sqlite_policy", SQLITE_REQUIRED_POLICY))
    sqlite_backed_ids = {
        str(log_id) for log_id in registry.get("sqlite_backed_log_ids", [])
    }
    return [
        SqliteOperationalLogRegistryEntry(
            log_id=log_id,
            module_path=f"src/techno_search/{log_id}.py",
            schema_path=f"schemas/{log_id}.schema.json",
            fixture_path=f"tests/fixtures/{log_id}.json",
            cli_command=overrides.get(
                log_id,
                f"{log_id.removesuffix('_log').replace('_', '-')}-summary",
            ),
            sqlite_policy=sqlite_policy,
            sqlite_backed=log_id in sqlite_backed_ids,
        )
        for log_id in log_ids
    ]


def sqlite_operational_log_registry_summary(
    path: Path | None = None,
    *,
    project_root: Path | None = None,
    schema_names: set[str] | None = None,
) -> dict[str, Any]:
    root = project_root if project_root is not None else _project_root()
    registry = load_sqlite_operational_log_registry(path)
    entries = load_sqlite_operational_log_registry_entries(path)
    cli_text = (root / "src" / "techno_search" / "cli.py").read_text(
        encoding="utf-8"
    )
    schema_key_set = (
        schema_names
        if schema_names is not None
        else {path.stem.removesuffix(".schema") for path in (root / "schemas").glob("*.json")}
    )

    expected_count = int(registry.get("expected_log_count", len(entries)))
    issues: list[str] = []
    log_ids = [entry.log_id for entry in entries]
    duplicate_ids = sorted({log_id for log_id in log_ids if log_ids.count(log_id) > 1})
    if duplicate_ids:
        issues.append("duplicate operational log registry IDs: " + ", ".join(duplicate_ids))
    if len(entries) != expected_count:
        issues.append(
            f"operational log registry count {len(entries)} != expected {expected_count}"
        )

    missing_modules = [
        entry.module_path for entry in entries if not (root / entry.module_path).exists()
    ]
    missing_schemas = [
        entry.schema_path for entry in entries if not (root / entry.schema_path).exists()
    ]
    missing_fixtures = [
        entry.fixture_path for entry in entries if not (root / entry.fixture_path).exists()
    ]
    missing_schema_keys = [
        entry.log_id for entry in entries if entry.log_id not in schema_key_set
    ]
    missing_cli_commands = [
        entry.cli_command for entry in entries if f'"{entry.cli_command}"' not in cli_text
    ]
    missing_sqlite_policy = [
        entry.log_id for entry in entries if entry.sqlite_policy != SQLITE_REQUIRED_POLICY
    ]

    if registry.get("require_module_files", True) and missing_modules:
        issues.append("missing operational log module(s): " + ", ".join(missing_modules))
    if registry.get("require_schema_files", True) and missing_schemas:
        issues.append("missing operational log schema(s): " + ", ".join(missing_schemas))
    if registry.get("require_fixture_files", True) and missing_fixtures:
        issues.append("missing operational log fixture(s): " + ", ".join(missing_fixtures))
    if registry.get("require_schema_keys", True) and missing_schema_keys:
        issues.append("missing SCHEMA_FILENAMES key(s): " + ", ".join(missing_schema_keys))
    if registry.get("require_cli_commands", True) and missing_cli_commands:
        issues.append("missing CLI summary command(s): " + ", ".join(missing_cli_commands))
    if registry.get("require_sqlite_policy", True) and missing_sqlite_policy:
        issues.append(
            "missing SQLite policy for log ID(s): " + ", ".join(missing_sqlite_policy)
        )

    sqlite_backed_count = sum(1 for entry in entries if entry.sqlite_backed)

    return {
        "schema_version": SQLITE_OPERATIONAL_LOG_REGISTRY_SCHEMA_VERSION,
        "disclaimer": SQLITE_OPERATIONAL_LOG_REGISTRY_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "expected_log_count": expected_count,
        "registered_log_count": len(entries),
        "module_file_count": len(entries) - len(missing_modules),
        "schema_file_count": len(entries) - len(missing_schemas),
        "fixture_file_count": len(entries) - len(missing_fixtures),
        "schema_key_count": len(entries) - len(missing_schema_keys),
        "cli_command_count": len(entries) - len(missing_cli_commands),
        "missing_module_count": len(missing_modules),
        "missing_schema_count": len(missing_schemas),
        "missing_fixture_count": len(missing_fixtures),
        "missing_schema_key_count": len(missing_schema_keys),
        "missing_cli_command_count": len(missing_cli_commands),
        "sqlite_policy_documented_count": len(entries) - len(missing_sqlite_policy),
        "missing_sqlite_policy_count": len(missing_sqlite_policy),
        "sqlite_backed_count": sqlite_backed_count,
        "sqlite_required_before_production_count": len(entries) - sqlite_backed_count,
        "records": [entry.__dict__ for entry in entries],
    }
