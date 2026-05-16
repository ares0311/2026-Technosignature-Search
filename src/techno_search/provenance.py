"""Provenance helpers for generated artifacts and live-data scaffolds."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
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
    service_url: str | None = None
    query_parameters: dict[str, str] | None = None
    cache_key: str | None = None
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
            "service_url": self.service_url,
            "query_parameters": self.query_parameters or {},
            "cache_key": self.cache_key,
            "source_ids": list(self.source_ids),
            "source_dataset": self.source_dataset,
        }


def build_provenance_record(
    *,
    input_path: Path | str | None = None,
    provider_name: str | None = None,
    service_url: str | None = None,
    query_parameters: Mapping[str, str] | None = None,
    cache_key: str | None = None,
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
        service_url=service_url,
        query_parameters=(
            None if query_parameters is None else dict(sorted(query_parameters.items()))
        ),
        cache_key=cache_key,
        source_ids=tuple(source_ids),
        source_dataset=source_dataset,
    )


def build_cache_key(
    *,
    provider_name: str,
    query: str,
    purpose: str,
    parameters: Mapping[str, str] | None = None,
    config_version: str = DEFAULT_SCORING_CONFIG_VERSION,
    schema_version: str = DEFAULT_SCHEMA_VERSION,
) -> str:
    """Build a deterministic cache key for live-provider request metadata."""

    payload = {
        "provider_name": provider_name,
        "query": query,
        "purpose": purpose,
        "parameters": dict(sorted((parameters or {}).items())),
        "config_version": config_version,
        "schema_version": schema_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


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


PROVENANCE_CHAIN_DISCLAIMER = (
    "Provenance chain validation is a local structural consistency check only. "
    "It verifies that report manifests carry required provenance fields. "
    "A passing check does not constitute external validation or a discovery claim."
)


def provenance_chain_validator(
    manifest_paths: list[Path] | None = None,
    report_dir: Path | None = None,
) -> dict[str, Any]:
    """Validate that all report manifests carry required provenance chain fields.

    Checks each manifest for: schema_version, config_version, generated_at_utc,
    and a provenance_summary block. Returns ok=True when all manifests pass.
    """

    required_fields = {"schema_version", "config_version", "generated_at_utc"}
    required_provenance_fields = {"generated_at_utc"}

    paths: list[Path] = []
    if manifest_paths is not None:
        paths = list(manifest_paths)
    elif report_dir is not None:
        paths = sorted(Path(report_dir).glob("*.manifest.json"))
    else:
        default_report_dir = Path(__file__).resolve().parents[2] / "examples" / "reports"
        paths = sorted(default_report_dir.glob("*.manifest.json"))

    missing_field_cases: list[dict[str, Any]] = []
    missing_provenance_cases: list[dict[str, Any]] = []

    for path in paths:
        try:
            with path.open(encoding="utf-8") as handle:
                manifest = json.load(handle)
        except (OSError, ValueError):
            missing_field_cases.append({"path": str(path), "reason": "unreadable"})
            continue

        missing = [f for f in required_fields if f not in manifest]
        if missing:
            missing_field_cases.append({"path": str(path), "missing_fields": missing})

        provenance = manifest.get("provenance_summary")
        if not isinstance(provenance, dict):
            missing_provenance_cases.append(
                {"path": str(path), "reason": "provenance_summary missing or not a dict"}
            )
        else:
            missing_prov = [f for f in required_provenance_fields if f not in provenance]
            if missing_prov:
                missing_provenance_cases.append(
                    {"path": str(path), "missing_provenance_fields": missing_prov}
                )

    ok = len(missing_field_cases) == 0 and len(missing_provenance_cases) == 0
    return {
        "disclaimer": PROVENANCE_CHAIN_DISCLAIMER,
        "manifest_count": len(paths),
        "ok": ok,
        "missing_field_case_count": len(missing_field_cases),
        "missing_provenance_case_count": len(missing_provenance_cases),
        "missing_field_cases": missing_field_cases,
        "missing_provenance_cases": missing_provenance_cases,
    }


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
