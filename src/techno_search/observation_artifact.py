"""Admission checks for local real-observation hit-table artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

OBSERVATION_ARTIFACT_SCHEMA_VERSION = "observation_artifact_provenance_v1"

SYNTHETIC_MARKERS = ("synth", "synthetic", "injected", "fixture")
APPROVED_REVIEW_STATUS = "approved"


@dataclass(frozen=True)
class ObservationArtifactAssessment:
    path: Path
    classification: str
    approved_for_pipeline: bool
    sha256: str
    provenance_path: Path
    issues: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": OBSERVATION_ARTIFACT_SCHEMA_VERSION,
            "path": str(self.path),
            "classification": self.classification,
            "approved_for_pipeline": self.approved_for_pipeline,
            "sha256": self.sha256,
            "provenance_path": str(self.provenance_path),
            "issues": list(self.issues),
            "warnings": list(self.warnings),
        }


def provenance_path_for(path: Path) -> Path:
    return path.with_name(path.name + ".provenance.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_prefix(path: Path, limit: int = 64 * 1024) -> str:
    return path.read_bytes()[:limit].decode("utf-8", errors="replace")


def _looks_synthetic(path: Path, content: str) -> bool:
    searchable = f"{path.name}\n{content}".lower()
    return any(marker in searchable for marker in SYNTHETIC_MARKERS)


def _looks_like_turboseti_dat(content: str) -> bool:
    return "# source:" in content.lower() and (
        "top_hit_#" in content.lower() or "drift_rate" in content.lower()
    )


def _load_provenance(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"Provenance sidecar is unreadable: {exc}"
    if not isinstance(raw, dict):
        return None, "Provenance sidecar must contain a JSON object."
    return raw, None


def assess_observation_artifact(path: Path) -> ObservationArtifactAssessment:
    """Classify a local turboSETI hit table and enforce human approval."""
    provenance_path = provenance_path_for(path)
    issues: list[str] = []
    warnings: list[str] = []

    if not path.is_file():
        return ObservationArtifactAssessment(
            path=path,
            classification="invalid",
            approved_for_pipeline=False,
            sha256="",
            provenance_path=provenance_path,
            issues=("Artifact does not exist or is not a regular file.",),
        )

    digest = sha256_file(path)
    content = _read_prefix(path)
    if not _looks_like_turboseti_dat(content):
        issues.append("Artifact is not a recognizable turboSETI hit table.")
        classification = "invalid"
    elif _looks_synthetic(path, content):
        issues.append("Artifact contains an explicit synthetic-data marker.")
        classification = "synthetic"
    else:
        classification = "unverified_real_observation"

    provenance, provenance_error = _load_provenance(provenance_path)
    if provenance_error:
        issues.append(provenance_error)
    if provenance is None:
        warnings.append("No provenance sidecar is present; human approval is required.")
    else:
        declared_classification = str(provenance.get("classification", ""))
        if declared_classification == "synthetic":
            classification = "synthetic"
            issues.append("Provenance sidecar declares the artifact synthetic.")
        elif declared_classification != "real_observation":
            issues.append("Provenance classification must be 'real_observation'.")

        if provenance.get("schema_version") != OBSERVATION_ARTIFACT_SCHEMA_VERSION:
            issues.append("Provenance sidecar has an unsupported schema_version.")
        if provenance.get("artifact_filename") != path.name:
            issues.append("Provenance artifact_filename does not match the local file.")
        if provenance.get("sha256") != digest:
            issues.append("Provenance SHA-256 does not match the local file.")

        source_url = str(provenance.get("source_url", ""))
        parsed_url = urlparse(source_url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            issues.append("Provenance source_url must be a complete HTTPS URL.")
        if not str(provenance.get("source_archive", "")).strip():
            issues.append("Provenance source_archive is required.")
        if not str(provenance.get("instrument", "")).strip():
            issues.append("Provenance instrument is required.")
        if not str(provenance.get("downloaded_utc", "")).strip():
            issues.append("Provenance downloaded_utc is required.")
        if provenance.get("data_use_review_status") != APPROVED_REVIEW_STATUS:
            issues.append("Data-use review has not been approved.")
        if provenance.get("provenance_review_status") != APPROVED_REVIEW_STATUS:
            issues.append("Provenance review has not been approved.")
        if provenance.get("human_approval_status") != APPROVED_REVIEW_STATUS:
            issues.append("Human approval has not been granted.")
        if provenance.get("approved_for_local_real_data") is not True:
            issues.append("Local real-data use is not explicitly authorized.")

        if not issues and classification == "unverified_real_observation":
            classification = "approved_real_observation"

    return ObservationArtifactAssessment(
        path=path,
        classification=classification,
        approved_for_pipeline=classification == "approved_real_observation",
        sha256=digest,
        provenance_path=provenance_path,
        issues=tuple(issues),
        warnings=tuple(warnings),
    )


def assess_observation_directory(path: Path) -> list[ObservationArtifactAssessment]:
    return [
        assess_observation_artifact(artifact)
        for artifact in sorted(path.glob("*.dat"))
        if artifact.is_file()
    ]


def approved_observation_artifacts(path: Path) -> list[Path]:
    return [
        assessment.path
        for assessment in assess_observation_directory(path)
        if assessment.approved_for_pipeline
    ]
