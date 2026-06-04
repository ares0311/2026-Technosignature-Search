from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

KNOWLEDGE_MANAGEMENT_LOG_SCHEMA_VERSION = "knowledge_management_log_v1"

ALLOWED_KNOWLEDGE_MANAGEMENT_KINDS = frozenset({
    "faq",
    "how_to",
    "known_error",
    "reference_document",
    "troubleshooting_guide",
})

ALLOWED_KNOWLEDGE_MANAGEMENT_STATUSES = frozenset({
    "approved",
    "draft",
    "published",
    "retired",
})

_DISCLAIMER = (
    "Knowledge management entries are operational provenance records — a knowledge"
    " management event does not modify candidate scores or pathway routing, does not"
    " authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "knowledge_management_log.json"
)


@dataclass(frozen=True)
class KnowledgeManagementEntry:
    entry_id: str
    knowledge_kind: str
    status: str
    actor_id: str
    resource_id: str
    timestamp_utc: str
    notes: str

    def __post_init__(self) -> None:
        if self.knowledge_kind not in ALLOWED_KNOWLEDGE_MANAGEMENT_KINDS:
            raise ValueError(
                f"knowledge_kind {self.knowledge_kind!r} not in"
                f" {sorted(ALLOWED_KNOWLEDGE_MANAGEMENT_KINDS)}"
            )
        if self.status not in ALLOWED_KNOWLEDGE_MANAGEMENT_STATUSES:
            raise ValueError(
                f"status {self.status!r} not in"
                f" {sorted(ALLOWED_KNOWLEDGE_MANAGEMENT_STATUSES)}"
            )


def load_knowledge_management_entries(
    fixture_path: Path | None = None,
) -> list[KnowledgeManagementEntry]:
    path = fixture_path or _DEFAULT_FIXTURE
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        KnowledgeManagementEntry(
            entry_id=e["entry_id"],
            knowledge_kind=e["knowledge_kind"],
            status=e["status"],
            actor_id=e["actor_id"],
            resource_id=e["resource_id"],
            timestamp_utc=e["timestamp_utc"],
            notes=e.get("notes", ""),
        )
        for e in data["entries"]
    ]


def knowledge_management_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_knowledge_management_entries(fixture_path)
    published_count = sum(1 for e in entries if e.status == "published")
    return {
        "schema_version": KNOWLEDGE_MANAGEMENT_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "published_count": published_count,
        "disclaimer": _DISCLAIMER,
    }
