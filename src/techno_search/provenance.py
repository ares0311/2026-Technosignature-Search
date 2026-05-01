"""Provenance helpers for generated artifacts and live-data scaffolds."""

from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from techno_search.constants import DEFAULT_SCHEMA_VERSION, DEFAULT_SCORING_CONFIG_VERSION
from techno_search.schemas import Candidate


@dataclass(frozen=True)
class ProvenanceRecord:
    """Structured provenance summary for reports and provider requests."""

    schema_version: str
    config_version: str
    generated_at_utc: str
    code_commit: str | None
    input_path: str | None = None
    provider_name: str | None = None
    query_parameters: dict[str, str] | None = None
    source_ids: tuple[str, ...] = ()
    source_dataset: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "config_version": self.config_version,
            "generated_at_utc": self.generated_at_utc,
            "code_commit": self.code_commit,
            "input_path": self.input_path,
            "provider_name": self.provider_name,
            "query_parameters": self.query_parameters or {},
            "source_ids": list(self.source_ids),
            "source_dataset": self.source_dataset,
        }


def build_provenance_record(
    *,
    input_path: Path | str | None = None,
    provider_name: str | None = None,
    query_parameters: Mapping[str, str] | None = None,
    source_ids: Sequence[str] = (),
    source_dataset: str | None = None,
    config_version: str = DEFAULT_SCORING_CONFIG_VERSION,
    schema_version: str = DEFAULT_SCHEMA_VERSION,
) -> ProvenanceRecord:
    """Build a provenance record."""

    return ProvenanceRecord(
        schema_version=schema_version,
        config_version=config_version,
        generated_at_utc=datetime.now(UTC).isoformat(),
        code_commit=git_commit(),
        input_path=None if input_path is None else str(input_path),
        provider_name=provider_name,
        query_parameters=(
            None if query_parameters is None else dict(sorted(query_parameters.items()))
        ),
        source_ids=tuple(source_ids),
        source_dataset=source_dataset,
    )


def candidate_provenance_record(
    candidate: Candidate,
    *,
    input_path: Path | str | None = None,
) -> ProvenanceRecord:
    """Build a provenance record from a candidate packet."""

    return build_provenance_record(
        input_path=input_path,
        source_ids=candidate.source_ids,
        source_dataset=_optional_str(candidate.provenance.get("source_dataset")),
        config_version=str(
            candidate.provenance.get("config_version", DEFAULT_SCORING_CONFIG_VERSION)
        ),
    )


def git_commit() -> str | None:
    """Return the current short git commit when available."""

    repo_root = Path(__file__).resolve().parents[2]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = result.stdout.strip()
    return commit or None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
