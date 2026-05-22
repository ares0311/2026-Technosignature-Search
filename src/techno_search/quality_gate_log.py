from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

QUALITY_GATE_SCHEMA_VERSION = "quality_gate_log_v1"

QUALITY_GATE_DISCLAIMER = (
    "Quality gate log entries are operational provenance records only. "
    "A quality gate entry records the result of a consistency or completeness "
    "check applied to a candidate during pipeline execution. Gate results are "
    "scheduling coordination aids and do not modify candidate scores, do not "
    "affect pathway routing, do not authorize external submission, and do not "
    "constitute a detection claim."
)

ALLOWED_GATE_KINDS = frozenset({
    "score_threshold",
    "provenance_completeness",
    "rfi_screen",
    "catalog_check",
    "review_coverage",
})

ALLOWED_GATE_RESULTS = frozenset({
    "pass",
    "fail",
    "warn",
    "not_applicable",
})


def _default_quality_gate_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests" / "fixtures" / "quality_gate_log.json"
    )


@dataclass
class QualityGateEntry:
    gate_id: str
    candidate_id: str
    gate_kind: str
    result: str
    checked_by: str
    checked_utc: str
    score_at_check: float | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "candidate_id": self.candidate_id,
            "gate_kind": self.gate_kind,
            "result": self.result,
            "checked_by": self.checked_by,
            "checked_utc": self.checked_utc,
            "score_at_check": self.score_at_check,
            "notes": self.notes,
        }


def load_quality_gate_entries(
    fixture_path: Path | None = None,
) -> list[QualityGateEntry]:
    path = fixture_path or _default_quality_gate_path()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = []
    for raw in data.get("quality_gate_entries", []):
        entries.append(QualityGateEntry(
            gate_id=raw["gate_id"],
            candidate_id=raw["candidate_id"],
            gate_kind=raw["gate_kind"],
            result=raw["result"],
            checked_by=raw["checked_by"],
            checked_utc=raw["checked_utc"],
            score_at_check=raw.get("score_at_check"),
            notes=raw.get("notes", ""),
        ))
    return entries


def quality_gate_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_quality_gate_entries(fixture_path)
    by_result: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for e in entries:
        by_result[e.result] = by_result.get(e.result, 0) + 1
        by_kind[e.gate_kind] = by_kind.get(e.gate_kind, 0) + 1
    return {
        "schema_version": QUALITY_GATE_SCHEMA_VERSION,
        "disclaimer": QUALITY_GATE_DISCLAIMER,
        "entry_count": len(entries),
        "pass_count": by_result.get("pass", 0),
        "fail_count": by_result.get("fail", 0),
        "warn_count": by_result.get("warn", 0),
        "not_applicable_count": by_result.get("not_applicable", 0),
        "by_result": by_result,
        "by_kind": by_kind,
    }
