from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CHANGE_REQUEST_LOG_SCHEMA_VERSION = "change_request_log_v1"

ALLOWED_CHANGE_REQUEST_KINDS = frozenset(
    {
        "emergency_change",
        "normal_change",
        "routine_change",
        "standard_change",
        "urgent_change",
    }
)

ALLOWED_CHANGE_REQUEST_STATUSES = frozenset(
    {
        "approved",
        "cancelled",
        "pending_review",
        "rejected",
    }
)

_DISCLAIMER = (
    "Change request entries are operational provenance records — a change request "
    "event does not modify candidate scores or pathway routing, does not authorize "
    "external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent / "tests" / "fixtures" / "change_request_log.json"
)


@dataclass(frozen=True)
class ChangeRequestEntry:
    entry_id: str
    change_kind: str
    status: str
    requestor_id: str
    description: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.change_kind not in ALLOWED_CHANGE_REQUEST_KINDS:
            raise ValueError(
                f"invalid change_kind {self.change_kind!r}; "
                f"allowed: {sorted(ALLOWED_CHANGE_REQUEST_KINDS)}"
            )
        if self.status not in ALLOWED_CHANGE_REQUEST_STATUSES:
            raise ValueError(
                f"invalid status {self.status!r}; "
                f"allowed: {sorted(ALLOWED_CHANGE_REQUEST_STATUSES)}"
            )


def load_change_request_entries(path: Path | None = None) -> list[ChangeRequestEntry]:
    fixture = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    return [
        ChangeRequestEntry(
            entry_id=e["entry_id"],
            change_kind=e["change_kind"],
            status=e["status"],
            requestor_id=e["requestor_id"],
            description=e["description"],
            notes=e.get("notes", ""),
        )
        for e in raw["entries"]
    ]


def change_request_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_change_request_entries(path)
    approved_count = sum(1 for e in entries if e.status == "approved")
    kind_counts = {k: 0 for k in ALLOWED_CHANGE_REQUEST_KINDS}
    status_counts = {s: 0 for s in ALLOWED_CHANGE_REQUEST_STATUSES}
    for e in entries:
        kind_counts[e.change_kind] += 1
        status_counts[e.status] += 1
    return {
        "schema_version": CHANGE_REQUEST_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "approved_count": approved_count,
        "kind_counts": kind_counts,
        "status_counts": status_counts,
        "disclaimer": _DISCLAIMER,
    }
