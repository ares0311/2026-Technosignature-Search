from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DOCUMENT_MANAGEMENT_LOG_SCHEMA_VERSION = "document_management_log_v1"

ALLOWED_DOCUMENT_MANAGEMENT_KINDS = frozenset(
    {
        "approval",
        "archival",
        "creation",
        "review",
        "revision",
    }
)

ALLOWED_DOCUMENT_MANAGEMENT_STATUSES = frozenset(
    {
        "active",
        "archived",
        "draft",
        "superseded",
    }
)

_DISCLAIMER = (
    "Document management entries are operational provenance records — a document "
    "management event does not modify candidate scores or pathway routing, does not "
    "authorize external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent
    / "tests"
    / "fixtures"
    / "document_management_log.json"
)


@dataclass(frozen=True)
class DocumentManagementEntry:
    entry_id: str
    document_kind: str
    status: str
    document_id: str
    description: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.document_kind not in ALLOWED_DOCUMENT_MANAGEMENT_KINDS:
            raise ValueError(
                f"invalid document_kind {self.document_kind!r}; "
                f"allowed: {sorted(ALLOWED_DOCUMENT_MANAGEMENT_KINDS)}"
            )
        if self.status not in ALLOWED_DOCUMENT_MANAGEMENT_STATUSES:
            raise ValueError(
                f"invalid status {self.status!r}; "
                f"allowed: {sorted(ALLOWED_DOCUMENT_MANAGEMENT_STATUSES)}"
            )


def load_document_management_entries(
    path: Path | None = None,
) -> list[DocumentManagementEntry]:
    fixture = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    return [
        DocumentManagementEntry(
            entry_id=e["entry_id"],
            document_kind=e["document_kind"],
            status=e["status"],
            document_id=e["document_id"],
            description=e["description"],
            notes=e.get("notes", ""),
        )
        for e in raw["entries"]
    ]


def document_management_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_document_management_entries(path)
    active_count = sum(1 for e in entries if e.status == "active")
    kind_counts = {k: 0 for k in ALLOWED_DOCUMENT_MANAGEMENT_KINDS}
    status_counts = {s: 0 for s in ALLOWED_DOCUMENT_MANAGEMENT_STATUSES}
    for e in entries:
        kind_counts[e.document_kind] += 1
        status_counts[e.status] += 1
    return {
        "schema_version": DOCUMENT_MANAGEMENT_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "active_count": active_count,
        "kind_counts": kind_counts,
        "status_counts": status_counts,
        "disclaimer": _DISCLAIMER,
    }
