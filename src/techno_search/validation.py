"""Validation helpers for conservative candidate and report artifacts."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from techno_search.background_search import (
    BACKGROUND_DRAFT_REPORT_DISCLAIMER,
    BACKGROUND_DRAFT_REPORT_MANIFEST_SCHEMA_VERSION,
)
from techno_search.log_store import sqlite_log_validation_errors
from techno_search.reporting import REQUIRED_DISCLAIMER
from techno_search.schemas import PosteriorClass, Track, candidate_from_mapping

BANNED_REPORT_PHRASES = (
    "alien signal",
    "confirmed alien",
    "proof of extraterrestrial",
    "discovery of extraterrestrial intelligence",
)

REQUIRED_PACKET_FIELDS = {
    "candidate_id",
    "track",
    "source_ids",
    "features",
    "posterior",
    "scores",
    "recommended_pathway",
    "positive_evidence",
    "negative_evidence",
    "blocking_issues",
    "provenance",
    "schema_version",
    "config_version",
    "disclaimer",
    "false_positive_discussion",
}

REQUIRED_MANIFEST_FIELDS = {
    "candidate_id",
    "track",
    "recommended_pathway",
    "schema_version",
    "markdown_path",
    "json_path",
    "config_version",
    "code_commit",
    "generated_at_utc",
    "provenance_summary",
}

REQUIRED_DRAFT_REPORT_MANIFEST_FIELDS = {
    "schema_version",
    "generated_at_utc",
    "source_readiness_path",
    "output_dir",
    "draft_report_count",
    "disclaimer",
    "reports",
}

REQUIRED_DRAFT_REPORT_ENTRY_FIELDS = {
    "draft_id",
    "readiness_id",
    "follow_up_id",
    "run_id",
    "target_id",
    "track",
    "draft_status",
    "markdown_path",
    "user_approval_required",
    "external_submission_allowed",
    "network_access_allowed",
}


@dataclass(frozen=True)
class ValidationResult:
    """Validation result with machine-readable messages."""

    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def validate_candidate_mapping(data: Mapping[str, Any]) -> ValidationResult:
    """Validate a normalized candidate JSON mapping."""

    errors: list[str] = []
    warnings: list[str] = []

    _require_mapping_fields(
        data,
        required=("candidate_id", "track", "features"),
        context="candidate",
        errors=errors,
    )
    if "track" in data:
        try:
            Track(str(data["track"]))
        except ValueError:
            errors.append(f"Unsupported candidate track: {data['track']!r}")

    if "features" in data and not isinstance(data["features"], Mapping):
        errors.append("candidate.features must be a mapping")
    if "provenance" in data and not isinstance(data["provenance"], Mapping):
        errors.append("candidate.provenance must be a mapping when present")
    if "source_ids" in data and not _is_string_sequence(data["source_ids"]):
        errors.append("candidate.source_ids must be a sequence of strings when present")

    if "provenance" not in data or not data.get("provenance"):
        warnings.append("candidate.provenance is empty or missing")

    errors.extend(_conservative_language_errors(data, context="candidate"))

    if not errors:
        try:
            candidate_from_mapping(data)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"candidate cannot be normalized: {exc}")

    return ValidationResult(tuple(errors), tuple(warnings))


def validate_candidate_file(path: Path | str) -> ValidationResult:
    """Validate a candidate JSON file."""

    try:
        data = _load_json_mapping(path)
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        return ValidationResult(errors=(f"candidate file cannot be read: {exc}",))
    return validate_candidate_mapping(data)


def validate_report_packet(data: Mapping[str, Any]) -> ValidationResult:
    """Validate a generated candidate review packet."""

    errors: list[str] = []
    warnings: list[str] = []

    _require_mapping_fields(
        data,
        required=tuple(sorted(REQUIRED_PACKET_FIELDS)),
        context="report packet",
        errors=errors,
    )
    if data.get("disclaimer") != REQUIRED_DISCLAIMER:
        errors.append("report packet disclaimer does not match the required disclaimer")
    if "posterior" in data:
        posterior = data["posterior"]
        if not isinstance(posterior, Mapping):
            errors.append("report packet posterior must be a mapping")
        else:
            missing = {item.value for item in PosteriorClass} - set(posterior)
            if missing:
                errors.append(f"report packet posterior missing fields: {sorted(missing)}")
    if "provenance" in data and not isinstance(data["provenance"], Mapping):
        errors.append("report packet provenance must be a mapping")
    if "negative_evidence" in data and not isinstance(data["negative_evidence"], list):
        errors.append("report packet negative_evidence must be a list")
    if "blocking_issues" in data and not isinstance(data["blocking_issues"], list):
        errors.append("report packet blocking_issues must be a list")
    if not data.get("false_positive_discussion"):
        warnings.append("report packet false_positive_discussion is empty")

    errors.extend(_conservative_language_errors(data, context="report packet"))
    return ValidationResult(tuple(errors), tuple(warnings))


def validate_report_manifest(data: Mapping[str, Any]) -> ValidationResult:
    """Validate a report persistence manifest."""

    errors: list[str] = []
    _require_mapping_fields(
        data,
        required=tuple(sorted(REQUIRED_MANIFEST_FIELDS)),
        context="report manifest",
        errors=errors,
    )
    if "track" in data:
        try:
            Track(str(data["track"]))
        except ValueError:
            errors.append(f"Unsupported report manifest track: {data['track']!r}")
    return ValidationResult(tuple(errors))


def validate_report_directory(path: Path | str) -> ValidationResult:
    """Validate generated report JSON packets and per-candidate manifests in a directory."""

    report_dir = Path(path)
    errors: list[str] = []
    warnings: list[str] = []

    if not report_dir.exists():
        return ValidationResult(errors=(f"report directory does not exist: {report_dir}",))

    packet_paths = sorted(
        item
        for item in report_dir.glob("*.json")
        if not item.name.endswith(".manifest.json") and item.name != "batch_manifest.json"
    )
    if not packet_paths:
        errors.append("report directory contains no candidate JSON packets")

    for packet_path in packet_paths:
        result = _validate_json_file(packet_path, validate_report_packet)
        errors.extend(f"{packet_path.name}: {error}" for error in result.errors)
        warnings.extend(f"{packet_path.name}: {warning}" for warning in result.warnings)

        manifest_path = packet_path.with_suffix(".manifest.json")
        if not manifest_path.exists():
            errors.append(f"{packet_path.name}: missing manifest {manifest_path.name}")
            continue
        manifest_result = _validate_json_file(manifest_path, validate_report_manifest)
        errors.extend(f"{manifest_path.name}: {error}" for error in manifest_result.errors)
        warnings.extend(
            f"{manifest_path.name}: {warning}" for warning in manifest_result.warnings
        )

    return ValidationResult(tuple(errors), tuple(warnings))


def validate_draft_report_manifest(data: Mapping[str, Any]) -> ValidationResult:
    """Validate a persisted background draft report manifest."""

    errors: list[str] = []
    _require_mapping_fields(
        data,
        required=tuple(sorted(REQUIRED_DRAFT_REPORT_MANIFEST_FIELDS)),
        context="draft report manifest",
        errors=errors,
    )
    if data.get("schema_version") != BACKGROUND_DRAFT_REPORT_MANIFEST_SCHEMA_VERSION:
        errors.append("draft report manifest schema_version is unsupported")
    if data.get("disclaimer") != BACKGROUND_DRAFT_REPORT_DISCLAIMER:
        errors.append("draft report manifest disclaimer is unsupported")
    reports = data.get("reports")
    if not isinstance(reports, list) or not reports:
        errors.append("draft report manifest reports must be a non-empty list")
    else:
        for index, report in enumerate(reports):
            if not isinstance(report, Mapping):
                errors.append(f"draft report manifest report {index} must be a mapping")
                continue
            _require_mapping_fields(
                report,
                required=tuple(sorted(REQUIRED_DRAFT_REPORT_ENTRY_FIELDS)),
                context=f"draft report manifest report {index}",
                errors=errors,
            )
            if report.get("external_submission_allowed") is not False:
                errors.append(
                    f"draft report manifest report {index} allows external submission"
                )
            if report.get("network_access_allowed") is not False:
                errors.append(
                    f"draft report manifest report {index} allows network access"
                )
    return ValidationResult(tuple(errors))


def validate_draft_report_directory(path: Path | str) -> ValidationResult:
    """Validate persisted conservative draft report Markdown and manifest files."""

    report_dir = Path(path)
    errors: list[str] = []
    warnings: list[str] = []
    if not report_dir.exists():
        return ValidationResult(
            errors=(f"draft report directory does not exist: {report_dir}",)
        )
    manifest_path = report_dir / "background_draft_report_manifest.json"
    if not manifest_path.exists():
        return ValidationResult(
            errors=(f"draft report manifest does not exist: {manifest_path}",)
        )
    manifest_result = _validate_json_file(
        manifest_path,
        validate_draft_report_manifest,
    )
    errors.extend(manifest_result.errors)
    warnings.extend(manifest_result.warnings)
    try:
        manifest = _load_json_mapping(manifest_path)
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        return ValidationResult(errors=(f"draft report manifest cannot be read: {exc}",))
    for report in manifest.get("reports", ()):
        if not isinstance(report, Mapping):
            continue
        markdown_path = Path(str(report.get("markdown_path", "")))
        if not markdown_path.exists():
            errors.append(f"draft report Markdown does not exist: {markdown_path}")
            continue
        text = markdown_path.read_text(encoding="utf-8")
        required_sections = (
            "## Evidence Supporting Follow-Up",
            "## Negative Evidence",
            "## Uncertainty And Limitations",
            "## Blocking Issues",
            "## Recommended Next Steps",
            "## Gates",
        )
        for section in required_sections:
            if section not in text:
                errors.append(f"{markdown_path.name}: missing section {section}")
        if BACKGROUND_DRAFT_REPORT_DISCLAIMER not in text:
            errors.append(f"{markdown_path.name}: missing draft report disclaimer")
        if "External submission allowed: `False`" not in text:
            errors.append(f"{markdown_path.name}: external submission gate missing")
        if "Network access allowed: `False`" not in text:
            errors.append(f"{markdown_path.name}: network access gate missing")
        lowered = text.lower()
        for phrase in BANNED_REPORT_PHRASES:
            if phrase in lowered:
                errors.append(
                    f"{markdown_path.name}: uses unsupported phrase {phrase!r}"
                )
    return ValidationResult(tuple(errors), tuple(warnings))


def validate_sqlite_log_database(path: Path | str) -> ValidationResult:
    """Validate top-level SQLite operational log invariants."""

    return ValidationResult(errors=sqlite_log_validation_errors(Path(path)))


def _validate_json_file(
    path: Path,
    validator: Callable[[Mapping[str, Any]], ValidationResult],
) -> ValidationResult:
    try:
        data = _load_json_mapping(path)
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        return ValidationResult(errors=(f"JSON file cannot be read: {exc}",))
    return validator(data)


def _load_json_mapping(path: Path | str) -> Mapping[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, Mapping):
        msg = "top-level JSON value must be an object"
        raise TypeError(msg)
    return data


def _require_mapping_fields(
    data: Mapping[str, Any],
    *,
    required: Sequence[str],
    context: str,
    errors: list[str],
) -> None:
    for field in required:
        if field not in data:
            errors.append(f"{context} missing required field: {field}")


def _is_string_sequence(value: object) -> bool:
    return isinstance(value, list | tuple) and all(isinstance(item, str) for item in value)


def _conservative_language_errors(data: Mapping[str, Any], *, context: str) -> list[str]:
    text = json.dumps(data, sort_keys=True).replace(REQUIRED_DISCLAIMER, "")
    lowered = text.lower()
    return [
        f"{context} uses unsupported phrase: {phrase!r}"
        for phrase in BANNED_REPORT_PHRASES
        if phrase in lowered
    ]
