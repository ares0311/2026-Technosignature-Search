"""Schema drift detector — checks that JSON schema files are loadable and structurally sound."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_DRIFT_DISCLAIMER = (
    "Schema drift detection is a shallow structural check only. "
    "It confirms that schema files are parseable and contain expected top-level fields. "
    "It does not perform deep semantic validation or guarantee schema correctness "
    "against all possible inputs."
)

_REQUIRED_SCHEMA_FIELDS = frozenset({"$schema", "title", "type", "required"})
_EXPECTED_SCHEMA_VALUE = "https://json-schema.org/draft/2020-12/schema"


def _default_schemas_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas"


def detect_schema_drift(
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Check that all schema files are loadable and have required top-level fields."""

    directory = schemas_dir or _default_schemas_dir()
    schema_paths = sorted(directory.glob("*.schema.json"))

    schema_count = len(schema_paths)
    drift_details: list[dict[str, str]] = []

    for path in schema_paths:
        issues = []
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            drift_details.append(
                {"schema_file": path.name, "issue": f"parse_error: {exc}"}
            )
            continue

        if schema.get("$schema") != _EXPECTED_SCHEMA_VALUE:
            issues.append(
                f"$schema mismatch: {schema.get('$schema')!r} != {_EXPECTED_SCHEMA_VALUE!r}"
            )
        for field in _REQUIRED_SCHEMA_FIELDS:
            if field not in schema:
                issues.append(f"missing required top-level field: {field!r}")
        if schema.get("type") != "object":
            issues.append(f"type is not 'object': {schema.get('type')!r}")
        if not schema.get("required"):
            issues.append("'required' field is empty or absent")

        for issue in issues:
            drift_details.append({"schema_file": path.name, "issue": issue})

    drift_count = len(drift_details)

    return {
        "disclaimer": SCHEMA_DRIFT_DISCLAIMER,
        "schemas_dir": str(directory),
        "schema_count": schema_count,
        "drift_count": drift_count,
        "ok": drift_count == 0,
        "drift_details": drift_details,
    }
