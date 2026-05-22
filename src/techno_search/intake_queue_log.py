from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

INTAKE_QUEUE_SCHEMA_VERSION = "intake_queue_log_v1"

INTAKE_QUEUE_DISCLAIMER = (
    "Intake queue log entries are local planning placeholders only. "
    "An intake queue entry records that a data source has been identified for "
    "potential ingestion and tracks its queue position and intake status. "
    "Intake remains blocked until real data policy, provenance, licensing, "
    "labeling, and external-review requirements are satisfied. Intake queue "
    "entries do not authorize real data intake, live-provider access, "
    "authorize external submission, or constitute a detection claim."
)

ALLOWED_INTAKE_STATUSES = frozenset({
    "queued",
    "blocked",
    "intake_ready",
    "intake_complete",
    "cancelled",
})

ALLOWED_INTAKE_SOURCE_KINDS = frozenset({
    "radio_survey",
    "infrared_catalog",
    "archival_image",
    "spectral_archive",
    "unknown",
})


def _default_intake_queue_path() -> Path:
    return (
        Path(__file__).parent.parent.parent
        / "tests"
        / "fixtures"
        / "intake_queue_log.json"
    )


@dataclass
class IntakeQueueEntry:
    intake_id: str
    source_kind: str
    source_description: str
    status: str
    queue_position: int
    requested_by: str
    requested_utc: str
    blocking_reason: str | None = None
    intake_utc: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "intake_id": self.intake_id,
            "source_kind": self.source_kind,
            "source_description": self.source_description,
            "status": self.status,
            "queue_position": self.queue_position,
            "requested_by": self.requested_by,
            "requested_utc": self.requested_utc,
            "blocking_reason": self.blocking_reason,
            "intake_utc": self.intake_utc,
            "notes": self.notes,
        }


def load_intake_queue_entries(
    fixture_path: Path | None = None,
) -> list[IntakeQueueEntry]:
    path = fixture_path or _default_intake_queue_path()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = []
    for raw in data.get("intake_queue_entries", []):
        entries.append(
            IntakeQueueEntry(
                intake_id=raw["intake_id"],
                source_kind=raw["source_kind"],
                source_description=raw["source_description"],
                status=raw["status"],
                queue_position=raw["queue_position"],
                requested_by=raw["requested_by"],
                requested_utc=raw["requested_utc"],
                blocking_reason=raw.get("blocking_reason"),
                intake_utc=raw.get("intake_utc"),
                notes=raw.get("notes", ""),
            )
        )
    return entries


def intake_queue_summary(
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    entries = load_intake_queue_entries(fixture_path)
    by_status: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for e in entries:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_kind[e.source_kind] = by_kind.get(e.source_kind, 0) + 1
    blocked_count = by_status.get("blocked", 0)
    queued_count = by_status.get("queued", 0)
    ready_count = by_status.get("intake_ready", 0)
    complete_count = by_status.get("intake_complete", 0)
    return {
        "schema_version": INTAKE_QUEUE_SCHEMA_VERSION,
        "disclaimer": INTAKE_QUEUE_DISCLAIMER,
        "entry_count": len(entries),
        "blocked_count": blocked_count,
        "queued_count": queued_count,
        "ready_count": ready_count,
        "complete_count": complete_count,
        "by_status": by_status,
        "by_kind": by_kind,
    }
