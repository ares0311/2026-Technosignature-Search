from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OPERATOR_HANDOFF_SCHEMA_VERSION = "operator_handoff_template_v1"

OPERATOR_HANDOFF_DISCLAIMER = (
    "Operator handoff templates are local scheduling artifacts only. "
    "An approved handoff template does not authorize external submission, "
    "does not constitute a detection claim, and does not modify candidate "
    "posteriors. External submission requires a separate explicit user decision record."
)

ALLOWED_HANDOFF_STATUSES = frozenset(
    {"draft", "pending_review", "approved", "rejected", "expired"}
)


def _default_handoff_fixture_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "operator_handoff_templates.json"
    )


@dataclass
class OperatorHandoffTemplate:
    handoff_id: str
    candidate_id: str
    model_id: str
    model_version: str
    inference_backend: str
    serving_id: str
    score: float
    pathway: str
    handoff_status: str
    operator_id: str
    created_utc: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "candidate_id": self.candidate_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "inference_backend": self.inference_backend,
            "serving_id": self.serving_id,
            "score": self.score,
            "pathway": self.pathway,
            "handoff_status": self.handoff_status,
            "operator_id": self.operator_id,
            "created_utc": self.created_utc,
            "notes": self.notes,
        }


def load_handoff_templates(
    fixture_path: Path | None = None,
) -> list[OperatorHandoffTemplate]:
    path = fixture_path or _default_handoff_fixture_path()
    data = json.loads(Path(path).read_text())
    templates = []
    for entry in data.get("handoff_templates", []):
        templates.append(
            OperatorHandoffTemplate(
                handoff_id=entry["handoff_id"],
                candidate_id=entry["candidate_id"],
                model_id=entry["model_id"],
                model_version=entry["model_version"],
                inference_backend=entry["inference_backend"],
                serving_id=entry["serving_id"],
                score=float(entry["score"]),
                pathway=entry["pathway"],
                handoff_status=entry["handoff_status"],
                operator_id=entry["operator_id"],
                created_utc=entry["created_utc"],
                notes=entry.get("notes", ""),
            )
        )
    return templates


def operator_handoff_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    templates = load_handoff_templates(fixture_path)
    by_status: dict[str, int] = {}
    by_pathway: dict[str, int] = {}
    by_model: dict[str, int] = {}
    for t in templates:
        by_status[t.handoff_status] = by_status.get(t.handoff_status, 0) + 1
        by_pathway[t.pathway] = by_pathway.get(t.pathway, 0) + 1
        by_model[t.model_id] = by_model.get(t.model_id, 0) + 1
    return {
        "schema_version": OPERATOR_HANDOFF_SCHEMA_VERSION,
        "disclaimer": OPERATOR_HANDOFF_DISCLAIMER,
        "template_count": len(templates),
        "approved_count": by_status.get("approved", 0),
        "pending_count": by_status.get("pending_review", 0),
        "rejected_count": by_status.get("rejected", 0),
        "draft_count": by_status.get("draft", 0),
        "by_status": by_status,
        "by_pathway": by_pathway,
        "by_model_id": by_model,
    }
