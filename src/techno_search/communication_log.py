from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COMMUNICATION_LOG_SCHEMA_VERSION = "communication_log_v1"

ALLOWED_COMMUNICATION_KINDS = frozenset(
    {
        "broadcast",
        "email_notification",
        "escalation_notice",
        "status_update",
        "team_announcement",
    }
)

ALLOWED_COMMUNICATION_STATUSES = frozenset(
    {
        "delivered",
        "draft",
        "failed",
        "sent",
    }
)

_DISCLAIMER = (
    "Communication entries are operational provenance records — a communication "
    "event does not modify candidate scores or pathway routing, does not authorize "
    "external submission, and does not constitute a detection claim."
)

_DEFAULT_FIXTURE = (
    Path(__file__).parent.parent.parent / "tests" / "fixtures" / "communication_log.json"
)


@dataclass(frozen=True)
class CommunicationEntry:
    entry_id: str
    communication_kind: str
    status: str
    sender_id: str
    subject: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.communication_kind not in ALLOWED_COMMUNICATION_KINDS:
            raise ValueError(
                f"invalid communication_kind {self.communication_kind!r}; "
                f"allowed: {sorted(ALLOWED_COMMUNICATION_KINDS)}"
            )
        if self.status not in ALLOWED_COMMUNICATION_STATUSES:
            raise ValueError(
                f"invalid status {self.status!r}; "
                f"allowed: {sorted(ALLOWED_COMMUNICATION_STATUSES)}"
            )


def load_communication_entries(path: Path | None = None) -> list[CommunicationEntry]:
    fixture = path if path is not None else _DEFAULT_FIXTURE
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    return [
        CommunicationEntry(
            entry_id=e["entry_id"],
            communication_kind=e["communication_kind"],
            status=e["status"],
            sender_id=e["sender_id"],
            subject=e["subject"],
            notes=e.get("notes", ""),
        )
        for e in raw["entries"]
    ]


def communication_summary(path: Path | None = None) -> dict[str, Any]:
    entries = load_communication_entries(path)
    delivered_count = sum(1 for e in entries if e.status == "delivered")
    kind_counts = {k: 0 for k in ALLOWED_COMMUNICATION_KINDS}
    status_counts = {s: 0 for s in ALLOWED_COMMUNICATION_STATUSES}
    for e in entries:
        kind_counts[e.communication_kind] += 1
        status_counts[e.status] += 1
    return {
        "schema_version": COMMUNICATION_LOG_SCHEMA_VERSION,
        "entry_count": len(entries),
        "delivered_count": delivered_count,
        "kind_counts": kind_counts,
        "status_counts": status_counts,
        "disclaimer": _DISCLAIMER,
    }
