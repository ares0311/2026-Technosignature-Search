"""DECISION-134 AI hardening production gate checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

AI_HARDENING_GATE_SCHEMA_VERSION = "ai_hardening_gate_v1"

AI_HARDENING_GATE_DISCLAIMER = (
    "AI hardening gate records are production-readiness controls for learned "
    "and AI-assisted pathway routing. They are local citizen-science evidence "
    "gates only. They do not constitute detections, discoveries, expert review, "
    "external validation, or authorization for external submission."
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_gate_path() -> Path:
    return _project_root() / "tests" / "fixtures" / "ai_hardening_gate.json"


def load_ai_hardening_gate(path: Path | None = None) -> dict[str, Any]:
    gate_path = path if path is not None else _default_gate_path()
    raw = json.loads(gate_path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], raw)


def _normalized_text(text: str) -> str:
    return " ".join(text.lower().split())


def _phrase_present(text: str, phrase: str) -> bool:
    return _normalized_text(phrase) in _normalized_text(text)


def _as_bool(value: object) -> bool:
    return bool(value) if isinstance(value, bool) else False


def _as_list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _path_exists(root: Path, path_text: str) -> bool:
    path = Path(path_text)
    candidate = path if path.is_absolute() else root / path
    return candidate.exists()


def _resolve_path(root: Path, path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else root / path


def _file_count(root: Path, path_text: str) -> int:
    candidate = _resolve_path(root, path_text)
    if not candidate.exists():
        return 0
    if candidate.is_file():
        return 1
    return sum(1 for item in candidate.rglob("*") if item.is_file())


def _calibration_holdout_summary(root: Path) -> dict[str, Any]:
    holdout_path = "data/calibration_corpus"
    path = _resolve_path(root, holdout_path)
    dat_files = sorted(path.glob("*.dat")) if path.exists() else []
    non_training_files = [
        item for item in dat_files if "HIP99427" not in item.name
    ]
    targets: set[str] = set()
    for item in non_training_files:
        parts = item.stem.split("_")
        hip_parts = [part for part in parts if part.startswith("HIP")]
        if hip_parts:
            targets.update(hip_parts)
        elif "Voyager1" in item.name:
            targets.add("VOYAGER-1")

    return {
        "local_calibration_holdout_path": holdout_path,
        "local_calibration_holdout_exists": path.exists(),
        "local_calibration_holdout_dat_file_count": len(dat_files),
        "local_calibration_holdout_non_training_dat_file_count": len(
            non_training_files
        ),
        "local_calibration_holdout_non_training_targets": sorted(targets),
        "local_calibration_holdout_provisional_only": bool(non_training_files),
        "local_calibration_holdout_gate_closure_ready": False,
        "local_calibration_holdout_limitation": (
            "Local calibration-corpus DAT files can support provisional "
            "held-out review because some files are outside HIP99427, but they "
            "do not by themselves close DECISION-134 because they were already "
            "used for calibration-threshold evidence and are not a populated "
            "DECISION-133 evidence stream."
        ),
    }


def ai_hardening_gate_summary(
    path: Path | None = None,
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    root = project_root if project_root is not None else _project_root()
    gate = load_ai_hardening_gate(path)

    status = str(gate.get("status", "unknown"))
    production_promotion_allowed = _as_bool(gate.get("production_promotion_allowed"))
    external_submission_allowed = _as_bool(gate.get("external_submission_allowed"))
    detection_claimed = _as_bool(gate.get("detection_claimed"))
    expert_review_claimed = _as_bool(gate.get("expert_review_claimed"))
    independent_methods_required = int(gate.get("independent_methods_required", 0))

    requirements = [
        cast(dict[str, Any], item)
        for item in _as_list(gate.get("requirements"))
        if isinstance(item, dict)
    ]
    blocking_requirements = [
        item
        for item in requirements
        if _as_bool(item.get("blocking")) and not _as_bool(item.get("satisfied"))
    ]
    satisfied_requirements = [
        item for item in requirements if _as_bool(item.get("satisfied"))
    ]

    methods = [
        cast(dict[str, Any], item)
        for item in _as_list(gate.get("independent_methods"))
        if isinstance(item, dict)
    ]
    recorded_methods = [item for item in methods if _as_bool(item.get("recorded"))]

    evidence_paths = [str(item) for item in _as_list(gate.get("evidence_paths"))]
    existing_evidence_paths = [
        item for item in evidence_paths if _path_exists(root, item)
    ]
    evidence_file_counts = {
        item: _file_count(root, item) for item in evidence_paths
    }
    populated_evidence_paths = [
        item for item in evidence_paths if evidence_file_counts[item] > 0
    ]
    empty_existing_evidence_paths = [
        item for item in existing_evidence_paths if evidence_file_counts[item] == 0
    ]
    total_evidence_file_count = sum(evidence_file_counts.values())
    local_holdout = _calibration_holdout_summary(root)

    required_phrases = [
        cast(dict[str, Any], item)
        for item in _as_list(gate.get("required_document_phrases"))
        if isinstance(item, dict)
    ]
    missing_document_phrases: list[dict[str, str]] = []
    for requirement in required_phrases:
        phrase = str(requirement.get("phrase", ""))
        for doc_path in [str(item) for item in _as_list(requirement.get("docs"))]:
            full_path = root / doc_path
            text = full_path.read_text(encoding="utf-8") if full_path.exists() else ""
            if phrase and not _phrase_present(text, phrase):
                missing_document_phrases.append({"doc": doc_path, "phrase": phrase})

    issues: list[str] = []
    if gate.get("schema_version") != AI_HARDENING_GATE_SCHEMA_VERSION:
        issues.append("AI hardening gate schema_version mismatch")
    if status not in {"open", "closed"}:
        issues.append(f"AI hardening gate status {status!r} is invalid")
    if production_promotion_allowed:
        issues.append("AI hardening gate allows production promotion while under review")
    if external_submission_allowed:
        issues.append("AI hardening gate allows external submission")
    if detection_claimed:
        issues.append("AI hardening gate records an unsupported detection claim")
    if expert_review_claimed:
        issues.append("AI hardening gate records unclaimed expert review")
    if missing_document_phrases:
        issues.append("AI hardening blocker visibility is missing from required docs")
    if status == "open" and not blocking_requirements:
        issues.append("AI hardening gate is open but has no blocking requirements")
    if status == "closed" and blocking_requirements:
        issues.append("AI hardening gate is closed with blocking requirements unresolved")
    if status == "closed" and len(recorded_methods) < independent_methods_required:
        issues.append("AI hardening gate is closed without enough independent methods")

    return {
        "schema_version": AI_HARDENING_GATE_SCHEMA_VERSION,
        "disclaimer": AI_HARDENING_GATE_DISCLAIMER,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "gate_id": str(gate.get("gate_id", "")),
        "status": status,
        "production_promotion_allowed": production_promotion_allowed,
        "external_submission_allowed": external_submission_allowed,
        "detection_claimed": detection_claimed,
        "expert_review_claimed": expert_review_claimed,
        "requirement_count": len(requirements),
        "satisfied_requirement_count": len(satisfied_requirements),
        "open_blocking_requirement_count": len(blocking_requirements),
        "open_blocking_requirement_ids": [
            str(item.get("requirement_id", "")) for item in blocking_requirements
        ],
        "independent_methods_required": independent_methods_required,
        "independent_methods_recorded_count": len(recorded_methods),
        "independent_method_ids": [str(item.get("method_id", "")) for item in methods],
        "recorded_independent_method_ids": [
            str(item.get("method_id", "")) for item in recorded_methods
        ],
        "evidence_path_count": len(evidence_paths),
        "existing_evidence_path_count": len(existing_evidence_paths),
        "populated_evidence_path_count": len(populated_evidence_paths),
        "empty_existing_evidence_path_count": len(empty_existing_evidence_paths),
        "total_evidence_file_count": total_evidence_file_count,
        "evidence_paths": evidence_paths,
        "existing_evidence_paths": existing_evidence_paths,
        "populated_evidence_paths": populated_evidence_paths,
        "empty_existing_evidence_paths": empty_existing_evidence_paths,
        "evidence_file_counts": evidence_file_counts,
        "required_document_phrase_count": len(required_phrases),
        "missing_document_phrase_count": len(missing_document_phrases),
        "missing_document_phrases": missing_document_phrases,
        **local_holdout,
    }
