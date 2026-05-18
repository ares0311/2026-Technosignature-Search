from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUBMISSION_READINESS_SCHEMA_VERSION = "submission_readiness_v1"

SUBMISSION_READINESS_DISCLAIMER = (
    "Submission readiness records are local provenance checklists only. "
    "A 'ready' status means all required local provenance fields are present — "
    "it does not authorize external submission, does not constitute a detection "
    "claim, and does not bypass the explicit user decision record requirement."
)

ALLOWED_READINESS_STATUSES = frozenset(
    {"ready", "blocked", "pending_review", "not_applicable"}
)

REQUIRED_PROVENANCE_FIELDS = frozenset(
    {
        "candidate_id",
        "scoring_config_version",
        "model_id",
        "model_version",
        "serving_id",
        "pathway",
        "has_negative_evidence",
        "has_blocking_issues_documented",
        "operator_handoff_id",
    }
)


def _default_submission_readiness_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "submission_readiness.json"
    )


@dataclass
class SubmissionReadinessRecord:
    readiness_id: str
    candidate_id: str
    pathway: str
    readiness_status: str
    present_provenance_fields: list[str]
    missing_provenance_fields: list[str]
    blocking_issues: list[str]
    operator_handoff_id: str
    assessed_utc: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "readiness_id": self.readiness_id,
            "candidate_id": self.candidate_id,
            "pathway": self.pathway,
            "readiness_status": self.readiness_status,
            "present_provenance_fields": self.present_provenance_fields,
            "missing_provenance_fields": self.missing_provenance_fields,
            "blocking_issues": self.blocking_issues,
            "operator_handoff_id": self.operator_handoff_id,
            "assessed_utc": self.assessed_utc,
            "notes": self.notes,
        }


def load_submission_readiness_records(
    fixture_path: Path | None = None,
) -> list[SubmissionReadinessRecord]:
    path = fixture_path or _default_submission_readiness_path()
    data = json.loads(Path(path).read_text())
    records = []
    for entry in data.get("submission_readiness_records", []):
        records.append(
            SubmissionReadinessRecord(
                readiness_id=entry["readiness_id"],
                candidate_id=entry["candidate_id"],
                pathway=entry["pathway"],
                readiness_status=entry["readiness_status"],
                present_provenance_fields=list(
                    entry.get("present_provenance_fields", [])
                ),
                missing_provenance_fields=list(
                    entry.get("missing_provenance_fields", [])
                ),
                blocking_issues=list(entry.get("blocking_issues", [])),
                operator_handoff_id=entry.get("operator_handoff_id", ""),
                assessed_utc=entry["assessed_utc"],
                notes=entry.get("notes", ""),
            )
        )
    return records


def submission_readiness_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    records = load_submission_readiness_records(fixture_path)
    by_status: dict[str, int] = {}
    by_pathway: dict[str, int] = {}
    total_blocking = 0
    total_missing = 0
    for r in records:
        by_status[r.readiness_status] = by_status.get(r.readiness_status, 0) + 1
        by_pathway[r.pathway] = by_pathway.get(r.pathway, 0) + 1
        total_blocking += len(r.blocking_issues)
        total_missing += len(r.missing_provenance_fields)
    ready = [r for r in records if r.readiness_status == "ready"]
    blocked = [r for r in records if r.readiness_status == "blocked"]
    return {
        "schema_version": SUBMISSION_READINESS_SCHEMA_VERSION,
        "disclaimer": SUBMISSION_READINESS_DISCLAIMER,
        "record_count": len(records),
        "ready_count": len(ready),
        "blocked_count": len(blocked),
        "total_blocking_issue_count": total_blocking,
        "total_missing_provenance_field_count": total_missing,
        "by_status": by_status,
        "by_pathway": by_pathway,
        "required_provenance_fields": sorted(REQUIRED_PROVENANCE_FIELDS),
    }
